# BrightLaw A2A Frontend

A React-based dashboard for interacting with the BrightLaw Multi-Agent System.

## Prerequisites

- Node.js 18+ installed
- Backend server running (`python server.py` from parent directory)

## Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Open in browser:**
   Navigate to `http://localhost:3000`

## Features

- **Dashboard**: View all registered agents and their capabilities
- **Architecture**: Understand how main.py and server.py connect
- **Email Workflow**: Process and triage incoming emails
- **Document Workflow**: Classify legal documents
- **Client Intake**: Handle new client onboarding

## Usage

1. First, start the backend API server:
   ```bash
   cd ..
   python server.py
   ```

2. Then start the frontend:
   ```bash
   npm run dev
   ```

3. The frontend will proxy API requests to `http://localhost:8000`

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx      # Agent overview
│   │   ├── Architecture.jsx   # System architecture docs
│   │   ├── EmailWorkflow.jsx  # Email processing form
│   │   ├── DocumentWorkflow.jsx # Document classification
│   │   ├── IntakeWorkflow.jsx # Client intake form
│   │   └── WorkflowResult.jsx # Results display
│   ├── App.jsx                # Main application
│   ├── main.jsx              # Entry point
│   └── index.css             # Styles
├── index.html
├── vite.config.js
└── package.json
```

## API Endpoints Used

- `GET /health` - Server health check
- `GET /api/agents` - List all agents
- `POST /api/workflow` - Execute a workflow
- `POST /api/agent/{agent_id}` - Direct agent invocation
