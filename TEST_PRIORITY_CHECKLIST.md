# TEST PRIORITY CHECKLIST
## Quick Reference for Test Development

**Goal:** Production-ready test coverage in 4-6 weeks

---

## 🚨 CRITICAL - WEEK 1-2 (MUST DO BEFORE PRODUCTION)

### Authentication & Authorization
- [ ] **JWT Token Verification Tests** (`auth.ts` - authenticateUser)
  - [ ] Valid token acceptance
  - [ ] Expired token rejection
  - [ ] Malformed token rejection
  - [ ] Invalid signature detection
  - [ ] Token from wrong project rejection
  - [ ] Network timeout handling
  - [ ] Firebase unavailable fallback

- [ ] **RBAC Tests** (`auth.ts` - requireRole)
  - [ ] Admin role access
  - [ ] Editor role access
  - [ ] Viewer role restrictions
  - [ ] Unauthorized access blocked
  - [ ] Role claim validation

- [ ] **Firebase Auth Service Tests** (`firebase-auth.ts`)
  - [ ] verifyIdToken - valid/invalid/expired
  - [ ] getUserById - found/not found
  - [ ] createUser - success/duplicate
  - [ ] setCustomClaims - size limits
  - [ ] revokeRefreshTokens - force logout
  - [ ] Session cookie creation/verification

### Payment & Billing
- [ ] **Cost Tracker Tests** (`cost-tracker.ts`)
  - [ ] recordCost - accurate calculations
  - [ ] recordCost - all model types
  - [ ] recordCost - database persistence
  - [ ] getDailyCosts - aggregation accuracy
  - [ ] getModelCosts - breakdown correct
  - [ ] getCostProjection - math validation
  - [ ] Negative/zero token handling
  - [ ] Unknown model fallback pricing
  - [ ] Database write failure recovery
  - [ ] Concurrent cost recording

### Database Migrations
- [ ] **Migration 002 Tests** (`002_feedback_and_knowledge.sql`)
  - [ ] Forward migration succeeds
  - [ ] Rollback succeeds
  - [ ] Idempotency (run twice)
  - [ ] Data integrity maintained

- [ ] **Migration 003 Tests** (`003_ai_credits.sql`)
  - [ ] Forward migration succeeds
  - [ ] Rollback succeeds
  - [ ] Default user seeding
  - [ ] Credit table constraints

- [ ] **Migration 004-006 Tests**
  - [ ] All forward migrations
  - [ ] All rollbacks
  - [ ] Index creation
  - [ ] Foreign keys work

---

## 🔴 CRITICAL - WEEK 3-4 (REVENUE BLOCKERS)

### Meta Ads Publishing
- [ ] **Meta Ads Manager Integration Tests** (`meta-ads-manager.ts`)
  - [ ] createCampaign - real API call
  - [ ] createAdSet - targeting validation
  - [ ] uploadVideo - file upload success
  - [ ] uploadVideo - timeout handling
  - [ ] uploadVideo - large file handling
  - [ ] createAdCreative - all CTA types
  - [ ] createAd - end-to-end flow
  - [ ] getCampaignInsights - data retrieval
  - [ ] Invalid access token handling
  - [ ] Expired token refresh
  - [ ] API rate limit handling
  - [ ] Network failure retry logic
  - [ ] Partial creation cleanup

### Google Ads Publishing
- [ ] **Google Ads Manager Integration Tests** (`google-ads-manager.ts`)
  - [ ] createCampaign - budget in micros
  - [ ] createAdGroup - success
  - [ ] createVideoAd - YouTube integration
  - [ ] getPerformanceMetrics - accuracy
  - [ ] OAuth credential validation
  - [ ] Refresh token expiration
  - [ ] API quota exceeded handling
  - [ ] Network failure handling
  - [ ] Customer ID validation

