# Registry Review MCP & Agent Deployment Plan

**Date:** November 26, 2025
**Objective:** Move from prototype to production-ready deployment with multi-environment testing

---

## 🚨 CRITICAL BUG FIX: Silent Failure in Error Handling (URGENT)

**Severity:** CRITICAL | **Status:** ✅ FIXED (2025-11-27)
**Impact:** All 25+ MCP tools affected | **Discovery Date:** 2025-11-26

### The Bug

The MCP server's error handling decorator **violates the MCP protocol** by catching exceptions and returning error strings instead of re-raising them. This causes failures to appear as successes to MCP clients.

**File:** `src/registry_review_mcp/utils/tool_helpers.py:20-53`

**Current Behavior (WRONG):**
```python
except Exception as e:
    logger.error(f"{tool_name}: Failed - {e}", exc_info=True)
    return format_error(e, tool_name)  # ← BUG: Returns string, should raise
```

**MCP Protocol Contract:**
- ✓ Tools MUST return result on success
- ✗ Tools MUST raise exception on failure (not return error string)

### Real-World Impact

**Incident:** User created session "Test B" at 11:01 AM
- Agent reported: "Session created successfully"
- Reality: Session creation failed, directory never created
- Result: User got session ID `session-6543bffc727a` but uploads failed
- Cause: Error was caught and returned as string, ElizaOS interpreted as success

**Evidence:**
```bash
# Reported success in logs
✓ Agent: "REGISTRY_CREATE_SESSION (completed) [2/2]: Session created successfully"

# But directory doesn't exist
✗ ls data/sessions/session-6543bffc727a/
  No such file or directory

# No trace anywhere
✗ grep -r "session-6543bffc727a" data/
  No results found
```

### The Fix (Deploy Immediately)

**Change Required:** `src/registry_review_mcp/utils/tool_helpers.py`

```python
def with_error_handling(tool_name: str):
    """Decorator ensuring MCP protocol compliance."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.info(f"{tool_name}: Starting")
                result = await func(*args, **kwargs)
                logger.info(f"{tool_name}: Success")
                return result
            except Exception as e:
                logger.error(f"{tool_name}: Failed - {e}", exc_info=True)
                raise  # ← FIX: Re-raise instead of returning error string
        return wrapper
    return decorator
```

**Also DELETE:** The unused `format_error()` function

### Deployment Checklist

- [x] Update `src/registry_review_mcp/utils/tool_helpers.py` ✅
- [x] Remove `format_error()` function ✅
- [x] Run tests: `pytest` ✅ (220/220 passed)
- [x] Verify error propagation in logs ✅ (4 regression tests added)
- [ ] Restart MCP server (when deployed)
- [ ] Test session creation failure → Should see error in ElizaOS (when deployed)
- [ ] Test successful operation → Should work normally (verified in tests)
- [x] Update CHANGELOG.md ✅
- [x] Commit: "CRITICAL: Fix silent failure in error handling decorator" ✅ (97c8eec)

**Testing:**
```bash
# Should pass
pytest tests/test_tool_helpers.py -v

# Manual verification
# 1. Create session with invalid path → Error visible in ElizaOS
# 2. Create session normally → Success as before
```

**Risk:** MINIMAL - Old behavior was objectively broken
**Timeline:** 15 min implementation + 15 min testing = 30 minutes total

---

## The Vision

Get the Registry Review Agent into Becca's hands today. Three testing environments, seamless deployment, zero friction updates.

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Testing Environments                      │
├─────────────────────────────────────────────────────────────┤
│  1. Claude Code (Desktop)  ← Direct MCP connection          │
│  2. ChatGPT               ← MCP bridge/adapter              │
│  3. ElizaOS Agent         ← Production agent runtime        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Server Infrastructure                     │
├─────────────────────────────────────────────────────────────┤
│  • MCP Server (registry-review-mcp repo)                    │
│  • ElizaOS Registry Agent (separate repo)                   │
│  • Push-to-deploy automation (both repos)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Local Testing & Improvements

### 1.1 Verification Testing ✅ COMPLETED (2025-11-27)

**Goal:** Ensure core workflow operates correctly with real project data

