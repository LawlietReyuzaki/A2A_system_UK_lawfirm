"""
Orchestrator Agent

The central coordinator for the A2A multi-agent system.
Responsible for:
- Receiving incoming requests
- Determining which agents to invoke
- Coordinating multi-agent workflows
- Aggregating results
- Managing escalations
"""

import time
import asyncio
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid

logger = logging.getLogger("brightlaw.orchestrator")

from core.a2a_protocol import (
    BaseAgent, AgentCard, AgentCapability, TaskRequest, TaskResponse,
    TaskState, TaskArtifact, A2AMessage, MessageType, AgentRegistry, MessageBus
)
from core.llm_client import GeminiClient, AgentLLM


class WorkflowType(str, Enum):
    EMAIL_PROCESSING = "email_processing"
    DOCUMENT_PROCESSING = "document_processing"
    NEW_CLIENT_INTAKE = "new_client_intake"
    DEADLINE_EXTRACTION = "deadline_extraction"
    CUSTOM = "custom"


class OrchestratorInput(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_type: str
    input_data: Dict[str, Any]
    priority: str = "normal"
    require_human_approval: bool = False


class WorkflowStep(BaseModel):
    step_id: str
    agent_id: str
    task_type: str
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int = 0


class WorkflowResult(BaseModel):
    request_id: str
    workflow_type: str
    status: str
    steps: List[WorkflowStep]
    final_result: Dict[str, Any]
    total_duration_ms: int
    agents_used: List[str]
    requires_human_review: bool
    escalation_reasons: List[str] = Field(default_factory=list)


SYSTEM_PROMPT = """You are the Orchestrator Agent for BrightLaw's AI automation platform.

Your role is to coordinate multiple specialized agents to handle complex legal workflows.

AVAILABLE AGENTS:
1. email_triage_agent - Classifies and routes incoming emails
2. document_classification_agent - Classifies legal documents
3. client_intake_agent - Handles new client onboarding
4. deadline_tracker_agent - Extracts and tracks deadlines
5. response_generator_agent - Generates response drafts

WORKFLOW PATTERNS:

EMAIL_PROCESSING:
1. email_triage_agent: Classify and extract
2. IF new_client → client_intake_agent
3. IF document_attached → document_classification_agent
4. IF deadline_mentioned → deadline_tracker_agent
5. response_generator_agent: Draft response

DOCUMENT_PROCESSING:
1. document_classification_agent: Classify document
2. deadline_tracker_agent: Extract deadlines
3. Return classification and deadlines

NEW_CLIENT_INTAKE:
1. client_intake_agent: Full intake process
2. IF documents_provided → document_classification_agent
3. response_generator_agent: Generate engagement letter

DEADLINE_EXTRACTION:
1. deadline_tracker_agent: Extract all deadlines
2. Return analysis and reminders

Always prioritize critical items and escalate when confidence is low.
"""


class OrchestratorAgent(BaseAgent):
    def __init__(self, llm_client: GeminiClient, registry: AgentRegistry):
        super().__init__(
            agent_id="orchestrator_agent",
            name="Orchestrator Agent",
            llm_client=llm_client
        )
        self.agent_llm = AgentLLM(llm_client, self.name, SYSTEM_PROMPT)
        self.registry = registry
        self.message_bus = MessageBus(registry)
    
    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description="Central orchestrator that coordinates multi-agent workflows",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="orchestrate_workflow",
                    description="Execute a complete workflow across multiple agents",
                    input_schema=OrchestratorInput.model_json_schema(),
                    output_schema=WorkflowResult.model_json_schema(),
                    estimated_duration_seconds=60,
                    requires_human_review=True
                ),
                AgentCapability(
                    name="route_request",
                    description="Route a single request to the appropriate agent",
                    input_schema={"request_type": "string", "data": "object"},
                    output_schema=TaskResponse.model_json_schema(),
                    estimated_duration_seconds=30,
                    requires_human_review=False
                )
            ],
            supported_input_types=["workflow_request", "generic_request"],
            supported_output_types=["workflow_result", "task_response"]
        )
    
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        start_time = time.time()
        
        try:
            if task.task_type == "orchestrate_workflow":
                input_data = OrchestratorInput(**task.input_data)
                logger.info(
                    "orchestrate_start request_id=%s workflow_type=%s",
                    input_data.request_id,
                    input_data.workflow_type,
                )
                result = await self._orchestrate_workflow(input_data)
                logger.info(
                    "orchestrate_end request_id=%s workflow_type=%s status=%s total_duration_ms=%s agents_used=%s requires_human_review=%s escalations=%s",
                    result.request_id,
                    result.workflow_type,
                    result.status,
                    result.total_duration_ms,
                    ",".join(result.agents_used),
                    result.requires_human_review,
                    "; ".join(result.escalation_reasons) if result.escalation_reasons else "",
                )
                artifact = TaskArtifact(
                    artifact_type="workflow_result",
                    content=result.model_dump()
                )
                
                return TaskResponse(
                    task_id=task.task_id,
                    state=TaskState.COMPLETED,
                    result=result.model_dump(),
                    artifacts=[artifact],
                    confidence_score=0.9,
                    requires_human_review=result.requires_human_review,
                    escalation_reason="; ".join(result.escalation_reasons) if result.escalation_reasons else None,
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
            
            elif task.task_type == "route_request":
                result = await self._route_single_request(task.input_data)
                return result
            
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                state=TaskState.FAILED,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def _orchestrate_workflow(self, input_data: OrchestratorInput) -> WorkflowResult:
        """Execute a complete workflow"""
        steps = []
        agents_used = []
        escalation_reasons = []
        requires_review = False
        final_result = {}
        
        workflow_start = time.time()
        
        if input_data.workflow_type == WorkflowType.EMAIL_PROCESSING.value:
            steps, final_result, escalation_reasons = await self._email_processing_workflow(
                input_data.request_id,
                input_data.input_data
            )
        elif input_data.workflow_type == WorkflowType.DOCUMENT_PROCESSING.value:
            steps, final_result, escalation_reasons = await self._document_processing_workflow(
                input_data.request_id,
                input_data.input_data
            )
        elif input_data.workflow_type == WorkflowType.NEW_CLIENT_INTAKE.value:
            steps, final_result, escalation_reasons = await self._client_intake_workflow(
                input_data.request_id,
                input_data.input_data
            )
        elif input_data.workflow_type == WorkflowType.DEADLINE_EXTRACTION.value:
            steps, final_result, escalation_reasons = await self._deadline_extraction_workflow(
                input_data.request_id,
                input_data.input_data
            )
        else:
            raise ValueError(f"Unknown workflow type: {input_data.workflow_type}")
        
        # Collect agents used
        agents_used = list(set(step.agent_id for step in steps))
        
        # Check if any step requires human review
        requires_review = any(
            step.result and step.result.get("requires_human_review", False)
            for step in steps
        ) or len(escalation_reasons) > 0
        
        total_duration = int((time.time() - workflow_start) * 1000)
        
        return WorkflowResult(
            request_id=input_data.request_id,
            workflow_type=input_data.workflow_type,
            status="completed" if all(s.status == "completed" for s in steps) else "partial",
            steps=steps,
            final_result=final_result,
            total_duration_ms=total_duration,
            agents_used=agents_used,
            requires_human_review=requires_review,
            escalation_reasons=escalation_reasons
        )
    
    async def _invoke_agent(
        self,
        request_id: str,
        agent_id: str,
        task_type: str,
        input_data: Dict[str, Any]
    ) -> tuple[WorkflowStep, TaskResponse]:
        """Invoke a single agent and return the step and response"""
        step_id = f"step_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        logger.info(
            "step_start request_id=%s step_id=%s agent_id=%s task_type=%s",
            request_id,
            step_id,
            agent_id,
            task_type,
        )
        
        task = TaskRequest(
            task_type=task_type,
            input_data=input_data
        )
        
        message = A2AMessage(
            message_type=MessageType.TASK_REQUEST,
            source_agent_id=self.agent_id,
            target_agent_id=agent_id,
            payload=task.model_dump()
        )
        
        try:
            response_msg = await self.message_bus.send(message)
            response = TaskResponse(**response_msg.payload)
            
            step = WorkflowStep(
                step_id=step_id,
                agent_id=agent_id,
                task_type=task_type,
                status="completed" if response.state == TaskState.COMPLETED else "failed",
                result=response.result,
                error=response.error,
                duration_ms=int((time.time() - start_time) * 1000)
            )

            logger.info(
                "step_end request_id=%s step_id=%s agent_id=%s task_type=%s status=%s duration_ms=%s requires_human_review=%s escalation_reason=%s",
                request_id,
                step_id,
                agent_id,
                task_type,
                step.status,
                step.duration_ms,
                response.requires_human_review,
                response.escalation_reason or "",
            )
            
            return step, response
            
        except Exception as e:
            step = WorkflowStep(
                step_id=step_id,
                agent_id=agent_id,
                task_type=task_type,
                status="failed",
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )
            logger.exception(
                "step_error request_id=%s step_id=%s agent_id=%s task_type=%s error=%s",
                request_id,
                step_id,
                agent_id,
                task_type,
                str(e),
            )
            return step, None
    
    async def _email_processing_workflow(
        self,
        request_id: str,
        input_data: Dict[str, Any]
    ) -> tuple[List[WorkflowStep], Dict[str, Any], List[str]]:
        """Process an incoming email through the full workflow"""
        steps = []
        escalations = []
        final_result = {}
        
        # Step 1: Email Triage
        step1, response1 = await self._invoke_agent(
            request_id,
            "email_triage_agent",
            "email_full_triage",
            input_data
        )
        steps.append(step1)
        
        if response1 and response1.result:
            final_result["triage"] = response1.result
            
            # Check for escalations
            if response1.requires_human_review:
                escalations.append(f"Email triage: {response1.escalation_reason}")
            
            # Step 2: If new client intent, trigger intake
            classification = response1.result.get("classification", {})
            if classification.get("intent") == "new_matter":
                intake_data = {
                    "inquiry_id": input_data.get("email_id", "unknown"),
                    "source": "email",
                    "client_name": response1.result.get("extracted_data", {}).get("client_name", "Unknown"),
                    "matter_description": input_data.get("body", ""),
                    "contact_email": input_data.get("sender_email", "")
                }
                
                step2, response2 = await self._invoke_agent(
                    request_id,
                    "client_intake_agent",
                    "full_intake",
                    intake_data
                )
                steps.append(step2)
                if response2 and response2.result:
                    final_result["intake"] = response2.result
                    if response2.requires_human_review:
                        escalations.append(f"Client intake: {response2.escalation_reason}")
            
            # Step 3: Check for deadlines in the email
            deadline_data = {
                "source_id": input_data.get("email_id", "unknown"),
                "source_type": "email",
                "content": input_data.get("body", "")
            }
            
            step3, response3 = await self._invoke_agent(
                request_id,
                "deadline_tracker_agent",
                "deadline_extraction",
                deadline_data
            )
            steps.append(step3)
            if response3 and response3.result:
                final_result["deadlines"] = response3.result
            
            # Step 4: Generate response draft
            response_data = {
                "inquiry_id": input_data.get("email_id", "unknown"),
                "original_message": input_data.get("body", ""),
                "sender_name": input_data.get("sender_name", "Client"),
                "sender_email": input_data.get("sender_email", ""),
                "context": {
                    "intent": classification.get("intent"),
                    "urgency": classification.get("urgency"),
                    "practice_area": classification.get("practice_area")
                }
            }
            
            step4, response4 = await self._invoke_agent(
                request_id,
                "response_generator_agent",
                "generate_response",
                response_data
            )
            steps.append(step4)
            if response4 and response4.result:
                final_result["draft_response"] = response4.result
        
        return steps, final_result, escalations
    
    async def _document_processing_workflow(
        self,
        request_id: str,
        input_data: Dict[str, Any]
    ) -> tuple[List[WorkflowStep], Dict[str, Any], List[str]]:
        """Process a document through classification and deadline extraction"""
        steps = []
        escalations = []
        final_result = {}
        
        # Step 1: Document Classification
        step1, response1 = await self._invoke_agent(
            request_id,
            "document_classification_agent",
            "document_full_classification",
            input_data
        )
        steps.append(step1)
        
        if response1 and response1.result:
            final_result["classification"] = response1.result
            
            if response1.requires_human_review:
                escalations.append(f"Document classification: {response1.escalation_reason}")
            
            # Step 2: Extract deadlines from document
            deadline_data = {
                "source_id": input_data.get("document_id", "unknown"),
                "source_type": "document",
                "content": input_data.get("content", "")
            }
            
            step2, response2 = await self._invoke_agent(
                request_id,
                "deadline_tracker_agent",
                "full_deadline_analysis",
                deadline_data
            )
            steps.append(step2)
            if response2 and response2.result:
                final_result["deadlines"] = response2.result
        
        return steps, final_result, escalations
    
    async def _client_intake_workflow(
        self,
        request_id: str,
        input_data: Dict[str, Any]
    ) -> tuple[List[WorkflowStep], Dict[str, Any], List[str]]:
        """Process a new client intake"""
        steps = []
        escalations = []
        final_result = {}
        
        # Step 1: Full intake process
        step1, response1 = await self._invoke_agent(
            request_id,
            "client_intake_agent",
            "full_intake",
            input_data
        )
        steps.append(step1)
        
        if response1 and response1.result:
            final_result["intake"] = response1.result
            
            if response1.requires_human_review:
                escalations.append(f"Client intake: {response1.escalation_reason}")
            
            # Step 2: Generate engagement letter response
            if response1.result.get("can_proceed", False):
                response_data = {
                    "inquiry_id": input_data.get("inquiry_id", "unknown"),
                    "original_message": input_data.get("matter_description", ""),
                    "sender_name": input_data.get("client_name", "Client"),
                    "sender_email": input_data.get("contact_email", ""),
                    "context": {
                        "type": "engagement_letter",
                        "practice_area": response1.result.get("practice_area"),
                        "fee_estimate": response1.result.get("fee_estimate")
                    },
                    "tone": "formal"
                }
                
                step2, response2 = await self._invoke_agent(
                    request_id,
                    "response_generator_agent",
                    "generate_response",
                    response_data
                )
                steps.append(step2)
                if response2 and response2.result:
                    final_result["engagement_response"] = response2.result
        
        return steps, final_result, escalations
    
    async def _deadline_extraction_workflow(
        self,
        request_id: str,
        input_data: Dict[str, Any]
    ) -> tuple[List[WorkflowStep], Dict[str, Any], List[str]]:
        """Extract and analyze deadlines"""
        steps = []
        escalations = []
        final_result = {}
        
        step1, response1 = await self._invoke_agent(
            request_id,
            "deadline_tracker_agent",
            "full_deadline_analysis",
            input_data
        )
        steps.append(step1)
        
        if response1 and response1.result:
            final_result["deadline_analysis"] = response1.result
            
            # Check for urgent warnings
            warnings = response1.result.get("warnings", [])
            if any("OVERDUE" in w or "URGENT" in w for w in warnings):
                escalations.append(f"Deadline warnings: {'; '.join(warnings[:3])}")
        
        return steps, final_result, escalations
    
    async def _route_single_request(self, input_data: Dict[str, Any]) -> TaskResponse:
        """Route a single request to the appropriate agent"""
        request_type = input_data.get("request_type", "")
        data = input_data.get("data", {})
        
        # Determine which agent to use based on request type
        routing_map = {
            "email": ("email_triage_agent", "email_full_triage"),
            "document": ("document_classification_agent", "document_full_classification"),
            "intake": ("client_intake_agent", "full_intake"),
            "deadline": ("deadline_tracker_agent", "full_deadline_analysis"),
            "response": ("response_generator_agent", "generate_response")
        }
        
        if request_type not in routing_map:
            raise ValueError(f"Unknown request type: {request_type}")
        
        agent_id, task_type = routing_map[request_type]
        _, response = await self._invoke_agent(agent_id, task_type, data)
        
        return response
