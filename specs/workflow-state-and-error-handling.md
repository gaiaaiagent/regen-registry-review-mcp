# Workflow State Management and Error Handling Specification

## Problem Statement

The current system has critical gaps in error communication and workflow state management that lead to confusing user experiences:

### Issue 1: Silent API Key Failures
When evidence extraction runs without an API key configured:
- The system returns "0 covered, 0 partial, 23 missing" without explaining WHY
- No error message indicates the API key is missing
- Users proceed to cross-validation which then fails on empty data
- The system suggests "proceed to Report Generation" when the real fix is to configure credentials and re-run extraction

### Issue 2: No Stage Invalidation
When a stage fails or produces incomplete results:
- Downstream stages run on stale/empty data without warning
- Cross-validation ran on 0 extracted fields and suggested proceeding to reports
- No indication that the user needs to re-run a previous stage
- The workflow progress shows "completed" even when the stage produced no useful output

### Issue 3: Missing Execution Quality Tracking
The system tracks whether stages "completed" but not whether they succeeded meaningfully:
- A stage that extracts 0/23 requirements is marked "completed"
- No distinction between "ran successfully" vs "ran but failed to extract data"
- No tracking of execution errors or failure reasons

### Issue 4: Gateway Timeouts on Long Operations
Evidence extraction with LLM calls can take several minutes for large document sets:
- Nginx `/api/registry/` route has NO explicit timeout (defaults to 60s)
- Evidence extraction for 7 documents with 23 requirements easily exceeds 60s
- User sees "504 Gateway Timeout" with no indication of progress
- No way to resume or check status of long-running operations
- System suggests "retry" or "generate report" when the real issue is infrastructure timeout

**Current nginx config** (`/api/registry/` route):
```nginx
location ^~ /api/registry/ {
    # NO timeout settings - uses default 60s
    proxy_pass http://172.17.0.1:8003/;
    ...
}
```

**Compare to other routes** (digests has 300s timeout):
```nginx
location /digests/ {
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    ...
}
```

---

## Current State Analysis

### What Exists

**WorkflowProgress Model** (`schemas.py:59-69`):
```python
class WorkflowProgress(BaseModel):
    initialize: Literal["pending", "in_progress", "completed"] = "pending"
    document_discovery: Literal["pending", "in_progress", "completed"] = "pending"
    requirement_mapping: Literal["pending", "in_progress", "completed"] = "pending"
    evidence_extraction: Literal["pending", "in_progress", "completed"] = "pending"
    cross_validation: Literal["pending", "in_progress", "completed"] = "pending"
    # ... etc
```

**API Key Check** (`llm_extractors.py:1226-1227`):
```python
if not settings.anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY not set - required for LLM extraction")
```

**Stage Dependency Check** (`evidence_tools.py:554-562`):
```python
if workflow_progress.get("requirement_mapping") != "completed":
    raise ValueError("Requirement mapping not complete. Run Stage 3 first...")
```

### What's Missing

1. **Stage quality metrics** - Did the stage produce meaningful output?
2. **Failure reason tracking** - Why did a stage fail or produce empty results?
3. **Stage invalidation** - When should a stage be considered "stale" and need re-running?
4. **Pre-flight checks** - Validate prerequisites before running expensive operations
5. **Actionable error messages** - Tell users exactly what to do to fix the problem

---

## Proposed Solution

### 1. Enhanced Stage Status Model

Replace simple "pending/in_progress/completed" with richer state:

```python
class StageExecution(BaseModel):
    """Tracks execution state and quality for a workflow stage."""

    status: Literal["pending", "in_progress", "completed", "failed", "stale"] = "pending"

    # Execution metadata
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Quality metrics (stage-specific)
    success_rate: Optional[float] = None  # 0.0 to 1.0
    items_processed: Optional[int] = None
    items_successful: Optional[int] = None
    items_failed: Optional[int] = None

    # Error tracking
    error_code: Optional[str] = None  # e.g., "MISSING_API_KEY", "EMPTY_INPUT", "LLM_ERROR"
    error_message: Optional[str] = None
    error_recoverable: bool = True

    # Staleness tracking
    invalidated_at: Optional[datetime] = None
    invalidated_reason: Optional[str] = None
    depends_on_stages: List[str] = []  # Stages this depends on


class WorkflowProgress(BaseModel):
    """Enhanced workflow progress with quality tracking."""

    initialize: StageExecution = StageExecution()
    document_discovery: StageExecution = StageExecution(depends_on_stages=["initialize"])
    requirement_mapping: StageExecution = StageExecution(depends_on_stages=["document_discovery"])
    evidence_extraction: StageExecution = StageExecution(depends_on_stages=["requirement_mapping"])
    cross_validation: StageExecution = StageExecution(depends_on_stages=["evidence_extraction"])
    report_generation: StageExecution = StageExecution(depends_on_stages=["evidence_extraction"])
    human_review: StageExecution = StageExecution(depends_on_stages=["cross_validation"])
    completion: StageExecution = StageExecution(depends_on_stages=["human_review"])
```

