"""
BrightLaw A2A Agents Module

Specialized agents for legal automation tasks.
"""

from .email_triage_agent import EmailTriageAgent
from .document_classification_agent import DocumentClassificationAgent
from .client_intake_agent import ClientIntakeAgent
from .deadline_tracker_agent import DeadlineTrackerAgent
from .response_generator_agent import ResponseGeneratorAgent
from .orchestrator_agent import OrchestratorAgent

__all__ = [
    "EmailTriageAgent",
    "DocumentClassificationAgent", 
    "ClientIntakeAgent",
    "DeadlineTrackerAgent",
    "ResponseGeneratorAgent",
    "OrchestratorAgent"
]
