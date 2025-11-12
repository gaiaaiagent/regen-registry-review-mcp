# Registry Review MCP - Implementation Roadmap

**Version:** 2.0.0
**Current Phase:** Phase 3 (Evidence Extraction)
**Timeline:** 5 weeks
**Status:** Phase 2 Complete - Moving to Phase 3

---

## Vision

Transform Becca's 6-8 hour manual registry review into a 60-90 minute guided workflow by automating document discovery, evidence extraction, and compliance checking. The system must be elegant, reliable, and maintain complete human control over final decisions.

---

## Success Metrics (MVP)

### Functional
- ✅ Process 1-2 real projects end-to-end without errors
- ✅ Map 85%+ of requirements automatically
- ✅ Flag <10% of requirements for manual investigation
- ✅ Generate reports reviewers can use directly

### Performance
- ✅ Complete workflow in <2 minutes (warm cache)
- ✅ Document discovery in <10 seconds
- ✅ Evidence extraction in <90 seconds

### Quality
- ✅ 95%+ accuracy on document classification
- ✅ 90%+ accuracy on evidence location (page numbers)
- ✅ 85%+ confidence on high-confidence findings

---

## Phase 1: Foundation (Week 1)

**Goal:** Working MCP server with basic infrastructure

### Deliverables
1. ✅ Project setup with `uv`
2. ✅ Server entry point with FastMCP initialization
3. ✅ Logging infrastructure (stderr for MCP, file for debugging)
4. ✅ Configuration management
5. ✅ Error hierarchy
6. ✅ State management with atomic updates
7. ✅ Example checklist JSON from `examples/checklist.md`

### Acceptance Criteria
- Server starts with `uv run python src/registry_review_mcp/server.py`
- Appears in MCP Inspector
- Basic `/list-capabilities` prompt works
- Can create and load session successfully
- All infrastructure tests pass

### Technical Components

**Directory Structure:**
```
regen-registry-review-mcp/
├── src/
│   └── registry_review_mcp/
│       ├── __init__.py
│       ├── server.py                # MCP entry point
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py          # Config management
│       ├── models/
│       │   ├── __init__.py
│       │   ├── schemas.py           # Pydantic models
│       │   └── errors.py            # Error hierarchy
│       └── utils/
│           ├── __init__.py
│           ├── cache.py             # PDF caching
│           ├── state.py             # Atomic state
│           └── patterns.py          # Regex patterns
├── data/
│   ├── checklists/
│   │   └── soil-carbon-v1.2.2.json  # Requirements
│   ├── sessions/                    # gitignored
│   └── cache/                       # gitignored
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_infrastructure.py
├── pyproject.toml
└── README.md
```

### Tasks (Phase 1)

- [ ] Initialize `uv` project with dependencies
- [ ] Create directory structure
- [ ] Implement `config/settings.py` with validation
- [ ] Build error hierarchy in `models/errors.py`
- [ ] Create Pydantic schemas for Session, Document, Requirement
- [ ] Implement atomic state management in `utils/state.py`
- [ ] Build server entry point with logging
- [ ] Create basic session tools (create, load, update)
- [ ] Implement `/list-capabilities` prompt
- [ ] Convert `examples/checklist.md` to JSON
- [ ] Write infrastructure tests
- [ ] Test in MCP Inspector

**Estimated Effort:** 2-3 days
**Priority:** P0 (Critical)

---

## Phase 2: Document Processing ✅ COMPLETE

**Goal:** Document discovery, classification, and text extraction
**Status:** Complete (November 12, 2025)
**Test Coverage:** 6 tests passing, 36 total tests passing

### Deliverables
1. ✅ `discover_documents()` tool with recursive scanning and classification
2. ✅ `classify_document_by_filename()` with pattern matching (95%+ confidence)
3. ✅ `extract_pdf_text()` with caching and page-range support
4. ✅ `extract_gis_metadata()` for shapefiles and GeoJSON
5. ✅ Document index generation (`documents.json`)
6. ✅ `/document-discovery` prompt with auto-selection
7. ✅ `start_review()` quick-start tool

### Acceptance Criteria
- Process all 7 files in `examples/22-23/`
- Correctly classify project plan, baseline report, etc.
- Extract text from PDFs with 95%+ accuracy
- Cache extracted text (verify with timing tests)
- Generate complete document index JSON

