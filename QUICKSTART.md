# BrightLaw A2A - Quick Start Guide

## 📦 What's Included

```
brightlaw-a2a/
├── core/                    # A2A protocol & LLM client
├── agents/                  # 6 specialized AI agents
├── demo_data/              # Sample test data
├── frontend/               # React dashboard UI
├── main.py                 # CLI demo application
├── server.py               # FastAPI REST server
├── .env                    # API key configuration
├── requirements.txt        # Python dependencies
└── README.md               # Full documentation
```

## 🚀 Setup Instructions

### Step 1: Extract the ZIP file
```bash
unzip brightlaw-a2a.zip
cd brightlaw-a2a
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Get a Gemini API Key
1. Go to https://aistudio.google.com/apikey
2. Create a new API key
3. Copy the key

### Step 5: Configure Your API Key
Edit the `.env` file in the project root:
```bash
GEMINI_API_KEY=your_actual_api_key_here
```

The `.env` file is automatically loaded by both `main.py` and `server.py`.

**Alternative:** Set environment variable directly:
```bash
# On Mac/Linux:
export GEMINI_API_KEY=your_api_key_here

# On Windows (PowerShell):
$env:GEMINI_API_KEY="your_api_key_here"
```

## ▶️ Running the Application

### Option A: Command Line Demo
```bash
python main.py
```

This will:
- Initialize all 6 agents
- Process a sample email through the full workflow
- Classify a sample document
- Run a client intake simulation
- Display results in the terminal

### Option B: REST API Server
```bash
python server.py
```

Then open your browser to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Option C: Specify API Key Directly
```bash
python main.py --api-key YOUR_GEMINI_API_KEY
```

### Option D: React Frontend Dashboard
```bash
# Terminal 1: Start the backend API
python server.py

# Terminal 2: Start the frontend
cd frontend
npm install
npm run dev
```

Then open your browser to **http://localhost:3000**

The frontend provides:
- **Dashboard**: See all registered agents and their capabilities
- **Architecture**: Visual explanation of how components connect
- **Email Workflow**: Interactive email processing with sample data
- **Document Workflow**: Document classification interface
- **Client Intake**: Full intake workflow with results visualization

## 🧪 Test API Endpoints

Once the server is running:

### Check Health
```bash
curl http://localhost:8000/health
```

### List All Agents
```bash
curl http://localhost:8000/api/agents
```

### Process an Email
```bash
curl -X POST http://localhost:8000/api/email/triage \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "test_001",
    "sender_email": "client@example.com",
    "sender_name": "John Smith",
    "subject": "Contract Review Needed",
    "body": "Hi, I need help reviewing my employment contract before signing."
  }'
```

## 🤖 Available Agents

| Agent | Purpose |
|-------|---------|
| `email_triage_agent` | Classifies & routes emails |
| `document_classification_agent` | Identifies document types |
| `client_intake_agent` | New client onboarding |
| `deadline_tracker_agent` | Extracts deadlines |
| `response_generator_agent` | Drafts replies |
| `orchestrator_agent` | Coordinates workflows |

## 📋 Available Workflows

| Workflow | What It Does |
|----------|--------------|
| `email_processing` | Full email → triage → deadlines → response |
| `document_processing` | Document → classify → extract deadlines |
| `new_client_intake` | Intake → conflicts → risk → fees |
| `deadline_extraction` | Extract all deadlines from content |

## ❓ Troubleshooting

### "GEMINI_API_KEY not set"
Make sure you've exported the environment variable in the same terminal session.

### Import errors
Make sure you're in the `brightlaw-a2a` directory and have activated your virtual environment.

### Connection refused on port 8000
The server might already be running. Try a different port:
```bash
uvicorn server:app --port 8001
```

## 🔗 How main.py and server.py Connect

Both entry points use the **same underlying agent system**:

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   main.py   │────▶│   Orchestrator   │◀────│  server.py  │
│  (CLI Demo) │     │     Agent        │     │  (REST API) │
└─────────────┘     └────────┬─────────┘     └─────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
  │Email Triage │    │  Document   │    │  Deadline   │
  │   Agent     │    │ Classifier  │    │  Tracker    │
  └─────────────┘    └─────────────┘    └─────────────┘
```

- **main.py**: Runs demo workflows directly via Python
- **server.py**: Exposes the same workflows via REST API
- **Both** use the same `core/` and `agents/` modules

## 📚 Next Steps

- Read `README.md` for full architecture documentation
- Explore `demo_data/sample_data.json` for test cases
- Check the agent files in `agents/` to understand task flows
- Use the FastAPI docs at `/docs` to test all endpoints
- Try the **React frontend** at `http://localhost:3000` for a visual experience

---

**Questions?** The system is designed to demonstrate A2A architecture for the Fescom Tech360 assessment.