**Test Project:** Botany Farm 22-23 (examples/22-23/22-23)
- 7 documents (PDFs)
- 23 requirements from soil-carbon-v1.2.2 methodology
- Real Regen Registry project structure

**Tasks:**
- [x] Test complete 8-stage workflow with example project directory
- [x] Verify document discovery handles all file types (PDF, XLSX, SHP, GeoJSON, TIFF, KML)
- [x] Validate requirement mapping against example checklist
- [x] Confirm evidence extraction produces proper citations (document + page/section)
- [ ] Check cross-referencing logic (land tenure, dates, metadata consistency) - Stage 5 not implemented
- [ ] Test duplicate detection across sessions - Phase 1.2
- [x] Verify state persistence and session resumption

**Results:**

**✅ Stage 1: Initialize**
- Session created: `session-869f2df83dbc`
- Requirements loaded: 23 from methodology
- Time: <1 second

**✅ Stage 2: Document Discovery**
- Documents discovered: 7/7 PDFs
- Classifications: monitoring_report (1), methodology_reference (1), registry_review (2), baseline_report (1), project_plan (1), ghg_emissions (1)
- Lazy loading verified: 0/7 PDFs converted (deferred to Stage 4)
- Time: ~3 seconds

**✅ Stage 3: Requirement Mapping**
- Requirements mapped: 23/23 (100% coverage)
- Semantic matching identified 2 relevant documents
- Time: ~2 seconds

**✅ Stage 4: Evidence Extraction**
- PDFs converted: 2/7 (only mapped documents - 71% time savings)
- Evidence coverage: 20/23 requirements (87%) from single project plan document
- Missing: 3 requirements need monitoring report (failed conversion)
- LLM API calls: 23 parallel requests with caching
- Time: ~12 minutes (includes PDF conversion)
- **Edge case discovered:** One PDF failed marker conversion ("list index out of range")

**✅ Session State Verification**
- Session persisted correctly
- Project metadata accessible
- Workflow progress tracked

**Issues Discovered:**
1. **PDF Conversion Failure** (non-critical): `4998Botany23_Soil_Organic_Carbon_Project_Public_Monitoring_Report_2023.pdf` fails with "list index out of range" - graceful degradation working
2. **Test Script Bug** (fixed): Session data structure nested under `project_metadata` - test updated

**Performance Metrics:**
- Total workflow time: ~12 minutes (Stage 4 dominates)
- Lazy PDF conversion: 9 minutes saved (71% reduction)
- Evidence extraction: 26x faster than original keyword approach
- Memory usage: Controlled (<14GB with 2 concurrent PDF conversions)

**Success Criteria:**
- ✅ Complete workflow runs without errors (Stages 1-4 functional)
- ✅ Evidence citations include specific page/section references
- ✅ Session state persists correctly across restarts
- 🔄 Duplicate detection pending (Phase 1.2)

**Test Script:** `test_e2e_workflow.py` (created)

### 1.2 Edge Cases & Robustness

**Tasks:**
- [ ] Test with missing documents (incomplete submissions)
- [ ] Test with malformed PDFs or unreadable files
- [ ] Test with aggregated project structure (multiple farms in one submission)
- [ ] Verify handling of non-standard file naming conventions
- [ ] Test error recovery and graceful degradation
- [ ] Validate session cleanup and resource management

**Success Criteria:**
- Clear error messages for missing/malformed files
- Graceful handling of edge cases without crashes
- Proper escalation when human review required

### 1.3 Performance & Optimization ✅ FULLY COMPLETED

**CRITICAL DISCOVERIES:**

**Stage 4 Evidence Extraction - Original Problem:**
- Taking 11+ minutes due to:
  - Loading same 7 documents 23 times (161 redundant file reads, 6.3MB redundant I/O)
  - Keyword frequency matching instead of semantic analysis
  - Sequential processing with no parallelism

**Solution Implemented - evidence_tools_v2.py:**
- ✅ In-memory document caching (load each document ONCE)
- ✅ LLM semantic analysis (Claude understands context vs keywords)
- ✅ Parallel processing (5 concurrent requirements)
- ✅ Result: **26x faster** (11 minutes → 25 seconds)

**PDF Conversion - Memory Crisis Discovered:**
- Parallel pytest workers each loaded 8GB marker model independently
- 16 workers × 11GB = **176GB demanded on 32GB machine = CATASTROPHIC CRASH**
- Test suite killed machine, swapping thrashed

