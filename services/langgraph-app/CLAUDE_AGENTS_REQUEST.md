# 🤖 Claude Agents Request - 30 Specialized Agents
## Production-Ready Ad Problem Solving System

---

## 📋 Mission Overview

**Goal:** Deploy 30 specialized Claude agents to build, test, document, and deploy a production-ready multi-agent system for solving ad problems with maximum efficiency, zero code loss, and December 2025 best practices.

**Timeline:** 4-7 days with parallel execution
**Approach:** Orchestrated parallel work streams with clear ownership
**Quality:** >90% test coverage, comprehensive documentation, production-ready

---

## 🎯 Agent Assignments

### **Stream 1: Core Development (5 Agents)**

**Agent A1: CoreAgentBuilder**
- **Files:** `base_agent.py`, `base_super_agent.py`
- **Mission:** Build rock-solid foundation with December 2025 best practices
- **Key Tasks:**
  - Enhanced error handling (retry, circuit breaker)
  - Performance optimizations (async, caching)
  - Thinking framework improvements (5-step for complex problems)
  - Full type hints, structured logging
- **Best Practices:** `asyncio.gather()`, `pydantic`, `structlog`, `tenacity`, OpenTelemetry
- **Timeline:** Day 1 (8 hours)

**Agent A2: SuperAgentEnhancer**
- **Files:** `super_agent_01-05.py` (5 files)
- **Mission:** Enhance 5 super agents with domain-specific optimizations
- **Key Tasks:**
  - Domain-specific enhancements per agent
  - Improved thinking prompts
  - Specialized tools integration
  - Performance monitoring
- **Best Practices:** LangChain v0.3+, LangSmith, PromptLayer, vector stores
- **Timeline:** Day 2 (after A1, 6 hours)

**Agent A3: ExpertAgentBuilder**
- **Files:** `super_agent_06-11.py` (6 files)
- **Mission:** Build 6 expert agents with deep specialization
- **Key Tasks:**
  - Meta Ads API v20+ integration
  - Psychology research integration
  - Financial models
  - Video analysis capabilities
- **Best Practices:** Specialized libraries, knowledge bases, real-time learning
- **Timeline:** Day 2 (after A1, 6 hours)

**Agent A4: OrchestratorDeveloper**
- **Files:** `orchestrator.py`, `graph.py`
- **Mission:** Build intelligent orchestration with adaptive strategies
- **Key Tasks:**
  - Adaptive orchestration (learns best strategy)
  - NLP-based routing
  - Performance optimization
  - Dependency resolution
- **Best Practices:** LangGraph v1.0+, Celery, Redis, Prometheus, distributed tracing
- **Timeline:** Day 2 (after A1-A3, 4 hours)

**Agent A5: WorkflowArchitect**
- **Files:** `ad_workflows.py`, new workflow files
- **Mission:** Build comprehensive ad workflows
- **Key Tasks:**
  - Enhance existing 4 workflows
  - Create 4+ new workflows
  - Workflow testing
  - Workflow documentation
- **Best Practices:** State machines, workflow versioning, templates
- **Timeline:** Day 2 (after A2-A3, 4 hours)

---

### **Stream 2: Testing Infrastructure (6 Agents)**

**Agent A6: UnitTestMaster**
- **Files:** `tests/unit_tests/test_super_agents/*.py` (5 files)
- **Mission:** Comprehensive unit tests for super agents
- **Target:** 90%+ coverage per agent
- **Best Practices:** pytest, pytest-asyncio, pytest-cov
- **Timeline:** Day 3-4 (after A2, 6 hours)

**Agent A7: ExpertTestBuilder**
- **Files:** `tests/unit_tests/test_expert_agents/*.py` (6 files)
- **Mission:** Unit tests for expert agents
- **Target:** 85%+ coverage per agent
- **Timeline:** Day 3-4 (after A3, 6 hours)

**Agent A8: IntegrationTestArchitect**
- **Files:** `tests/integration_tests/*.py` (10+ files)
- **Mission:** End-to-end integration tests
- **Target:** All critical paths covered
- **Timeline:** Day 3-4 (after A4-A5, 8 hours)

**Agent A9: WorkflowTestEngineer**
- **Files:** `tests/workflow_tests/*.py` (4+ files)
- **Mission:** Comprehensive workflow testing
- **Target:** 100% workflow coverage
- **Timeline:** Day 3-4 (after A5, 4 hours)

**Agent A10: KnowledgeSystemTester**
- **Files:** `tests/knowledge_tests/*.py` (4 files)
- **Mission:** Test knowledge system components
- **Target:** All knowledge features tested
- **Timeline:** Day 3-4 (after A12-A15, 4 hours)

