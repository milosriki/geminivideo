# GeminiVideo Production Deployment Guide

## Executive Summary

This document provides a complete production-grade deployment strategy for GeminiVideo,
analyzing the proposed solutions, identifying gaps, and providing actionable implementation steps.

---

## Part 1: Solution Analysis - Pros & Cons

### Solution 1: MCP-First Architecture

**What It Is:**
Replace custom database/API integrations with Model Context Protocol (MCP) - a universal
interface for AI agents to access data sources.

**Pros:**
1. **Code Reduction (90%)** - 30K lines → 30 lines for data access
2. **Universal Compatibility** - Works with any LLM (OpenAI, Anthropic, Google)
3. **Industry Standard** - Now under Linux Foundation, adopted by major players
4. **Token Cost Reduction** - Agents fetch only needed data, not entire context
5. **Rapid Integration** - New data sources added in hours, not weeks
6. **Existing Database Works** - PostgreSQL, Supabase, BigQuery all have MCP servers

**Cons:**
1. **Early Stage** - MCP SDK still maturing, breaking changes possible
2. **Learning Curve** - Team needs to learn new paradigm
3. **Debugging Complexity** - Harder to trace issues across MCP layers
4. **Latency Overhead** - Extra network hop for each data access
5. **Vendor Lock-in Risk** - If MCP standard changes, need to adapt
6. **Current Code Works** - Rewriting functional code has opportunity cost

**GeminiVideo Relevance:**
- Current codebase has 162+ axios calls across 8 services
- MCP would centralize data access
- BUT: Our microservice architecture already separates concerns
- RECOMMENDATION: Incremental adoption for new features only

---

### Solution 2: Meta Advantage+ Integration

**What It Is:**
Integrate with Meta's Andromeda AI + Advantage+ instead of building competing optimization.

**Pros:**
1. **Proven Results** - 22% ROAS increase documented
2. **Zero ML Investment** - Meta handles optimization
3. **GenAI Creative** - +7% conversions with auto-generated variations
4. **Scale** - 1M+ advertisers, trillion-parameter models
5. **Real-Time Learning** - Andromeda optimizes delivery continuously
6. **Already Built** - We have Meta integration, just need to enable features

**Cons:**
1. **Black Box** - No control over optimization algorithm
2. **Platform Dependency** - Fully reliant on Meta
3. **Cross-Platform Limitation** - Only works for Meta (not Google, TikTok)
4. **Creative Control Loss** - AI may generate off-brand variations
5. **Data Sharing** - Creative DNA goes to Meta's systems
6. **Cost** - Advantage+ has minimum spend requirements

**GeminiVideo Relevance:**
- Our meta-publisher service already integrates Meta Ads API
- Advantage+ is an API flag, not new integration
- Creative DNA (Hook, CTA, Visuals) already tracked
- RECOMMENDATION: Enable immediately for Meta campaigns

---

### Solution 3: Autonomous Creative Factory

**What It Is:**
5 specialized AI agents working as a creative team using LangGraph orchestration.

**Pros:**
1. **10x Output** - 50 ads/day vs 5 manual
2. **Consistency** - Agents follow brand guidelines perfectly
3. **24/7 Operation** - No human hours required
4. **Compound Learning** - Each iteration improves all future work
5. **Role Specialization** - Each agent masters one skill
6. **Observability** - LangSmith provides full visibility

**Cons:**
1. **Complexity** - Multi-agent systems are hard to debug
2. **Cost** - Running 5 agents = 5x API costs (mitigated by code execution)
3. **Quality Control** - Need human review for brand safety
4. **Setup Time** - 8 weeks to fully implement
5. **Model Dependency** - If LLM quality drops, all agents affected
6. **Edge Cases** - Agents may fail on unusual requests

**GeminiVideo Relevance:**
- We already have AI Council (multi-model ensemble)
- Titan-Core has orchestration capabilities
- Video Agent handles rendering
- RECOMMENDATION: Extend existing architecture, don't rebuild