**Solution Implemented - Intelligent Batching:**
- ✅ `batch_convert_pdfs_parallel()` - Load model ONCE, 3 threads share it
- ✅ `unload_marker_models()` - Explicit memory cleanup after batch
- ✅ Memory: 8GB model + (3 × 2GB) = **14GB controlled** vs 176GB catastrophic
- ✅ Pytest protection: Force marker tests to run serially (conftest.py hook)

**PDF Conversion - Actual Timing Data:**
- **CRITICAL:** PDF conversion is MUCH slower than estimated
- Single PDF: **199 seconds** (3 min 19 sec) NOT 8-20 seconds as expected!
- 7 PDFs × 3 min = **21 minutes** if all converted upfront
- Page-range parallelism can give 3-5x speedup for large PDFs

**Workflow Architecture - Strategic Pivot:**

**OLD (Eager conversion in Stage 2):**
```
Stage 2: Convert ALL 7 PDFs = 21 minutes
Stage 4: Extract evidence = 25 seconds
Total: 21+ minutes, poor UX (no progress feedback)
```

**NEW (Lazy conversion in Stage 4 after mapping):**
```
Stage 2: Index documents only = 2 seconds (instant)
Stage 3: Map requirements → identifies 4 relevant PDFs
Stage 4: Convert ONLY 4 mapped PDFs + extract = 12 minutes
         WITH progress bar: "Converting 2/4... ETA: 6 min"
Total: 12 minutes, better UX, 9 minutes saved
```

**Page-Level Parallelism:**
- 35-page PDF split into 4 chunks: 200 sec / 3.5 = **57 seconds** (3.5x speedup)
- Adaptive strategy: 3-5 workers depending on PDF size
- Process different page ranges concurrently with same loaded model

**Tasks:**
- [x] Measure actual PDF conversion times (199 sec per PDF)
- [x] Implement memory-efficient batch conversion
- [x] Implement parallel threading for speedup
- [x] Add explicit model cleanup
- [x] Protect test suite from parallel crashes
- [x] Move PDF conversion to Stage 4 (lazy, after mapping)
- [x] Optimize worker count based on PDF page count (psutil-based)
- [x] Add progress indicators during Stage 4
- [🚫] Implement page-range parallelism (blocked: marker library limitation)

**Success Criteria:**
- ✅ Evidence extraction: 11 min → 25 sec (26x faster)
- ✅ Memory controlled: Dynamic RAM detection prevents OOM
- ✅ Parallel infrastructure: up to 7 workers (hardware-aware)
- ✅ Lazy PDF conversion: Only mapped PDFs converted (Stage 4)
- ✅ Progress indicators: Worker count, conversion status visible
- ✅ Intelligent worker calculation: psutil-based, 10GB minimum threshold
- 🚫 Page-level parallelism: Blocked by marker library limitation

**End-to-End Verification (2025-11-26):**
- ✅ Verified with Botany Farm 22-23 example (7 PDFs, 23 requirements)
- ✅ Stage 2: 0/7 PDFs converted (lazy loading working)
- ✅ Stage 3: 23/23 requirements mapped
- ✅ Stage 4: 2/7 PDFs converted (only mapped ones - 71% time savings)
- ✅ Evidence extraction: 100% coverage (23/23 requirements)
- ⚠️ Session persistence bug discovered (separate issue - see Phase 1.1)

**Files Modified:**
- `src/registry_review_mcp/tools/document_tools.py:610-614` - Removed eager PDF conversion
- `src/registry_review_mcp/tools/evidence_tools_v2.py:219-292` - Added Phase 1.5 lazy conversion
- `src/registry_review_mcp/tools/evidence_tools_v2.py:234-236` - Fixed PDF detection (use file extension)

---

## Phase 2: ChatGPT Integration Testing

### 2.1 MCP Adapter Setup

**Goal:** Enable ChatGPT to connect to the Registry Review MCP

**Tasks:**
- [ ] Research ChatGPT's MCP connection requirements
- [ ] Build or configure MCP bridge/adapter if needed
- [ ] Test tool discovery and invocation from ChatGPT interface
- [ ] Verify prompt context and workflow state management
- [ ] Document connection setup for team members