### 2. Pre-Flight Validation System

Before running any stage, validate all prerequisites:

```python
class PreFlightCheck(BaseModel):
    """Result of a pre-flight validation check."""
    check_name: str
    passed: bool
    message: str
    severity: Literal["error", "warning", "info"]
    fix_action: Optional[str] = None  # What the user should do


class PreFlightResult(BaseModel):
    """Aggregated pre-flight check results."""
    can_proceed: bool
    checks: List[PreFlightCheck]
    blocking_issues: List[str]
    warnings: List[str]


async def preflight_evidence_extraction(session_id: str) -> PreFlightResult:
    """Validate all prerequisites before evidence extraction."""
    checks = []

    # Check 1: API Key configured
    if not settings.anthropic_api_key:
        checks.append(PreFlightCheck(
            check_name="api_key_configured",
            passed=False,
            message="Anthropic API key not configured",
            severity="error",
            fix_action="Set REGISTRY_REVIEW_ANTHROPIC_API_KEY in .env file and restart the service"
        ))
    else:
        checks.append(PreFlightCheck(
            check_name="api_key_configured",
            passed=True,
            message="API key configured",
            severity="info"
        ))

    # Check 2: Previous stage completed successfully
    session = await load_session(session_id)
    mapping_stage = session.workflow_progress.requirement_mapping

    if mapping_stage.status != "completed":
        checks.append(PreFlightCheck(
            check_name="mapping_completed",
            passed=False,
            message="Requirement mapping not completed",
            severity="error",
            fix_action="Run Stage 3 (Requirement Mapping) first"
        ))
    elif mapping_stage.success_rate == 0:
        checks.append(PreFlightCheck(
            check_name="mapping_quality",
            passed=False,
            message="Requirement mapping produced no results",
            severity="error",
            fix_action="Check that documents were uploaded and re-run Stage 2 and Stage 3"
        ))

    # Check 3: Documents available
    documents = await load_documents(session_id)
    if not documents:
        checks.append(PreFlightCheck(
            check_name="documents_available",
            passed=False,
            message="No documents found for extraction",
            severity="error",
            fix_action="Upload documents and run Stage 2 (Document Discovery)"
        ))

    # Check 4: LLM extraction enabled
    if not settings.llm_extraction_enabled:
        checks.append(PreFlightCheck(
            check_name="llm_extraction_enabled",
            passed=False,
            message="LLM extraction is disabled in configuration",
            severity="warning",
            fix_action="Set REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED=true in .env"
        ))

    blocking = [c for c in checks if not c.passed and c.severity == "error"]
    warnings = [c for c in checks if not c.passed and c.severity == "warning"]

    return PreFlightResult(
        can_proceed=len(blocking) == 0,
        checks=checks,
        blocking_issues=[c.message for c in blocking],
        warnings=[c.message for c in warnings]
    )
```

### 3. Stage Invalidation Logic

When upstream stages are re-run, automatically invalidate downstream results:

```python
STAGE_DEPENDENCIES = {
    "document_discovery": ["initialize"],
    "requirement_mapping": ["document_discovery"],
    "evidence_extraction": ["requirement_mapping"],
    "cross_validation": ["evidence_extraction"],
    "report_generation": ["evidence_extraction", "cross_validation"],
    "human_review": ["cross_validation"],
    "completion": ["human_review"]
}


async def invalidate_downstream_stages(session_id: str, changed_stage: str) -> List[str]:
    """Mark all stages that depend on changed_stage as stale."""
    invalidated = []
    session = await load_session(session_id)

    for stage_name, dependencies in STAGE_DEPENDENCIES.items():
        if changed_stage in dependencies:
            stage = getattr(session.workflow_progress, stage_name)
            if stage.status == "completed":
                stage.status = "stale"
                stage.invalidated_at = datetime.utcnow()
                stage.invalidated_reason = f"Upstream stage '{changed_stage}' was re-run"
                invalidated.append(stage_name)

                # Recursively invalidate further downstream
                invalidated.extend(
                    await invalidate_downstream_stages(session_id, stage_name)
                )

    await save_session(session)
    return invalidated
```

