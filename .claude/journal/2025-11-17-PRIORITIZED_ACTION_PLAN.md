# Prioritized Action Plan - Registry Review MCP

**Based on:** 10 comprehensive UX analyses (100,000+ words)
**Date:** November 13, 2025
**Timeline:** 5 weeks to production-ready
**Goal:** Transform from B+ prototype to A production system

---

## Sprint 1: Critical Fixes (Week 1-2) - P0

### Day 1-2: Duplicate Session Detection

**Issue:** Users can create multiple sessions for same project, losing track of work

**Files to Modify:**
- `src/registry_review_mcp/prompts/initialize.py`
- `src/registry_review_mcp/tools/session_tools.py`

**Implementation:**
```python
# In initialize.py
def check_for_duplicates(project_name, documents_path):
    """Check if session already exists for this project."""
    state_manager = StateManager(None)
    sessions = state_manager.list_sessions()

    matches = [s for s in sessions
               if s['project_name'] == project_name
               and s['documents_path'] == documents_path]

    return matches

# In initialize_prompt()
existing = check_for_duplicates(project_name, documents_path)
if existing:
    return AskUserQuestion([{
        "question": "A session already exists for this project. What would you like to do?",
        "header": "Duplicate",
        "multiSelect": False,
        "options": [
            {
                "label": "Resume existing session",
                "description": f"Continue working on {existing[0]['session_id']}"
            },
            {
                "label": "Create new session anyway",
                "description": "Start fresh (will have two sessions for same project)"
            },
            {
                "label": "Delete old and create new",
                "description": f"Delete {existing[0]['session_id']} first"
            }
        ]
    }])
```

**Testing:**
- Test: Create session, try to create again with same name/path
- Test: Resume flow works correctly
- Test: Delete and recreate works
- Test: Create anyway creates separate session

**Success Criteria:**
- Zero accidental duplicate sessions
- Users can explicitly choose to resume or replace

---

### Day 3-6: Integration Test Suite

**Issue:** No E2E tests, only 40% production readiness

**Files to Create:**
- `tests/test_integration_full_workflow.py`
- `tests/test_integration_stage_handoffs.py`
- `tests/test_integration_error_recovery.py`

**Test Scenarios:**

**1. Happy Path E2E (test_full_workflow_botany_farm)**
```python
async def test_full_workflow_botany_farm():
    """Complete workflow on Botany Farm example."""

    # Stage 1: Initialize
    session = await create_session("Botany Farm", "/path/to/22-23")
    assert session["status"] == "active"

    # Stage 2: Document Discovery
    docs = await discover_documents(session["session_id"])
    assert docs["documents_found"] == 7
    assert "project_plan" in docs["classification_summary"]

    # Stage 3: Evidence Extraction
    evidence = await extract_evidence(session["session_id"])
    assert evidence["requirements_covered"] >= 18
    assert evidence["overall_coverage"] >= 0.85

    # Stage 4: Cross-Validation
    validation = await cross_validate(session["session_id"])
    assert validation["summary"]["total_validations"] >= 3

    # Stage 5: Report Generation
    report = await generate_report(session["session_id"])
    assert Path(report["markdown_path"]).exists()

    # Stage 6: Human Review (if flags exist)
    review = await human_review_prompt(session["session_id"])
    # Check structure

    # Stage 7: Complete
    completion = await complete_prompt(session["session_id"])
    # Verify assessment logic
```

**2. Error Recovery Tests**
```python
async def test_recovery_from_interrupted_evidence_extraction():
    """Test resuming after extraction failure."""
    session = await create_session("Test", "/path")
    await discover_documents(session["session_id"])

    # Simulate failure mid-extraction
    # ... force error after 10 requirements

    # Verify can resume
    evidence = await extract_evidence(session["session_id"])
    # Should complete remaining requirements
```

