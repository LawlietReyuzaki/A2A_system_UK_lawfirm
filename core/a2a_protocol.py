"""
A2A (Agent-to-Agent) Protocol for BrightLaw AI Platform

This module defines the core protocol for agent communication, including:
- Message types and schemas
- Agent card definitions
- Task lifecycle management
- Inter-agent messaging
"""

from enum import Enum
from typing import Any, Optional, List, Dict, Callable
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import asyncio
from abc import ABC, abstractmethod


# =============================================================================
# A2A Message Types
# =============================================================================

class TaskState(str, Enum):
    """Task lifecycle states per A2A protocol"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_INPUT = "waiting_for_input"
    DELEGATED = "delegated"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageType(str, Enum):
    """Types of A2A messages"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    TASK_UPDATE = "task_update"
    AGENT_DISCOVERY = "agent_discovery"
    CAPABILITY_QUERY = "capability_query"
    HUMAN_ESCALATION = "human_escalation"


class Priority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


# =============================================================================
# A2A Data Models
# =============================================================================

class AgentCapability(BaseModel):
    """Defines a specific capability an agent can perform"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    estimated_duration_seconds: int = 30
    requires_human_review: bool = False


class AgentCard(BaseModel):
    """Agent identity and capability declaration (A2A Agent Card)"""
    agent_id: str
    name: str
    description: str
    version: str = "1.0.0"
    capabilities: List[AgentCapability]
    supported_input_types: List[str]
    supported_output_types: List[str]
    max_concurrent_tasks: int = 5
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskArtifact(BaseModel):
    """Output artifact from a task"""
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    artifact_type: str  # e.g., "document", "classification", "extraction", "response"
    content: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class A2AMessage(BaseModel):
    """Core A2A message structure"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType
    source_agent_id: str
    target_agent_id: str
    correlation_id: Optional[str] = None  # For linking related messages
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any]
    priority: Priority = Priority.NORMAL


class TaskRequest(BaseModel):
    """Request to execute a task"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str
    input_data: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    timeout_seconds: int = 300
    callback_agent_id: Optional[str] = None
    parent_task_id: Optional[str] = None  # For subtasks


class TaskResponse(BaseModel):
    """Response from task execution"""
    task_id: str
    state: TaskState
    result: Optional[Any] = None
    artifacts: List[TaskArtifact] = Field(default_factory=list)
    error: Optional[str] = None
    confidence_score: float = 1.0
    requires_human_review: bool = False
    escalation_reason: Optional[str] = None
    execution_time_ms: int = 0
    subtasks_spawned: List[str] = Field(default_factory=list)


# =============================================================================
# Base Agent Class
# =============================================================================

class BaseAgent(ABC):
    """
    Abstract base class for all A2A agents.
    
    Each agent must implement:
    - get_agent_card(): Returns the agent's capability declaration
    - process_task(): Main task processing logic
    """
    
    def __init__(self, agent_id: str, name: str, llm_client: Any = None):
        self.agent_id = agent_id
        self.name = name
        self.llm_client = llm_client
        self.active_tasks: Dict[str, TaskRequest] = {}
        self.message_handlers: Dict[MessageType, Callable] = {}
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup default message handlers"""
        self.message_handlers[MessageType.TASK_REQUEST] = self._handle_task_request
        self.message_handlers[MessageType.CAPABILITY_QUERY] = self._handle_capability_query
    
    @abstractmethod
    def get_agent_card(self) -> AgentCard:
        """Return this agent's capability card"""
        pass
    
    @abstractmethod
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        """Process a task and return results"""
        pass
    
    async def receive_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Handle incoming A2A message"""
        handler = self.message_handlers.get(message.message_type)
        if handler:
            return await handler(message)
        return None
    
    async def _handle_task_request(self, message: A2AMessage) -> A2AMessage:
        """Handle incoming task request"""
        task = TaskRequest(**message.payload)
        self.active_tasks[task.task_id] = task
        
        try:
            response = await self.process_task(task)
        except Exception as e:
            response = TaskResponse(
                task_id=task.task_id,
                state=TaskState.FAILED,
                error=str(e)
            )
        finally:
            del self.active_tasks[task.task_id]
        
        return A2AMessage(
            message_type=MessageType.TASK_RESPONSE,
            source_agent_id=self.agent_id,
            target_agent_id=message.source_agent_id,
            correlation_id=message.message_id,
            payload=response.model_dump()
        )
    
    async def _handle_capability_query(self, message: A2AMessage) -> A2AMessage:
        """Respond to capability queries"""
        return A2AMessage(
            message_type=MessageType.TASK_RESPONSE,
            source_agent_id=self.agent_id,
            target_agent_id=message.source_agent_id,
            correlation_id=message.message_id,
            payload={"agent_card": self.get_agent_card().model_dump()}
        )
    
    def create_subtask_request(
        self,
        target_agent_id: str,
        task_type: str,
        input_data: Dict[str, Any],
        parent_task_id: str
    ) -> A2AMessage:
        """Create a subtask request to send to another agent"""
        task = TaskRequest(
            task_type=task_type,
            input_data=input_data,
            parent_task_id=parent_task_id,
            callback_agent_id=self.agent_id
        )
        
        return A2AMessage(
            message_type=MessageType.TASK_REQUEST,
            source_agent_id=self.agent_id,
            target_agent_id=target_agent_id,
            payload=task.model_dump()
        )


# =============================================================================
# Agent Registry
# =============================================================================

class AgentRegistry:
    """Registry for discovering and routing to agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.capability_index: Dict[str, List[str]] = {}  # capability -> [agent_ids]
    
    def register(self, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent.agent_id] = agent
        card = agent.get_agent_card()
        
        for capability in card.capabilities:
            if capability.name not in self.capability_index:
                self.capability_index[capability.name] = []
            self.capability_index[capability.name].append(agent.agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def find_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """Find agents that support a specific capability"""
        agent_ids = self.capability_index.get(capability, [])
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    def get_all_cards(self) -> List[AgentCard]:
        """Get all registered agent cards"""
        return [agent.get_agent_card() for agent in self.agents.values()]


# =============================================================================
# Message Bus (Simple In-Memory Implementation)
# =============================================================================

class MessageBus:
    """
    Simple message bus for agent communication.
    In production, this would be replaced with Pub/Sub, Redis Streams, etc.
    """
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.response_futures: Dict[str, asyncio.Future] = {}
    
    async def send(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Send a message and optionally wait for response"""
        target_agent = self.registry.get_agent(message.target_agent_id)
        if not target_agent:
            raise ValueError(f"Agent not found: {message.target_agent_id}")
        
        # Direct invocation for simplicity (in production, use queue)
        response = await target_agent.receive_message(message)
        return response
    
    async def send_and_wait(
        self,
        message: A2AMessage,
        timeout: float = 300.0
    ) -> A2AMessage:
        """Send message and wait for response with timeout"""
        response = await asyncio.wait_for(
            self.send(message),
            timeout=timeout
        )
        if response is None:
            raise TimeoutError(f"No response from agent {message.target_agent_id}")
        return response
    
    async def broadcast(
        self,
        message: A2AMessage,
        agent_ids: List[str]
    ) -> List[A2AMessage]:
        """Broadcast message to multiple agents"""
        tasks = []
        for agent_id in agent_ids:
            msg_copy = message.model_copy()
            msg_copy.target_agent_id = agent_id
            tasks.append(self.send(msg_copy))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in responses if isinstance(r, A2AMessage)]
