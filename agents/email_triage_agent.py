"""
Email Triage Agent

Responsible for:
- Classifying incoming emails by intent, urgency, and practice area
- Extracting key information from emails
- Generating response suggestions
- Routing to appropriate downstream agents

Task Flow:
1. Receive raw email data (subject, body, sender, attachments)
2. Classify intent (inquiry type, urgency level, practice area)
3. Extract key entities (client name, matter reference, dates, actions requested)
4. Determine if this is from existing client or new inquiry
5. Generate preliminary response draft if applicable
6. Route to appropriate next agent or human queue
"""

import time
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from core.a2a_protocol import (
    BaseAgent, AgentCard, AgentCapability, TaskRequest, TaskResponse,
    TaskState, TaskArtifact, Priority
)
from core.llm_client import GeminiClient, AgentLLM


# =============================================================================
# Email Triage Data Models
# =============================================================================

def _coerce_json_object(value: Any, *, context: str) -> dict:
    """
    Gemini JSON mode sometimes returns a list (e.g. `[ {...} ]`) instead of an object.
    This helper normalizes common variants into a dict for pydantic `Model(**dict)` usage.
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        if len(value) == 1 and isinstance(value[0], dict):
            return value[0]
        raise ValueError(f"{context}: expected JSON object, got list (len={len(value)})")
    raise ValueError(f"{context}: expected JSON object, got {type(value).__name__}")


class EmailInput(BaseModel):
    """Input schema for email triage"""
    email_id: str
    sender_email: str
    sender_name: Optional[str] = None
    subject: str
    body: str
    received_at: str
    attachments: List[str] = Field(default_factory=list)
    is_reply: bool = False
    thread_id: Optional[str] = None


class EmailClassification(BaseModel):
    """Classification result for an email"""
    intent: str  # status_inquiry, document_request, appointment, complaint, new_matter, etc.
    urgency: str  # critical, high, normal, low
    practice_area: str  # corporate, employment, property, general
    sentiment: str  # positive, neutral, negative, urgent
    confidence: float
    requires_immediate_attention: bool
    reasoning: str


class ExtractedEmailData(BaseModel):
    """Extracted entities from email"""
    client_name: Optional[str] = None
    matter_reference: Optional[str] = None
    dates_mentioned: List[str] = Field(default_factory=list)
    action_requested: Optional[str] = None
    key_entities: List[str] = Field(default_factory=list)
    questions_asked: List[str] = Field(default_factory=list)


class EmailTriageResult(BaseModel):
    """Complete triage result"""
    classification: EmailClassification
    extracted_data: ExtractedEmailData
    suggested_response: Optional[str] = None
    routing_recommendation: str
    next_agent: Optional[str] = None
    human_review_required: bool = False
    human_review_reason: Optional[str] = None


# =============================================================================
# Email Triage Agent
# =============================================================================

SYSTEM_PROMPT = """You are the Email Triage Agent for BrightLaw, a UK legal services firm.

Your responsibilities:
1. CLASSIFY emails by intent, urgency, and practice area
2. EXTRACT key information like client names, matter references, dates, and requested actions  
3. DETERMINE the appropriate routing for each email
4. GENERATE response suggestions when appropriate

Classification Guidelines:

INTENT TYPES:
- status_inquiry: Client asking about case progress, updates, next steps
- document_request: Request for documents, contracts, or file copies
- appointment: Scheduling meetings, calls, or consultations
- new_matter: New legal inquiry or potential client
- complaint: Expression of dissatisfaction or concern
- general_inquiry: General questions about services, fees, processes
- payment: Invoice, payment, or billing related
- urgent_legal: Time-sensitive legal matters requiring immediate attention

URGENCY LEVELS:
- critical: Court deadlines, limitation periods, immediate legal risk
- high: Client expressing frustration, time-sensitive requests
- normal: Standard inquiries with no time pressure
- low: FYI messages, acknowledgments, non-urgent follow-ups

PRACTICE AREAS:
- corporate: Company formation, M&A, commercial contracts
- employment: HR issues, dismissal, tribunal, contracts
- property: Conveyancing, leases, property disputes
- litigation: Disputes, court proceedings
- general: Cross-practice or unclear

ROUTING RECOMMENDATIONS:
- auto_respond: Safe to send automated response
- lawyer_review: Needs lawyer review before response
- urgent_callback: Requires immediate phone call
- new_client_intake: Route to intake agent
- document_agent: Route to document processing agent
- escalate_senior: Escalate to senior partner