**3. State Consistency Tests**
```python
async def test_state_transitions_valid():
    """Test workflow stage transitions."""
    session = await create_session("Test", "/path")

    # Cannot skip stages
    with pytest.raises(PreconditionError):
        await cross_validate(session["session_id"])  # No evidence yet

    # Can re-run stages idempotently
    await discover_documents(session["session_id"])
    docs1 = await discover_documents(session["session_id"])  # Run again
    # Should be same results
```

**Coverage Target:** 90%+ integration coverage

---

### Day 7-8: Progress Indicators

**Issue:** Long operations appear frozen, causing user anxiety

**Files to Modify:**
- `src/registry_review_mcp/tools/document_tools.py`
- `src/registry_review_mcp/tools/evidence_tools.py`
- `src/registry_review_mcp/extractors/llm_extractors.py`

**Implementation:**
```python
# In document_tools.py
async def discover_documents(session_id: str) -> str:
    """Discover with progress updates."""

    manager = StateManager(session_id)
    documents_path = manager.read_json("session.json")["project_metadata"]["documents_path"]

    # Count files first
    all_files = list(Path(documents_path).rglob("*"))
    file_count = len([f for f in all_files if f.is_file()])

    print(f"🔍 Scanning {file_count} files...")

    results = []
    for i, filepath in enumerate(all_files, 1):
        if i % 10 == 0 or i == file_count:
            print(f"  📄 Processed {i}/{file_count} files ({i/file_count*100:.0f}%)")
        # ... process file

    print(f"✅ Discovery complete: {len(results)} documents found")
    return format_results(results)
```

**Testing:**
- Test: Progress shows for 100+ files
- Test: Progress updates don't slow processing
- Test: Final count matches discovered

---

### Day 9-10: Error Message Enhancement

**Issue:** Silent failures in document processing

**Files to Modify:**
- `src/registry_review_mcp/tools/document_tools.py`
- `src/registry_review_mcp/prompts/document_discovery.py`

**Implementation:**
```python
# Track errors during discovery
class DiscoveryResult:
    documents: list[Document]
    errors: list[DiscoveryError]
    warnings: list[DiscoveryWarning]

class DiscoveryError:
    filepath: str
    error_type: str  # "permission_denied", "corrupted_pdf", "missing_component"
    message: str
    recovery_steps: list[str]

# In discover_documents()
result = DiscoveryResult(documents=[], errors=[], warnings=[])

for filepath in all_files:
    try:
        doc = classify_and_process(filepath)
        result.documents.append(doc)
    except PermissionError as e:
        result.errors.append(DiscoveryError(
            filepath=str(filepath),
            error_type="permission_denied",
            message=f"Cannot read {filepath}: Permission denied",
            recovery_steps=[
                "Check file permissions: chmod 644 <file>",
                "Ensure you own the file: chown $USER <file>",
                "Try running with sudo (not recommended)"
            ]
        ))

# In prompt, show errors:
if result.errors:
    error_section = format_errors(result.errors)
    # Include in response with recovery guidance
```

**Testing:**
- Test: Permission errors caught and reported
- Test: Corrupted PDFs don't crash, show helpful error
- Test: Missing shapefile components detected
- Test: All errors include recovery steps

---

## Sprint 2: High Priority UX (Week 3-5) - P1

### Week 3, Day 11-12: Decision Recording System

**Issue:** No way to document human review decisions

**Files to Create:**
- `src/registry_review_mcp/models/decisions.py`
- `src/registry_review_mcp/tools/decision_tools.py`

**Implementation:**
```python
# models/decisions.py
class Decision(BaseModel):
    decision_id: str
    validation_id: str
    decision_type: Literal["accept", "defer", "escalate"]
    rationale: str
    made_by: str
    made_at: datetime
    protocol_references: list[str] = []

class DeferredItem(BaseModel):
    validation_id: str
    question: str
    information_needed: str
    expected_resolution: datetime | None

# tools/decision_tools.py
async def record_decision(
    session_id: str,
    validation_id: str,
    decision_type: str,
    rationale: str
) -> str:
    """Record a human review decision."""

    decision = Decision(
        decision_id=f"DEC-{uuid.uuid4().hex[:8]}",
        validation_id=validation_id,
        decision_type=decision_type,
        rationale=rationale,
        made_by="becca",  # TODO: Get from auth
        made_at=datetime.now()
    )

    manager = StateManager(session_id)
    decisions = manager.read_json("decisions.json", default=[])
    decisions.append(decision.model_dump())
    manager.write_json("decisions.json", decisions)

    return f"✅ Decision recorded: {decision_type.upper()}"
```