### Test Case
```python
async def test_document_discovery():
    session = await create_session(
        "Botany Farm",
        "/path/to/examples/22-23",
        "soil-carbon-v1.2.2"
    )

    results = await discover_documents(session["session_id"])

    assert results["documents_found"] == 7
    assert results["classification_summary"]["project_plan"] == 1
    assert results["classification_summary"]["baseline_report"] == 1
    assert results["classification_summary"]["gis_shapefile"] >= 1
```

### Technical Components

**New Files:**
```
src/registry_review_mcp/
├── tools/
│   ├── __init__.py
│   ├── session_tools.py     # Already exists from Phase 1
│   └── document_tools.py    # NEW - discovery, classification
└── prompts/
    ├── __init__.py
    └── document_discovery.py  # NEW - workflow orchestration
```

### Tasks (Phase 2)

- [x] Implement `discover_documents()` with recursive scanning
- [x] Build filename-based classification heuristics
- [x] Add content-based classification fallback
- [x] Integrate `pdfplumber` for PDF extraction
- [x] Implement caching layer for PDF text
- [x] Add `fiona` for GIS metadata extraction
- [x] Create document index schema and storage
- [x] Build `/document-discovery` prompt with auto-selection
- [x] Write document processing tests (6 tests)
- [x] Test against Botany Farm example data
- [x] Add `start_review()` quick-start tool
- [x] Implement auto-session selection for better UX
- [x] Fix critical deadlock bug in locking mechanism

**Actual Effort:** 1 day (with TDD approach)
**Priority:** P0 (Critical) - COMPLETE

### Achievements Beyond Scope
- **Locking Bug Fix**: Discovered and fixed critical deadlock in `update_json()` using TDD
- **UX Improvements**: Auto-selection, better error messages, quick-start workflow
- **Test Coverage**: 36 total tests (100% passing)
- **Cache Robustness**: Fixed directory creation issues in cache

---

## Phase 3: Evidence Extraction (Week 3)

**Goal:** Requirement mapping and evidence snippet extraction

### Deliverables
1. ✅ `map_requirement_to_documents()` with keyword search
2. ✅ `extract_evidence()` with snippet extraction
3. ✅ `extract_structured_fields()` for specific data
4. ✅ Requirement coverage calculation
5. ✅ `/evidence-extraction` prompt

### Acceptance Criteria
- Map 18+ of 20 requirements successfully
- Extract evidence snippets with page numbers
- Calculate coverage status (covered/partial/missing)
- Flag 2-3 requirements for human review
- Confidence scores >0.8 for clear evidence

### Test Case
```python
async def test_evidence_extraction():
    # Assume session with discovered documents
    results = await evidence_extraction(session_id)

    assert results["requirements_total"] == 20
    assert results["requirements_covered"] >= 15
    assert results["requirements_partial"] <= 5
    assert results["requirements_missing"] <= 2

    # Check specific requirement
    req_002 = get_finding(results, "REQ-002")  # Land Tenure
    assert req_002["status"] in ["covered", "partial"]
    assert len(req_002["evidence_snippets"]) >= 1
    assert req_002["evidence_snippets"][0]["page"] is not None
```

### Technical Components

**New Files:**
```
src/registry_review_mcp/
├── tools/
│   └── evidence_tools.py    # NEW - mapping, extraction
└── prompts/
    └── evidence_extraction.py  # NEW - workflow
```

### Tasks (Phase 3)

- [ ] Load and parse checklist JSON
- [ ] Implement keyword extraction from requirements
- [ ] Build document relevance scoring
- [ ] Create snippet extraction with context (±100 words)
- [ ] Add page number and section tracking
- [ ] Implement confidence scoring
- [ ] Build coverage calculation logic
- [ ] Create `/evidence-extraction` prompt
- [ ] Add structured field extraction for specific data
- [ ] Write evidence extraction tests
- [ ] Test against all 23 requirements

**Estimated Effort:** 4-5 days
**Priority:** P0 (Critical)

---

## Phase 4: Validation & Reporting (Week 4)

**Goal:** Cross-validation and report generation

### Deliverables
1. ✅ `validate_date_alignment()` implementation
2. ✅ `validate_land_tenure()` with fuzzy matching
3. ✅ `generate_review_report()` in Markdown/JSON
4. ✅ `export_review()` to PDF
5. ✅ `/cross-validation` and `/report-generation` prompts

### Acceptance Criteria
- Date validation correctly checks 4-month rule
- Land tenure handles name variations (surname match)
- Report includes all 20 requirements with findings
- Report cites page numbers for all evidence
- PDF export works and is readable