### ML Predictions
- [ ] **ML Service Endpoint Tests** (`main.py`)
  - [ ] POST /api/ml/predict-ctr - valid input
  - [ ] POST /api/ml/predict-ctr - confidence intervals
  - [ ] POST /api/ml/predict-batch - batch handling
  - [ ] POST /api/ml/train - model training
  - [ ] POST /api/ml/feedback - feedback loop
  - [ ] GET /api/ml/accuracy - tracking
  - [ ] Model file missing fallback
  - [ ] NaN/Inf prediction handling
  - [ ] Large batch memory management

- [ ] **Prediction Routes Tests** (`predictions.ts`)
  - [ ] POST /api/predictions/ctr - integration
  - [ ] POST /api/predictions/roas - calculation
  - [ ] Database prediction logging
  - [ ] ML service unavailable fallback
  - [ ] Fallback prediction values
  - [ ] Confidence calculation

---

## 🟠 HIGH PRIORITY - WEEK 5-8

### Campaign Management
- [ ] **Campaign Routes Tests** (`campaigns.ts`)
  - [ ] POST /api/campaigns - creation
  - [ ] GET /api/campaigns - list with pagination
  - [ ] GET /api/campaigns/:id - single retrieval
  - [ ] PUT /api/campaigns/:id - update
  - [ ] DELETE /api/campaigns/:id - soft delete
  - [ ] POST /api/campaigns/:id/launch - status change
  - [ ] POST /api/campaigns/:id/pause - status change
  - [ ] Budget validation
  - [ ] Concurrent updates
  - [ ] ML service notification

### Ads Management
- [ ] **Ads Routes Tests** (`ads.ts`)
  - [ ] POST /api/ads - creation with predictions
  - [ ] GET /api/ads - list
  - [ ] GET /api/ads/:id - retrieval
  - [ ] PUT /api/ads/:id - update
  - [ ] DELETE /api/ads/:id - delete
  - [ ] POST /api/ads/:id/approve - approval flow
  - [ ] POST /api/ads/:id/publish - publishing
  - [ ] ML prediction integration
  - [ ] Video/asset linking

### Analytics
- [ ] **Analytics Routes Tests** (`analytics.ts`)
  - [ ] GET /api/analytics/campaigns - aggregation
  - [ ] GET /api/analytics/campaigns/:id - single campaign
  - [ ] GET /api/analytics/ads/:id - ad performance
  - [ ] GET /api/analytics/overview - dashboard data
  - [ ] GET /api/analytics/export - CSV/Excel export
  - [ ] Date range filtering
  - [ ] Large dataset handling

### A/B Testing
- [ ] **A/B Test Routes Tests** (`ab-tests.ts`)
  - [ ] POST /api/ab-tests - test creation
  - [ ] GET /api/ab-tests - list
  - [ ] GET /api/ab-tests/:id - retrieval
  - [ ] PUT /api/ab-tests/:id - update
  - [ ] POST /api/ab-tests/:id/start - lifecycle
  - [ ] POST /api/ab-tests/:id/stop - lifecycle
  - [ ] GET /api/ab-tests/:id/results - analysis
  - [ ] POST /api/ab-tests/:id/winner - selection
  - [ ] Statistical significance
  - [ ] Minimum sample size

### Alerts System (LARGEST GAP - 17 endpoints!)
- [ ] **Alert Routes Tests** (`alerts.ts`)
  - [ ] GET /api/alerts - list with filters
  - [ ] GET /api/alerts/:id - single alert
  - [ ] POST /api/alerts/:id/acknowledge - workflow
  - [ ] POST /api/alerts/:id/resolve - workflow
  - [ ] GET /api/alerts/rules - rule list
  - [ ] POST /api/alerts/rules - rule creation
  - [ ] PUT /api/alerts/rules/:id - rule update
  - [ ] DELETE /api/alerts/rules/:id - rule deletion
  - [ ] POST /api/alerts/test - alert testing
  - [ ] GET /api/alerts/history - historical
  - [ ] GET /api/alerts/unread - unread count
  - [ ] POST /api/alerts/mark-all-read - bulk action
  - [ ] GET /api/alerts/settings - user settings
  - [ ] PUT /api/alerts/settings - settings update
  - [ ] POST /api/alerts/channels - channel mgmt
  - [ ] DELETE /api/alerts/channels/:id - channel removal
  - [ ] POST /api/alerts/test-channel - channel testing