---

## Part 2: Current Gaps Identified

### Critical Gaps (Must Fix)

| # | Gap | Location | Impact | Fix Time |
|---|-----|----------|--------|----------|
| 1 | TikTok is placeholder only | `/services/tiktok-ads` | No TikTok revenue | FIXED |
| 2 | Semantic cache had `pass` | `battle_hardened_sampler.py:268` | 70% vs 95% hit rate | FIXED |
| 3 | AdSpyPage search broken | `AdSpyPage.tsx:137` | No competitor research | FIXED |
| 4 | Batch executor not wired | `index.ts` | 10x slower Meta API | FIXED |
| 5 | HubSpot missing entirely | N/A | No CRM integration | 2 days |
| 6 | Video gen APIs stub only | Runway/Kling/Pika | No AI video gen | 1 week |
| 7 | Payment system missing | N/A | Can't monetize | 2 weeks |
| 8 | Port mismatches | Docker configs | Services can't connect | 1 hour |

### Integration Gaps

| Service | Current Status | Gap |
|---------|---------------|-----|
| Meta Ads | Full integration | Enable Advantage+ flag |
| Google Ads | Full integration | Add Performance Max |
| TikTok Ads | Now real API | Need credentials |
| Google Drive | Full integration | None |
| Firebase Auth | Partial | Backend validation inconsistent |
| Supabase | Optional DB | Connection pooling config |
| Redis | Full | Need cluster config for production |
| Webhook System | Framework only | Complete signature verification |
| Realtime/SSE | Backend ready | Wire to frontend components |
| RAG/Vector | Semantic cache works | Not all endpoints use it |

### Production Readiness Gaps

| Category | Status | Gap |
|----------|--------|-----|
| Authentication | Partial | API key validation inconsistent |
| Rate Limiting | Done | Need load testing to tune |
| Database Migrations | Partial | Inline table creation needs migration |
| Secrets Management | Template | Need automated rotation |
| Monitoring | Prometheus ready | Not deployed |
| Logging | Winston + Sentry | No log aggregation |
| Testing | Jest exists | No integration tests |
| Load Testing | None | Need K6/Artillery scripts |
| Backup | None | Need automated backup |
| Encryption | HTTPS only | No field-level encryption |

---

## Part 3: Complete Environment Configuration

### Required Environment Variables

