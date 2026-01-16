# BrightLaw A2A Multi-Agent System

An Agent-to-Agent (A2A) architecture for AI-powered legal automation, designed for UK legal services firms.

## 🏗️ Architecture Overview

This system implements a multi-agent architecture where specialized AI agents collaborate to handle complex legal workflows. Each agent is responsible for a specific domain task and communicates through a standardized A2A protocol.

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR AGENT                          │
│        (Coordinates workflows, routes requests)                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│  Email Triage   │ │  Document   │ │ Client Intake   │
│     Agent       │ │Classification│ │    Agent        │
│                 │ │   Agent     │ │                 │
│ • Classify      │ │ • Classify  │ │ • Conflict check│
│ • Extract       │ │ • Extract   │ │ • Risk assess   │
│ • Route         │ │   metadata  │ │ • Fee estimate  │
└─────────────────┘ └─────────────┘ └─────────────────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────────────────────┐
│ Response Gen    │ │      Deadline Tracker Agent     │
│    Agent        │ │                                 │
│                 │ │ • Extract deadlines             │
│ • Draft replies │ │ • Calculate limitations         │
│ • Match tone    │ │ • Generate reminders            │
└─────────────────┘ └─────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google Gemini API key

### Installation

```bash
# Clone or navigate to the project
cd brightlaw-a2a

# Install dependencies
pip install -r requirements.txt

# Set your API key
export GEMINI_API_KEY=your_api_key_here
```

### Running the Demo

```bash
# Run the command-line demo
python main.py

# Or specify API key directly
python main.py --api-key YOUR_API_KEY
```

### Running the API Server

```bash
# Start the FastAPI server
python server.py

# Or with uvicorn for development
uvicorn server:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## 📁 Project Structure

```
brightlaw-a2a/
├── core/
│   ├── __init__.py
│   ├── a2a_protocol.py      # A2A message types, base agent class
│   └── llm_client.py        # Gemini API wrapper
├── agents/
│   ├── __init__.py
│   ├── email_triage_agent.py
│   ├── document_classification_agent.py
│   ├── client_intake_agent.py
│   ├── deadline_tracker_agent.py
│   ├── response_generator_agent.py
│   └── orchestrator_agent.py
├── demo_data/
│   └── sample_data.json     # Sample emails, documents, intakes
├── main.py                  # CLI demo application
├── server.py                # FastAPI server
├── requirements.txt
└── README.md
```

## 🤖 Agents

### 1. Email Triage Agent
**ID:** `email_triage_agent`

Classifies and routes incoming emails.

**Capabilities:**
- `email_classification` - Classify by intent, urgency, practice area
- `email_entity_extraction` - Extract client names, dates, actions
- `email_full_triage` - Complete triage with routing recommendation

**Intent Types:** status_inquiry, document_request, appointment, new_matter, complaint, general_inquiry, payment, urgent_legal

### 2. Document Classification Agent
**ID:** `document_classification_agent`

Classifies legal documents and extracts metadata.

**Capabilities:**
- `document_classification` - Identify document type
- `document_metadata_extraction` - Extract parties, dates, terms
- `document_full_classification` - Complete analysis with flags

**Document Types:** Contracts, correspondence, court documents, corporate documents, property documents

### 3. Client Intake Agent
**ID:** `client_intake_agent`

Processes new client inquiries and onboarding.

**Capabilities:**
- `conflict_check` - Check against existing clients
- `risk_assessment` - Assess matter risk level
- `fee_estimation` - Generate fee estimates
- `full_intake` - Complete intake process

### 4. Deadline Tracker Agent
**ID:** `deadline_tracker_agent`

Extracts and monitors deadlines.

**Capabilities:**
- `deadline_extraction` - Extract dates from content
- `full_deadline_analysis` - Complete analysis with reminders

**Deadline Types:** Limitation periods, court deadlines, contractual, regulatory, internal

### 5. Response Generator Agent
**ID:** `response_generator_agent`

Generates draft responses to client communications.

**Capabilities:**
- `generate_response` - Full response draft
- `generate_acknowledgment` - Quick acknowledgment

### 6. Orchestrator Agent
**ID:** `orchestrator_agent`

Coordinates multi-agent workflows.

**Workflows:**
- `email_processing` - Full email handling pipeline
- `document_processing` - Document classification + deadline extraction
- `new_client_intake` - Complete intake workflow
- `deadline_extraction` - Standalone deadline analysis

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### List Agents
```bash
GET /api/agents
```

### Execute Workflow
```bash
POST /api/workflow
Content-Type: application/json

