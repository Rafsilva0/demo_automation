# Ada Agent Provisioning Automation

Automated workflow for provisioning Ada AI agents when Salesforce opportunities reach Stage 0.

## Overview

This replaces a 31-step Zapier workflow with a Python FastAPI service that:
1. Receives webhook triggers from Salesforce (when Opp moves to Stage 0)
2. Retrieves account and partner data from Salesforce
3. Uses OpenAI to generate company descriptions, knowledge articles, and agent configurations
4. Provisions the complete Ada agent via API (knowledge sources, endpoints, channels, conversations)
5. Notifies the SC team via Slack

## Architecture

```
Salesforce Flow → Platform Event → FastAPI Webhook → Workflow Orchestrator
                                                              ↓
                                    ┌─────────────────────────┴──────────────────────┐
                                    ↓                         ↓                      ↓
                            Salesforce API              OpenAI API              Ada API
                            (Account data)         (Content generation)    (Agent provisioning)
                                    ↓                         ↓                      ↓
                                    └─────────────────────────┬──────────────────────┘
                                                              ↓
                                                         Slack API
                                                    (Team notification)
```

## Project Structure

```
ada_agent_provisioning/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration and environment variables
│   ├── models/                 # Pydantic models for data validation
│   │   ├── salesforce.py
│   │   ├── ada.py
│   │   └── workflow.py
│   ├── clients/                # API clients
│   │   ├── salesforce.py
│   │   ├── ada.py
│   │   ├── openai_client.py
│   │   └── slack.py
│   ├── services/               # Business logic
│   │   ├── workflow.py         # Main orchestration
│   │   ├── knowledge_builder.py
│   │   ├── agent_builder.py
│   │   └── content_generator.py
│   └── utils/                  # Utilities
│       ├── logger.py
│       └── retry.py
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Setup (To Be Updated)

1. Clone repository
2. Copy `.env.example` to `.env` and configure:
   - Salesforce credentials
   - Ada API key
   - OpenAI API key
   - Slack webhook URL
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `uvicorn app.main:app --reload`

## Deployment

TBD - Will support:
- Docker containerization
- Cloud deployment (AWS Lambda / Google Cloud Run / Azure Functions)
- Kubernetes for production

## Status

🚧 **In Development** - Awaiting Zapier configuration export to build implementation

## Next Steps

1. Export Zapier configuration (prompts, webhook URLs, API details)
2. Implement API clients (Salesforce, Ada, OpenAI, Slack)
3. Build workflow orchestration with error handling
4. Add comprehensive logging and monitoring
5. Create deployment configuration
