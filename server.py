#!/usr/bin/env python3
"""
BrightLaw A2A Multi-Agent System - FastAPI Server

RESTful API server for the multi-agent system.
Provides endpoints for processing emails, documents, voice calls, and chats.
All processed cases are stored persistently.

Usage:
    uvicorn server:app --reload --port 8000
    
Or:
    python server.py
"""

import os
import sys
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

logger = logging.getLogger("brightlaw")
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.a2a_protocol import AgentRegistry, TaskRequest, AgentCard
from core.llm_client import GeminiClient
from core.case_storage import case_storage, StoredCase, CaseType, CaseStatus
from agents import (
    EmailTriageAgent,
    DocumentClassificationAgent,
    ClientIntakeAgent,
    DeadlineTrackerAgent,
    ResponseGeneratorAgent,
    OrchestratorAgent
)


# =============================================================================
# Global State
# =============================================================================

class AppState:
    llm_client: Optional[GeminiClient] = None
    registry: Optional[AgentRegistry] = None
    orchestrator: Optional[OrchestratorAgent] = None


state = AppState()


# =============================================================================
# Request/Response Models
# =============================================================================

class WorkflowRequest(BaseModel):
    workflow_type: str = Field(..., description="Type of workflow: email_processing, document_processing, new_client_intake, deadline_extraction, voice_call_processing, chat_processing")
    input_data: Dict[str, Any] = Field(..., description="Input data for the workflow")
    priority: str = Field(default="normal", description="Priority level: critical, high, normal, low")
    # Optional: store case after processing
    store_case: bool = Field(default=True, description="Whether to store the case after processing")
    case_type: Optional[str] = Field(default=None, description="Case type for storage: email, voice_call, chat, document")


class AgentRequest(BaseModel):
    agent_id: str = Field(..., description="Target agent ID")
    task_type: str = Field(..., description="Task type to execute")
    input_data: Dict[str, Any] = Field(..., description="Input data for the task")


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    agents_registered: int
    cases_stored: int
    version: str = "1.0.0"


# =============================================================================
# Lifespan Management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agents on startup"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("Warning: GEMINI_API_KEY not set. Set it before making requests.")
    else:
        initialize_agents(api_key)
    
    yield
    
    # Cleanup on shutdown
    state.llm_client = None
    state.registry = None
    state.orchestrator = None


def initialize_agents(api_key: str):
    """Initialize all agents"""
    print("Initializing BrightLaw A2A System...")
    
    state.llm_client = GeminiClient(api_key=api_key)
    state.registry = AgentRegistry()
    
    # Create and register agents
    agents = [
        EmailTriageAgent(state.llm_client),
        DocumentClassificationAgent(state.llm_client),
        ClientIntakeAgent(state.llm_client),
        DeadlineTrackerAgent(state.llm_client),
        ResponseGeneratorAgent(state.llm_client)
    ]
    
    for agent in agents:
        state.registry.register(agent)
        print(f"  ✓ Registered: {agent.name}")
    
    state.orchestrator = OrchestratorAgent(state.llm_client, state.registry)
    state.registry.register(state.orchestrator)
    print(f"  ✓ Registered: {state.orchestrator.name}")
    
    print(f"System ready with {len(state.registry.agents)} agents")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="BrightLaw A2A Multi-Agent System",
    description="AI-powered legal automation platform using Agent-to-Agent architecture",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Status Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    stats = case_storage.get_stats()
    return HealthResponse(
        status="healthy" if state.registry else "initializing",
        timestamp=datetime.utcnow().isoformat(),
        agents_registered=len(state.registry.agents) if state.registry else 0,
        cases_stored=stats.get('total', 0)
    )


@app.post("/api/initialize")
async def initialize_system(api_key: str):
    """Initialize the system with an API key"""
    if state.registry and len(state.registry.agents) > 0:
        return {"message": "System already initialized", "agents": len(state.registry.agents)}
    
    try:
        initialize_agents(api_key)
        return {"message": "System initialized", "agents": len(state.registry.agents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents")
async def list_agents():
    """List all registered agents and their capabilities"""
    if not state.registry:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    agents = []
    for card in state.registry.get_all_cards():
        agents.append({
            "agent_id": card.agent_id,
            "name": card.name,
            "description": card.description,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "estimated_duration_seconds": cap.estimated_duration_seconds,
                    "requires_human_review": cap.requires_human_review
                }
                for cap in card.capabilities
            ]
        })
    
    return {"agents": agents}


# =============================================================================
# Case Storage Endpoints
# =============================================================================

@app.get("/api/cases")
async def list_cases(
    case_type: Optional[str] = Query(None, description="Filter by case type: email, voice_call, chat, document"),
    limit: int = Query(100, description="Maximum number of cases to return")
):
    """List all stored cases"""
    ct = CaseType(case_type) if case_type else None
    cases = case_storage.get_all(case_type=ct, limit=limit)
    return {"cases": [c.model_dump() for c in cases]}


