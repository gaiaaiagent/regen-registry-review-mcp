# Registry Review Workflow: Eight-Stage Process

**Document Type:** Canonical Specification
**Created:** November 20, 2025
**Status:** Authoritative Reference
**Purpose:** Single source of truth for the Registry Review Agent workflow

---

## Executive Summary

The Registry Review Agent automates carbon credit project documentation review through an eight-stage workflow. Each stage produces a discrete artifact that the human reviewer can verify before proceeding. The agent handles tedious document organization, data extraction, and consistency checking while the human provides expertise, judgment, and final approval.

**Success Metrics:**
- 50-70% reduction in manual review time
- Sub-10% escalation rate (issues requiring deep human investigation)
- 95%+ accuracy in document discovery and requirement mapping
- 100+ annual project capacity

**Collaboration Model:**
- AI writes in blue (automated findings with citations)
- Human writes in black (expert analysis and decisions)
- Every stage includes human verification checkpoints

---

## The Eight Stages

### Stage 1: Initialize

**Purpose:** Establish review context and prepare workspace for evaluation.

**Agent Actions:**
- Create unique review session ID
- Accept uploaded files or folder links (Google Drive, SharePoint)
- Load selected checklist template (Credit Class + Methodology specific)
- Generate Resource Descriptors for each file with metadata:
  - IRI, title, source, visibility, checksum, indexedAt
- Set session status to `Initialized`

**Human Actions:**
- Select or create Registry project
- Choose data source mode:
  - **Mirror mode** (default): upload files or link Google Drive folder
  - **Reference mode** (optional): link SharePoint folder
- Select appropriate checklist template from available options
- Confirm session creation

**Stage Output:**
- Session metadata record with:
  - Project ID / Review session ID
  - List of provided files/links with Resource Descriptors
  - Selected checklist template ID
  - Chosen access mode (Mirror/Reference)
  - Session status: `Initialized`

**Success Criteria:**
- All required inputs present (files/links AND checklist template)
- Resource Descriptors created with valid checksums
- Session appears in "Recent Reviews" list

**State Transitions:**
- ✓ Proceed to Stage 2: Document Discovery
- ✗ Block if missing required inputs (show validation message)

---

### Stage 2: Document Discovery

**Purpose:** Identify, normalize, and classify all available documents.

**Agent Actions:**
- Scan configured folder/links (respecting Mirror vs Reference mode)
- Extract file metadata (name, type, size, last modified)
- Normalize file names (trim noise, preserve clarity)
- Classify files by type:
  - Technical reports (project plans, monitoring reports)
  - Legal documents (land tenure, deeds, titles)
  - Geospatial data (shapefiles, GeoJSON, KML)
  - Spreadsheets (emissions data, sampling plans, yield data)
  - Images (maps, field photos)
  - Other/Unknown
- Generate document inventory with classification confidence scores

**Human Actions:**
- Review discovered documents list
- Mark documents as:
  - **In Scope** (default): included in review
  - **Ignored**: excluded from context
  - **Pinned**: critical context for agent
- Correct misclassifications if needed
- Confirm document inventory completeness

**Stage Output:**
- Document inventory table with:
  - Normalized name
  - Original source name
  - File type and classification
  - Source (Drive/SharePoint/upload)
  - Status (In scope / Ignored / Pinned)
  - Resource IRI and checksum
- Updated session status: `Documents Discovered`

**Success Criteria:**
- All files successfully scanned and classified
- Classification accuracy >85% (measured by human corrections)
- Only non-ignored documents exposed to subsequent stages
- Changes persisted between sessions

**State Transitions:**
- ✓ Proceed to Stage 3: Requirement Mapping
- ↻ Re-run if new documents added
- ✗ Flag if critical file types missing (e.g., no project plan found)

---

### Stage 3: Requirement Mapping

**Purpose:** Connect discovered documents to specific checklist requirements.

**Agent Actions:**
- Load machine-readable checklist template for selected Credit Class + Methodology
- Parse checklist into structured requirements list with:
  - Requirement ID (e.g., REQ-001)
  - Requirement text
  - Evidence type expected (document type, data points)
  - Source citation (Program Guide section, Protocol section)