### Test Case
```python
async def test_full_workflow():
    """End-to-end test against Botany Farm example"""

    # Initialize
    session = await create_session("Botany Farm", "/path/to/examples/22-23")
    sid = session["session_id"]

    # Discovery
    docs = await discover_documents(sid)
    assert docs["documents_found"] == 7

    # Extraction
    evidence = await evidence_extraction(sid)
    assert evidence["requirements_covered"] >= 15

    # Validation
    validation = await cross_validation(sid)
    assert validation["validations_passed"] >= 3

    # Report
    report = await generate_review_report(sid)
    assert Path(report["report_path"]).exists()

    content = Path(report["report_path"]).read_text()
    assert "Botany Farm" in content
    assert "C06-4997" in content
    assert "REQ-002" in content
```

### Technical Components

**New Files:**
```
src/registry_review_mcp/
├── tools/
│   └── validation_tools.py    # NEW - cross-validation
└── prompts/
    ├── cross_validation.py    # NEW - workflow
    └── report_generation.py   # NEW - workflow
```

### Tasks (Phase 4)

- [ ] Implement date alignment validation
- [ ] Add fuzzy matching for land tenure validation
- [ ] Build project ID consistency checker
- [ ] Create Markdown report generator
- [ ] Add JSON report export
- [ ] Implement PDF export (using reportlab or similar)
- [ ] Build `/cross-validation` prompt
- [ ] Build `/report-generation` prompt
- [ ] Write validation and reporting tests
- [ ] Test complete workflow end-to-end

**Estimated Effort:** 4-5 days
**Priority:** P0 (Critical)

---

## Phase 5: Integration & Polish (Week 5)

**Goal:** Complete workflow, testing, documentation

### Deliverables
1. ✅ `/initialize`, `/human-review`, `/complete` prompts
2. ✅ Comprehensive error handling
3. ✅ Integration test suite
4. ✅ Developer documentation
5. ✅ Example workflows
6. ✅ Performance optimization (caching, parallel processing)

### Acceptance Criteria
- All 7 prompts work end-to-end
- Error messages are clear and actionable
- Integration tests pass on CI/CD
- README with setup and usage instructions
- Process Botany Farm example in <2 minutes (warm cache)

### Technical Components

**New Files:**
```
src/registry_review_mcp/
├── prompts/
│   ├── initialize.py          # NEW - workflow start
│   ├── human_review.py        # NEW - review guidance
│   └── complete.py            # NEW - finalization
├── resources/
│   ├── __init__.py
│   └── data_resources.py      # NEW - MCP resources
tests/
└── test_integration.py        # NEW - E2E tests
```

### Tasks (Phase 5)