@app.get("/api/cases/stats")
async def get_case_stats():
    """Get statistics about stored cases"""
    return case_storage.get_stats()


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    """Get a specific case by ID"""
    case = case_storage.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return case.model_dump()


@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: str):
    """Delete a specific case"""
    if case_storage.delete(case_id):
        return {"message": "Case deleted", "case_id": case_id}
    raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")


@app.delete("/api/cases")
async def clear_all_cases(confirm: bool = Query(False, description="Must be true to confirm deletion")):
    """Clear all stored cases (requires confirmation)"""
    if not confirm:
        raise HTTPException(status_code=400, detail="Must set confirm=true to clear all cases")
    case_storage.clear_all()
    return {"message": "All cases cleared"}


# =============================================================================
# Workflow Execution Endpoints
# =============================================================================

def _determine_case_type(workflow_type: str, explicit_type: Optional[str]) -> CaseType:
    """Determine the case type based on workflow type"""
    if explicit_type:
        return CaseType(explicit_type)
    
    mapping = {
        "email_processing": CaseType.EMAIL,
        "document_processing": CaseType.DOCUMENT,
        "voice_call_processing": CaseType.VOICE_CALL,
        "chat_processing": CaseType.CHAT,
        "new_client_intake": CaseType.EMAIL,  # Default to email for intakes
        "deadline_extraction": CaseType.DOCUMENT,
    }
    return mapping.get(workflow_type, CaseType.EMAIL)


def _extract_classification(result: Dict[str, Any], workflow_type: str) -> Dict[str, Any]:
    """Extract classification data from workflow result for storage"""
    classification = {}
    
    final_result = result.get("final_result", {})
    
    # Email processing
    if "triage" in final_result:
        triage = final_result["triage"]
        if "classification" in triage:
            classification = triage["classification"]
    
    # Document processing
    if "classification" in final_result:
        doc_class = final_result["classification"]
        if "classification" in doc_class:
            classification = doc_class["classification"]
    
    # Intake processing
    if "intake" in final_result:
        intake = final_result["intake"]
        if "practice_area" in intake:
            classification["practice_area"] = intake.get("practice_area")
        if "risk_assessment" in intake:
            classification["risk_level"] = intake["risk_assessment"].get("overall_risk")
    
    return classification