Be conservative with confidence scores. If unsure, recommend human review.
Always consider GDPR and solicitor-client privilege in your analysis.
"""


class EmailTriageAgent(BaseAgent):
    """
    Agent responsible for triaging incoming emails.
    
    Capabilities:
    - Email classification (intent, urgency, practice area)
    - Entity extraction from email content
    - Response generation
    - Routing recommendations
    """
    
    def __init__(self, llm_client: GeminiClient):
        super().__init__(
            agent_id="email_triage_agent",
            name="Email Triage Agent",
            llm_client=llm_client
        )
        self.agent_llm = AgentLLM(
            client=llm_client,
            agent_name=self.name,
            system_prompt=SYSTEM_PROMPT
        )
    
    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description="Triages incoming emails by classifying intent, extracting entities, and routing appropriately",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="email_classification",
                    description="Classify email by intent, urgency, and practice area",
                    input_schema=EmailInput.model_json_schema(),
                    output_schema=EmailClassification.model_json_schema(),
                    estimated_duration_seconds=5,
                    requires_human_review=False
                ),
                AgentCapability(
                    name="email_entity_extraction",
                    description="Extract key entities from email content",
                    input_schema=EmailInput.model_json_schema(),
                    output_schema=ExtractedEmailData.model_json_schema(),
                    estimated_duration_seconds=5,
                    requires_human_review=False
                ),
                AgentCapability(
                    name="email_full_triage",
                    description="Complete email triage with classification, extraction, and routing",
                    input_schema=EmailInput.model_json_schema(),
                    output_schema=EmailTriageResult.model_json_schema(),
                    estimated_duration_seconds=15,
                    requires_human_review=True
                )
            ],
            supported_input_types=["email"],
            supported_output_types=["classification", "extraction", "routing"]
        )
    
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        """Process an email triage task"""
        start_time = time.time()
        
        try:
            email_data = EmailInput(**task.input_data)
            
            if task.task_type == "email_classification":
                result = await self._classify_email(email_data)
                artifact = TaskArtifact(
                    artifact_type="classification",
                    content=result.model_dump()
                )
                
            elif task.task_type == "email_entity_extraction":
                result = await self._extract_entities(email_data)
                artifact = TaskArtifact(
                    artifact_type="extraction",
                    content=result.model_dump()
                )
                
            elif task.task_type == "email_full_triage":
                result = await self._full_triage(email_data)
                artifact = TaskArtifact(
                    artifact_type="triage_result",
                    content=result.model_dump()
                )
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Determine if human review needed
            requires_review = False
            escalation_reason = None
            
            if hasattr(result, 'confidence') and result.confidence < 0.7:
                requires_review = True
                escalation_reason = f"Low confidence score: {result.confidence}"
            elif hasattr(result, 'human_review_required') and result.human_review_required:
                requires_review = True
                escalation_reason = result.human_review_reason
            
            return TaskResponse(
                task_id=task.task_id,
                state=TaskState.COMPLETED,
                result=result.model_dump() if hasattr(result, 'model_dump') else result,
                artifacts=[artifact],
                confidence_score=result.confidence if hasattr(result, 'confidence') else 0.9,
                requires_human_review=requires_review,
                escalation_reason=escalation_reason,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                state=TaskState.FAILED,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def _classify_email(self, email: EmailInput) -> EmailClassification:
        """Classify an email"""
        prompt = f"""Classify this email:

From: {email.sender_name} <{email.sender_email}>
Subject: {email.subject}

Body:
{email.body}

Attachments: {', '.join(email.attachments) if email.attachments else 'None'}
Is Reply: {email.is_reply}

Respond with JSON:
{{
    "intent": "<intent type>",
    "urgency": "<urgency level>",
    "practice_area": "<practice area>",
    "sentiment": "<sentiment>",
    "confidence": <0.0-1.0>,
    "requires_immediate_attention": <true/false>,
    "reasoning": "<brief explanation>"
}}"""
        
        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.2
        )

        obj = _coerce_json_object(response.structured_output, context="email_classification")
        return EmailClassification(**obj)
    
    async def _extract_entities(self, email: EmailInput) -> ExtractedEmailData:
        """Extract entities from email"""
        prompt = f"""Extract key information from this email:

From: {email.sender_name} <{email.sender_email}>
Subject: {email.subject}

Body:
{email.body}

Extract and respond with JSON:
{{
    "client_name": "<name or null>",
    "matter_reference": "<reference number or null>",
    "dates_mentioned": ["<dates in ISO format>"],
    "action_requested": "<what the sender wants>",
    "key_entities": ["<people, companies, properties mentioned>"],
    "questions_asked": ["<specific questions in the email>"]
}}"""
        
        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.1
        )

        obj = _coerce_json_object(response.structured_output, context="email_entity_extraction")
        return ExtractedEmailData(**obj)
    
    async def _full_triage(self, email: EmailInput) -> EmailTriageResult:
        """Perform complete email triage"""
        # Get classification
        classification = await self._classify_email(email)
        
        # Get entity extraction
        extracted_data = await self._extract_entities(email)
        
        # Determine routing and generate response if appropriate
        routing_prompt = f"""Based on this email triage:

Classification:
- Intent: {classification.intent}
- Urgency: {classification.urgency}
- Practice Area: {classification.practice_area}
- Requires Immediate Attention: {classification.requires_immediate_attention}

Extracted Data:
- Client: {extracted_data.client_name}
- Matter Ref: {extracted_data.matter_reference}
- Action Requested: {extracted_data.action_requested}

Original Email Subject: {email.subject}
Original Email Body (first 500 chars): {email.body[:500]}

Determine:
1. Routing recommendation (auto_respond, lawyer_review, urgent_callback, new_client_intake, document_agent, escalate_senior)
2. Which agent should handle next (or null if human)
3. Whether human review is required
4. If safe to auto-respond, generate a professional response draft

Respond with JSON:
{{
    "routing_recommendation": "<recommendation>",
    "next_agent": "<agent_id or null>",
    "human_review_required": <true/false>,
    "human_review_reason": "<reason or null>",
    "suggested_response": "<response draft if auto_respond, else null>"
}}"""
        
        response = await self.agent_llm.client.generate(
            prompt=routing_prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.3
        )

        routing_result = _coerce_json_object(response.structured_output, context="email_routing")
        
        return EmailTriageResult(
            classification=classification,
            extracted_data=extracted_data,
            suggested_response=routing_result.get("suggested_response"),
            routing_recommendation=routing_result.get("routing_recommendation", "lawyer_review"),
            next_agent=routing_result.get("next_agent"),
            human_review_required=routing_result.get("human_review_required", True),
            human_review_reason=routing_result.get("human_review_reason")
        )