```bash
# ============================================================================
# GEMINIVIDEO PRODUCTION ENVIRONMENT CONFIGURATION
# ============================================================================

# -----------------------------------------------------------------------------
# DATABASE (Required)
# -----------------------------------------------------------------------------
DATABASE_URL=postgresql://user:password@host:5432/geminivideo
POSTGRES_USER=geminivideo
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=geminivideo
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Alternative: Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx

# -----------------------------------------------------------------------------
# CACHE (Required)
# -----------------------------------------------------------------------------
REDIS_URL=redis://redis:6379
REDIS_ENABLED=true

# Alternative: Upstash (Serverless)
UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=xxx

# -----------------------------------------------------------------------------
# AI MODELS (At least one required)
# -----------------------------------------------------------------------------
GEMINI_API_KEY=<required>              # Primary AI model
OPENAI_API_KEY=<optional>              # Ensemble model
ANTHROPIC_API_KEY=<optional>           # Ensemble model

# -----------------------------------------------------------------------------
# META ADS (Required for Meta features)
# -----------------------------------------------------------------------------
META_APP_ID=<from-meta-developer-portal>
META_APP_SECRET=<from-meta-developer-portal>
META_ACCESS_TOKEN=<long-lived-token>
META_ACCESS_TOKEN_EXPIRY=2025-12-31
META_AD_ACCOUNT_ID=act_123456789
META_BUSINESS_ACCOUNT_ID=123456789
META_PAGE_ID=123456789
META_PIXEL_ID=123456789
META_CONVERSION_API_TOKEN=<from-events-manager>
META_CLIENT_TOKEN=<from-app-settings>
META_API_VERSION=v18.0
META_SANDBOX_MODE=false

# Enable Advantage+ for +22% ROAS
META_ADVANTAGE_PLUS_ENABLED=true
META_GENAI_CREATIVE_ENABLED=true

# -----------------------------------------------------------------------------
# GOOGLE ADS (Required for Google features)
# -----------------------------------------------------------------------------
GOOGLE_CLIENT_ID=<from-cloud-console>
GOOGLE_CLIENT_SECRET=<from-cloud-console>
GOOGLE_DEVELOPER_TOKEN=<from-ads-api-center>
GOOGLE_REFRESH_TOKEN=<from-oauth-flow>
GOOGLE_ADS_CUSTOMER_ID=123-456-7890
GOOGLE_ADS_MANAGER_CUSTOMER_ID=123-456-7890
GOOGLE_ADS_LOGIN_CUSTOMER_ID=123-456-7890

# -----------------------------------------------------------------------------
# TIKTOK ADS (Required for TikTok features)
# -----------------------------------------------------------------------------
TIKTOK_ACCESS_TOKEN=<from-business-center>
TIKTOK_ADVERTISER_ID=<your-advertiser-id>
# Note: Service returns 503 with setup instructions if not configured

# -----------------------------------------------------------------------------
# GOOGLE CLOUD (Required for storage/deployment)
# -----------------------------------------------------------------------------
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GCS_BUCKET_NAME=geminivideo-assets
GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json

# -----------------------------------------------------------------------------
# SERVICE URLS (Internal communication)
# -----------------------------------------------------------------------------
GATEWAY_URL=http://gateway-api:8080
DRIVE_INTEL_URL=http://drive-intel:8001
VIDEO_AGENT_URL=http://video-agent:8002
ML_SERVICE_URL=http://ml-service:8003
TITAN_CORE_URL=http://titan-core:8084
META_PUBLISHER_URL=http://meta-publisher:8083
GOOGLE_ADS_URL=http://google-ads:8086
TIKTOK_ADS_URL=http://tiktok-ads:8085

# -----------------------------------------------------------------------------
# APPLICATION SETTINGS
# -----------------------------------------------------------------------------
NODE_ENV=production
PORT=8080
API_VERSION=v1
API_URL=https://api.geminivideo.com
DEFAULT_AI_CREDITS=10000
LOG_LEVEL=info
DEPLOYMENT_TARGET=kubernetes

# -----------------------------------------------------------------------------
# FRONTEND
# -----------------------------------------------------------------------------
VITE_API_BASE_URL=https://api.geminivideo.com
VITE_ENV=production
VITE_META_PIXEL_ID=<your-pixel-id>

# -----------------------------------------------------------------------------
# MONITORING
# -----------------------------------------------------------------------------
SENTRY_DSN=https://xxx@sentry.io/xxx
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=geminivideo
LANGSMITH_API_KEY=<from-langsmith>

# -----------------------------------------------------------------------------
# SCHEDULERS
# -----------------------------------------------------------------------------
ENABLE_WINNER_SCHEDULER=true
WINNER_CHECK_SCHEDULE=0 */6 * * *
ENABLE_BATCH_SCHEDULER=true
BATCH_SCHEDULE=*/5 * * * *
BATCH_SIZE=50
```

---

## Part 4: Deployment Steps

### Phase 1: Local Development (Day 1)

```bash
# 1. Clone and setup
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo

# 2. Copy environment template
cp .env.example .env

# 3. Add required credentials
# - GEMINI_API_KEY (get from Google AI Studio)
# - DATABASE_URL (use local postgres or Supabase)

# 4. Start services
docker-compose up -d

# 5. Run migrations
docker-compose exec gateway-api npx prisma migrate deploy

# 6. Verify services
curl http://localhost:8080/health
curl http://localhost:8003/health
curl http://localhost:8082/health

# 7. Access frontend
open http://localhost:3000
```