**Update `/human-review` prompt:**
```markdown
**Action Required:**
To record your decision, use:

`record_decision {session_id}, {validation_id}, accept, "Confirmed with proponent via email 11/10/25"`

Or:

`record_decision {session_id}, {validation_id}, defer, "Need clarification on baseline date"`
```

**Testing:**
- Test: Record accept decision
- Test: Record defer with question
- Test: Record escalate with rationale
- Test: Decisions persist across sessions
- Test: Decisions flow into report

---

### Week 3, Day 13-14: Change Detection

**Issue:** Documents modified between runs, no detection

**Files to Modify:**
- `src/registry_review_mcp/tools/document_tools.py`
- `src/registry_review_mcp/models/schemas.py`

**Implementation:**
```python
# Add to DocumentMetadata
class DocumentMetadata:
    # ... existing fields
    file_hash: str  # SHA-256 of file content
    file_size: int
    last_modified: datetime

# In discover_documents()
def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

# Check for changes
previous_docs = manager.read_json("documents.json", default=[])
previous_by_path = {doc['filepath']: doc for doc in previous_docs}

changes = {
    'added': [],
    'removed': [],
    'modified': []
}

for current_doc in current_docs:
    if current_doc['filepath'] not in previous_by_path:
        changes['added'].append(current_doc)
    elif previous_by_path[current_doc['filepath']]['file_hash'] != current_doc['file_hash']:
        changes['modified'].append(current_doc)

for prev_path in previous_by_path:
    if prev_path not in {doc['filepath'] for doc in current_docs}:
        changes['removed'].append(previous_by_path[prev_path])

# Show changes in prompt
if any(changes.values()):
    return f"""⚠️ **Documents have changed since last discovery!**

Added: {len(changes['added'])} files
Modified: {len(changes['modified'])} files
Removed: {len(changes['removed'])} files

**Recommendation:** Re-run evidence extraction to include changes.
"""
```

**Testing:**
- Test: Detect added file
- Test: Detect modified file (change content)
- Test: Detect removed file
- Test: No false positives on unchanged files

---

### Week 4, Day 15-16: Circuit Breaker for LLM API

**Issue:** No fallback when Claude API fails

**Files to Create:**
- `src/registry_review_mcp/utils/circuit_breaker.py`

**Implementation:**
```python
class CircuitBreaker:
    """Circuit breaker pattern for external API calls."""

    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""

        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half_open"
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"

            raise

# In llm_extractors.py
circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

async def extract_with_claude(self, text: str) -> dict:
    """Extract with circuit breaker protection."""
    try:
        return await circuit_breaker.call(
            self._call_claude_api, text
        )
    except CircuitBreakerOpenError:
        logger.warning("Circuit breaker open, using fallback")
        return self._fallback_extraction(text)
```

**Testing:**
- Test: Circuit opens after 5 failures
- Test: Circuit resets after timeout
- Test: Half-open state works
- Test: Fallback extraction activates

---

### Week 4, Day 17-19: State Corruption Recovery

**Issue:** Corrupted sessions require manual fix

**Files to Create:**
- `src/registry_review_mcp/utils/state_repair.py`

