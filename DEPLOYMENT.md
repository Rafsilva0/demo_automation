# Deployment Guide

This guide covers deploying the Ada Agent Provisioning Service to various environments.

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