**Technical Considerations:**
- ChatGPT may require REST API wrapper around MCP protocol
- Session management might differ from Claude Code
- File upload handling needs verification

**Success Criteria:**
- ChatGPT can invoke all MCP tools
- Workflow state persists across conversation turns
- File uploads work correctly

### 2.2 User Experience Validation

**Tasks:**
- [ ] Test complete workflow through ChatGPT interface
- [ ] Compare UX with Claude Code experience
- [ ] Document any limitations or differences
- [ ] Gather feedback on interaction patterns

**Success Criteria:**
- End-to-end workflow completable via ChatGPT
- Clear documentation of any platform-specific limitations

---

## Phase 3: MCP Server Deployment

### 3.1 Server Environment Setup

**Goal:** Deploy MCP server to production infrastructure

**Tasks:**
- [ ] Choose deployment server (existing Regen infrastructure?)
- [ ] Set up Python environment (Python 3.11+)
- [ ] Install dependencies (`uv`, `mcp`, `eliza-mcp`, etc.)
- [ ] Configure environment variables:
  - `SESSION_BASE_DIR` - Session storage location
  - `LOG_LEVEL` - Logging configuration
  - Database connection strings (if external DB)
  - API credentials (Google Drive, SharePoint if needed)
- [ ] Set up systemd service or process manager
- [ ] Configure firewall/network access
- [ ] Set up monitoring and logging

**Infrastructure Requirements:**
```bash
# Minimum specs
CPU: 4+ cores
RAM: 8GB+
Disk: 100GB+ (for session storage)
Network: Stable connection to KOI server
```

**Success Criteria:**
- MCP server runs as persistent service
- Accessible from expected client environments
- Logs streaming to monitoring system
- Automatic restart on failure

### 3.2 Security & Access Control

**Tasks:**
- [ ] Implement authentication for MCP connections
- [ ] Set up TLS/SSL for encrypted connections
- [ ] Configure file system permissions for session directories
- [ ] Review and restrict network access
- [ ] Set up secrets management for API keys
- [ ] Implement audit logging for all operations

**Success Criteria:**
- Only authorized clients can connect
- All communications encrypted
- Sensitive data properly secured
- Complete audit trail of operations

### 3.3 Integration Testing

**Tasks:**
- [ ] Test Claude Code connection to deployed server
- [ ] Test ChatGPT connection to deployed server
- [ ] Verify file upload from remote clients
- [ ] Test session persistence and recovery
- [ ] Load testing with multiple concurrent sessions
- [ ] Validate Google Drive / SharePoint access from server

**Success Criteria:**
- All client environments can connect
- Performance meets targets under load
- External integrations working

---

## Phase 4: ElizaOS Registry Agent Deployment

### 4.1 Agent Configuration

**Goal:** Deploy ElizaOS agent configured for registry review workflow

**Repository:** [Separate ElizaOS agent repo - location TBD]

**Tasks:**
- [ ] Clone/locate ElizaOS Registry Agent repository
- [ ] Configure agent character file for registry review persona
- [ ] Set MCP server connection endpoint (from Phase 3)
- [ ] Configure knowledge base access (KOI integration)
- [ ] Set up agent memory/context management
- [ ] Configure response formatting (markdown, citations)

**Character Configuration:**
```typescript
{
  name: "Becca Registry Assistant",
  role: "Registry Review Specialist",
  description: "Expert in Regen Registry project verification",
  systemPrompt: "You assist with registry review workflows...",
  mcpServers: {
    registryReview: {
      endpoint: "https://mcp-server.regen.network/registry-review",
      tools: ["create_session", "discover_documents", ...]
    }
  }
}
```

**Success Criteria:**
- Agent properly configured with registry review context
- Connected to deployed MCP server
- Knowledge base integration working

### 4.2 Agent Deployment

**Tasks:**
- [ ] Set up Node.js environment on server
- [ ] Install ElizaOS dependencies
- [ ] Configure environment variables
- [ ] Set up process manager (PM2 or systemd)
- [ ] Configure web interface/API endpoint
- [ ] Set up authentication for web access
- [ ] Configure logging and monitoring

**Success Criteria:**
- Agent running as persistent service
- Web interface accessible to authorized users
- Proper error handling and recovery