{
  "workflow_type": "email_processing",
  "input_data": {
    "email_id": "email_001",
    "sender_email": "client@example.com",
    "sender_name": "John Smith",
    "subject": "Contract Review",
    "body": "..."
  },
  "priority": "normal"
}
```

### Direct Agent Invocation
```bash
POST /api/agent/email_triage_agent
Content-Type: application/json

{
  "agent_id": "email_triage_agent",
  "task_type": "email_classification",
  "input_data": {...}
}
```

### Convenience Endpoints
```bash
POST /api/email/triage
POST /api/document/classify
POST /api/intake/new
```

## 🔄 A2A Protocol

The system implements a standardized Agent-to-Agent protocol:

### Message Types
- `TASK_REQUEST` - Request to execute a task
- `TASK_RESPONSE` - Response with results
- `TASK_UPDATE` - Progress updates
- `HUMAN_ESCALATION` - Escalation to human review

### Task States
- `pending` - Task queued
- `in_progress` - Task executing
- `waiting_for_input` - Needs additional input
- `delegated` - Delegated to another agent
- `completed` - Successfully completed
- `failed` - Execution failed

### Agent Card
Each agent declares its capabilities via an Agent Card:
```python
{
    "agent_id": "email_triage_agent",
    "name": "Email Triage Agent",
    "description": "...",
    "capabilities": [
        {
            "name": "email_classification",
            "input_schema": {...},
            "output_schema": {...},
            "estimated_duration_seconds": 5,
            "requires_human_review": false
        }
    ]
}
```

## 🛡️ Human-in-the-Loop

The system includes built-in escalation mechanisms:

1. **Confidence Thresholds** - Low confidence scores trigger human review
2. **Critical Tasks** - Certain tasks always require approval
3. **Risk Flags** - High-risk matters escalate to senior partners
4. **Conflict Detection** - Potential conflicts require human decision

## 🇬🇧 UK Legal Context

The system is designed for UK legal practice:

- **SRA Compliance** - Solicitors Regulation Authority requirements
- **GDPR** - Data protection considerations
- **Legal Privilege** - Confidentiality handling
- **Limitation Periods** - UK-specific time limits
- **AML/KYC** - Anti-money laundering checks

## 📊 Example Output

```
======================================================================
  EMAIL PROCESSING WORKFLOW
======================================================================

Processing email from: John Smith
Subject: Urgent: Employment Contract Review Needed

--- Email Triage Results ---
  Intent: new_matter
  Urgency: high
  Practice Area: employment
  Confidence: 87%
  Client: TechCorp Ltd
  Action Requested: Review employment contracts for compliance

--- Generated Response Draft ---
  Subject: Re: Urgent: Employment Contract Review Needed
  Confidence: 82%
  
  Body:
  Dear Mr Smith,
  
  Thank you for your enquiry regarding employment contract reviews...

--- Workflow Summary ---
  Steps Executed: 4
  Agents Used: email_triage_agent, deadline_tracker_agent, response_generator_agent
  Duration: 4523ms
  Requires Human Review: Yes
  Escalation Reasons:
    - New client intake requires lawyer approval
```

## 🔧 Configuration

Environment variables:
```bash
GEMINI_API_KEY=your_api_key      # Required
GEMINI_MODEL=gemini-2.0-flash    # Optional, default model
```

## 📝 License

Proprietary - For assessment purposes only.

---

Built for the Fescom Tech360 AI Senior Engineer Technical Assessment.