- Analyze Pinned + In Scope documents using semantic matching
- Suggest document → requirement mappings with confidence scores
- Flag requirements with no plausible document matches

**Human Actions:**
- Review suggested mappings in matrix view (rows: requirements, columns: documents)
- Confirm high-confidence suggestions
- Remove incorrect mappings
- Manually add missing mappings
- Prioritize requirements needing attention (unmapped, low-confidence)

**Stage Output:**
- Requirement mapping matrix with:
  - Each requirement linked to 0+ document IDs
  - Mapping status: `Suggested` → `Confirmed` / `Removed` / `Unmapped`
  - Confidence scores for agent suggestions
- List of unmapped requirements flagged for human attention
- Updated session status: `Requirements Mapped`

**Success Criteria:**
- Each requirement has mapping status (confirmed/unmapped/manual)
- Unmapped requirements clearly visible with warning icons
- Mapping changes persisted and audit-logged
- >90% of obvious mappings suggested correctly by agent

**State Transitions:**
- ✓ Proceed to Stage 4: Evidence Extraction
- ↻ Re-run mapping if documents added/removed
- ⚠ Escalate if >50% requirements unmapped (possible wrong checklist selected)

---

### Stage 4: Evidence Extraction

**Purpose:** Extract key data points and text snippets from mapped documents.

**Agent Actions:**
- For each requirement with mapped documents:
  - Parse document content (PDF text extraction, table recognition, metadata parsing)
  - Identify relevant sections using requirement context
  - Extract 0-3 evidence snippets per requirement:
    - Short quote or data point (~2-3 sentences max)
    - Source citation (document name, page number, section)
    - Extraction confidence score
  - Extract structured data where applicable:
    - Dates (sampling dates, imagery dates, crediting periods)
    - Locations (coordinates, parcel IDs, field boundaries)
    - Ownership information (names, entities, deed references)
    - Numerical data (areas, carbon values, sample counts)
- Store extractions in structured format: `{ requirementId, docId, location, snippetText, dataPoints }`

**Human Actions:**
- Review extracted evidence snippets in collapsible panels per requirement
- Delete irrelevant or incorrect snippets
- Add manual notes/observations alongside snippets
- Request re-extraction for specific documents if needed
- Flag requirements where extraction failed or seems incomplete

**Stage Output:**
- Evidence database with:
  - Snippets linked to requirement + source document + location
  - Structured data points extracted (dates, locations, values)
  - Extraction confidence scores
  - Human annotations and corrections
- Requirements marked: `Evidence Found` / `No Automatic Evidence` / `Manual Review Needed`
- Updated session status: `Evidence Extracted`

**Success Criteria:**
- >85% of mapped requirements have at least one evidence snippet
- All snippets include source citations (document + page/section)
- Extracted dates, coordinates, and values are parseable and valid
- False positive rate <5% (snippets reviewer disputes as irrelevant)

**State Transitions:**
- ✓ Proceed to Stage 5: Cross-Validation
- ↻ Re-run extraction for specific requirements/documents
- ⚠ Escalate requirements with repeated extraction failures

---

### Stage 5: Cross-Validation

**Purpose:** Verify consistency, completeness, and compliance across all extracted evidence.

**Agent Actions:**
- **Completeness Check:**
  - Verify each requirement has mapped documents
  - Check mapped documents contain expected evidence types
  - Compute coverage status:
    - `Covered`: mapped documents + sufficient evidence found
    - `Partially Covered`: mapped documents but incomplete/ambiguous evidence
    - `Missing`: no mapped documents or clearly insufficient evidence
    - `Needs Manual Review`: cannot assess (unsupported format, complex judgment)
- **Consistency Validation:**
  - Cross-check project metadata across documents (project name, ID, dates)
  - Verify land tenure: ownership claims in project plan match deed/title documents
  - Validate temporal alignment: sampling dates within ±4 months of imagery dates
  - Check geolocation consistency: field boundaries match across GIS files and reports
  - Verify numerical consistency: areas, parcel counts, sample counts align
- **Protocol Compliance:**
  - Check methodology-specific requirements (stratification, sample depth, core counts)
  - Validate buffer pool contributions, leakage tests, additionality evidence
  - Flag MAPE >20% between baseline and monitoring results
  - Verify lab analysis includes SOC% and accreditation
