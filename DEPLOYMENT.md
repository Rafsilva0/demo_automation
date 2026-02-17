# Deploying to Fly.io

This guide explains how to deploy the Ada Agent Provisioning service to Fly.io so your team can provision AI agents by just providing a company name.

## What is Fly.io?

Fly.io is a platform for running full-stack apps globally. It:
- Runs Docker containers on servers around the world
- Automatically scales based on demand (0 to many machines)
- Provides **free tier** with 3 shared CPUs and 256MB RAM
- Perfect for APIs and automation services like this
- Spins up in ~1 second when a request comes in

## Can Playwright Run on Fly.io?

**Yes!** Playwright works perfectly on Fly.io because:
1. Fly.io supports full Docker containers with system access
2. The Dockerfile installs all necessary browser dependencies (Chromium + deps)
3. Headless Chromium runs great in the container
4. Each provisioning job gets its own isolated browser session
5. The container has enough resources to run automated browser tasks

## How Your Team Will Use It

After deployment, your team members can:

1. **Via Web UI**: Go to `https://your-app.fly.dev` and enter a company name
2. **Via API**: POST to `/api/provision` with `{"company_name": "Trader Joes"}`
3. **Via Zapier**: Connect Zapier to auto-provision when opportunities are created

That's it! No technical knowledge needed.

## Prerequisites

- Docker (for containerized deployment)
- Access to:
  - Salesforce org with API access
  - Ada platform with API credentials
  - OpenAI API key
  - Slack workspace with webhook access

## Local Development

### 1. Setup Environment

```bash
# Clone repository
git clone <repository-url>
cd ada_agent_provisioning

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your credentials
```

### 2. Configure Environment Variables

Edit `.env` with your actual credentials:

```bash
# Salesforce
SALESFORCE_USERNAME=your_username@company.com
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_token

# Ada
ADA_API_KEY=your_ada_key

# OpenAI
OPENAI_API_KEY=sk-your_openai_key

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 3. Run Locally

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --port 8000

# Or using Docker Compose
docker-compose up
```

Access the API at: http://localhost:8000

View docs at: http://localhost:8000/docs

## Production Deployment Options

### Option 1: AWS Lambda (Serverless)

#### Setup

1. Install AWS SAM CLI
2. Create `template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  AdaProvisioningFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.main.handler
      Runtime: python3.11
      MemorySize: 512
      Timeout: 900
      Environment:
        Variables:
          SALESFORCE_USERNAME: !Ref SalesforceUsername
          ADA_API_KEY: !Ref AdaApiKey
          # ... other env vars
      Events:
        SalesforceWebhook:
          Type: Api
          Properties:
            Path: /webhook/salesforce/opportunity
            Method: post
```

3. Deploy:

```bash
sam build
sam deploy --guided
```

### Option 2: Google Cloud Run

```bash
# Build container
docker build -t ada-provisioning .

# Tag for GCR
docker tag ada-provisioning gcr.io/PROJECT_ID/ada-provisioning

# Push to GCR
docker push gcr.io/PROJECT_ID/ada-provisioning

# Deploy to Cloud Run
gcloud run deploy ada-provisioning \
  --image gcr.io/PROJECT_ID/ada-provisioning \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "$(cat .env | xargs)"
```

### Option 3: Azure Container Instances

```bash
# Create Azure Container Registry
az acr create --resource-group myResourceGroup \
  --name adaProvisioningRegistry --sku Basic

# Build and push
az acr build --registry adaProvisioningRegistry \
  --image ada-provisioning:latest .

# Deploy
az container create --resource-group myResourceGroup \
  --name ada-provisioning \
  --image adaProvisioningRegistry.azurecr.io/ada-provisioning:latest \
  --dns-name-label ada-provisioning \
  --ports 8000 \
  --environment-variables $(cat .env | xargs)
```

### Option 4: Kubernetes (Production Grade)

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ada-provisioning
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ada-provisioning
  template:
    metadata:
      labels:
        app: ada-provisioning
    spec:
      containers:
      - name: ada-provisioning
        image: your-registry/ada-provisioning:latest
        ports:
        - containerPort: 8000
        env:
        - name: SALESFORCE_USERNAME
          valueFrom:
            secretKeyRef:
              name: ada-secrets
              key: salesforce-username
        # ... other env vars
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ada-provisioning-service
spec:
  selector:
    app: ada-provisioning
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:

```bash
# Create secrets
kubectl create secret generic ada-secrets \
  --from-env-file=.env

# Deploy
kubectl apply -f k8s-deployment.yaml
```

## Salesforce Integration

### Configure Salesforce Flow