### Reports
- [ ] **Report Routes Tests** (`reports.ts`)
  - [ ] GET /api/reports - list
  - [ ] POST /api/reports/generate - generation
  - [ ] GET /api/reports/:id - retrieval
  - [ ] GET /api/reports/:id/download - download
  - [ ] DELETE /api/reports/:id - deletion
  - [ ] PDF generation
  - [ ] Excel generation
  - [ ] Large dataset handling

### Image Generation
- [ ] **Image Generation Routes Tests** (`image-generation.ts`)
  - [ ] POST /api/images/generate - AI generation
  - [ ] GET /api/images/:id - retrieval
  - [ ] GET /api/images/:id/status - status check
  - [ ] POST /api/images/:id/regenerate - regeneration
  - [ ] POST /api/images/batch - batch generation
  - [ ] GET /api/images/styles - style list
  - [ ] POST /api/images/upscale - upscaling
  - [ ] POST /api/images/variations - variations
  - [ ] DELETE /api/images/:id - deletion
  - [ ] GET /api/images/history - history

---

## 🟡 MEDIUM PRIORITY - WEEK 9-12

### Onboarding
- [ ] **Onboarding Routes Tests** (`onboarding.ts`)
  - [ ] GET /api/onboarding/progress
  - [ ] POST /api/onboarding/step
  - [ ] POST /api/onboarding/complete
  - [ ] GET /api/onboarding/requirements
  - [ ] POST /api/onboarding/skip

### Demo Mode
- [ ] **Demo Routes Tests** (`demo.ts`)
  - [ ] GET /api/demo/status
  - [ ] POST /api/demo/enable
  - [ ] POST /api/demo/disable
  - [ ] GET /api/demo/campaigns
  - [ ] GET /api/demo/analytics
  - [ ] POST /api/demo/reset
  - [ ] GET /api/demo/videos
  - [ ] POST /api/demo/simulate-publish
  - [ ] POST /api/demo/simulate-metrics
  - [ ] GET /api/demo/sample-data
  - [ ] POST /api/demo/load-scenario
  - [ ] DELETE /api/demo/clear

### ROAS Dashboard
- [ ] **ROAS Routes Tests** (`roas-dashboard.ts`)
  - [ ] GET /api/roas/overview
  - [ ] GET /api/roas/predictions
  - [ ] GET /api/roas/actuals

### WebSocket/Streaming
- [ ] **Streaming Tests** (`streaming.ts`)
  - [ ] WebSocket connection
  - [ ] Message broadcasting
  - [ ] Channel subscription
  - [ ] Unsubscribe handling
  - [ ] Connection timeout
  - [ ] Reconnection logic
  - [ ] Message ordering
  - [ ] Concurrent connections

### Error Handling & Security
- [ ] **Middleware Tests**
  - [ ] Global error handler
  - [ ] Error response formatting
  - [ ] Stack trace sanitization (production)
  - [ ] Rate limiting enforcement
  - [ ] Input sanitization
  - [ ] SQL injection prevention
  - [ ] XSS prevention
  - [ ] CORS configuration

### Caching
- [ ] **Cache Middleware Tests** (`cache.ts`)
  - [ ] Cache hit behavior
  - [ ] Cache miss behavior
  - [ ] Cache key generation
  - [ ] Cache invalidation
  - [ ] TTL expiration
  - [ ] Redis unavailable fallback
  - [ ] Concurrent cache updates