- Generate validation flags:
  - `Info`: notable patterns, non-blocking observations
  - `Warning`: potential issues requiring attention
  - `Error`: clear requirement violations or critical gaps

**Human Actions:**
- Review overall coverage summary (e.g., "34/50 covered, 10 partial, 6 missing")
- Filter and prioritize by status (focus on Missing/Partial/Errors first)
- Review validation flags and agent notes
- Override agent assessments where expert judgment differs
- Add contextual notes explaining gray areas or acceptable variations

**Stage Output:**
- Coverage summary statistics by requirement status
- Validation results for each requirement:
  - Status (Covered/Partial/Missing/Manual Review)
  - Mapped documents list
  - Evidence snippets
  - Validation flags (Info/Warning/Error)
  - Consistency check results
  - Agent-generated notes
  - Human override notes
- List of critical gaps requiring proponent revision
- Updated session status: `Cross-Validated`

**Success Criteria:**
- Every requirement has computed coverage status
- Consistency checks run for all applicable requirement pairs
- Validation logic matches protocol version and methodology
- Human can quickly understand status without reading all documents
- <10% false positive validation errors (agent flags non-issues)

**State Transitions:**
- ✓ Proceed to Stage 6: Report Generation
- ↻ Return to Stage 4 if new evidence needed for specific requirements
- ⚠ Branch to revision workflow if critical gaps identified
- ✗ Block if fundamental issues detected (wrong protocol, corrupt files)

---

### Stage 6: Report Generation

**Purpose:** Produce structured, auditable Registry Review Report.

**Agent Actions:**
- Compile complete review findings into structured report
- Generate two representations:
  - **JSON**: machine-readable for internal systems and audit trails
  - **Human-readable**: HTML/PDF/Markdown for sharing and archival
- Include in report:
  - **Header:** Project metadata, review date, reviewer, session ID, checklist template
  - **Executive Summary:** Coverage statistics, critical findings, overall assessment
  - **Per-Requirement Entries:**
    - Requirement ID and text
    - Coverage status
    - Mapped documents (names + IRIs/URLs)
    - Evidence snippets with citations
    - Validation flags and notes
    - Human annotations
  - **Provenance Section:**
    - Document source (Drive/SharePoint/upload)
    - Resolver URLs
    - Checksums for verification
    - Access mode used
  - **Appendices:**
    - Complete document inventory
    - Validation logic applied (protocol version, methodology)
    - Agent configuration and version
- Assign report version ID and timestamp
- Store in session reports collection

**Human Actions:**
- Review generated report for completeness and clarity
- Request regeneration if format issues or missing sections
- Export report in preferred format (PDF/Markdown download)
- Prepare for final human review stage

**Stage Output:**
- **Registry Review Report** in dual formats:
  - `report-{sessionId}-v{version}.json`
  - `report-{sessionId}-v{version}.pdf`
- Report metadata:
  - Version ID and timestamp
  - Generation parameters
  - Link to source session
- Updated session status: `Report Generated`

**Success Criteria:**
- Report includes all requirements with complete data
- All citations resolve to actual documents and locations
- Provenance section allows independent verification
- Report versioning enables tracking changes across regenerations
- Human-readable format is clear and professional

**State Transitions:**
- ✓ Proceed to Stage 7: Human Review
- ↻ Regenerate report if issues found or data updated
- ← Return to earlier stages if major gaps discovered during report review

---

### Stage 7: Human Review

**Purpose:** Expert validation, annotation, and revision handling.

**Agent Actions:**
- Present report in editable interface
- Track all human edits with timestamps and attribution
- Support revision workflows:
  - Mark requirements as `Pending Proponent Revision`
  - Accept revised/additional documents
  - Re-run relevant stages for updated materials
- Maintain change log:
  - Document additions/removals
  - Agent re-runs (which stages, when)
  - Report regenerations
  - Status changes
- Enable communication:
  - Generate revision request summaries for proponents
  - Template emails with specific gaps identified

**Human Actions:**
- Review complete report with critical eye
- Edit narrative sections and notes
- Override agent assessments using expert judgment
- Identify items requiring proponent revision:
  - Missing documents
  - Insufficient evidence
  - Inconsistencies needing explanation
  - Protocol requirement violations
