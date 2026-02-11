# Ada Agent Provisioning - Deployment Options

## Overview
This document outlines different deployment strategies for the Ada Agent Provisioning automation, considering both internal team use and external customer access.

## Architecture Components

### Core Service (FastAPI Backend)
- Handles webhook triggers from Salesforce/Zapier
- Provides REST API for web UI
- Manages workflow orchestration
- Stores configuration and state

### Web UI (React/Next.js Frontend)
- Simple form interface for manual provisioning
- Real-time progress tracking
- Authentication/authorization
- Dashboard for viewing created demos

---

## Deployment Options

### Option 1: Cloud Hosting (Recommended for External Access)
**Best for: Sharing with customers, broader team access, production use**

#### A. AWS (Recommended)
```
Frontend: AWS Amplify or S3 + CloudFront
Backend: AWS Lambda + API Gateway (serverless)
Database: DynamoDB or RDS PostgreSQL
Queue: SQS for async job processing
```

**Pros:**
- Scalable and reliable
- Pay only for what you use
- Easy to set up authentication (AWS Cognito)
- Can handle external traffic securely

**Estimated Cost:** $20-50/month for low volume

#### B. Google Cloud Platform
```
Frontend: Firebase Hosting
Backend: Cloud Run (containerized FastAPI)
Database: Firestore or Cloud SQL
Queue: Cloud Tasks
```

**Pros:**
- Simple deployment with Cloud Run
- Good integration with Firebase Auth
- Generous free tier

**Estimated Cost:** $15-40/month for low volume

#### C. Vercel + Railway (Easiest Setup)
```
Frontend: Vercel (free tier)
Backend: Railway (FastAPI container)
Database: Railway PostgreSQL
```

**Pros:**
- Fastest to deploy
- Great developer experience
- Automatic HTTPS
- Good for MVPs

**Estimated Cost:** $5-20/month (Railway has free tier)

---

### Option 2: Self-Hosted (Your Infrastructure)
**Best for: Internal use only, data security requirements**

#### A. Docker + Your Server
```bash
# Single docker-compose.yml deploys everything
docker-compose up -d
```

**Pros:**
- Full control
- No external costs (except server)
- Keep all data in-house

**Cons:**
- You manage uptime/backups
- Need to set up SSL/DNS
- Scaling is manual

#### B. Kubernetes (if you already have k8s)
```
Deploy as microservices in your existing k8s cluster
```

**Pros:**
- Enterprise-grade
- Auto-scaling
- Existing infrastructure

**Cons:**
- Complex setup if you don't already have k8s

---

## Recommended Solution: **Hybrid Cloud Approach**

### Phase 1: Internal Team (Quick Start)
```
Deploy to Railway or AWS Lambda
- Team access only (password protected)
- Zapier webhook works
- Simple web form for manual runs
```

**Timeline:** 1-2 days to deploy
**Cost:** $5-20/month

### Phase 2: Customer Self-Service (Future)
```
Upgrade to production-grade
- Public web UI with authentication
- Customer accounts/tenants
- Usage tracking and billing
- Better security and rate limiting
```

**Timeline:** 1-2 weeks additional development
**Cost:** $50-200/month depending on usage

---

## Authentication Strategies

### For Internal Team Only
```
- Simple password protection
- Or email allowlist
- OAuth with Google Workspace
```

### For External Customers
```
- Email/password signup
- Magic link authentication
- OAuth (Google, Microsoft)
- API keys for programmatic access
```

---

## Zapier Integration

### Current Flow (Maintained)
```
Salesforce Opportunity (Stage 0)
    ↓
Zapier Webhook Trigger
    ↓
Your Hosted Service (/api/webhook/salesforce)
    ↓
Automated Provisioning
    ↓
Slack Notification to Team
```

### New Flow (Web UI)
```
User fills form at https://demo.yourcompany.com
    ↓
Submits company name
    ↓
Your Hosted Service (/api/provision)
    ↓
Shows real-time progress
    ↓
Displays results + login credentials
```

---

## Security Considerations

### For Internal Use
- VPN or IP allowlist
- Basic authentication
- HTTPS only
- Environment variable secrets

### For External Use
- Rate limiting (prevent abuse)
- API key management
- User authentication
- Input validation and sanitization
- Audit logging
- CAPTCHA for public forms

---

## Recommended Tech Stack

### Backend
```python
FastAPI (Python)
- Async/await for performance
- Automatic API docs
- Easy to deploy
- Type hints for safety
```

### Frontend
```javascript
Next.js (React)
- Server-side rendering
- API routes
- Easy deployment (Vercel)
- Great DX
```

### Database
```
PostgreSQL
- Store provisioning history
- Track API keys
- User accounts (if needed)
- Queue status
```

### Job Queue
```
Celery + Redis or AWS SQS
- Handle long-running workflows
- Retry failed jobs
- Monitor progress
```

---

## Cost Breakdown (Estimated)

### Small Scale (< 50 demos/month)
- **Railway/Vercel:** $10-20/month
- **AWS Lambda + S3:** $20-30/month
- **Total:** $10-30/month

### Medium Scale (50-200 demos/month)
- **AWS (Lambda + RDS + S3):** $50-100/month
- **GCP (Cloud Run + SQL):** $40-80/month
- **Total:** $40-100/month

### Large Scale (200+ demos/month)
- **AWS with dedicated compute:** $200-500/month
- **Enterprise features:** Additional costs
- **Total:** $200-500/month

---

## Next Steps

1. **Choose Deployment Strategy**
   - Internal only? → Railway or Docker on your server
   - Customer-facing? → AWS Lambda or GCP Cloud Run

2. **Build Web UI**
   - Simple form (company name, description)
   - Progress tracking
   - Results display

3. **Add Authentication**
   - Start with simple password protection
   - Upgrade to OAuth later if needed

4. **Deploy & Test**
   - Deploy backend first
   - Test webhook from Zapier
   - Add web UI
   - Test manual provisioning

5. **Monitor & Iterate**
   - Add logging/monitoring
   - Collect feedback
   - Improve UX

---

## Questions to Decide

1. **Who needs access?**
   - Just your team? → Simple deployment
   - External customers? → Need auth + public hosting

2. **Budget?**
   - < $20/month? → Railway or self-hosted
   - $50-100/month? → AWS/GCP
   - No limit? → Enterprise-grade setup

3. **Timeline?**
   - Need it this week? → Railway (fastest)
   - Can wait 2 weeks? → AWS Lambda (better long-term)

4. **Technical expertise?**
   - Comfortable with DevOps? → Self-hosted Docker
   - Prefer managed services? → Railway/Vercel/AWS

---

## My Recommendation

**Start with Railway + Vercel (Week 1)**
```
Backend: Railway ($5-10/month)
Frontend: Vercel (free)
Database: Railway PostgreSQL (included)
Total: ~$10/month
```

**Why?**
- Deployed in hours, not days
- Easy to upgrade later
- Good for MVP/testing
- Can handle both webhook and web UI
- Cheap enough to run indefinitely

**Then upgrade to AWS if needed (Week 2-4)**
```
When: If you need more scale or external access
Backend: AWS Lambda
Frontend: AWS Amplify or S3+CloudFront
Database: RDS PostgreSQL
Total: ~$50/month
```

**Why upgrade?**
- Better for customer-facing product
- More robust and scalable
- Better security features
- Enterprise credibility