### 4. Improved Error Responses

Return structured error information that tells users exactly what to do:

```python
class WorkflowError(BaseModel):
    """Structured error response for workflow operations."""

    error_code: str
    error_message: str
    stage: str

    # Recovery guidance
    is_recoverable: bool
    fix_actions: List[str]

    # Context
    related_stages: List[str] = []
    diagnostic_info: Dict[str, Any] = {}


# Example error codes and their fix actions:
ERROR_CATALOG = {
    "MISSING_API_KEY": {
        "message": "Anthropic API key not configured for LLM extraction",
        "is_recoverable": True,
        "fix_actions": [
            "1. Add REGISTRY_REVIEW_ANTHROPIC_API_KEY to .env file",
            "2. Restart the service: pm2 restart registry-review-api",
            "3. Re-run evidence extraction"
        ]
    },
    "UPSTREAM_STAGE_FAILED": {
        "message": "Cannot proceed because a required upstream stage failed",
        "is_recoverable": True,
        "fix_actions": [
            "1. Check the status of upstream stages",
            "2. Fix any issues with failed stages",
            "3. Re-run stages in order"
        ]
    },
    "UPSTREAM_STAGE_STALE": {
        "message": "Upstream stage data is stale and needs to be re-run",
        "is_recoverable": True,
        "fix_actions": [
            "1. Re-run the stale upstream stage",
            "2. Then re-run this stage"
        ]
    },
    "EMPTY_EXTRACTION_RESULTS": {
        "message": "Evidence extraction completed but found no evidence",
        "is_recoverable": True,
        "fix_actions": [
            "1. Verify documents are text-based PDFs (not scanned images)",
            "2. Check that documents contain relevant project information",
            "3. Verify API key is valid and has sufficient credits",
            "4. Re-run evidence extraction"
        ]
    },
    "VALIDATION_ON_EMPTY_DATA": {
        "message": "Cross-validation cannot run meaningfully on empty evidence data",
        "is_recoverable": True,
        "fix_actions": [
            "1. Check evidence extraction results (Stage 4)",
            "2. If 0% coverage, re-run evidence extraction",
            "3. Then re-run cross-validation"
        ]
    }
}
```

### 5. Smart Next-Step Recommendations

Replace static "next step" suggestions with context-aware recommendations:

```python
async def get_recommended_next_step(session_id: str) -> Dict[str, Any]:
    """Determine the best next action based on current workflow state."""
    session = await load_session(session_id)
    wp = session.workflow_progress

    # Check for failed stages that need attention
    for stage_name in ["evidence_extraction", "requirement_mapping", "document_discovery"]:
        stage = getattr(wp, stage_name)

        if stage.status == "failed":
            return {
                "action": "fix_failed_stage",
                "stage": stage_name,
                "message": f"Stage '{stage_name}' failed and needs attention",
                "error_code": stage.error_code,
                "fix_actions": ERROR_CATALOG.get(stage.error_code, {}).get("fix_actions", [])
            }

        if stage.status == "completed" and stage.success_rate == 0:
            return {
                "action": "investigate_empty_results",
                "stage": stage_name,
                "message": f"Stage '{stage_name}' completed but produced no results",
                "fix_actions": [
                    f"1. Check inputs to {stage_name}",
                    f"2. Review any error logs",
                    f"3. Re-run {stage_name} after fixing issues"
                ]
            }

        if stage.status == "stale":
            return {
                "action": "rerun_stale_stage",
                "stage": stage_name,
                "message": f"Stage '{stage_name}' is stale and should be re-run",
                "reason": stage.invalidated_reason,
                "fix_actions": [f"Re-run {stage_name}"]
            }

    # Check for low-quality completed stages
    if wp.evidence_extraction.status == "completed":
        if wp.evidence_extraction.success_rate < 0.1:  # Less than 10% coverage
            return {
                "action": "investigate_low_coverage",
                "stage": "evidence_extraction",
                "message": f"Evidence extraction has very low coverage ({wp.evidence_extraction.success_rate:.0%})",
                "fix_actions": [
                    "1. Verify API key is configured correctly",
                    "2. Check that documents are text-extractable",
                    "3. Review mapped documents in Stage 3",
                    "4. Re-run evidence extraction"
                ],
                "warning": "Proceeding to validation with low coverage will produce poor results"
            }

    # Normal progression
    stages_order = [
        "initialize", "document_discovery", "requirement_mapping",
        "evidence_extraction", "cross_validation", "report_generation",
        "human_review", "completion"
    ]

    for stage_name in stages_order:
        stage = getattr(wp, stage_name)
        if stage.status == "pending":
            return {
                "action": "run_next_stage",
                "stage": stage_name,
                "message": f"Ready to proceed with {stage_name.replace('_', ' ').title()}"
            }

    return {
        "action": "workflow_complete",
        "message": "All stages completed"
    }
```