- Request revisions from proponent if needed
- Upload/link revised documents when received
- Re-run affected workflow stages for new materials
- Make final determination:
  - **Approve**: project meets requirements, ready for completion
  - **Conditional Approval**: minor fixes needed, can proceed with notes
  - **Reject**: major gaps, requires substantial rework
  - **On Hold**: awaiting information, cannot assess yet

**Stage Output:**
- Finalized report with:
  - Human validation annotations
  - Expert judgment notes
  - Revision history showing all changes
  - Version history of agent re-runs
  - Final determination status
- Change log documenting:
  - Who changed what and when
  - Which stages re-run and why
  - Communication with proponents
- Updated session status: `Human Review Complete` (with approval/rejection/conditional/hold)

**Success Criteria:**
- All requirements have human-verified status
- Reviewer can clearly articulate approval rationale or rejection reasons
- Revision workflows handled smoothly without data loss
- Change log provides complete audit trail
- Report ready for final archival or proponent communication

**State Transitions:**
- ✓ Proceed to Stage 8: Completion (if approved/conditional)
- ↻ Return to Stage 2-6 if revisions received (partial workflow re-run)
- ⏸ Pause if on hold (preserve state for later resumption)
- ✗ Archive as rejected (preserve for learning/future reference)

---

### Stage 8: Completion

**Purpose:** Finalize approved review and prepare for archival and on-chain registration.

**Agent Actions:**
- Lock finalized report (prevent further edits without new version)
- Generate final report package:
  - Approved Registry Review Report (PDF + JSON)
  - Complete document inventory with checksums
  - Audit trail (all changes, re-runs, human decisions)
  - Provenance metadata for all resources
- Prepare data for on-chain registration:
  - Project metadata ready for Regen Ledger
  - Document IRIs for data module anchoring
  - Review attestation signed by reviewer
- Archive session materials:
  - All uploaded documents (if Mirror mode)
  - Complete review history
  - Communication logs
- Update project status in tracking system
- Generate data posts for project pages (if approved)

**Human Actions:**
- Final sign-off on completed review
- Submit project for on-chain registration (if approved)
- Communicate final decision to proponent
- Archive review materials according to organizational standards
- Note lessons learned or process improvements for future reviews

**Stage Output:**
- **Finalized Review Package:**
  - Locked report (no further edits)
  - Complete audit trail
  - Signed attestation
  - Archive-ready materials
- **On-chain registration data** (if approved):
  - Project instantiation parameters
  - Document IRI anchors
  - Review attestation hash
- **Session closure record:**
  - Final status (Approved/Conditional/Rejected)
  - Completion timestamp
  - Reviewer sign-off
- Updated session status: `Completed`

**Success Criteria:**
- Report locked and immutable (except new versions)
- All materials archived and retrievable
- On-chain data prepared correctly (if applicable)
- Clear communication sent to proponent
- Session marked complete in tracking system

**State Transitions:**
- ✓ Archive session (success path)
- ↻ Reopen only via explicit "New Version" action (creates new session ID)
- ⚠ Flag for audit if unusual patterns detected

---

## Stage Progression Rules

### Linear Flow (Happy Path)
```
Initialize → Document Discovery → Requirement Mapping → Evidence Extraction
  → Cross-Validation → Report Generation → Human Review → Completion
```

### Branch Points & Loops

**After Stage 2 (Document Discovery):**
- ↻ Loop: New documents added → re-run discovery
- ✗ Block: Critical file types missing → request from proponent

**After Stage 3 (Requirement Mapping):**
- ↻ Loop: Documents changed → re-run mapping
- ⚠ Escalate: >50% unmapped → wrong checklist selected

**After Stage 4 (Evidence Extraction):**
- ↻ Loop: Re-extract specific requirements if initial attempt failed
- ← Return: New documents require remapping (Stage 3)

**After Stage 5 (Cross-Validation):**
- ✓ Happy path: Proceed to report
- ⚠ Revision needed: Critical gaps → request proponent fixes → wait → Stage 2
- ✗ Fatal issues: Wrong protocol/corrupt files → reject early

**After Stage 6 (Report Generation):**
- ↻ Loop: Regenerate if format issues or data updated
- ← Return: Major gaps found → may return to Stage 3-5

