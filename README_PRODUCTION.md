# Ada Agent Provisioning - Production Guide

Automated workflow for provisioning Ada AI agent demos when clients reach Stage 0.

## 🚀 Quick Start

### 1. Setup

```bash
# Clone and navigate to the project
cd ada_agent_provisioning

# Run setup script
./setup.sh

# Edit .env with your API keys
nano .env
```

### 2. Run via CLI (Fastest)

```bash
# With manual Ada API key
python3 provision.py --company "Pepsi" --ada-key "abc123..."

# With automatic key retrieval
python3 provision.py --company "Coca-Cola" --auto

# With custom settings
python3 provision.py --company "Starbucks" --ada-key "xyz789..." --articles 15 --questions 100

# Dry run (validate only)
python3 provision.py --company "Nike" --ada-key "test123" --dry-run
```

### 3. Run via Web UI

```bash
# Terminal 1: Start API server
python3 api_server.py

# Terminal 2: Serve web UI
cd web && python3 -m http.server 3000

# Open browser to http://localhost:3000
```

---

## 📁 Project Structure

```
ada_agent_provisioning/
├── provision.py          # Main CLI tool (production-ready)
├── api_server.py         # FastAPI server for webhooks + web UI
├── setup.sh              # Setup and validation script
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (API keys)
│
├── web/                  # Web UI
│   └── index.html       # Simple single-page app
│
├── app/                  # Original modular code
│   ├── main.py
│   ├── clients/
│   ├── services/
│   └── models/
│
├── run_pepsi_standalone.py    # Legacy standalone script
└── DEPLOYMENT_OPTIONS.md      # Deployment guide
```

---

## 🔑 Environment Variables

Required in `.env` file:

```bash
# Anthropic API (Required)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Ada Bot Cloning (Required)
ADA_CLONE_SECRET=nRk3zkYVe>@Khm?Q2dY8axrR.5ucqPGF
ADA_EMAIL=scteam@ada.support
ADA_PASSWORD=Adalovelace123!

# Beeceptor (Required for API endpoints)
BEECEPTOR_AUTH_TOKEN=3db584716ce6764c1004850ee20e610e470aee7cTnwDhrdgQaknDva

# Optional
PLAYWRIGHT_HEADLESS=false    # Set to true for headless browser
SLACK_CHANNEL_ID=...         # For notifications (future feature)
```

---

## 🛠️ Features

### ✅ What's Implemented

1. **CLI Tool** (`provision.py`)
   - Production-ready command-line interface
   - Manual or automatic Ada API key retrieval
   - Configurable article/question/conversation counts
   - Dry-run mode for validation
   - Colored terminal output
   - Progress tracking

2. **Web UI** (`web/index.html`)
   - Simple form interface
   - Real-time progress tracking
   - Result display with clickable links
   - Mobile-responsive design

3. **API Server** (`api_server.py`)
   - FastAPI backend
   - Webhook endpoint for Salesforce/Zapier
   - REST API for web UI
   - Background job processing
   - Job status tracking
   - CORS enabled

4. **Setup Script** (`setup.sh`)
   - Dependency installation
   - Environment validation
   - API key testing
   - Playwright browser installation

### 🔄 Workflow Phases

1. **Bot Handle Generation** - Clean handle from company name
2. **Bot Cloning** - Clone template bot via API
3. **API Key Retrieval** - Manual or Playwright automation
4. **Knowledge Base** - Generate description + articles
5. **Questions** - Generate customer questions
6. **Beeceptor Endpoints** - Create mock API endpoints
7. **Conversations** - Create channel + conversations

---

## 🌐 Deployment Options

### Option 1: Railway (Recommended for MVP)

**Fastest deployment, lowest cost**

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and initialize
railway login
railway init

# 3. Add environment variables in Railway dashboard
# (Copy from .env file)

# 4. Deploy
railway up
```

**Cost:** ~$5-10/month
**Setup Time:** ~30 minutes

### Option 2: AWS Lambda

**Best for production scale**

See `DEPLOYMENT_OPTIONS.md` for detailed AWS setup.

**Cost:** ~$20-50/month
**Setup Time:** ~2-4 hours

### Option 3: Docker (Self-Hosted)

```bash
# Build image
docker build -t ada-provisioning .

# Run container
docker run -p 8000:8000 --env-file .env ada-provisioning
```

---

## 🔌 Zapier Integration

### Current Zapier Webhook Setup

1. **Trigger:** Salesforce Opportunity updated
2. **Filter:** Stage = "Stage 0"
3. **Action:** Webhook POST to your API

### Webhook URL (Update in Zapier)
```
https://your-domain.com/api/webhook/salesforce
```

### Webhook Payload
```json
{
  "opportunity_id": "{{opportunity_id}}",
  "account_name": "{{account_name}}",
  "stage": "{{stage}}",
  "ada_api_key": null
}
```

---

## 📊 API Documentation

### Start Server
```bash
python3 api_server.py
```

### Interactive API Docs
Open browser to `http://localhost:8000/docs`