### 6. Long-Running Operation Handling

For operations that may exceed HTTP timeouts (evidence extraction, report generation):

```python
class AsyncOperation(BaseModel):
    """Track long-running operations that may exceed HTTP timeouts."""

    operation_id: str
    operation_type: Literal["evidence_extraction", "report_generation", "batch_validation"]
    session_id: str

    # Status
    status: Literal["pending", "running", "completed", "failed", "timeout"] = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Progress tracking
    total_items: int = 0
    processed_items: int = 0
    progress_percent: float = 0.0
    current_item: Optional[str] = None  # e.g., "Processing REQ-015"

    # Results (when completed)
    result_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


async def start_async_evidence_extraction(session_id: str) -> AsyncOperation:
    """Start evidence extraction as an async operation with progress tracking."""
    operation = AsyncOperation(
        operation_id=f"op-{uuid4().hex[:12]}",
        operation_type="evidence_extraction",
        session_id=session_id,
        status="running",
        started_at=datetime.utcnow()
    )

    # Save operation state
    await save_operation(operation)

    # Start background task
    asyncio.create_task(run_evidence_extraction_async(operation))

    return operation


async def get_operation_status(operation_id: str) -> AsyncOperation:
    """Check status of a long-running operation."""
    return await load_operation(operation_id)
```

**Nginx Configuration Fix:**

Update `/api/registry/` route with appropriate timeouts:

```nginx
location ^~ /api/registry/ {
    auth_basic off;
    client_max_body_size 100M;

    proxy_pass http://172.17.0.1:8003/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # ADDED: Timeout settings for LLM operations (10 minutes)
    proxy_connect_timeout 60s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;

    # ADDED: Buffer settings for large responses
    proxy_buffer_size 128k;
    proxy_buffers 4 256k;
    proxy_busy_buffers_size 256k;

    # CORS headers
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Origin, Content-Type, Accept, Authorization' always;
}
```

**REST API Endpoints for Async Operations:**

```
# Start async evidence extraction
POST /sessions/{session_id}/evidence/async
Response: { "operation_id": "op-abc123", "status": "running", "check_url": "/operations/op-abc123" }

# Check operation status
GET /operations/{operation_id}
Response: {
    "operation_id": "op-abc123",
    "status": "running",
    "progress_percent": 45.0,
    "current_item": "Processing REQ-011",
    "processed_items": 10,
    "total_items": 23
}

# List active operations for session
GET /sessions/{session_id}/operations
Response: { "operations": [...] }
```

---

## Implementation Plan

### Phase 0: Immediate Nginx Fix (Critical - Do Now)
1. Update `/api/registry/` nginx route with 600s timeouts
2. Reload nginx configuration
3. Test evidence extraction completes without 504

```bash
# Update nginx.conf with timeout settings, then:
docker exec nginx nginx -s reload
```

### Phase 1: Enhanced State Model (High Priority)
1. Update `WorkflowProgress` model with `StageExecution` class
2. Add quality metrics to each stage's completion logic
3. Store error information when stages fail
4. Migrate existing sessions to new format

### Phase 2: Pre-Flight Checks (High Priority)
1. Implement `preflight_evidence_extraction()` with API key check
2. Add pre-flight checks to all stage endpoints
3. Return pre-flight failures BEFORE attempting expensive operations
4. Include fix_actions in all error responses

### Phase 3: Stage Invalidation (Medium Priority)
1. Implement `invalidate_downstream_stages()` logic
2. Call invalidation when stages are re-run
3. Show "stale" status in session info responses
4. Warn users when running stages on stale data

### Phase 4: Smart Recommendations (Medium Priority)
1. Implement `get_recommended_next_step()` with quality checks
2. Replace static next_steps with dynamic recommendations
3. Add warnings when proceeding would be unproductive
4. Include diagnostic information in responses