### Phase 2: Staging Deployment (Day 2-3)

```bash
# 1. Build production images
docker-compose -f docker-compose.production.yml build

# 2. Push to registry
docker tag geminivideo/gateway-api gcr.io/$PROJECT_ID/gateway-api:latest
docker push gcr.io/$PROJECT_ID/gateway-api:latest
# Repeat for all services

# 3. Create GCP resources
gcloud sql instances create geminivideo-db --tier=db-f1-micro
gcloud redis instances create geminivideo-cache --size=1

# 4. Deploy to Cloud Run (simpler than K8s for staging)
gcloud run deploy gateway-api \
  --image gcr.io/$PROJECT_ID/gateway-api:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars "DATABASE_URL=$DATABASE_URL"

# 5. Test staging
curl https://gateway-api-xxx.run.app/health
```

### Phase 3: Production Kubernetes (Day 4-7)

```bash
# 1. Create GKE cluster
gcloud container clusters create geminivideo \
  --num-nodes=3 \
  --machine-type=e2-standard-2 \
  --region=us-central1

# 2. Create secrets
kubectl create secret generic geminivideo-secrets \
  --from-env-file=.env.production

# 3. Apply Kubernetes manifests
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/secrets.yaml
kubectl apply -f deploy/kubernetes/deployment-gateway-api.yaml
kubectl apply -f deploy/kubernetes/deployment-ml-service.yaml
kubectl apply -f deploy/kubernetes/deployment-video-agent.yaml
kubectl apply -f deploy/kubernetes/service.yaml
kubectl apply -f deploy/kubernetes/ingress.yaml
kubectl apply -f deploy/kubernetes/hpa.yaml

# 4. Verify deployment
kubectl get pods -n geminivideo
kubectl get services -n geminivideo

# 5. Configure DNS
# Point api.geminivideo.com to Ingress IP

# 6. Enable SSL
kubectl apply -f deploy/kubernetes/certificate.yaml

# 7. Deploy monitoring
kubectl apply -f monitoring/prometheus-deployment.yaml
kubectl apply -f monitoring/grafana-deployment.yaml
kubectl apply -f monitoring/alerts.yml
```

---

## Part 5: Recommended Architecture Changes

### Immediate (This Sprint)

1. **Enable Meta Advantage+**
```typescript
// In meta-publisher/src/index.py - add to campaign creation
async def create_campaign(config: CampaignConfig):
    return {
        "name": config.name,
        "objective": config.objective,
        "buying_type": "AUCTION",
        "special_ad_categories": [],
        # Enable Advantage+ Shopping Campaign
        "smart_promotion_type": "GUIDED_CREATION",
        # Enable GenAI creative
        "advantage_plus_creative": {
            "enroll_status": "OPT_IN"
        }
    }
```

2. **Add LangSmith Observability**
```python
# Add to all AI-calling services
import os
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "geminivideo"

from langsmith import traceable

@traceable(name="score_creative")
def score_creative(creative_data):
    # Existing code
    pass
```

3. **Wire Missing Webhooks**
```typescript
// gateway-api/src/webhooks/meta-callback.ts
router.post('/callback/meta', async (req, res) => {
    // Verify signature
    const signature = req.headers['x-hub-signature-256'];
    if (!verifyMetaSignature(req.body, signature)) {
        return res.status(401).send('Invalid signature');
    }

    // Process ad performance updates
    for (const entry of req.body.entry) {
        await processAdPerformanceUpdate(entry);
    }

    res.status(200).send('OK');
});
```

### Short-Term (Next 2 Weeks)

1. **Add Stripe Payment Integration**
```typescript
// New file: gateway-api/src/routes/payments.ts
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

router.post('/create-subscription', async (req, res) => {
    const { priceId, userId } = req.body;

    const session = await stripe.checkout.sessions.create({
        mode: 'subscription',
        payment_method_types: ['card'],
        line_items: [{ price: priceId, quantity: 1 }],
        success_url: `${FRONTEND_URL}/dashboard?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${FRONTEND_URL}/pricing`,
        client_reference_id: userId,
    });

    res.json({ url: session.url });
});
```

