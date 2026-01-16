"""
Deadline Tracker Agent

Responsible for:
- Extracting deadlines from documents and emails
- Identifying legal limitation periods
- Creating calendar reminders
- Monitoring approaching deadlines
- Generating deadline reports
"""

import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import uuid

import sys
sys.path.insert(0, '/home/claude/brightlaw-a2a')

from core.a2a_protocol import (
    BaseAgent, AgentCard, AgentCapability, TaskRequest, TaskResponse,
    TaskState, TaskArtifact
)
from core.llm_client import GeminiClient, AgentLLM


class DateInput(BaseModel):
    source_id: str
    source_type: str
    content: str
    matter_id: Optional[str] = None
    reference_date: Optional[str] = None
    jurisdiction: str = "England and Wales"


class ExtractedDeadline(BaseModel):
    deadline_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    date: str
    date_type: str
    description: str
    source_text: str
    confidence: float
    is_business_days: bool = False
    is_approximate: bool = False
    related_party: Optional[str] = None
    consequence_of_missing: Optional[str] = None


class ReminderSchedule(BaseModel):
    deadline_id: str
    reminders: List[Dict[str, Any]]


class DeadlineAnalysis(BaseModel):
    total_deadlines: int
    critical_count: int
    overdue_count: int
    upcoming_7_days: int
    upcoming_30_days: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]


class DeadlineExtractionResult(BaseModel):
    source_id: str
    deadlines: List[ExtractedDeadline]
    reminder_schedules: List[ReminderSchedule]
    analysis: DeadlineAnalysis
    warnings: List[str] = Field(default_factory=list)
    calendar_entries: List[Dict[str, Any]] = Field(default_factory=list)


SYSTEM_PROMPT = """You are the Deadline Tracker Agent for BrightLaw, a UK legal services firm.

LIMITATION PERIODS (UK):
- Contract claims: 6 years from breach
- Tort claims: 6 years from damage  
- Personal injury: 3 years from injury/knowledge
- Employment tribunal: 3 months less 1 day from dismissal
- Judicial review: 3 months from decision

DEADLINE TYPES:
- limitation: Legal limitation periods (CRITICAL)
- court: Court-imposed deadlines (CRITICAL)
- contractual: Contract deadlines (HIGH)
- regulatory: Filing deadlines (HIGH)
- internal: Internal deadlines (MEDIUM)
- client: Client-requested (MEDIUM)

Always extract dates in YYYY-MM-DD format.
Flag any dates that seem incorrect or inconsistent.
"""