@app.post("/api/workflow")
async def execute_workflow(request: WorkflowRequest):
    """Execute a complete workflow through the orchestrator and store the result"""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    valid_workflows = [
        "email_processing", "document_processing", "new_client_intake", 
        "deadline_extraction", "voice_call_processing", "chat_processing"
    ]
    if request.workflow_type not in valid_workflows:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid workflow type. Must be one of: {valid_workflows}"
        )
    
    request_id = str(uuid.uuid4())
    case_type = _determine_case_type(request.workflow_type, request.case_type)
    
    logger.info(
        "workflow_start request_id=%s workflow_type=%s case_type=%s priority=%s",
        request_id,
        request.workflow_type,
        case_type.value,
        request.priority,
    )
    
    # Create case record before processing
    stored_case = None
    if request.store_case:
        stored_case = StoredCase(
            case_id=request_id,
            case_type=case_type,
            status=CaseStatus.PROCESSING,
            input_data=request.input_data,
            customer_name=request.input_data.get("sender_name") or request.input_data.get("client_name") or request.input_data.get("caller_name"),
            customer_email=request.input_data.get("sender_email") or request.input_data.get("contact_email"),
            attachments=request.input_data.get("attachments", []),
        )
        case_storage.create(stored_case)

    # For voice call and chat, we use email processing as the base
    # (the triage agent can handle text from any source)
    actual_workflow = request.workflow_type
    if request.workflow_type in ["voice_call_processing", "chat_processing"]:
        actual_workflow = "email_processing"  # Reuse email triage for text content
    
    task = TaskRequest(
        task_type="orchestrate_workflow",
        input_data={
            "request_id": request_id,
            "workflow_type": actual_workflow,
            "input_data": request.input_data,
            "priority": request.priority
        },
        context={"request_id": request_id},
    )
    
    try:
        response = await state.orchestrator.process_task(task)
        
        logger.info(
            "workflow_end request_id=%s status=%s duration_ms=%s requires_human_review=%s",
            request_id,
            response.state.value,
            response.execution_time_ms,
            response.requires_human_review,
        )
        
        result_data = {
            "request_id": request_id,
            "case_id": request_id,
            "task_id": response.task_id,
            "status": response.state.value,
            "result": response.result,
            "confidence_score": response.confidence_score,
            "requires_human_review": response.requires_human_review,
            "escalation_reason": response.escalation_reason,
            "execution_time_ms": response.execution_time_ms
        }
        
        # Update stored case with results
        if request.store_case and stored_case:
            classification = _extract_classification(response.result or {}, request.workflow_type)
            case_storage.update(request_id, {
                "status": CaseStatus.REQUIRES_REVIEW.value if response.requires_human_review else CaseStatus.COMPLETED.value,
                "processing_result": response.result,
                "classification": classification,
                "processed_at": datetime.utcnow().isoformat(),
                "processing_duration_ms": response.execution_time_ms,
                "requires_human_review": response.requires_human_review,
                "escalation_reason": response.escalation_reason,
            })
        
        return result_data
        
    except Exception as e:
        logger.exception("workflow_error request_id=%s error=%s", request_id, str(e))
        
        # Update case with error
        if request.store_case and stored_case:
            case_storage.update(request_id, {
                "status": CaseStatus.FAILED.value,
                "processing_result": {"error": str(e)},
                "processed_at": datetime.utcnow().isoformat(),
            })
        
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/{agent_id}")
async def invoke_agent(agent_id: str, request: AgentRequest):
    """Directly invoke a specific agent"""
    if not state.registry:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    agent = state.registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    
    task = TaskRequest(
        task_type=request.task_type,
        input_data=request.input_data
    )
    
    try:
        response = await agent.process_task(task)
        return {
            "task_id": response.task_id,
            "status": response.state.value,
            "result": response.result,
            "confidence_score": response.confidence_score,
            "requires_human_review": response.requires_human_review,
            "escalation_reason": response.escalation_reason,
            "execution_time_ms": response.execution_time_ms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Convenience Endpoints
# =============================================================================

@app.post("/api/email/triage")
async def triage_email(
    email_id: str,
    sender_email: str,
    sender_name: str,
    subject: str,
    body: str,
    attachments: list[str] = []
):
    """Convenience endpoint for email triage"""
    request = WorkflowRequest(
        workflow_type="email_processing",
        case_type="email",
        input_data={
            "email_id": email_id,
            "sender_email": sender_email,
            "sender_name": sender_name,
            "subject": subject,
            "body": body,
            "attachments": attachments,
            "received_at": datetime.utcnow().isoformat(),
            "is_reply": False
        }
    )
    return await execute_workflow(request)


@app.post("/api/voice/process")
async def process_voice_call(
    call_id: str,
    caller_name: str,
    caller_phone: str,
    transcript: str,
    duration_seconds: int = 0,
    attachments: list[str] = []
):
    """Process a voice call transcript"""
    request = WorkflowRequest(
        workflow_type="voice_call_processing",
        case_type="voice_call",
        input_data={
            "email_id": call_id,  # Reuse email_id field for compatibility
            "sender_email": caller_phone,
            "sender_name": caller_name,
            "subject": f"Voice Call from {caller_name}",
            "body": transcript,
            "attachments": attachments,
            "received_at": datetime.utcnow().isoformat(),
            "is_reply": False,
            "call_duration_seconds": duration_seconds,
            "source_type": "voice_call"
        }
    )
    return await execute_workflow(request)


@app.post("/api/chat/process")
async def process_chat(
    chat_id: str,
    customer_name: str,
    customer_email: str,
    messages: str,
    attachments: list[str] = []
):
    """Process a chat conversation"""
    request = WorkflowRequest(
        workflow_type="chat_processing",
        case_type="chat",
        input_data={
            "email_id": chat_id,
            "sender_email": customer_email,
            "sender_name": customer_name,
            "subject": f"Chat with {customer_name}",
            "body": messages,
            "attachments": attachments,
            "received_at": datetime.utcnow().isoformat(),
            "is_reply": False,
            "source_type": "chat"
        }
    )
    return await execute_workflow(request)


@app.post("/api/document/classify")
async def classify_document(
    document_id: str,
    filename: str,
    content: str,
    file_type: str = "pdf",
    page_count: int = 1
):
    """Convenience endpoint for document classification"""
    request = WorkflowRequest(
        workflow_type="document_processing",
        case_type="document",
        input_data={
            "document_id": document_id,
            "filename": filename,
            "content": content,
            "file_type": file_type,
            "page_count": page_count,
            "source": "api"
        }
    )
    return await execute_workflow(request)


@app.post("/api/intake/new")
async def new_client_intake(
    inquiry_id: str,
    client_name: str,
    matter_description: str,
    contact_email: str = "",
    contact_phone: str = "",
    client_type: str = "individual",
    practice_area: str = "",
    urgency: str = "normal",
    opposing_parties: list[str] = []
):
    """Convenience endpoint for new client intake"""
    request = WorkflowRequest(
        workflow_type="new_client_intake",
        input_data={
            "inquiry_id": inquiry_id,
            "source": "api",
            "client_name": client_name,
            "client_type": client_type,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "matter_description": matter_description,
            "practice_area": practice_area,
            "urgency": urgency,
            "opposing_parties": opposing_parties
        }
    )
    return await execute_workflow(request)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