### Database Service
- [ ] **Database Tests** (`database.ts`)
  - [ ] Connection pooling
  - [ ] Query timeout handling
  - [ ] Transaction management
  - [ ] Deadlock handling
  - [ ] Connection retry logic
  - [ ] Bulk operations
  - [ ] Database failover

---

## 🟢 ONGOING - WEEK 13+

### Video Processing
- [ ] Auto captions generation
- [ ] Voice synthesis
- [ ] AI video generation
- [ ] Smart crop algorithm
- [ ] Format conversion

### Edge Computing
- [ ] Asset delivery workers
- [ ] Trending hooks cache
- [ ] A/B routing logic
- [ ] Creative scoring
- [ ] Prediction caching

### Third-Party Integrations
- [ ] HubSpot integration
- [ ] AnyTrack integration
- [ ] Meta Conversions API
- [ ] Google Drive OAuth
- [ ] TikTok Ads API

### ML Features
- [ ] Auto-promotion logic
- [ ] Auto-scaling logic
- [ ] Creative DNA matching
- [ ] Semantic caching
- [ ] Cross-campaign learning
- [ ] Batch processing
- [ ] Vector embeddings
- [ ] Accuracy tracking

### AI Council
- [ ] Multi-model consensus
- [ ] Director agent
- [ ] VEO director
- [ ] Model routing
- [ ] Vertex AI integration

---

## Test Metrics Targets

### Phase 1 (Week 1-4)
- [ ] Authentication: 90%+ coverage
- [ ] Cost Tracker: 90%+ coverage
- [ ] Migrations: 100% tested
- [ ] Publishing: Integration tests passing

### Phase 2 (Week 5-8)
- [ ] API Endpoints: 80%+ coverage
- [ ] ML Service: 80%+ coverage
- [ ] Error Handling: 90%+ coverage

### Phase 3 (Week 9+)
- [ ] Overall: 80%+ code coverage
- [ ] E2E: Critical paths covered
- [ ] Performance: Baselines established

---

## Daily Progress Tracking

### Week 1
- [ ] Monday: Auth middleware tests
- [ ] Tuesday: Firebase auth service tests
- [ ] Wednesday: Cost tracker tests
- [ ] Thursday: Migration tests (002-003)
- [ ] Friday: Migration tests (004-006)

### Week 2
- [ ] Monday: Meta integration tests setup
- [ ] Tuesday: Meta campaign/adset tests
- [ ] Wednesday: Meta upload/creative tests
- [ ] Thursday: Google Ads setup
- [ ] Friday: Google Ads integration tests

### Week 3
- [ ] Monday: ML service endpoint tests
- [ ] Tuesday: Prediction routes tests
- [ ] Wednesday: Campaign routes tests
- [ ] Thursday: Ads routes tests
- [ ] Friday: Analytics routes tests

### Week 4
- [ ] Monday: A/B test routes
- [ ] Tuesday-Thursday: Alert system (17 endpoints!)
- [ ] Friday: Reports & streaming

---

## Success Criteria Checklist

### Ready for Production?
- [ ] All CRITICAL tests passing (Week 1-4)
- [ ] Zero auth vulnerabilities
- [ ] Billing calculations accurate
- [ ] Migrations tested with rollbacks
- [ ] Publishing APIs integration tested
- [ ] ML predictions validated
- [ ] Overall coverage >60%
- [ ] CI/CD pipeline green
- [ ] Load tests passing
- [ ] Security audit passed

### Ready for Scale?
- [ ] All HIGH priority tests passing
- [ ] Overall coverage >80%
- [ ] E2E tests covering critical paths
- [ ] Performance benchmarks established
- [ ] Chaos testing implemented
- [ ] Monitoring and alerting validated

---

**Start Here:** Week 1, Monday morning - Authentication middleware tests
**End Goal:** Production-ready test suite in 4-6 weeks

**Good luck! 🚀**