### Phase 5: REST API Updates (Required for all phases)
1. Add `/sessions/{id}/preflight/{stage}` endpoint
2. Update all stage endpoints to return structured errors
3. Add `stage_quality` field to session info responses
4. Update GPT instructions to use new error information

### Phase 6: Async Operations (Medium Priority)
1. Implement `AsyncOperation` model for long-running tasks
2. Add `/sessions/{id}/evidence/async` endpoint
3. Add `/operations/{id}` status endpoint
4. Implement background task runner with progress updates
5. Update GPT instructions to use async operations for large document sets

---

## API Changes

### New Endpoint: Pre-Flight Check

```
GET /sessions/{session_id}/preflight/{stage_name}

Response:
{
    "can_proceed": false,
    "checks": [
        {
            "check_name": "api_key_configured",
            "passed": false,
            "message": "Anthropic API key not configured",
            "severity": "error",
            "fix_action": "Set REGISTRY_REVIEW_ANTHROPIC_API_KEY in .env and restart service"
        }
    ],
    "blocking_issues": ["Anthropic API key not configured"],
    "warnings": []
}
```

### Enhanced Session Info Response

```
GET /sessions/{session_id}

Response:
{
    "session_id": "session-abc123",
    "status": "Evidence Extraction Failed",
    "workflow_progress": {
        "evidence_extraction": {
            "status": "completed",
            "success_rate": 0.0,
            "items_processed": 23,
            "items_successful": 0,
            "error_code": "MISSING_API_KEY",
            "error_message": "API key not configured during extraction"
        }
    },
    "recommended_action": {
        "action": "investigate_empty_results",
        "stage": "evidence_extraction",
        "message": "Evidence extraction completed but produced no results",
        "fix_actions": [
            "1. Verify REGISTRY_REVIEW_ANTHROPIC_API_KEY is set in .env",
            "2. Restart service: pm2 restart registry-review-api",
            "3. Re-run evidence extraction"
        ]
    }
}
```

### Structured Error Response

```
POST /sessions/{session_id}/evidence

Response (on error):
{
    "error": {
        "code": "MISSING_API_KEY",
        "message": "Anthropic API key not configured for LLM extraction",
        "stage": "evidence_extraction",
        "is_recoverable": true,
        "fix_actions": [
            "1. Add REGISTRY_REVIEW_ANTHROPIC_API_KEY to .env file",
            "2. Restart the service: pm2 restart registry-review-api",
            "3. Re-run evidence extraction"
        ]
    }
}
```

---

## Success Criteria

1. **Users never see "0% coverage" without explanation** - Always explain WHY extraction failed
2. **Users never proceed on stale data unknowingly** - Warn when upstream stages need re-running
3. **Every error includes fix instructions** - No error without actionable guidance
4. **Pre-flight catches issues before wasting time** - Validate prerequisites before expensive operations
5. **Smart recommendations prevent unproductive workflows** - Don't suggest "generate report" when evidence is empty

---

## Appendix: Error Code Reference

| Code | Stage | Cause | Recovery |
|------|-------|-------|----------|
| `MISSING_API_KEY` | evidence_extraction | ANTHROPIC_API_KEY not in .env | Add key, restart, re-run |
| `INVALID_API_KEY` | evidence_extraction | API key rejected by Anthropic | Check key validity |
| `LLM_RATE_LIMITED` | evidence_extraction | Hit API rate limits | Wait and retry |
| `UPSTREAM_STAGE_PENDING` | any | Required stage not run | Run upstream stage first |
| `UPSTREAM_STAGE_FAILED` | any | Required stage failed | Fix and re-run upstream |
| `UPSTREAM_STAGE_STALE` | any | Upstream was re-run | Re-run this stage |
| `EMPTY_EXTRACTION_RESULTS` | evidence_extraction | LLM found no evidence | Check docs, re-run |
| `VALIDATION_ON_EMPTY_DATA` | cross_validation | No evidence to validate | Fix extraction first |
| `NO_DOCUMENTS` | requirement_mapping | No documents uploaded | Upload docs, run discovery |
| `UNPARSEABLE_DOCUMENTS` | evidence_extraction | PDFs are scanned images | OCR or replace documents |
| `GATEWAY_TIMEOUT` | any | Nginx 504 (operation too long) | Increase nginx timeout, retry |
| `OPERATION_TIMEOUT` | evidence_extraction | LLM call exceeded timeout | Use async endpoint, check API |
| `OPERATION_IN_PROGRESS` | any | Previous operation still running | Wait for completion or cancel |