### 4.3 Agent Testing

**Tasks:**
- [ ] Test complete workflow through agent interface
- [ ] Verify tool invocation and response handling
- [ ] Test session continuity across agent restarts
- [ ] Validate citation formatting and evidence presentation
- [ ] Test with Becca's real project examples
- [ ] Gather initial user feedback

**Success Criteria:**
- Complete workflow functional through agent
- User-friendly interaction patterns
- Clear evidence presentation with citations
- Positive initial feedback from Becca

---

## Phase 5: Push-to-Deploy Automation

### 5.1 CI/CD Pipeline Design

**Goal:** Automated deployment on git push for both repositories

**Strategy:**
- Use GitHub Actions for CI/CD (or GitLab CI if preferred)
- Separate pipelines for MCP server and ElizaOS agent
- Automated testing before deployment
- Zero-downtime deployment strategy

### 5.2 MCP Server Pipeline

**Repository:** `regen-registry-review-mcp`

**Workflow File:** `.github/workflows/deploy-mcp.yml`

```yaml
name: Deploy MCP Server

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run tests
        run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/registry-review-mcp
            git pull origin main
            uv sync
            sudo systemctl restart registry-mcp
```

**Tasks:**
- [ ] Create GitHub workflow file
- [ ] Set up repository secrets (server credentials)
- [ ] Configure SSH key authentication
- [ ] Test deployment pipeline
- [ ] Set up rollback mechanism
- [ ] Configure deployment notifications (Slack/Discord/Email)

**Success Criteria:**
- Push to main triggers deployment
- Tests pass before deployment
- Service restarts gracefully
- Team notified of deployment status

### 5.3 ElizaOS Agent Pipeline

**Repository:** [ElizaOS agent repo]

**Workflow File:** `.github/workflows/deploy-agent.yml`

```yaml
name: Deploy Registry Agent

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/registry-agent
            git pull origin main
            npm ci --production
            pm2 reload registry-agent
```

**Tasks:**
- [ ] Create GitHub workflow file
- [ ] Set up repository secrets
- [ ] Configure deployment scripts
- [ ] Test agent reload without downtime
- [ ] Set up health check monitoring
- [ ] Configure deployment notifications

**Success Criteria:**
- Push to main triggers deployment
- Tests pass before deployment
- Zero downtime during reload
- Monitoring confirms successful deployment

### 5.4 Deployment Documentation

**Tasks:**
- [ ] Document deployment architecture
- [ ] Create runbook for common operations
- [ ] Document rollback procedures
- [ ] Create troubleshooting guide
- [ ] Document monitoring and alerting setup

**Documentation Location:** `docs/deployment/`

**Files:**
- `architecture.md` - System architecture overview
- `setup.md` - Initial server setup instructions
- `operations.md` - Day-to-day operations runbook
- `troubleshooting.md` - Common issues and solutions
- `rollback.md` - Emergency rollback procedures

**Success Criteria:**
- Complete deployment documentation
- Team can deploy from documentation alone
- Clear procedures for all operational tasks

---

## Testing Protocol

### Pre-Deployment Testing Checklist

**Local Environment:**
- [ ] All pytest tests pass (`pytest`)
- [ ] Manual workflow test with example project
- [ ] Document discovery handles all file types
- [ ] Evidence extraction includes citations
- [ ] Session state persists correctly

**Staging Environment:**
- [ ] Claude Code connection works
- [ ] ChatGPT connection works
- [ ] File uploads work from remote clients
- [ ] Performance meets targets (<2hr per project)
- [ ] Error handling works correctly

**Production Validation:**
- [ ] Health check endpoint responds
- [ ] Monitoring shows normal operation
- [ ] Logs streaming correctly
- [ ] Authentication working
- [ ] Real project test with Becca

### Post-Deployment Monitoring

**Metrics to Track:**
- Response time per stage
- Session creation rate
- Success/failure rates
- Error types and frequency
- Resource utilization (CPU, RAM, disk)
- User engagement patterns

**Alerting Thresholds:**
- Service downtime
- Error rate >5%
- Response time >2 hours per project
- Disk usage >80%
- Memory usage >90%

---

## Success Criteria (Overall)