- [ ] Implement `/initialize` prompt
- [ ] Implement `/human-review` prompt
- [ ] Implement `/complete` prompt
- [ ] Add MCP resources (checklist://, session://, documents://)
- [ ] Comprehensive error handling and user-friendly messages
- [ ] Performance profiling and optimization
- [ ] Add parallel document classification
- [ ] Improve caching strategy
- [ ] Write integration tests
- [ ] Create README.md with setup instructions
- [ ] Write developer documentation
- [ ] Create example workflow guide
- [ ] Final testing with Botany Farm data
- [ ] Prepare for deployment

**Estimated Effort:** 4-5 days
**Priority:** P0 (Critical)

---

## Technical Stack

### Core Dependencies
```toml
[project]
dependencies = [
    "mcp[cli]>=1.21.0",         # MCP protocol
    "pdfplumber>=0.11.0",        # PDF extraction
    "pydantic>=2.11.0",          # Data validation
    "python-dateutil>=2.8.0",    # Date parsing
    "fiona>=1.9.0",              # GIS files
    "structlog>=24.0.0",         # Structured logging
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "black>=24.0.0",
    "ruff>=0.1.0",
]
```

### Architecture Principles

1. **Standalone Completeness** - Works independently without external MCPs
2. **Optional Integration** - Can enhance with KOI/Ledger but doesn't require them
3. **Session-Based State** - All state persists in local JSON files
4. **Fail-Explicit** - Escalate to human review when uncertain, never guess
5. **Evidence Traceability** - Every finding cites source document, page, section
6. **Workflow-Oriented** - Prompts guide sequential stages, not isolated tools

---

## Risk Management

### Identified Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| PDF extraction accuracy | High | Use pdfplumber + fallback to OCR, test on real docs |
| Performance on large projects | Medium | Implement caching, parallel processing, lazy loading |
| Complex GIS file handling | Medium | Start with basic metadata, defer advanced GIS to Phase 3+ |
| Requirement mapping accuracy | High | Keyword-based with confidence scoring, flag low confidence |
| Date parsing ambiguity | Low | Use multiple date formats, require ISO format when ambiguous |

### Contingency Plans

- **Behind schedule Week 2-3**: Reduce GIS support to metadata only
- **Evidence extraction <80% accuracy**: Add more sophisticated NLP or flag for human review
- **Performance issues**: Batch processing, increase cache TTL, optimize PDF extraction
- **Integration issues**: Prioritize standalone functionality, defer optional integrations

---

## Post-MVP Enhancements (Phase 3+)

### Deferred Features

1. **Batch Processing** - Handle 70-farm aggregated projects
2. **Credit Issuance Workflows** - Extend beyond registration review
3. **Cloud Storage** - Google Drive / SharePoint connectors
4. **KOI Commons Integration** - Methodology documentation queries
5. **Regen Ledger Integration** - On-chain metadata validation
6. **Multi-Methodology Support** - Beyond Soil Carbon v1.2.2
7. **Advanced GIS** - Spatial analysis, boundary validation
8. **ML-Based Classification** - Train on historical reviews

---

## Communication Plan

### Weekly Check-ins
- **Tuesday Stand-ups**: Progress, blockers, priorities
- **Thursday Reviews**: Demo completed features, gather feedback

### Stakeholders
- **Becca (Registry Agent)**: Primary user, provide workflow feedback
- **Regen Network Team**: Context on registry process, test data
- **Development Team**: Technical implementation, code reviews

### Status Reporting
- **Weekly**: Progress against roadmap, risks, decisions
- **Monthly**: Milestone completion, metrics, next phase planning

---

## Testing Strategy

### Unit Tests
- Infrastructure: State management, config, errors
- Document Tools: Discovery, classification, extraction
- Evidence Tools: Mapping, snippet extraction, confidence
- Validation Tools: Date alignment, land tenure, consistency

### Integration Tests
- End-to-end workflow: Initialize → Discovery → Extraction → Validation → Report
- Botany Farm scenario: Complete real-world test case
- Error handling: Graceful failures, recovery

### Manual Testing
- MCP Inspector: Tool/prompt testing
- Claude Code Integration: Agent workflow testing
- User Acceptance: Becca validates outputs

---

## Success Definition

**MVP is successful when:**

1. Becca can review Botany Farm project in <2 minutes (vs 6-8 hours manual)
2. 85%+ of requirements mapped with citations
3. Generated report is directly usable for approval decision
4. System escalates unclear cases rather than guessing
5. All acceptance criteria met for Phases 1-5

**Next phase triggers:**

- Positive user feedback from 2+ real reviews
- 50%+ time savings demonstrated
- <5% error rate in evidence location
- Team confidence in architecture and code quality

---

## Implementation Priorities

### P0 (Must Have for MVP)
- All Phase 1-5 deliverables
- Botany Farm end-to-end test passing
- Core 20 requirements for Soil Carbon v1.2.2

### P1 (Should Have, Post-MVP)
- Additional methodology support
- Batch processing
- Performance optimization beyond targets

### P2 (Nice to Have, Future)
- Cloud storage connectors
- KOI/Ledger integration
- Advanced GIS analysis
- ML-based classification

---

## Phase Completion Summary

### Phase 1: Foundation ✅ COMPLETE
- ✅ Session management
- ✅ Atomic state persistence with locking
- ✅ Configuration management
- ✅ Error hierarchy
- ✅ Caching infrastructure
- ✅ Checklist system (23 requirements)
- **Tests:** 23/36 passing
- **Status:** Production-ready

### Phase 2: Document Processing ✅ COMPLETE
- ✅ Document discovery and classification
- ✅ PDF text extraction with caching
- ✅ GIS metadata extraction
- ✅ Auto-selection and quick-start workflows
- ✅ Comprehensive UX improvements
- **Tests:** 36/36 passing (100%)
- **Status:** Production-ready
- **Notable:** Fixed critical deadlock bug using TDD

### Phase 3: Evidence Extraction 🚧 NEXT
- **Start Date:** November 13, 2025
- **Goal:** Requirement mapping and evidence extraction
- **Prerequisites:** All met (Phases 1-2 complete)

---

**Document Owner:** Development Team
**Last Updated:** November 12, 2025
**Next Review:** End of Phase 3 (Evidence Extraction Complete)