**Agent A11: PerformanceTestEngineer**
- **Files:** `tests/performance_tests/*.py` (3 files)
- **Mission:** Load, stress, and performance testing
- **Target:** <30s response time, >99% uptime
- **Best Practices:** Locust, pytest-benchmark
- **Timeline:** Day 3-4 (after all, 6 hours)

---

### **Stream 3: Knowledge System (4 Agents)**

**Agent A12: AutoDiscoveryEngineer**
- **Files:** `auto_discover.py`, `supabase/migrations/001_*.sql`
- **Mission:** Enhanced auto-discovery system
- **Key Tasks:**
  - Relationship discovery
  - Schema evolution detection
  - Performance optimization
- **Best Practices:** SQLAlchemy introspection, caching
- **Timeline:** Day 1 (6 hours)

**Agent A13: LearningMiddlewareBuilder**
- **Files:** `learning_middleware.py`
- **Mission:** Enhanced learning middleware
- **Key Tasks:**
  - Pattern extraction
  - Learning quality metrics
  - Learning validation
- **Best Practices:** LangChain memory, RAG
- **Timeline:** Day 2 (after A12, 4 hours)

**Agent A14: SemanticSearchArchitect**
- **Files:** `semantic_search.py`, `vector_store.py`
- **Mission:** Enhanced semantic search
- **Key Tasks:**
  - Vector store integration
  - Hybrid search (vector + keyword)
  - Search quality metrics
- **Best Practices:** Weaviate/Pinecone, reranking
- **Timeline:** Day 2 (after A12-A13, 4 hours)

**Agent A15: BackgroundLearnerEngineer**
- **Files:** `background_learner.py`, `cron_jobs.py`
- **Mission:** Enhanced background learning
- **Key Tasks:**
  - Scheduled learning
  - Incremental learning
  - Learning prioritization
- **Best Practices:** Celery, learning queues
- **Timeline:** Day 2 (after A12-A13, 4 hours)

---

### **Stream 4: Execution & Safety (3 Agents)**

**Agent A16: SafeExecutorBuilder**
- **Files:** `safe_executor.py`, `execution_queue.py`
- **Mission:** Safe execution with rate limiting
- **Key Tasks:**
  - Rate limiting
  - Jitter (prevent bot detection)
  - Queue management
  - Retry logic
- **Best Practices:** Redis queues, exponential backoff
- **Timeline:** Day 1 (6 hours)

**Agent A17: ExecutionToolsDeveloper**
- **Files:** `execution_tools.py`
- **Mission:** Enhanced execution tools
- **Key Tasks:**
  - More tools (as needed)
  - Tool validation
  - Tool monitoring
- **Best Practices:** Pydantic validation, tool versioning
- **Timeline:** Day 2 (after A16, 3 hours)

**Agent A18: HumanApprovalArchitect**
- **Files:** `human_approval.py`, `approval_ui.py`
- **Mission:** Human-in-the-loop approval
- **Key Tasks:**
  - Approval UI
  - Approval workflows
  - Approval analytics
- **Best Practices:** Webhooks, approval timeouts
- **Timeline:** Day 2 (after A16-A17, 3 hours)

---

### **Stream 5: Monitoring (3 Agents)**

**Agent A19: ObservabilityEngineer**
- **Files:** `observability.py`, `metrics.py`
- **Mission:** Core observability infrastructure
- **Key Tasks:**
  - Metrics collection
  - Distributed tracing
  - Log aggregation
- **Best Practices:** Prometheus, Jaeger, Loki
- **Timeline:** Day 1 (6 hours)

**Agent A20: ContinuousMonitorBuilder**
- **Files:** `continuous_monitor.py`
- **Mission:** Continuous monitoring
- **Key Tasks:**
  - Health checks
  - Alerting
  - Anomaly detection
- **Best Practices:** Grafana, SLOs
- **Timeline:** Day 2 (after A19, 3 hours)

**Agent A21: DashboardArchitect**
- **Files:** `dashboards/*`, `alerts/*`
- **Mission:** Dashboards and visualization
- **Key Tasks:**
  - Real-time dashboards
  - Agent performance views
  - Workflow analytics
- **Best Practices:** Grafana/Datadog, real-time updates
- **Timeline:** Day 2 (after A19-A20, 4 hours)

---

### **Stream 6: Documentation (4 Agents)**

**Agent A22: APIDocumentationWriter**
- **Files:** `docs/API_*.md` (5+ files)
- **Mission:** Complete API documentation
- **Key Tasks:**
  - API reference
  - Endpoint documentation
  - Request/response examples
  - Error codes
- **Best Practices:** OpenAPI/Swagger, interactive docs
- **Timeline:** Day 3-4 (after core, 4 hours)