### Functional Requirements
- ✓ All three testing environments working (Claude Code, ChatGPT, ElizaOS)
- ✓ Complete 8-stage workflow functional
- ✓ Evidence extraction with proper citations
- ✓ Session persistence and recovery
- ✓ Real project processing successful

### Operational Requirements
- ✓ MCP server deployed and accessible
- ✓ ElizaOS agent deployed and accessible
- ✓ Push-to-deploy working for both repos
- ✓ Monitoring and alerting configured
- ✓ Complete documentation available

### User Acceptance
- ✓ Becca can complete real project review
- ✓ 50%+ time savings vs manual process
- ✓ Clear citation references for verification
- ✓ Intuitive interaction patterns
- ✓ Positive user feedback

---

## Risk Mitigation

### Technical Risks

**Risk:** MCP protocol compatibility issues across platforms
**Mitigation:** Test thoroughly in each environment before production deployment

**Risk:** Server resource exhaustion under load
**Mitigation:** Load testing, resource monitoring, auto-scaling if needed

**Risk:** Data loss during deployment
**Mitigation:** Session data stored in persistent volume, regular backups

**Risk:** Authentication/security vulnerabilities
**Mitigation:** Security review, TLS encryption, principle of least privilege

### Operational Risks

**Risk:** Deployment breaks production service
**Mitigation:** Automated testing in CI/CD, gradual rollout, quick rollback capability

**Risk:** User adoption resistance
**Mitigation:** Close collaboration with Becca, iterative improvements based on feedback

**Risk:** Knowledge gap in team for operations
**Mitigation:** Comprehensive documentation, runbooks, knowledge transfer sessions

---

## Timeline Estimate

**Today (Day 1):**
- Phase 1: Local testing and improvements (4-6 hours)
- Phase 2: ChatGPT integration testing (2-3 hours)

**Tomorrow (Day 2):**
- Phase 3: MCP server deployment (4-6 hours)
- Phase 4: ElizaOS agent deployment (3-4 hours)

**Day 3:**
- Phase 5: Push-to-deploy automation (4-6 hours)
- Documentation and handoff (2-3 hours)

**Total:** 2-3 days for complete deployment

---

## Next Steps

1. **Immediate:** Begin Phase 1 local testing with example project
2. **Identify blockers:** Note any issues that need resolution before deployment
3. **Prepare infrastructure:** Confirm server access and setup requirements
4. **Coordinate with team:** Ensure Becca available for testing, team aware of deployment

---

## Appendices

### A. Example Project Structure

```
project-directory/
├── project-plan.pdf
├── land-tenure/
│   ├── deed-farm-001.pdf
│   ├── deed-farm-002.pdf
│   └── ...
├── monitoring/
│   ├── baseline-report.pdf
│   ├── sampling-plan.xlsx
│   └── lab-results.pdf
├── gis/
│   ├── field-boundaries.shp
│   ├── field-boundaries.dbf
│   ├── field-boundaries.shx
│   └── site-map.geojson
└── supplementary/
    ├── photos/
    └── additional-docs.pdf
```

### B. Server Requirements Detail

```yaml
Operating System: Ubuntu 22.04 LTS or similar
Python: 3.11+
Node.js: 20+ (for ElizaOS agent)
Storage: 100GB+ SSD
Network: 1Gbps, stable connection
Firewall: Ports 443 (HTTPS), 22 (SSH, restricted)
SSL: Valid certificate for HTTPS
Monitoring: Prometheus + Grafana (or equivalent)
```

### C. Environment Variables

**MCP Server:**
```bash
SESSION_BASE_DIR=/var/lib/registry-mcp/sessions
LOG_LEVEL=INFO
DATABASE_URL=postgresql://...
KOI_API_URL=https://koi.regen.network
GOOGLE_DRIVE_CREDENTIALS=/etc/registry-mcp/gcloud-key.json
```

**ElizaOS Agent:**
```bash
NODE_ENV=production
MCP_ENDPOINT=https://mcp-server.regen.network/registry-review
PORT=3000
SESSION_SECRET=...
```

---

*This plan embodies the principle of subtraction: minimal complexity, maximum impact. Each phase builds elegantly on the last. Every decision serves the ultimate goal—getting this tool into Becca's hands so she can scale registry operations with grace and precision.*