1. In Salesforce Setup, go to **Flows**
2. Create a **Record-Triggered Flow**:
   - Object: Opportunity
   - Trigger: When a record is updated
   - Condition: StageName equals "Stage 0"
3. Add action: **Platform Event** or **HTTP Callout**
   - URL: `https://your-deployment-url/webhook/salesforce/opportunity`
   - Method: POST
   - Body:
     ```json
     {
       "opportunity_id": "{!$Record.Id}",
       "stage": "{!$Record.StageName}",
       "account_id": "{!$Record.AccountId}",
       "timestamp": "{!$Flow.CurrentDateTime}"
     }
     ```

### Alternative: Salesforce Process Builder

If Flow is not available, use Process Builder with similar configuration.

## Monitoring and Observability

### Logs

The service uses structured logging. In production, configure log aggregation:

**CloudWatch (AWS):**
```bash
# Already configured if using Lambda
```

**Google Cloud Logging:**
```bash
# Automatic with Cloud Run
```

**Custom (ELK Stack):**
```bash
# Configure logstash forwarder
```

### Metrics

Add Prometheus metrics (optional):

```python
# app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### Alerts

Configure alerts for:
- Workflow failures
- API timeouts
- High error rates

Example Slack alert webhook in code (already implemented in SlackClient).

## Security

### Environment Variables

Never commit `.env` to version control. Use:
- AWS Secrets Manager (AWS)
- Google Secret Manager (GCP)
- Azure Key Vault (Azure)
- Kubernetes Secrets (K8s)

### Webhook Security

Enable webhook signature validation:

1. Set `WEBHOOK_SECRET` in environment
2. Salesforce sends `X-Webhook-Signature` header
3. Service validates before processing

### API Rate Limiting

Add rate limiting middleware:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/webhook/salesforce/opportunity")
@limiter.limit("10/minute")
async def handle_salesforce_opportunity(...):
    ...
```

## Testing Deployment

### Health Check

```bash
curl https://your-deployment-url/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "salesforce": "not_checked",
    "ada": "not_checked",
    "openai": "not_checked",
    "slack": "not_checked"
  }
}
```

### Test Webhook

```bash
curl -X POST https://your-deployment-url/webhook/salesforce/opportunity \
  -H "Content-Type: application/json" \
  -d '{
    "opportunity_id": "006XXXXXXXXXXXXXXX",
    "stage": "Stage 0",
    "account_id": "001XXXXXXXXXXXXXXX",
    "timestamp": "2024-01-01T00:00:00Z"
  }'
```

Expected response:
```json
{
  "success": true,
  "workflow_id": "wf_006XXXXXXXXXXXXXXX_1234567890",
  "message": "Ada agent provisioning workflow started for opportunity 006XXXXXXXXXXXXXXX"
}
```

## Rollback Plan

If deployment fails:

### Docker/K8s:
```bash
kubectl rollout undo deployment/ada-provisioning
```

### Cloud Run:
```bash
gcloud run services update-traffic ada-provisioning \
  --to-revisions=PREVIOUS_REVISION=100
```

### Lambda:
Use AWS Console to revert to previous version.

## Support

For issues or questions:
- Check logs: `kubectl logs -f deployment/ada-provisioning`
- Review workflow status: `GET /workflow/{workflow_id}`
- Contact: [your-team@company.com]

1. Install Fly.io CLI:
   ```bash
   brew install flyctl
   ```

2. Sign up and login:
   ```bash
   fly auth signup
   # or if you have an account:
   fly auth login
   ```

## Deployment Steps

### 1. Set Environment Variables

Your Ada credentials and API keys need to be stored as secrets on Fly.io:

```bash
fly secrets set \
  ADA_EMAIL="your-ada-email@example.com" \
  ADA_PASSWORD="your-ada-password" \
  OPENAI_API_KEY="your-openai-api-key"
```

### 2. Create the App

```bash
fly launch --config fly.toml --no-deploy
```

This creates the app but doesn't deploy yet (so you can configure it first).

### 3. Configure Resources (Optional)

The default config allocates 1GB RAM. For heavy usage, you can increase:

```bash
fly scale memory 2048  # 2GB RAM
```

### 4. Deploy

```bash
fly deploy
```

This will:
- Build the Docker image (includes Playwright + Chromium)
- Push to Fly.io's registry
- Deploy to their global network
- Start accepting requests

First deployment takes ~5 minutes. Subsequent deploys are faster.

### 5. Get Your API URL

```bash
fly status
```

Your API will be available at: `https://ada-agent-provisioning.fly.dev`

## Usage Examples

### Via Web UI

1. Open: `https://ada-agent-provisioning.fly.dev`
2. Enter company name: "Trader Joes"
3. Click "Provision Demo"
4. Wait 2-3 minutes
5. Get your provisioned AI agent!