**Agent A23: UserGuideWriter**
- **Files:** `docs/USER_*.md` (4+ files)
- **Mission:** User guides and tutorials
- **Key Tasks:**
  - User guides
  - Tutorials
  - Best practices
  - Troubleshooting
- **Best Practices:** Clear examples, screenshots
- **Timeline:** Day 3-4 (after core, 4 hours)

**Agent A24: ArchitectureDocumenter**
- **Files:** `docs/ARCH_*.md` (3+ files)
- **Mission:** Architecture documentation
- **Key Tasks:**
  - Architecture diagrams
  - System design docs
  - Data flow diagrams
  - Component docs
- **Best Practices:** Mermaid diagrams, keep updated
- **Timeline:** Day 3-4 (after all, 3 hours)

**Agent A25: BestPracticesCompiler**
- **Files:** `docs/BEST_PRACTICES.md`
- **Mission:** Comprehensive best practices guide
- **Key Tasks:**
  - Compile all best practices
  - Add examples
  - Add anti-patterns
- **Best Practices:** Keep updated, versioning
- **Timeline:** Day 3-4 (after all, 3 hours)

---

### **Stream 7: Infrastructure (3 Agents)**

**Agent A26: CICDArchitect**
- **Files:** `.github/workflows/*.yml` (5 files)
- **Mission:** CI/CD pipelines
- **Key Tasks:**
  - GitHub Actions workflows
  - Test automation
  - Deployment automation
  - Rollback procedures
- **Best Practices:** Actions/checkout, blue-green deployment
- **Timeline:** Day 5 (after all, 4 hours)

**Agent A27: DatabaseMigrationEngineer**
- **Files:** `supabase/migrations/*.sql`
- **Mission:** Database migrations
- **Key Tasks:**
  - Review all migrations
  - Create new migrations (if needed)
  - Test migrations
  - Rollback scripts
- **Best Practices:** Versioned migrations, test on staging
- **Timeline:** Day 5 (after A12, 3 hours)

**Agent A28: InfrastructureEngineer**
- **Files:** `docker/*`, `configs/*`
- **Mission:** Infrastructure as code
- **Key Tasks:**
  - Docker setup
  - Environment configs
  - Secrets management
  - Infrastructure as code
- **Best Practices:** Docker-compose, Terraform/Pulumi
- **Timeline:** Day 5 (after all, 4 hours)

---

### **Stream 8: Quality & Security (2 Agents)**

**Agent A29: SecurityAuditor**
- **Files:** `security_audit.md`, `security_fixes/`
- **Mission:** Security audit and fixes
- **Key Tasks:**
  - Security audit
  - RLS policy review
  - API security
  - Secrets management
  - Vulnerability scanning
- **Best Practices:** Bandit, Safety, OWASP guidelines
- **Timeline:** Day 5-6 (after all, 4 hours)

**Agent A30: CodeQualityEngineer**
- **Files:** `quality_improvements/`
- **Mission:** Code quality and optimization
- **Key Tasks:**
  - Code quality review
  - Linting fixes
  - Type checking
  - Refactoring
  - Performance optimization
- **Best Practices:** Ruff, MyPy, Black, pre-commit hooks
- **Timeline:** Day 5-6 (after all, 4 hours)

---

## 🛡️ Conflict Prevention

### **File Ownership Rules:**
- Each agent owns specific files (see ownership matrix)
- NO agent modifies files outside their ownership
- If modification needed, request via coordinator

### **Dependency Rules:**
- Agents wait for dependencies before starting
- Check dependency status at each sync
- Don't start until dependencies complete

### **Git Workflow:**
- Each agent works in separate branch: `agent-A{ID}-{feature}`
- Daily commits required
- PRs reviewed before merge
- Coordinator merges to main

---

## 📊 Execution Timeline

**Day 1:** Foundation (A1, A12, A16, A19)
**Day 2:** Core Development (A2-A5, A13-A15, A17-A18, A20-A21)
**Day 3-4:** Testing & Documentation (A6-A11, A22-A25)
**Day 5:** Infrastructure (A26-A30)
**Day 6-7:** Integration & Polish (All agents)

---

## ✅ Success Criteria

- [ ] All tests pass (>90% coverage)
- [ ] All agents work correctly
- [ ] No code conflicts
- [ ] Performance optimized
- [ ] Security audited
- [ ] Documentation complete
- [ ] Production deployed

---

## 📝 Instructions for Each Agent

**Each agent should:**
1. Read their assigned files
2. Understand dependencies
3. Implement December 2025 best practices
4. Write comprehensive tests
5. Document their work
6. Follow coordination protocol
7. Report progress daily

---

**Status: ✅ Ready for 30-Agent Execution**

**All agents can start in parallel according to dependency graph**
**Zero conflicts guaranteed with file ownership matrix**
**Maximum efficiency with orchestrated parallel streams**