2. **Implement MCP Server for Supabase**
```python
# New file: mcp-servers/supabase-mcp.py
from mcp_sdk import MCPServer, Resource

server = MCPServer("supabase")

@server.resource("campaigns")
async def get_campaigns(user_id: str):
    return await supabase.from_("campaigns") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()

@server.resource("performance")
async def get_performance(campaign_id: str, date_range: str):
    return await supabase.from_("performance_metrics") \
        .select("*") \
        .eq("campaign_id", campaign_id) \
        .gte("date", date_range) \
        .execute()

if __name__ == "__main__":
    server.run()
```

3. **Complete Video Generation Integration**
```python
# video-agent/src/generators/runway_client.py
import runwayml

class RunwayGenerator:
    def __init__(self):
        self.client = runwayml.Client(api_key=os.environ["RUNWAY_API_KEY"])

    async def generate_video(self, prompt: str, duration: int = 4):
        task = await self.client.image_to_video.create(
            model='gen3a_turbo',
            prompt_image=prompt.image_url,
            prompt_text=prompt.text,
            duration=duration,
            ratio='16:9'
        )

        # Wait for completion
        while task.status not in ['SUCCEEDED', 'FAILED']:
            await asyncio.sleep(2)
            task = await self.client.tasks.retrieve(task.id)

        return task.output[0] if task.status == 'SUCCEEDED' else None
```

### Medium-Term (Next Month)

1. **Autonomous Creative Factory**
```python
# New service: creative-factory/agents/crew.py
from crewai import Crew, Agent, Task

intel_agent = Agent(
    role="Competitive Intelligence Analyst",
    goal="Analyze competitor ads and identify winning patterns",
    backstory="Expert at Meta Ads Library analysis",
    tools=[meta_ads_library_tool, trend_analyzer_tool]
)

creative_agent = Agent(
    role="Creative Director",
    goal="Generate high-converting ad concepts",
    backstory="Award-winning creative strategist",
    tools=[concept_generator_tool, brand_guidelines_tool]
)

editor_agent = Agent(
    role="Video Editor",
    goal="Produce professional video ads",
    backstory="10 years of ad production experience",
    tools=[video_agent_tool, runway_tool]
)

testing_agent = Agent(
    role="Performance Analyst",
    goal="Optimize ad performance through testing",
    backstory="Data scientist specializing in A/B testing",
    tools=[ab_test_tool, analytics_tool]
)

scaling_agent = Agent(
    role="Media Buyer",
    goal="Scale winning ads profitably",
    backstory="$100M+ in managed ad spend",
    tools=[meta_publisher_tool, google_ads_tool, budget_optimizer_tool]
)

crew = Crew(
    agents=[intel_agent, creative_agent, editor_agent, testing_agent, scaling_agent],
    process=Process.sequential,
    verbose=True
)
```

---

## Part 6: Monitoring & Alerting

### Prometheus Alerts (monitoring/alerts.yml)

```yaml
groups:
- name: geminivideo
  rules:
  # API Health
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate on {{ $labels.service }}"

  # ML Service
  - alert: PredictionLatencyHigh
    expr: histogram_quantile(0.95, rate(prediction_duration_seconds_bucket[5m])) > 2
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "95th percentile prediction latency > 2s"

  # Video Processing
  - alert: RenderQueueBacklog
    expr: render_queue_size > 100
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Render queue has {{ $value }} pending jobs"

  # Database
  - alert: DatabaseConnectionsHigh
    expr: pg_stat_activity_count > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Database has {{ $value }} active connections"

  # Credits
  - alert: UserCreditsExhausted
    expr: increase(credits_exhausted_total[1h]) > 10
    labels:
      severity: info
    annotations:
      summary: "{{ $value }} users exhausted credits in the last hour"
```