**Implementation:**
```python
class StateRepair:
    """Utilities for detecting and repairing corrupted state."""

    @staticmethod
    def validate_session(session_data: dict) -> list[str]:
        """Validate session schema and return errors."""
        errors = []

        try:
            Session(**session_data)
        except ValidationError as e:
            for error in e.errors():
                errors.append(f"{error['loc']}: {error['msg']}")

        return errors

    @staticmethod
    def repair_session(session_data: dict) -> dict:
        """Attempt to repair corrupted session."""
        # Set defaults for missing required fields
        defaults = {
            'status': 'active',
            'workflow_progress': {...},
            'statistics': {...}
        }

        for field, default in defaults.items():
            if field not in session_data:
                session_data[field] = default

        return session_data

# Add to session_tools.py
async def load_session(session_id: str) -> dict:
    """Load session with corruption detection."""
    manager = StateManager(session_id)

    try:
        session_data = manager.read_json("session.json")

        # Validate
        errors = StateRepair.validate_session(session_data)
        if errors:
            # Attempt repair
            repaired = StateRepair.repair_session(session_data)
            manager.write_json("session.json", repaired)
            logger.warning(f"Repaired session {session_id}: {errors}")
            return repaired

        return session_data

    except json.JSONDecodeError:
        # Completely corrupted, cannot recover
        raise SessionCorruptedError(
            f"Session {session_id} is corrupted and cannot be recovered. "
            "Please delete and create a new session."
        )
```

**Testing:**
- Test: Detect missing required fields
- Test: Repair with defaults
- Test: Handle completely corrupted JSON
- Test: Don't repair sessions with manual edits

---

### Week 5, Day 20-22: Batch Operations

**Issue:** Must review similar flags individually

**Files to Modify:**
- `src/registry_review_mcp/prompts/human_review.py`
- `src/registry_review_mcp/tools/decision_tools.py`

**Implementation:**
```python
# In decision_tools.py
async def detect_patterns(flagged_items: list) -> list[Pattern]:
    """Detect patterns in flagged items."""
    patterns = []

    # Group by type and similar characteristics
    by_type = {}
    for item in flagged_items:
        key = (item['type'], item['status'])
        if key not in by_type:
            by_type[key] = []
        by_type[key].append(item)

    # Create patterns for groups of 3+
    for (item_type, status), items in by_type.items():
        if len(items) >= 3:
            patterns.append(Pattern(
                pattern_id=f"PAT-{uuid.uuid4().hex[:8]}",
                description=f"{len(items)} {item_type} items with {status} status",
                items=items,
                suggested_action="accept"  # Based on historical data
            ))

    return patterns

# Add batch_record_decisions tool
async def batch_record_decisions(
    session_id: str,
    validation_ids: list[str],
    decision_type: str,
    rationale: str,
    exceptions: list[str] = []
) -> str:
    """Record decisions for multiple validations at once."""

    recorded = 0
    for val_id in validation_ids:
        if val_id not in exceptions:
            await record_decision(session_id, val_id, decision_type, rationale)
            recorded += 1

    return f"✅ Recorded {recorded} decisions ({len(exceptions)} exceptions)"
```

**Update `/human-review` prompt:**
```markdown
## Patterns Detected

### Pattern 1: 5 Land Tenure Name Variations
All items show minor name spelling differences (Nick/Nicholas).

**Suggested Action:** Accept all (Name variations are common and verified)

**Apply to all:**
`batch_record_decisions {session_id}, [{val_ids}], accept, "Name variations verified"`

**Review individually instead:**
Continue below for item-by-item review
```

**Testing:**
- Test: Detect patterns correctly
- Test: Batch apply with exceptions
- Test: Undo batch decision
- Test: Audit trail shows batch operation

---

## Sprint 3: Polish & Operations (Month 2) - P2

*(Documented for future implementation)*

### Confidence Calibration (Week 6-7)
- Collect Becca's decisions over 20 reviews
- Analyze agreement with high/medium/low confidence
- Adjust thresholds to achieve 95%+ calibration
- Implement learning from feedback

### Report Preview (Week 7)
- Show first 50-100 lines in MCP response
- Add table of contents
- Inline evidence snippets
- Don't require opening files

### Cost Transparency (Week 8)
- Pre-extraction cost estimates
- Real-time tracking during extraction
- Cost attribution by stage/requirement
- Budget warnings