class DeadlineTrackerAgent(BaseAgent):
    def __init__(self, llm_client: GeminiClient):
        super().__init__(
            agent_id="deadline_tracker_agent",
            name="Deadline Tracker Agent",
            llm_client=llm_client
        )
        self.agent_llm = AgentLLM(llm_client, self.name, SYSTEM_PROMPT)
        self.today = datetime.now().strftime("%Y-%m-%d")
    
    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description="Extracts deadlines, calculates limitation periods, generates reminders",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="deadline_extraction",
                    description="Extract all deadlines from document content",
                    input_schema=DateInput.model_json_schema(),
                    output_schema={"type": "array"},
                    estimated_duration_seconds=15,
                    requires_human_review=True
                ),
                AgentCapability(
                    name="full_deadline_analysis",
                    description="Complete deadline extraction with reminders",
                    input_schema=DateInput.model_json_schema(),
                    output_schema=DeadlineExtractionResult.model_json_schema(),
                    estimated_duration_seconds=30,
                    requires_human_review=True
                )
            ],
            supported_input_types=["document_text", "email"],
            supported_output_types=["deadlines", "reminders", "calendar_entries"]
        )
    
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        start_time = time.time()
        
        try:
            date_input = DateInput(**task.input_data)
            
            if task.task_type == "deadline_extraction":
                deadlines = await self._extract_deadlines(date_input)
                result = {"deadlines": [d.model_dump() for d in deadlines]}
                artifact = TaskArtifact(artifact_type="deadlines", content=result)
                
            elif task.task_type == "full_deadline_analysis":
                extraction_result = await self._full_analysis(date_input)
                result = extraction_result.model_dump()
                artifact = TaskArtifact(artifact_type="deadline_analysis", content=result)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            return TaskResponse(
                task_id=task.task_id,
                state=TaskState.COMPLETED,
                result=result,
                artifacts=[artifact],
                confidence_score=0.85,
                requires_human_review=True,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                state=TaskState.FAILED,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def _extract_deadlines(self, input_data: DateInput) -> List[ExtractedDeadline]:
        reference_date = input_data.reference_date or self.today
        
        prompt = f"""Extract all deadlines from this content:

Source: {input_data.source_type}
Reference Date: {reference_date}
Today: {self.today}

Content:
{input_data.content[:4000]}

Return JSON array:
[{{"deadline_id": "dl_001", "date": "YYYY-MM-DD", "date_type": "limitation|court|contractual|regulatory|internal|client", "description": "...", "source_text": "exact quote", "confidence": 0.0-1.0, "is_business_days": false, "is_approximate": false, "related_party": null, "consequence_of_missing": "..."}}]

Return [] if no deadlines found."""

        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.1
        )
        
        data = response.structured_output
        if isinstance(data, dict):
            data = data.get("deadlines", [])
        return [ExtractedDeadline(**d) for d in (data or [])]
    
    async def _full_analysis(self, input_data: DateInput) -> DeadlineExtractionResult:
        deadlines = await self._extract_deadlines(input_data)
        
        # Generate reminder schedules
        schedules = []
        for dl in deadlines:
            schedule = self._generate_reminder_schedule(dl)
            schedules.append(schedule)
        
        # Analyze deadlines
        analysis = self._analyze_deadlines(deadlines)
        
        # Generate calendar entries
        calendar_entries = self._generate_calendar_entries(deadlines)
        
        # Check for warnings
        warnings = self._check_warnings(deadlines)
        
        return DeadlineExtractionResult(
            source_id=input_data.source_id,
            deadlines=deadlines,
            reminder_schedules=schedules,
            analysis=analysis,
            warnings=warnings,
            calendar_entries=calendar_entries
        )
    
    def _generate_reminder_schedule(self, deadline: ExtractedDeadline) -> ReminderSchedule:
        reminders = []
        try:
            dl_date = datetime.strptime(deadline.date, "%Y-%m-%d")
            
            # Critical deadlines get more reminders
            if deadline.date_type in ["limitation", "court"]:
                intervals = [90, 30, 14, 7, 3, 1]
            elif deadline.date_type in ["contractual", "regulatory"]:
                intervals = [30, 14, 7, 1]
            else:
                intervals = [14, 7]
            
            for days in intervals:
                reminder_date = dl_date - timedelta(days=days)
                if reminder_date > datetime.now():
                    reminders.append({
                        "date": reminder_date.strftime("%Y-%m-%d"),
                        "days_before": days,
                        "message": f"Reminder: {deadline.description} due in {days} days"
                    })
        except:
            pass
        
        return ReminderSchedule(deadline_id=deadline.deadline_id, reminders=reminders)
    
    def _analyze_deadlines(self, deadlines: List[ExtractedDeadline]) -> DeadlineAnalysis:
        today = datetime.now()
        by_type = {}
        by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        overdue = 0
        upcoming_7 = 0
        upcoming_30 = 0
        critical = 0
        
        for dl in deadlines:
            by_type[dl.date_type] = by_type.get(dl.date_type, 0) + 1
            
            try:
                dl_date = datetime.strptime(dl.date, "%Y-%m-%d")
                days_until = (dl_date - today).days
                
                if days_until < 0:
                    overdue += 1
                elif days_until <= 7:
                    upcoming_7 += 1
                elif days_until <= 30:
                    upcoming_30 += 1
                
                if dl.date_type in ["limitation", "court"]:
                    critical += 1
                    by_priority["critical"] += 1
                elif dl.date_type in ["contractual", "regulatory"]:
                    by_priority["high"] += 1
                else:
                    by_priority["medium"] += 1
            except:
                pass
        
        return DeadlineAnalysis(
            total_deadlines=len(deadlines),
            critical_count=critical,
            overdue_count=overdue,
            upcoming_7_days=upcoming_7,
            upcoming_30_days=upcoming_30,
            by_type=by_type,
            by_priority=by_priority
        )
    
    def _generate_calendar_entries(self, deadlines: List[ExtractedDeadline]) -> List[Dict]:
        entries = []
        for dl in deadlines:
            entries.append({
                "title": f"DEADLINE: {dl.description}",
                "date": dl.date,
                "type": dl.date_type,
                "all_day": True,
                "description": f"Source: {dl.source_text}\nConsequence: {dl.consequence_of_missing or 'Not specified'}"
            })
        return entries
    
    def _check_warnings(self, deadlines: List[ExtractedDeadline]) -> List[str]:
        warnings = []
        today = datetime.now()
        
        for dl in deadlines:
            try:
                dl_date = datetime.strptime(dl.date, "%Y-%m-%d")
                days_until = (dl_date - today).days
                
                if days_until < 0:
                    warnings.append(f"OVERDUE: {dl.description} was due {dl.date}")
                elif days_until <= 7 and dl.date_type in ["limitation", "court"]:
                    warnings.append(f"URGENT: {dl.description} due in {days_until} days")
                
                if dl.confidence < 0.7:
                    warnings.append(f"LOW CONFIDENCE: {dl.description} - verify date {dl.date}")
            except:
                pass
        
        return warnings
