#!/usr/bin/env python3
"""
BrightLaw A2A Multi-Agent System - Demo Application

This demo showcases the Agent-to-Agent (A2A) architecture for legal automation.
It processes sample emails, documents, and client intakes through specialized agents.

Usage:
    python main.py --api-key YOUR_GEMINI_API_KEY
    
Or set environment variable:
    export GEMINI_API_KEY=your_key
    python main.py
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.a2a_protocol import AgentRegistry, TaskRequest
from core.llm_client import GeminiClient
from agents import (
    EmailTriageAgent,
    DocumentClassificationAgent,
    ClientIntakeAgent,
    DeadlineTrackerAgent,
    ResponseGeneratorAgent,
    OrchestratorAgent
)


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_subheader(text: str):
    """Print a formatted subheader"""
    print(f"\n--- {text} ---")


def print_result(result: Dict[str, Any], indent: int = 2):
    """Pretty print a result dictionary"""
    print(json.dumps(result, indent=indent, default=str))


async def demo_email_triage(orchestrator: OrchestratorAgent, sample_email: Dict[str, Any]):
    """Demo the email processing workflow"""
    print_header("EMAIL PROCESSING WORKFLOW")
    print(f"\nProcessing email from: {sample_email['sender_name']}")
    print(f"Subject: {sample_email['subject']}")
    print(f"Urgency indicators: {sample_email.get('urgency', 'to be determined')}")
    
    # Create workflow request
    task = TaskRequest(
        task_type="orchestrate_workflow",
        input_data={
            "workflow_type": "email_processing",
            "input_data": sample_email
        }
    )
    
    print_subheader("Executing Workflow")
    response = await orchestrator.process_task(task)
    
    if response.result:
        result = response.result
        
        # Show triage results
        if "triage" in result.get("final_result", {}):
            triage = result["final_result"]["triage"]
            print_subheader("Email Triage Results")
            
            classification = triage.get("classification", {})
            print(f"  Intent: {classification.get('intent', 'unknown')}")
            print(f"  Urgency: {classification.get('urgency', 'unknown')}")
            print(f"  Practice Area: {classification.get('practice_area', 'unknown')}")
            print(f"  Confidence: {classification.get('confidence', 0):.0%}")
            
            extracted = triage.get("extracted_data", {})
            if extracted.get("client_name"):
                print(f"  Client: {extracted['client_name']}")
            if extracted.get("action_requested"):
                print(f"  Action Requested: {extracted['action_requested']}")
        
        # Show draft response
        if "draft_response" in result.get("final_result", {}):
            draft = result["final_result"]["draft_response"]
            print_subheader("Generated Response Draft")
            print(f"  Subject: {draft.get('subject', 'N/A')}")
            print(f"  Confidence: {draft.get('confidence', 0):.0%}")
            print(f"\n  Body:\n  {draft.get('body', 'No response generated')[:500]}...")
        
        # Show workflow summary
        print_subheader("Workflow Summary")
        print(f"  Steps Executed: {len(result.get('steps', []))}")
        print(f"  Agents Used: {', '.join(result.get('agents_used', []))}")
        print(f"  Duration: {result.get('total_duration_ms', 0)}ms")
        print(f"  Requires Human Review: {result.get('requires_human_review', False)}")
        
        if result.get("escalation_reasons"):
            print(f"  Escalation Reasons:")
            for reason in result["escalation_reasons"]:
                print(f"    - {reason}")
    else:
        print(f"Error: {response.error}")


async def demo_document_classification(orchestrator: OrchestratorAgent, sample_doc: Dict[str, Any]):
    """Demo the document processing workflow"""
    print_header("DOCUMENT PROCESSING WORKFLOW")
    print(f"\nProcessing document: {sample_doc['filename']}")
    print(f"File type: {sample_doc['file_type']}")
    print(f"Pages: {sample_doc['page_count']}")
    
    task = TaskRequest(
        task_type="orchestrate_workflow",
        input_data={
            "workflow_type": "document_processing",
            "input_data": sample_doc
        }
    )
    
    print_subheader("Executing Workflow")
    response = await orchestrator.process_task(task)
    
    if response.result:
        result = response.result
        
        # Show classification results
        if "classification" in result.get("final_result", {}):
            classification = result["final_result"]["classification"]
            doc_class = classification.get("classification", {})
            
            print_subheader("Document Classification")
            print(f"  Type: {doc_class.get('document_type', 'unknown')}")
            print(f"  Subtype: {doc_class.get('document_subtype', 'N/A')}")
            print(f"  Practice Area: {doc_class.get('practice_area', 'unknown')}")
            print(f"  Confidence: {doc_class.get('confidence', 0):.0%}")
            print(f"  Is Executed: {doc_class.get('is_executed', False)}")
            
            metadata = classification.get("metadata", {})
            if metadata:
                print_subheader("Extracted Metadata")
                if metadata.get("parties"):
                    print(f"  Parties: {', '.join(metadata['parties'])}")
                if metadata.get("date"):
                    print(f"  Date: {metadata['date']}")
                if metadata.get("effective_date"):
                    print(f"  Effective Date: {metadata['effective_date']}")
                if metadata.get("key_terms"):
                    print(f"  Key Terms: {', '.join(metadata['key_terms'][:5])}")
            
            flags = classification.get("flags", {})
            if any(flags.values()):
                print_subheader("Sensitivity Flags")
                for flag, value in flags.items():
                    if value and flag != "flagged_clauses":
                        print(f"  ⚠️  {flag.replace('_', ' ').title()}")
        
        # Show deadline extraction
        if "deadlines" in result.get("final_result", {}):
            deadlines = result["final_result"]["deadlines"]
            analysis = deadlines.get("analysis", {})
            
            print_subheader("Deadline Analysis")
            print(f"  Total Deadlines Found: {analysis.get('total_deadlines', 0)}")
            print(f"  Critical: {analysis.get('critical_count', 0)}")
            print(f"  Upcoming 7 Days: {analysis.get('upcoming_7_days', 0)}")
            print(f"  Upcoming 30 Days: {analysis.get('upcoming_30_days', 0)}")
            
            if deadlines.get("deadlines"):
                print("\n  Key Dates:")
                for dl in deadlines["deadlines"][:5]:
                    print(f"    • {dl['date']}: {dl['description'][:50]}...")
        
        # Show workflow summary
        print_subheader("Workflow Summary")
        print(f"  Duration: {result.get('total_duration_ms', 0)}ms")
        print(f"  Requires Human Review: {result.get('requires_human_review', False)}")
    else:
        print(f"Error: {response.error}")


async def demo_client_intake(orchestrator: OrchestratorAgent, sample_intake: Dict[str, Any]):
    """Demo the client intake workflow"""
    print_header("CLIENT INTAKE WORKFLOW")
    print(f"\nNew inquiry from: {sample_intake['client_name']}")
    print(f"Practice Area: {sample_intake.get('practice_area', 'to be determined')}")
    print(f"Urgency: {sample_intake.get('urgency', 'normal')}")
    
    task = TaskRequest(
        task_type="orchestrate_workflow",
        input_data={
            "workflow_type": "new_client_intake",
            "input_data": sample_intake
        }
    )
    
    print_subheader("Executing Workflow")
    response = await orchestrator.process_task(task)
    
    if response.result:
        result = response.result
        
        if "intake" in result.get("final_result", {}):
            intake = result["final_result"]["intake"]
            
            # Conflict Check
            conflict = intake.get("conflict_check", {})
            print_subheader("Conflict Check")
            print(f"  Status: {conflict.get('status', 'unknown').upper()}")
            print(f"  Can Proceed: {'✓ Yes' if conflict.get('can_proceed') else '✗ No'}")
            if conflict.get("conflicts_found"):
                print(f"  Conflicts Found: {len(conflict['conflicts_found'])}")
            
            # Risk Assessment
            risk = intake.get("risk_assessment", {})
            print_subheader("Risk Assessment")
            print(f"  Overall Risk: {risk.get('overall_risk', 'unknown').upper()}")
            if risk.get("risk_factors"):
                print(f"  Risk Factors:")
                for factor in risk["risk_factors"][:3]:
                    print(f"    - {factor}")
            print(f"  Senior Review Required: {'Yes' if risk.get('requires_senior_review') else 'No'}")
            
            # Fee Estimate
            fee = intake.get("fee_estimate", {})
            print_subheader("Fee Estimate")
            print(f"  Type: {fee.get('estimate_type', 'unknown')}")
            low = fee.get('low_estimate_gbp', 0)
            high = fee.get('high_estimate_gbp', 0)
            print(f"  Range: £{low:,.0f} - £{high:,.0f} + VAT")
            if fee.get("assumptions"):
                print(f"  Key Assumptions:")
                for assumption in fee["assumptions"][:2]:
                    print(f"    - {assumption}")
            
            # Next Steps
            if intake.get("next_steps"):
                print_subheader("Next Steps")
                for i, step in enumerate(intake["next_steps"][:5], 1):
                    print(f"  {i}. {step}")
            
            # Overall Decision
            print_subheader("Intake Decision")
            if intake.get("can_proceed"):
                print("  ✓ APPROVED - Proceed with client onboarding")
            else:
                print(f"  ✗ DECLINED - {intake.get('decline_reason', 'Unknown reason')}")
        
        print_subheader("Workflow Summary")
        print(f"  Duration: {result.get('total_duration_ms', 0)}ms")
        print(f"  Requires Human Review: {result.get('requires_human_review', False)}")
    else:
        print(f"Error: {response.error}")


async def run_demo(api_key: str):
    """Run the full demo"""
    print_header("BrightLaw A2A Multi-Agent System Demo")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize LLM client
    print("\nInitializing Gemini client...")
    llm_client = GeminiClient(api_key=api_key)
    
    # Create agent registry
    print("Creating agent registry...")
    registry = AgentRegistry()
    
    # Initialize all agents
    print("Initializing agents...")
    agents = [
        EmailTriageAgent(llm_client),
        DocumentClassificationAgent(llm_client),
        ClientIntakeAgent(llm_client),
        DeadlineTrackerAgent(llm_client),
        ResponseGeneratorAgent(llm_client)
    ]
    
    for agent in agents:
        registry.register(agent)
        print(f"  ✓ Registered: {agent.name}")
    
    # Create orchestrator
    orchestrator = OrchestratorAgent(llm_client, registry)
    registry.register(orchestrator)
    print(f"  ✓ Registered: {orchestrator.name}")
    
    # Load sample data
    print("\nLoading sample data...")
    demo_data_path = os.path.join(os.path.dirname(__file__), "demo_data", "sample_data.json")
    with open(demo_data_path, "r") as f:
        sample_data = json.load(f)
    
    # Display registered agents
    print_subheader("Registered Agents")
    for card in registry.get_all_cards():
        print(f"  • {card.name} ({card.agent_id})")
        for cap in card.capabilities[:2]:
            print(f"      - {cap.name}")
    
    # Run demos
    try:
        # Demo 1: Email Processing
        await demo_email_triage(orchestrator, sample_data["sample_emails"][0])
        
        # Demo 2: Document Classification
        await demo_document_classification(orchestrator, sample_data["sample_documents"][1])
        
        # Demo 3: Client Intake
        await demo_client_intake(orchestrator, sample_data["sample_intakes"][0])
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
    
    print_header("Demo Complete")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    parser = argparse.ArgumentParser(
        description="BrightLaw A2A Multi-Agent System Demo"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("GEMINI_API_KEY"),
        help="Google Gemini API key (or set GEMINI_API_KEY env var)"
    )
    parser.add_argument(
        "--workflow",
        type=str,
        choices=["all", "email", "document", "intake"],
        default="all",
        help="Which workflow demo to run"
    )
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("Error: Please provide a Gemini API key via --api-key or GEMINI_API_KEY environment variable")
        sys.exit(1)
    
    asyncio.run(run_demo(args.api_key))


if __name__ == "__main__":
    main()
