"""
Response Generator Agent

Responsible for:
- Generating draft responses to client emails
- Creating appropriate tone and content for different situations
- Ensuring compliance with legal communication standards
- Handling templates and personalization
"""

import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

import sys
sys.path.insert(0, '/home/claude/brightlaw-a2a')

from core.a2a_protocol import (
    BaseAgent, AgentCard, AgentCapability, TaskRequest, TaskResponse,
    TaskState, TaskArtifact
)
from core.llm_client import GeminiClient, AgentLLM


class ResponseTone(str, Enum):
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    SYMPATHETIC = "sympathetic"
    URGENT = "urgent"
    APOLOGETIC = "apologetic"


class ResponseInput(BaseModel):
    inquiry_id: str
    original_message: str
    sender_name: str
    sender_email: str
    context: Dict[str, Any] = Field(default_factory=dict)
    matter_id: Optional[str] = None
    client_history: Optional[str] = None
    tone: str = "professional"
    include_disclaimer: bool = True
    max_length: int = 500


class GeneratedResponse(BaseModel):
    response_id: str
    subject: str
    body: str
    tone_used: str
    confidence: float
    requires_review: bool
    review_reasons: List[str] = Field(default_factory=list)
    placeholders: List[str] = Field(default_factory=list)
    suggested_attachments: List[str] = Field(default_factory=list)


SYSTEM_PROMPT = """You are the Response Generator Agent for BrightLaw, a UK legal services firm.

Your responsibilities:
1. Generate professional, appropriate responses to client communications
2. Match the appropriate tone for the situation
3. Ensure compliance with SRA communication standards
4. Include appropriate disclaimers when needed

GUIDELINES:
- Never provide specific legal advice in automated responses
- Always be professional and courteous
- Acknowledge the client's concerns
- Set realistic expectations for response times
- Use placeholders [PLACEHOLDER] for information you don't have
- Flag responses that definitely need lawyer review

TONE GUIDELINES:
- formal: For new clients, complaints, serious matters
- professional: Standard business communication
- sympathetic: For clients going through difficult situations
- urgent: Time-sensitive matters requiring quick action
- apologetic: When delays or issues have occurred

DISCLAIMER (include when requested):
"This email and any attachments are confidential and intended solely for the addressee. 
If you are not the intended recipient, please notify us immediately and delete this email."

UK LEGAL CONTEXT:
- Reference SRA regulations where appropriate
- Be mindful of privilege and confidentiality
- Don't promise outcomes
"""


class ResponseGeneratorAgent(BaseAgent):
    def __init__(self, llm_client: GeminiClient):
        super().__init__(
            agent_id="response_generator_agent",
            name="Response Generator Agent",
            llm_client=llm_client
        )
        self.agent_llm = AgentLLM(llm_client, self.name, SYSTEM_PROMPT)
    
    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description="Generates professional draft responses to client communications",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="generate_response",
                    description="Generate a draft response to a client message",
                    input_schema=ResponseInput.model_json_schema(),
                    output_schema=GeneratedResponse.model_json_schema(),
                    estimated_duration_seconds=10,
                    requires_human_review=True
                ),
                AgentCapability(
                    name="generate_acknowledgment",
                    description="Generate a quick acknowledgment email",
                    input_schema=ResponseInput.model_json_schema(),
                    output_schema=GeneratedResponse.model_json_schema(),
                    estimated_duration_seconds=5,
                    requires_human_review=False
                )
            ],
            supported_input_types=["email", "inquiry"],
            supported_output_types=["response_draft"]
        )
    
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        start_time = time.time()
        
        try:
            input_data = ResponseInput(**task.input_data)
            
            if task.task_type == "generate_response":
                result = await self._generate_full_response(input_data)
            elif task.task_type == "generate_acknowledgment":
                result = await self._generate_acknowledgment(input_data)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            artifact = TaskArtifact(
                artifact_type="response_draft",
                content=result.model_dump()
            )
            
            return TaskResponse(
                task_id=task.task_id,
                state=TaskState.COMPLETED,
                result=result.model_dump(),
                artifacts=[artifact],
                confidence_score=result.confidence,
                requires_human_review=result.requires_review,
                escalation_reason="; ".join(result.review_reasons) if result.review_reasons else None,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                state=TaskState.FAILED,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def _generate_full_response(self, input_data: ResponseInput) -> GeneratedResponse:
        context_str = "\n".join([f"- {k}: {v}" for k, v in input_data.context.items()]) if input_data.context else "None provided"
        
        prompt = f"""Generate a professional response email.

ORIGINAL MESSAGE:
From: {input_data.sender_name} <{input_data.sender_email}>
Content: {input_data.original_message}

CONTEXT:
{context_str}

Client History: {input_data.client_history or 'New client / No history'}
Matter ID: {input_data.matter_id or 'Not assigned'}
Requested Tone: {input_data.tone}
Max Length: {input_data.max_length} words
Include Disclaimer: {input_data.include_disclaimer}

Generate a response and return JSON:
{{
    "response_id": "resp_001",
    "subject": "Re: ...",
    "body": "Dear ...",
    "tone_used": "{input_data.tone}",
    "confidence": 0.0-1.0,
    "requires_review": true/false,
    "review_reasons": ["reason if requires_review"],
    "placeholders": ["[PLACEHOLDER] items used"],
    "suggested_attachments": ["relevant documents to attach"]
}}"""

        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.6
        )
        
        return GeneratedResponse(**response.structured_output)
    
    async def _generate_acknowledgment(self, input_data: ResponseInput) -> GeneratedResponse:
        prompt = f"""Generate a brief acknowledgment email.

From: {input_data.sender_name}
Subject relates to: {input_data.original_message[:200]}

Create a short acknowledgment (2-3 sentences) that:
1. Thanks them for their message
2. Confirms receipt
3. Sets expectation for follow-up (within 24-48 hours)

Return JSON:
{{
    "response_id": "ack_001",
    "subject": "Re: ...",
    "body": "Dear ...",
    "tone_used": "professional",
    "confidence": 0.9,
    "requires_review": false,
    "review_reasons": [],
    "placeholders": [],
    "suggested_attachments": []
}}"""

        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.4
        )
        
        return GeneratedResponse(**response.structured_output)