**After Stage 7 (Human Review):**
- ✓ Approved → Stage 8
- ↻ Revisions received → return to appropriate stage (2-6)
- ⏸ On hold → preserve state
- ✗ Rejected → archive

### Partial Re-runs

The workflow supports **surgical re-execution** of stages without full restart:
- New document added → re-run Stage 2 → update Stages 3-7 only for new doc
- Extraction improved → re-run Stage 4 → update Stages 5-7
- Protocol updated → reload checklist → re-run Stages 3-7

---

## Agent vs. Human Responsibilities

| Stage | Agent (Automated) | Human (Expert Judgment) |
|-------|------------------|-------------------------|
| **1. Initialize** | Create session, generate metadata | Select project, choose checklist, confirm inputs |
| **2. Discovery** | Scan, normalize, classify files | Review inventory, mark pinned/ignored, confirm completeness |
| **3. Mapping** | Suggest doc→requirement matches | Confirm, correct, prioritize mappings |
| **4. Extraction** | Parse documents, extract snippets & data | Review snippets, delete irrelevant, add notes |
| **5. Validation** | Check completeness, consistency, compliance | Override assessments, explain gray areas, prioritize gaps |
| **6. Report** | Generate structured output with citations | Review for clarity, export final version |
| **7. Human Review** | Track edits, support revisions, maintain logs | Make approval decision, request fixes, finalize |
| **8. Completion** | Lock report, archive, prepare on-chain data | Sign off, communicate decision, note lessons learned |

---

## Data Models

### Session State
```json
{
  "sessionId": "RR-2025-001",
  "projectId": "EC-2024-045",
  "projectName": "Regenerative Farm Portfolio",
  "createdAt": "2025-11-20T10:00:00Z",
  "currentStage": 5,
  "status": "Cross-Validated",
  "checklistTemplateId": "soil-carbon-v1.2.2",
  "accessMode": "mirror",
  "reviewer": "becca.harman@regen.network",
  "stageHistory": [
    {"stage": 1, "completedAt": "2025-11-20T10:15:00Z", "status": "success"},
    {"stage": 2, "completedAt": "2025-11-20T10:45:00Z", "status": "success"},
    {"stage": 3, "completedAt": "2025-11-20T11:30:00Z", "status": "success"},
    {"stage": 4, "completedAt": "2025-11-20T13:00:00Z", "status": "success"},
    {"stage": 5, "completedAt": "2025-11-20T14:30:00Z", "status": "success"}
  ]
}
```

### Requirement Mapping
```json
{
  "requirementId": "REQ-007",
  "requirementText": "Evidence of land tenure for all enrolled parcels",
  "source": "Program Guide 8.1, Soil Carbon Protocol 3.2",
  "mappedDocuments": [
    {
      "docId": "doc-land-tenure-farm-a",
      "mappingStatus": "confirmed",
      "confidence": 0.96,
      "mappedBy": "agent",
      "confirmedBy": "becca.harman@regen.network",
      "confirmedAt": "2025-11-20T11:15:00Z"
    }
  ],
  "mappingStatus": "confirmed"
}
```

### Evidence Snippet
```json
{
  "snippetId": "ev-REQ007-001",
  "requirementId": "REQ-007",
  "documentId": "doc-land-tenure-farm-a",
  "location": "page 3, section 2.1",
  "snippetText": "Farm A is owned by John Smith as evidenced by deed #45-2021 recorded with County Recorder on 2019-03-15. Total area: 145 hectares.",
  "extractedData": {
    "owner": "John Smith",
    "deedNumber": "45-2021",
    "recordingDate": "2019-03-15",
    "area": 145,
    "areaUnit": "hectares"
  },
  "confidence": 0.94,
  "extractedAt": "2025-11-20T12:30:00Z",
  "humanAnnotation": "Verified against county records - matches",
  "status": "approved"
}
```

### Validation Result
```json
{
  "validationId": "val-REQ007-consistency",
  "requirementId": "REQ-007",
  "validationType": "consistency",
  "description": "Cross-check land tenure claims vs. deed documents",
  "status": "pass",
  "details": {
    "claimedOwner": "John Smith",
    "deedOwner": "John Smith",
    "claimedArea": 145,
    "deedArea": 145,
    "match": true
  },
  "confidence": 0.98,
  "flag": null,
  "validatedAt": "2025-11-20T14:00:00Z"
}
```