### Deployment Documentation (Week 8-9)
- Dockerfile and docker-compose
- CI/CD pipeline (GitHub Actions)
- Environment configuration guide
- Backup/restore procedures
- Monitoring setup (Prometheus/Grafana)

---

## Success Metrics by Sprint

### Sprint 1 (Week 1-2) Success Criteria

**Deployment Readiness:**
- ✅ Integration test coverage >90%
- ✅ Zero duplicate sessions in testing
- ✅ All error messages include recovery steps
- ✅ Progress indicators on long operations

**User Experience:**
- ✅ Users report "no more confusion about sessions"
- ✅ Users report "system feels responsive"
- ✅ Users can self-recover from 90%+ errors

### Sprint 2 (Week 3-5) Success Criteria

**Reliability:**
- ✅ Zero session corruption incidents
- ✅ LLM API failures don't crash workflow
- ✅ Change detection catches 100% of modifications

**Efficiency:**
- ✅ Human review 40% faster (batch operations)
- ✅ Decisions documented and flow to report
- ✅ No manual re-runs due to stale data

### Sprint 3 (Month 2) Success Criteria

**Production Operations:**
- ✅ Can deploy with one command
- ✅ Monitoring dashboards show health
- ✅ Cost tracking prevents budget overruns
- ✅ Reports preview without file opening

**User Satisfaction:**
- ✅ Becca rates system "essential"
- ✅ Would recommend to other registries
- ✅ 70% time savings validated (6-8hr → 60-90min)

---

## Daily Standups

**Format:**
- What did I complete yesterday?
- What will I complete today?
- Any blockers?

**Check-ins:**
- Tuesday/Thursday with team
- Friday demos with Becca (if available)
- Monday planning for next week

---

## Risk Mitigation

### If Behind Schedule

**Week 1-2 (P0):**
- Cannot skip - blocks production
- Add resources if needed
- Work weekends if critical

**Week 3-5 (P1):**
- Can defer Week 5 to Month 2
- Minimum: Decision recording + circuit breaker
- Batch operations can wait

**Month 2 (P2):**
- Flexible timeline
- Can adjust based on pilot feedback
- Deploy without full polish if needed

### If Becca Unavailable for Testing

- Use synthetic test cases
- Record questions for async feedback
- Schedule dedicated testing session

### If LLM API Costs Exceed Budget

- Implement cost caps immediately
- Reduce extraction frequency
- Use smaller Claude model for simple extractions

---

## Handoff Checklist

**Before Starting Sprint 1:**
- [ ] Review executive summary with team
- [ ] Confirm priority rankings
- [ ] Get Becca availability for testing
- [ ] Set up integration test environment
- [ ] Create feature branch: `feature/ux-sprint-1`

**Before Starting Sprint 2:**
- [ ] Demo Sprint 1 results to Becca
- [ ] Gather feedback
- [ ] Adjust Sprint 2 priorities if needed
- [ ] Merge Sprint 1 to main
- [ ] Deploy to staging

**Before Starting Sprint 3:**
- [ ] Pilot with Becca on 2-3 real projects
- [ ] Measure time savings
- [ ] Collect usability feedback
- [ ] Adjust Sprint 3 based on findings

**Before Production Deployment:**
- [ ] All tests passing (unit + integration)
- [ ] Becca signs off on pilot results
- [ ] Deployment docs complete
- [ ] Monitoring configured
- [ ] Rollback plan documented

---

## Summary

This plan transforms the Registry Review MCP from **prototype to production** in **5 focused weeks**:

- **Week 1-2:** Fix critical blockers (tests, duplicates, errors, progress)
- **Week 3-5:** Polish UX and reliability (decisions, changes, resilience, batch)
- **Month 2:** Operational readiness (costs, deployment, monitoring)

Each sprint builds on the previous, with clear success criteria and risk mitigation strategies. The system will be **pilot-ready after Week 5** and **production-ready after Month 2**.

---

**Plan Owner:** Development Team
**Review Frequency:** Weekly
**Last Updated:** November 13, 2025
**Next Review:** End of Week 1 (Sprint 1 completion)