### Via API

```bash
# Start provisioning
curl -X POST https://ada-agent-provisioning.fly.dev/api/provision \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Trader Joes"}'

# Response
{
  "job_id": "abc123",
  "status": "processing",
  "message": "Provisioning started for Trader Joes"
}

# Check status
curl https://ada-agent-provisioning.fly.dev/api/jobs/abc123
```

### Via Zapier Webhook

Set up a Zapier workflow:

1. **Trigger**: When new Salesforce Opportunity reaches Stage 0
2. **Action**: Webhooks by Zapier - POST
3. **URL**: `https://ada-agent-provisioning.fly.dev/api/provision`
4. **Body**: 
   ```json
   {
     "company_name": "{{Account Name}}"
   }
   ```

Your team can now auto-provision AI agents when deals close!

## Monitoring

### View Logs

```bash
fly logs           # Recent logs
fly logs --tail    # Live logs
```

### View Metrics

```bash
fly dashboard      # Opens web dashboard
fly status         # Shows current status
```

### Check Health

```bash
curl https://ada-agent-provisioning.fly.dev/health
```

## Scaling

Fly.io automatically scales based on demand:

- **Idle**: 0 machines running (saves costs)
- **1 request**: Spins up 1 machine in ~1 second
- **Multiple requests**: Can scale to multiple machines

Configure scaling:

```bash
# Set minimum machines (always running)
fly scale count 1      # Keep 1 machine always on

# Set maximum machines
fly scale count 1-5    # Scale from 1 to 5 machines

# For free tier, use 0-1
fly scale count 0-1    # Spin up only when needed
```

## Costs

### Free Tier (Recommended for Testing)

Includes:
- 3 shared CPUs
- 256MB RAM per machine  
- 160GB outbound transfer per month

Should handle: **10-20 provisioning jobs per day**

### Paid Tier (For Production)

If you need more:
- ~$2/month for always-on 1GB machine
- ~$0.02/GB for additional transfer
- Pay only for what you use

Estimate: **$5-10/month for 100+ jobs/day**

## Troubleshooting

### Browser Crashes

If Chromium crashes during provisioning:

```bash
fly scale memory 2048  # Increase to 2GB RAM
```

### Slow Provisioning

Check if app is in the right region:

```bash
fly regions list                    # Show all regions
fly regions add iad                 # Add US East (Virginia)
fly regions remove sjc              # Remove US West if not needed
```

### Deployment Fails

View build logs:

```bash
fly logs --tail
```

Common issues:
- Missing environment variables → Check `fly secrets list`
- Playwright install fails → Memory too low, scale up
- Port conflicts → Ensure Dockerfile exposes 5001

### View Running Machines

```bash
fly machines list
```

## Security Best Practices

### 1. Secrets Management

✅ **Good**: Use `fly secrets`
```bash
fly secrets set ADA_PASSWORD="secret"
```

❌ **Bad**: Hardcode in code or commit `.env` files

### 2. CORS Configuration

Update `api_server.py` for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

### 3. Rate Limiting

Consider adding rate limiting for public APIs:

```bash
fly secrets set RATE_LIMIT="100/minute"
```

### 4. Authentication (Optional)

For internal use, add API key auth:

```python
@app.post("/api/provision")
async def provision(
    request: ProvisionRequest,
    api_key: str = Header(None, alias="X-API-Key")
):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(401, "Invalid API key")
    # ... rest of code
```

## Updating the App

After making code changes:

```bash
# Commit changes
git add .
git commit -m "Update provisioning logic"

# Deploy to Fly.io
fly deploy
```

Fly.io will:
1. Build new Docker image
2. Test the health check
3. Roll out to machines
4. Keep old version if new one fails

Zero-downtime deploys! ✨

## Rollback

If something breaks:

```bash
fly releases                    # Show release history
fly releases rollback <version> # Rollback to specific version
```

## Monitoring & Alerts

Set up alerts for failures:

```bash
fly dashboard
# Go to "Monitoring" → "Set up alerts"
# Alert when: Health checks fail OR CPU > 80%
```

## Next Steps

Once deployed:

1. ✅ Test with 1-2 companies
2. ✅ Share URL with your team
3. ✅ Set up Zapier integration
4. ✅ Monitor logs for first few runs
5. ✅ Adjust resources if needed

## Support

Issues? Check:
- Logs: `fly logs --tail`
- Status: `fly status`
- Health: `curl https://your-app.fly.dev/health`

Common fixes:
- Increase memory: `fly scale memory 2048`
- Restart app: `fly apps restart`
- Redeploy: `fly deploy --force`