---

## Success Metrics by Stage

| Stage | Key Metric | Target | Measurement Method |
|-------|-----------|--------|-------------------|
| **1. Initialize** | Session creation time | <2 min | User timing |
| **2. Discovery** | Classification accuracy | >85% | Human corrections / total files |
| **3. Mapping** | Mapping suggestion accuracy | >90% | Accepted suggestions / total |
| **4. Extraction** | Evidence found rate | >85% | Requirements with snippets / mapped requirements |
| **5. Validation** | False positive rate | <5% | Disputed flags / total flags |
| **6. Report** | Citation completeness | 100% | Snippets with citations / total snippets |
| **7. Human Review** | Time saved vs. manual | >50% | Hours per project before/after |
| **8. Completion** | On-chain data correctness | 100% | Failed registrations / total |

**Overall Workflow Metrics:**
- End-to-end review time: <4 hours (from upload to report)
- Escalation rate: <10% (requiring deep investigation)
- Reviewer satisfaction: >80% report workflow helpful
- Annual throughput: >100 projects

---

## Integration Points

### Upstream Systems (Input Sources)
- **Airtable:** Project submissions, metadata
- **Google Drive:** Document storage (Mirror mode)
- **SharePoint:** Partner document repositories (Reference mode)
- **KOI Knowledge Commons:** Checklist templates, protocol requirements, historical examples

### Downstream Systems (Outputs)
- **Regen Ledger:** Project instantiation, document IRI anchoring, attestations
- **Data Module:** On-chain metadata storage
- **Project Pages:** Public-facing project information
- **Tracking Systems:** Internal project status management

### Cross-Cutting Services
- **KOI Permissioning API:** Access control for resource queries
- **Commons Graph Store:** Semantic indexing of review data
- **Audit Logging:** All queries, modifications, decisions
- **Notification Systems:** Alerts to reviewers, proponents

---

## Deployment Considerations

### MVP (Phase 1) — Stages 1-8 Basic Implementation
- Focus on Registration reviews (simpler than Issuance)
- Mirror mode only (avoid SharePoint complexity)
- Manual checklist templates (no automated generation yet)
- Basic evidence extraction (text-based, no complex table parsing)
- Citation at document level (not yet page/section precision)

### Enhancement (Phase 2) — Accuracy & Refinement
- Add Reference mode (SharePoint read-through)
- ML-based table/form recognition
- Page-level citation precision
- Confidence scoring refinement
- Feedback loops for continuous learning

### Scale (Phase 3) — Issuance & Multi-Protocol
- Extend to Issuance reviews (more complex)
- Support multiple methodologies
- Automated checklist generation from protocol documents
- Advanced GIS data validation
- Integration with third-party verifier workflows

### Vision (Phase 4) — Self-Service & Commons Integration
- Proponent-facing interface (self-check before submission)
- Full KOI permissioning and on-chain provenance
- Verifier collaboration features
- Analytics dashboard for process improvement
- Open access for ecosystem partners

---

## References

**Related Documents:**
- [High-Level Specs for Registry AI Agents](2025-09-09-high-level-spec-for-registry-ai-agents.md)
- [Regen Knowledge Commons & Registry Agent Infrastructure](2025-10-30-regen-knowledge-commons-registry-review-agent-infrastructure.md)
- [Registry Review MVP Workflow](2025-11-11-registry-review-mvp-workflow.md)

**Transcripts:**
- [Regen Network AI Agents Meeting (Sept 17)](../transcripts/2025-09-17-regen-network-ai-agents.md)
- [Project Registration Review Process (Oct 21)](../transcripts/2025-10-21-project-registration-review-process.md)
- [Registry Agent Development Meeting (Nov 18)](../transcripts/2025-11-18-registry-agent-development-meeting.md)
- [Product Advisory (Nov 19)](../transcripts/2025-11-19-product-advisory.md)
- [Transcript Synthesis (Nov 11)](../transcripts/2025-11-11-transcript-synthesis.md)

---

**Document History:**
- 2025-11-20: Initial canonical eight-stage specification created