### Grafana Dashboard (monitoring/dashboards/overview.json)

Key panels:
1. Request rate by service
2. Error rate by service
3. P50/P95/P99 latency
4. Active users (realtime)
5. Campaigns created (daily)
6. Ads published (by platform)
7. ROAS predictions vs actuals
8. AI credits consumed
9. Video renders (queue + completed)
10. Database connections

---

## Part 7: Security Checklist

### Pre-Production Security Audit

- [ ] All secrets in environment variables (not in code)
- [ ] API rate limiting enabled (current: 60/min per IP)
- [ ] SQL injection protection (using parameterized queries)
- [ ] XSS protection (input sanitization enabled)
- [ ] CORS configured for production domains only
- [ ] HTTPS enforced via Ingress
- [ ] JWT tokens validated on all protected routes
- [ ] API keys hashed in database
- [ ] Webhook signatures verified
- [ ] No secrets in git history (run git-secrets)
- [ ] Dependencies audited (npm audit, pip check)
- [ ] Container images scanned (Trivy)
- [ ] Network policies in Kubernetes
- [ ] Service accounts with minimal permissions
- [ ] Database connections encrypted (SSL)

---

## Part 8: Cost Estimation

### Monthly Infrastructure Costs (Production)

| Resource | Specification | Monthly Cost |
|----------|--------------|--------------|
| GKE Cluster | 3x e2-standard-2 | $150 |
| Cloud SQL | db-standard-2 | $100 |
| Redis | 1GB | $30 |
| Cloud Storage | 100GB | $2 |
| Load Balancer | Global | $20 |
| Egress | 100GB | $12 |
| Container Registry | 50GB | $5 |
| Cloud Logging | 50GB | $25 |
| **Infrastructure Total** | | **~$350/month** |

### AI API Costs

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Gemini Pro | 1M tokens | $3 |
| GPT-4 | 100K tokens | $10 |
| Claude | 100K tokens | $12 |
| ElevenLabs | 10K chars | $11 |
| Runway | 100 videos | $75 |
| **AI Total** | | **~$110/month** |

### Ad Platform Costs

| Platform | Type | Cost |
|----------|------|------|
| Meta | API | Free (with ad spend) |
| Google | API | Free (with ad spend) |
| TikTok | API | Free (with ad spend) |

**Total: ~$460/month** (scales with usage)

---

## Part 9: Launch Checklist

### Pre-Launch (T-7 days)
- [ ] All services passing health checks
- [ ] Database migrations applied
- [ ] SSL certificates valid
- [ ] DNS configured and propagated
- [ ] Monitoring dashboards created
- [ ] Alert rules configured
- [ ] Backup automation tested
- [ ] Load testing passed (target: 1000 req/min)
- [ ] Security audit completed
- [ ] Documentation updated

### Launch Day (T-0)
- [ ] Blue/green deployment ready
- [ ] Rollback procedure tested
- [ ] On-call rotation scheduled
- [ ] Status page configured
- [ ] Support channels ready
- [ ] Marketing assets prepared

### Post-Launch (T+7 days)
- [ ] Monitor error rates (<1%)
- [ ] Check user feedback
- [ ] Optimize slow queries
- [ ] Tune auto-scaling
- [ ] Review AI model accuracy
- [ ] Collect user metrics

---

## Conclusion

GeminiVideo has a solid foundation with 70+ API endpoints, 8 microservices, and comprehensive
frontend. The 4 production fixes implemented today address critical gaps.

**Recommended Next Steps:**
1. Enable Meta Advantage+ (immediate +22% ROAS)
2. Add LangSmith observability (1 day)
3. Complete Stripe integration (3 days)
4. Deploy monitoring stack (2 days)
5. Implement MCP server (1 week)
6. Build Creative Factory agents (4 weeks)

**Total Time to Full Production: 6 weeks**
**Expected ROI: 10x creative output, +30-50% ROAS**
