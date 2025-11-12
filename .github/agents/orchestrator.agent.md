# Agent Orchestrator Configuration

## Mission
Coordinate 10 specialized agents to build complete AI video ads machine in parallel.

## Agent Fleet

### Backend Team (4 Agents)

#### Agent 1: Database Architect
- **Task:** Implement PostgreSQL persistence layer
- **Priority:** HIGH (blocks other agents)
- **Files:** `shared/db.py`, `services/*/migrations/`
- **Dependencies:** None
- **Output:** Working database with schemas for assets, clips, predictions

#### Agent 2: ML Engineer - Video Processing
- **Task:** Real scene detection + emotion recognition
- **Priority:** HIGH
- **Files:** `services/drive-intel/src/main.py`, `services/drive-intel/src/features/`
- **Dependencies:** None (uses existing stubs)
- **Output:** DeepFace integration, real PySceneDetect, FAISS index

#### Agent 3: ML Engineer - Prediction Models
- **Task:** XGBoost CTR prediction + Vowpal Wabbit optimization
- **Priority:** MEDIUM
- **Files:** `services/gateway-api/src/prediction.py`, `services/meta-publisher/src/optimization.py`
- **Dependencies:** Agent 1 (needs DB)
- **Output:** Trained models, prediction endpoints

#### Agent 4: Video Rendering Engineer
- **Task:** Real FFmpeg rendering + MoviePy composition
- **Priority:** MEDIUM
- **Files:** `services/video-agent/src/index.py`, `services/video-agent/src/render/`
- **Dependencies:** Agent 2 (needs emotion data)
- **Output:** Working video generation with transitions

### Frontend Team (2 Agents)

#### Agent 5: Frontend UI Developer
- **Task:** Wire up React frontend with API calls
- **Priority:** HIGH
- **Files:** `services/frontend/src/App.tsx`, `services/frontend/src/pages/`, `services/frontend/src/api/`
- **Dependencies:** None (can work with stubs initially)
- **Output:** Working UI with all buttons connected

#### Agent 6: UX Enhancement Specialist
- **Task:** Loading states, error handling, metrics dashboard
- **Priority:** LOW
- **Files:** `services/frontend/src/components/`, CSS files
- **Dependencies:** Agent 5 (needs base UI)
- **Output:** Polished user experience

### Integration Team (2 Agents)

#### Agent 7: Meta Integration Engineer
- **Task:** Real Facebook SDK integration + A/B testing
- **Priority:** HIGH
- **Files:** `services/meta-publisher/src/index.ts`, `services/meta-publisher/src/facebook/`
- **Dependencies:** Agent 3 (needs optimization models)
- **Output:** Working ad publishing with Thompson Sampling

#### Agent 8: API Integration Engineer
- **Task:** Google Drive API + GCS storage
- **Priority:** MEDIUM
- **Files:** `services/drive-intel/src/integrations/`, `services/gateway-api/src/knowledge.ts`
- **Dependencies:** Agent 1 (needs DB)
- **Output:** Real Drive ingestion, GCS hot-reload

### DevOps & Quality Team (2 Agents)

#### Agent 9: Testing Engineer
- **Task:** Write comprehensive tests for all new features
- **Priority:** MEDIUM
- **Files:** `tests/`, all service test files
- **Dependencies:** All other agents (tests their code)
- **Output:** 80%+ test coverage, integration tests

#### Agent 10: DevOps Engineer
- **Task:** Docker, CI/CD, deployment, monitoring
- **Priority:** MEDIUM
- **Files:** `Dockerfile`s, `.github/workflows/`, `docker-compose.yml`
- **Dependencies:** Agent 1 (needs DB setup)
- **Output:** One-command local dev, automated GCP deployment

## Coordination Protocol

### Phase 1: Foundation (Hours 0-4)
**Parallel Work:**
- Agent 1: Database schema
- Agent 2: Scene detection + emotion
- Agent 5: Frontend API client
- Agent 10: Docker Compose setup

**Blockers:** None - all independent

### Phase 2: Core Features (Hours 4-12)
**Parallel Work:**
- Agent 3: Prediction models (needs Agent 1 DB)
- Agent 4: Video rendering (needs Agent 2 emotion)
- Agent 7: Meta SDK (can start with mocks)
- Agent 8: Drive API

**Blockers:** Wait for Agent 1 and 2

### Phase 3: Integration (Hours 12-20)
**Parallel Work:**
- Agent 5: Wire real APIs to frontend
- Agent 6: Polish UI/UX
- Agent 7: Connect optimization to Meta
- Agent 9: Write tests

**Blockers:** Wait for Phase 2

### Phase 4: Deploy (Hours 20-24)
**Sequential Work:**
- Agent 9: Run all tests
- Agent 10: Deploy to GCP
- Agent 6: Final UX polish

## Communication

### Shared State
- **Branch naming:** `agent-{number}-{feature}`
- **PR naming:** `[Agent {N}] Feature Name`
- **Status updates:** Comment in this file every 2 hours

### Conflict Resolution
- **Database schema:** Agent 1 owns, others request changes
- **API contracts:** Document in `shared/api-contracts.md`
- **Merge order:** Follow phase order above

### Integration Points
```
Agent 1 (DB) → Agents 3, 8
Agent 2 (ML) → Agents 4, 7
Agent 5 (Frontend) → All backend agents
Agent 9 (Tests) → All agents
Agent 10 (DevOps) → All agents
```

## Success Metrics
- [ ] All agents have pushed working code
- [ ] All PRs merged without breaking main
- [ ] Full system works end-to-end
- [ ] Tests pass (80%+ coverage)
- [ ] Deployed to GCP successfully

## Emergency Protocol
If agents conflict or block each other:
1. **Pause all agents** in that phase
2. **Orchestrator resolves** (human or lead agent)
3. **Resume** with clear contracts