### Endpoints

#### POST `/api/provision`
Create new provisioning job

**Request:**
```json
{
  "company_name": "Pepsi",
  "ada_api_key": "abc123..." or null,
  "auto_retrieve_key": true,
  "num_articles": 10,
  "num_questions": 70,
  "num_conversations": 70
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "message": "Provisioning job started"
}
```

#### GET `/api/jobs/{job_id}`
Get job status

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "company_name": "Pepsi",
  "result": {
    "bot_url": "https://pepsi-ai-agent-demo.ada.support",
    "api_key": "abc...",
    ...
  }
}
```

#### POST `/api/webhook/salesforce`
Webhook for Salesforce/Zapier triggers

---

## 🧪 Testing

### Test CLI
```bash
# Dry run
python3 provision.py --company "Test Corp" --ada-key "test" --dry-run

# Real run with minimal settings
python3 provision.py --company "Test Corp" --ada-key "your_key" --articles 2 --questions 5 --conversations 3
```

### Test API Server
```bash
# Start server
python3 api_server.py &

# Test health check
curl http://localhost:8000/

# Test provisioning
curl -X POST http://localhost:8000/api/provision \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Test", "ada_api_key": "test123"}'
```

---

## 🐛 Troubleshooting

### Issue: Playwright fails to get API key

**Solution 1:** Use manual key instead
```bash
python3 provision.py --company "Pepsi" --ada-key "abc123..."
```

**Solution 2:** Check Playwright browser
```bash
playwright install chromium
```

**Solution 3:** Set headless mode
```bash
# In .env
PLAYWRIGHT_HEADLESS=true
```

### Issue: Anthropic API errors

**Check key is valid:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 -c "from anthropic import Anthropic; Anthropic(api_key='$ANTHROPIC_API_KEY').messages.create(model='claude-sonnet-4-5-20250929', max_tokens=10, messages=[{'role':'user','content':'hi'}])"
```

### Issue: Ada API returns 401

The Ada API key may have expired or not yet activated.
- Wait 28 days after key creation for activation
- Or retrieve a new key via Playwright
- Or manually create a new key in Ada dashboard

---

## 📈 Monitoring & Logging

### CLI Logging
All output goes to stdout with colored status indicators:
- 🎭 Cyan: In progress
- ✅ Green: Success
- ⚠️ Yellow: Warning
- ❌ Red: Error

### API Server Logging
Logs are written to stdout. In production, configure log aggregation:
- AWS CloudWatch
- Datadog
- LogDNA
- Papertrail

### Job History
Currently in-memory. For production, persist to:
- PostgreSQL
- DynamoDB
- MongoDB

---

## 🔐 Security Notes

### Production Checklist
- [ ] Use environment variables, not hardcoded keys
- [ ] Enable HTTPS/SSL
- [ ] Add authentication to web UI (Basic Auth, OAuth, JWT)
- [ ] Rate limiting on API endpoints
- [ ] Input validation and sanitization
- [ ] CORS restrictions (update allowed origins)
- [ ] API key rotation policy
- [ ] Audit logging for all provisioning actions

### Recommended: Add Authentication

```python
# In api_server.py
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@app.post("/api/provision")
async def provision(
    request: ProvisionRequest,
    credentials: HTTPBasicCredentials = Depends(security)
):
    # Validate credentials
    if credentials.username != "admin" or credentials.password != "secret":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # ... rest of code
```

---

## 📚 Additional Resources

- [DEPLOYMENT_OPTIONS.md](./DEPLOYMENT_OPTIONS.md) - Detailed deployment guide
- [ZAPIER_WORKFLOW_ANALYSIS.md](./ZAPIER_WORKFLOW_ANALYSIS.md) - Original Zapier workflow analysis
- FastAPI Docs: https://fastapi.tiangolo.com
- Railway Docs: https://docs.railway.app

---

## 🎯 Roadmap

### Completed ✅
- [x] CLI tool with full configuration
- [x] Web UI with real-time progress
- [x] FastAPI server with webhooks
- [x] Setup script and validation
- [x] Dry-run mode

### In Progress 🚧
- [ ] Improved Playwright API key extraction
- [ ] Deployment to Railway/Vercel
- [ ] Authentication for web UI

### Future Features 🔮
- [ ] Slack notifications
- [ ] Email reports
- [ ] Multi-tenant support
- [ ] Custom branding options
- [ ] Advanced analytics dashboard
- [ ] Batch provisioning
- [ ] Template management
- [ ] Audit logging
- [ ] User management

---

## 👥 Team Access

### Internal Team Only (Current)
Deploy behind VPN or with basic password protection

### External Customers (Future)
Add user authentication, per-customer API keys, usage tracking

---

## 💬 Support

Questions? Contact the Solutions Consulting team.

**Last Updated:** February 10, 2026
