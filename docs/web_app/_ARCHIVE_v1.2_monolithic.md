# Registry Review Web Application

## Planning Document v1.2

**Status:** Planning
**Created:** January 2026
**Updated:** January 2026 (incorporated architectural feedback)
**Target:** Q1 2026 MVP

---

## Executive Summary

The Registry Review Web Application transforms the existing MCP-based carbon credit verification workflow into a purpose-built, document-centric web interface. While the current system supports ChatGPT Custom GPT and Claude Code interfaces, these require users to context-switch between their documents and the AI interface. The web app solves this by embedding the workflow directly alongside the documents being reviewed.

**Core Value Proposition:** Enable registry reviewers (like Becca, a soil scientist) to complete project reviews 5-10x faster by providing a unified interface where:
- Documents are visible alongside the checklist
- Evidence is linked via drag-and-drop (not tedious popup menus)
- Progress through the 8-stage workflow is always visible
- Collaboration between reviewer and proponent is native
- Batch processing handles 111+ farms efficiently via templates

**Existing Assets (Already Built):**
- Complete MCP server with 8-stage workflow (`registry_review_mcp`)
- REST API wrapper for HTTP access (`chatgpt_rest_api.py`)
- 45+ API endpoints covering all workflow operations
- Pydantic models for all data structures
- LLM-powered evidence extraction with 80%+ accuracy
- File-based session persistence with audit trails

**Gap to Fill:**
- Purpose-built web frontend
- PDF viewer with persistent highlighting
- Real-time progress visualization
- Evidence scratchpad for "find first, sort later" workflow
- Project templates for batch processing
- Internal vs external collaboration features

---

## Table of Contents

1. [Vision](#vision)
2. [User Personas](#user-personas)
3. [MVP Scope Definition](#mvp-scope-definition)
4. [End-to-End User Journeys](#end-to-end-user-journeys)
5. [Current System Architecture](#current-system-architecture)
6. [Interaction Design Principles](#interaction-design-principles)
7. [Workflow Navigation (Soft Gating)](#workflow-navigation-soft-gating)
8. [AI & Visualization Features](#ai--visualization-features)
9. [Evidence Anchoring Strategy](#evidence-anchoring-strategy)
10. [Batch Processing Architecture](#batch-processing-architecture-111-farms)
11. [Collaboration Features](#collaboration-features)
12. [RBAC & Permissions Model](#rbac--permissions-model)
13. [Web Application Design](#web-application-design)
14. [Technical Architecture](#technical-architecture)
15. [Data Handling & Compliance](#data-handling--compliance)
16. [Implementation Roadmap](#implementation-roadmap)
17. [Success Metrics](#success-metrics)

---

## Vision

### The Problem Today

A registry reviewer processing a carbon credit project currently:

1. **Opens 5-15 PDF documents** in separate tabs
2. **Cross-references a methodology checklist** (23 requirements for Soil Carbon v1.2.2)
3. **Manually searches** each document for evidence addressing each requirement
4. **Copies snippets** into a spreadsheet with page citations
5. **Validates consistency** across documents (do dates align? do owner names match?)
6. **Writes a determination** for each requirement
7. **Generates a report** summarizing findings

This takes **6-8 hours per project**. With 111 farms waiting from the Czech/Slovak partnership alone, scaling is impossible without automation.

### The Vision

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  REGISTRY REVIEW WORKSPACE                              Project: Botany Farm 22      │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  Progress: ████████████░░░░░ Stage 5/8: Cross-Validation    [💾 Save] [📤 Export]    │
├────────────────────────────────────┬─────────────────────────────────────────────────┤
│                                    │                                                 │
│  📄 DOCUMENT VIEWER                │  ✓ CHECKLIST              📋 SCRATCHPAD (3)    │
│  ──────────────────────            │  ─────────────────────────────────────────────  │
│  [baseline_report.pdf ▼]           │                                                 │
│                                    │  Progress: 18/23 (78%)  ████████▓░░             │
│  ┌──────────────────────────────┐  │  Filter: [All ▼] [Flagged] [Missing]           │
│  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  │                                                 │
│  │ ░░░░░▓▓▓▓░░░░░░░░░░░░░░░░░░░ │← │  ▼ Land Tenure & Eligibility (3/3) ✓           │
│  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  │    ✓ REQ-001 Methodology version               │
│  │ ░░░░░░░░░░░░▓▓▓▓▓▓░░░░░░░░░░ │← │    ✓ REQ-002 Land tenure proof                 │
│  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  │    ✓ REQ-003 No ecosystem conversion           │
│  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  │                                                 │
│  │        [HEATMAP SCROLLBAR]   │  │  ▼ GHG Accounting (2/5) ⏳                      │
│  └──────────────────────────────┘  │    ✓ REQ-004 Baseline calculation              │
│                                    │    ┌─────────────────────────────────────────┐ │
│  ┌──────────────────────────────┐  │    │ ⏳ REQ-005 Monitoring protocol  [FOCUS] │ │
│  │                              │  │    │                                         │ │
│  │  ╔════════════════════════╗  │  │    │ Status: Partial (0.67)                  │ │
│  │  ║ "Soil samples were     ║  │  │    │ AI Confidence: ⓘ "Date found but..."   │ │
│  │  ║  collected on          ║  │  │    │                                         │ │
│  │  ║  2024-03-15..."        ║══╪══╪════│ [DRAG HERE TO LINK]                     │ │
│  │  ╚════════════════════════╝  │  │    │                                         │ │
│  │                              │  │    │ Evidence (1):                           │ │
│  │   DRAG selected text ───────┼──┼────▶│ • "Soil samples collected..."           │ │
│  │   to requirement card       │  │    │   📄 baseline_report.pdf, pg 12          │ │
│  │                              │  │    │                                         │ │
│  └──────────────────────────────┘  │    │ [✓ Accept] [✏️ Edit] [✗ Reject]         │ │
│                                    │    └─────────────────────────────────────────┘ │
│  [◀ Prev] Page 12/45 [▶] 🔍 100%   │                                                 │
│                                    │    ○ REQ-006 Uncertainty quantified            │
│  Documents (7):                    │    ○ REQ-007 Leakage assessment                │
│  ├─ 📄 baseline_report.pdf    ✓    │                                                 │
│  ├─ 📄 monitoring_2024.pdf    ⏳    │  ▶ Safeguards (0/4)                            │
│  └─ 📄 deed_records.pdf  ★ REL     │  ▶ Monitoring (0/6)                            │
│      ↑ Smart filter: relevant      │                                                 │
│        to current requirement      │                                                 │
└────────────────────────────────────┴─────────────────────────────────────────────────┘
│  Stages: [✓ Init] [✓ Discover] [✓ Map] [✓ Extract] [⏳ Validate] [○ Report] [○ Review]│
│          ⚠️ 3 requirements need evidence before Report                               │
│                                                              [▶ Run Cross-Validation] │
└──────────────────────────────────────────────────────────────────────────────────────┘

KEYBOARD: J/K navigate requirements | 1-5 set status | Cmd+L link selection | Cmd+S save
```

**Target:** 60-90 minutes per review (50-70% reduction)
**With Templates:** 30-45 minutes for farms in same cluster

---

## User Personas

### Primary: Registry Reviewer (Becca)

**Background:**
- Soil scientist with master's degree
- 3+ years experience in carbon credit verification
- Deep expertise in methodology requirements
- Not a software developer
- Power user who values keyboard shortcuts

**Current Pain Points:**
- Hours spent on mechanical cross-referencing
- Easy to miss a page citation
- Difficult to track what's been reviewed
- No good way to collaborate with proponents
- Context-switching between tools breaks flow

**Needs from Web App:**
- See documents and checklist side-by-side
- **Drag-and-drop evidence linking** (not popup menus)
- **Keyboard shortcuts** for rapid status updates
- Clear progress visualization
- Ability to request revisions from proponents
- Audit trail of all decisions
- **Evidence scratchpad** for "find first, sort later" workflow

**Success Criteria:**
- Complete a review in under 90 minutes
- Never miss a requirement
- Traceable evidence for every determination
- Flow state maintained (no waiting for saves)

### Secondary: Project Proponent

**Background:**
- Farm owner or project developer
- Submitted documentation for registration
- Waiting for review feedback
- May need to provide additional documents

**Needs from Web App:**
- View revision requests clearly
- Upload additional documents
- See status of their review
- Respond to reviewer questions
- **Clear distinction** between what's public and what's internal

### Tertiary: Registry Administrator

**Background:**
- Manages multiple reviewers
- Oversees quality and consistency
- Reports on throughput and outcomes

**Needs from Web App:**
- Dashboard of all active reviews
- **Batch actions** (assign, export, status update)
- Monitor review quality
- Export reports for compliance
- **Template management** for project clusters

---

## MVP Scope Definition

### Explicit Scope Boundaries

**MVP (Phases 1-7):**
- Single-user review workflow (one reviewer per project at a time)
- PDF viewing with react-pdf-highlighter
- Drag-and-drop evidence linking
- Evidence scratchpad
- Keyboard shortcuts
- Soft-gated stage navigation
- Basic cross-validation fact sheets
- Markdown/JSON report export
- Session-based authentication
- File-based storage (existing backend)

**Future (Post-MVP):**
- Multi-reviewer concurrent editing with conflict resolution
- Real-time collaboration (WebSockets)
- PDF annotation layers (separate from evidence highlights)
- Advanced template versioning
- Offline support with IndexedDB sync
- PDF export with embedded highlights
- Integration with external registries
- Advanced RBAC (role-based access control beyond MVP)
- Audit compliance reporting
- Mobile-optimized interface

### Feature Priority Matrix

| Feature | MVP | v1.1 | Future | Rationale |
|---------|-----|------|--------|-----------|
| PDF viewer with highlights | ✓ | | | Core workflow |
| Drag-drop evidence | ✓ | | | UX critical path |
| Keyboard shortcuts | ✓ | | | Power user productivity |
| Evidence scratchpad | ✓ | | | Matches cognitive model |
| Soft-gated navigation | ✓ | | | Non-linear workflow |
| Basic RBAC | ✓ | | | Security minimum |
| Fact sheet validation | ✓ | | | Scannable results |
| Heatmap scrollbar | | ✓ | | Enhancement |
| AI reasoning tooltips | | ✓ | | Trust building |
| Project templates | | ✓ | | 111 farms use case |
| Internal/external comments | | ✓ | | Collaboration |
| Revision snapshotting | | ✓ | | Audit trail |
| Multi-reviewer | | | ✓ | Complexity |
| Offline support | | | ✓ | Edge case |

---

## End-to-End User Journeys

### Journey 1: New Project Review (Happy Path)

**Actor:** Becca (Reviewer)
**Goal:** Complete review of a new carbon credit project

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  JOURNEY: New Project Review                                                │
│  Estimated Duration: 60-90 minutes                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. LOGIN & SELECT PROJECT                                    [5 min]       │
│     ─────────────────────────────────────────────────────────────────────  │
│     • Reviewer logs in with credentials                                     │
│     • Views dashboard with assigned projects                                │
│     • Clicks "Botany Farm 22" to open workspace                             │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Login completes in <2 sec                                            │
│     ✓ Dashboard shows project list with status indicators                   │
│     ✓ Clicking project loads workspace with documents                       │
│                                                                             │
│  2. DOCUMENT DISCOVERY & SCAN                                 [10 min]      │
│     ─────────────────────────────────────────────────────────────────────  │
│     • System auto-discovers 7 uploaded PDFs                                 │
│     • Reviewer scans each document (heatmap shows coverage)                 │
│     • Clips interesting passages to scratchpad (Cmd+C)                      │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ PDFs render correctly with searchable text                           │
│     ✓ Page navigation is responsive (<100ms)                               │
│     ✓ Scratchpad clips include page citation automatically                 │
│     ✓ Heatmap shows which pages have existing evidence                     │
│                                                                             │
│  3. REQUIREMENT-BY-REQUIREMENT REVIEW                         [40 min]      │
│     ─────────────────────────────────────────────────────────────────────  │
│     • Reviewer focuses on REQ-001 (press F for Focus Mode)                  │
│     • Smart filter shows relevant documents (deed_records.pdf ★★★)         │
│     • Drags text snippet from PDF to requirement card                       │
│     • Evidence links instantly (optimistic UI)                              │
│     • Presses "1" to mark as Covered, "J" to move to next                   │
│     • Repeats for all 23 requirements                                       │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Focus Mode expands requirement to full width                         │
│     ✓ Drag-drop from PDF to requirement takes <500ms                       │
│     ✓ Keyboard shortcuts work (1-5, J/K, Cmd+L)                            │
│     ✓ Evidence persists on page refresh                                    │
│     ✓ Status updates are reflected immediately                             │
│                                                                             │
│  4. CROSS-VALIDATION CHECK                                    [10 min]      │
│     ─────────────────────────────────────────────────────────────────────  │
│     • Navigates to Cross-Validation stage (soft-gated warning shows)        │
│     • Views Fact Sheet: Date Alignment table                                │
│     • Spots 97-day gap (within 120-day tolerance)                           │
│     • Views Land Tenure table - all fields match                            │
│     • Clicks "Continue" to proceed                                          │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Soft gate shows warnings but allows navigation                       │
│     ✓ Fact Sheet tables are scannable in <30 sec                           │
│     ✓ Warnings are clickable (jump to relevant requirement)                │
│                                                                             │
│  5. REPORT GENERATION & EXPORT                                [5 min]       │
│     ─────────────────────────────────────────────────────────────────────  │
│     • Clicks "Generate Report"                                              │
│     • Reviews auto-generated markdown                                       │
│     • Gaps are clearly marked (3 requirements need human review)            │
│     • Exports as Markdown for email                                         │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Report generates in <10 sec                                          │
│     ✓ Gaps are highlighted with visual distinction                         │
│     ✓ Export downloads immediately                                         │
│                                                                             │
│  6. HUMAN REVIEW & FINALIZATION                               [20 min]      │
│     ─────────────────────────────────────────────────────────────────────  │
│     • Reviews 3 flagged requirements                                        │
│     • Adds internal note to REQ-005 (date concern)                          │
│     • Sets override status for REQ-006 (Covered - manual review)            │
│     • Sends revision request to proponent for REQ-007                       │
│     • Saves progress (auto-saved already)                                   │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Internal notes are visually distinct (yellow background)             │
│     ✓ Override status shows "Manual" badge                                 │
│     ✓ Revision request creates audit entry                                 │
│     ✓ Auto-save indicator shows last save time                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Journey 2: Revision Response (Proponent Flow)

**Actor:** Thomas (Project Proponent)
**Goal:** Respond to revision request

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  JOURNEY: Revision Response                                                 │
│  Estimated Duration: 15 minutes                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. VIEW REVISION REQUEST                                     [2 min]       │
│     • Proponent receives email notification                                 │
│     • Logs in and sees "1 pending revision" on dashboard                    │
│     • Opens revision detail: "Clarify soil sampling date"                   │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Email contains direct link to revision                               │
│     ✓ Only public comments visible (not internal notes)                    │
│     ✓ Revision request shows specific requirement context                  │
│                                                                             │
│  2. UPLOAD SUPPORTING DOCUMENT                                [5 min]       │
│     • Clicks "Upload Response"                                              │
│     • Drags monitoring_schedule_2024.pdf into upload zone                   │
│     • Adds note: "Attached detailed sampling schedule"                      │
│     • Submits response                                                      │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Drag-drop upload works                                               │
│     ✓ PDF is validated (< 50MB, is valid PDF)                              │
│     ✓ Response creates notification for reviewer                           │
│                                                                             │
│  3. TRACK REVIEW PROGRESS                                     [1 min]       │
│     • Views project status: "Stage 6/8 - Awaiting Review"                   │
│     • Sees revision status change to "Under Review"                         │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Status updates reflect actual backend state                          │
│     ✓ Proponent cannot see internal reviewer notes                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Journey 3: Batch Farm Review (Template Flow)

**Actor:** Becca (Reviewer)
**Goal:** Process 10 Czech farms using template

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  JOURNEY: Batch Farm Review                                                 │
│  Estimated Duration: 6 hours (10 farms × ~35 min each + setup)              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CREATE/SELECT TEMPLATE                                    [30 min]      │
│     • Creates "Czech Farm Cluster 2024" template                            │
│     • Uploads shared docs: methodology, legal structure, baseline           │
│     • Marks 8 requirements as "inherited" (pre-verified)                    │
│     • Verifies template thoroughly (2 hours one-time)                       │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Template creation wizard is clear                                    │
│     ✓ Shared documents are stored once, referenced by children             │
│     ✓ Inherited requirements show evidence from template                   │
│                                                                             │
│  2. BATCH CREATE PROJECTS                                     [5 min]       │
│     • Selects template on dashboard                                         │
│     • Clicks "Create from Template"                                         │
│     • Uploads CSV with 10 farm names                                        │
│     • 10 projects created with inherited evidence                           │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Batch creation handles 10+ projects                                  │
│     ✓ Each project inherits template evidence                              │
│     ✓ Farm-specific requirements are marked "pending"                      │
│                                                                             │
│  3. REVIEW FARM-SPECIFIC REQUIREMENTS                         [35 min/farm] │
│     • Opens Farm CZ-001                                                     │
│     • 8 requirements already Covered (inherited)                            │
│     • Only 15 farm-specific requirements to review                          │
│     • Uploads farm-specific: soil samples, boundary, tenure                 │
│     • Completes review, moves to next farm                                  │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Inherited requirements show "From Template" badge                    │
│     ✓ Inherited evidence is read-only (no accidental edits)                │
│     ✓ Per-farm time is 30-45 min (not 90 min)                              │
│                                                                             │
│  4. BULK EXPORT REPORTS                                       [10 min]      │
│     • Selects all 10 completed farms on dashboard                           │
│     • Clicks "Bulk Export Reports"                                          │
│     • Downloads ZIP with 10 markdown reports                                │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Bulk selection works with checkboxes                                 │
│     ✓ Export generates all reports in <60 sec                              │
│     ✓ ZIP file is properly structured                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Journey 4: Administrator Dashboard (Oversight Flow)

**Actor:** Registry Administrator
**Goal:** Monitor team progress and quality

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  JOURNEY: Administrator Oversight                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. VIEW TEAM DASHBOARD                                                     │
│     • Sees all active reviews across reviewers                              │
│     • Filters by status: "Awaiting Revision" (5 projects)                   │
│     • Sorts by "Oldest First" to identify bottlenecks                       │
│                                                                             │
│  2. REASSIGN STALLED PROJECT                                                │
│     • Selects project stuck for 7 days                                      │
│     • Clicks "Reassign" → selects different reviewer                        │
│     • Adds note explaining reassignment                                     │
│                                                                             │
│  3. EXPORT METRICS REPORT                                                   │
│     • Clicks "Export Metrics"                                               │
│     • Selects date range and format (CSV)                                   │
│     • Downloads: reviews completed, avg time, approval rate                 │
│                                                                             │
│     ACCEPTANCE CRITERIA:                                                    │
│     ✓ Dashboard aggregates across all reviewers                            │
│     ✓ Reassignment preserves all existing evidence/notes                   │
│     ✓ Metrics export includes all key performance indicators               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Current System Architecture

### MCP Server (Existing)

```
registry_review_mcp/
├── server.py                    # FastMCP entry point
├── prompts/                     # 8-stage workflow orchestration
│   ├── A_initialize.py          # Create session, load methodology
│   ├── B_document_discovery.py  # Scan and classify documents
│   ├── C_requirement_mapping.py # Map requirements to documents
│   ├── D_evidence_extraction.py # Extract snippets with citations
│   ├── E_cross_validation.py    # Validate consistency
│   ├── F_report_generation.py   # Generate reports
│   ├── G_human_review.py        # Expert validation
│   └── H_completion.py          # Finalize and lock
├── tools/                       # Atomic operations
│   ├── session_tools.py         # CRUD for sessions
│   ├── document_tools.py        # PDF extraction, classification
│   ├── mapping_tools.py         # Requirement-document mapping
│   ├── evidence_tools.py        # Evidence extraction
│   ├── validation_tools.py      # Cross-document validation
│   ├── human_review_tools.py    # Overrides, annotations, determination
│   ├── report_tools.py          # Report generation
│   └── upload_tools.py          # File upload handling
├── extractors/                  # Content extraction
│   ├── marker_extractor.py      # PDF → Markdown via marker
│   ├── llm_extractors.py        # LLM-powered field extraction
│   └── fast_extractor.py        # Quick regex-based extraction
├── models/                      # Pydantic schemas
│   ├── schemas.py               # Session, Document, Requirement
│   ├── evidence.py              # EvidenceSnippet, RequirementFinding
│   ├── validation.py            # DateAlignment, LandTenure, ProjectID
│   └── report.py                # ReviewReport, ReportSummary
└── utils/
    ├── state.py                 # File-based session persistence
    └── cache.py                 # TTL caching for expensive operations
```

### REST API (Existing)

**File:** `chatgpt_rest_api.py` (57K lines)
**Framework:** FastAPI
**Deployment:** `https://regen.gaiaai.xyz/registry`

**Key Endpoints:**

| Category | Endpoint | Method | Purpose |
|----------|----------|--------|---------|
| **Sessions** | `/sessions` | POST | Create new review session |
| | `/sessions` | GET | List all sessions |
| | `/sessions/{id}` | GET | Get session details |
| | `/sessions/{id}` | DELETE | Delete session |
| **Documents** | `/sessions/{id}/discover` | POST | Discover and classify documents |
| | `/sessions/{id}/documents` | GET | List discovered documents |
| | `/sessions/{id}/upload` | POST | Upload files to session |
| **Mapping** | `/sessions/{id}/map` | POST | Map all requirements to documents |
| | `/sessions/{id}/mapping` | GET | Get mapping status |
| **Evidence** | `/sessions/{id}/evidence` | POST | Extract evidence for all requirements |
| | `/sessions/{id}/evidence` | GET | Get extracted evidence |
| **Validation** | `/sessions/{id}/validate` | POST | Run cross-validation |
| | `/sessions/{id}/validation` | GET | Get validation results |
| **Human Review** | `/sessions/{id}/overrides` | POST | Set requirement override |
| | `/sessions/{id}/overrides` | GET | Get all overrides |
| | `/sessions/{id}/annotations` | POST | Add annotation |
| | `/sessions/{id}/determination` | POST | Set final determination |
| | `/sessions/{id}/revisions` | POST | Request revision from proponent |
| **Reports** | `/sessions/{id}/report` | POST | Generate review report |
| | `/sessions/{id}/report` | GET | Get generated report |
| **Completion** | `/sessions/{id}/complete` | POST | Finalize and lock session |

### Data Models

**Session:**
```typescript
interface Session {
  session_id: string;
  created_at: string;
  updated_at: string;
  status: string;
  parent_template_id: string | null;  // NEW: for template inheritance
  project_metadata: {
    project_name: string;
    project_id: string | null;
    methodology: string;
    proponent: string | null;
    crediting_period: string | null;
    cluster_id: string | null;  // NEW: for batch grouping
  };
  workflow_progress: {
    initialize: "pending" | "in_progress" | "completed";
    document_discovery: "pending" | "in_progress" | "completed";
    requirement_mapping: "pending" | "in_progress" | "completed";
    evidence_extraction: "pending" | "in_progress" | "completed";
    cross_validation: "pending" | "in_progress" | "completed";
    report_generation: "pending" | "in_progress" | "completed";
    human_review: "pending" | "in_progress" | "completed";
    completion: "pending" | "in_progress" | "completed";
  };
  statistics: {
    documents_found: number;
    requirements_total: number;
    requirements_covered: number;
    requirements_partial: number;
    requirements_missing: number;
    validations_passed: number;
    validations_failed: number;
  };
}
```

**EvidenceSnippet:**
```typescript
interface EvidenceSnippet {
  snippet_id: string;
  text: string;
  document_id: string;
  document_name: string;
  page: number | null;
  section: string | null;
  confidence: number;
  confidence_reason: string | null;  // NEW: AI reasoning explanation
  extraction_method: "keyword" | "llm" | "manual" | "drag_drop";  // NEW: drag_drop
  highlight_coordinates: HighlightCoords | null;  // NEW: for persistent highlights
}

interface HighlightCoords {
  page: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}
```

---

## Interaction Design Principles

### 1. Drag-and-Drop Evidence Linking

**Problem:** The original design (Select → Popup → Search → Click) is too slow for hundreds of linking operations.

**Solution:** Direct drag-and-drop from PDF to requirement cards.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DRAG-AND-DROP LINKING FLOW                                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  1. User selects text in PDF (no popup appears)                             │
│                                                                             │
│  2. User drags selection toward checklist panel                             │
│     ┌─────────────────────┐                                                 │
│     │ "127.4 hectares of  │ ─────drag─────▶  Requirement cards light up    │
│     │  managed grassland" │                   showing valid drop targets    │
│     └─────────────────────┘                                                 │
│                                                                             │
│  3. User drops on requirement card                                          │
│     ┌────────────────────────────────┐                                      │
│     │ REQ-002 Land tenure    [DROP]  │ ← Card highlights as drop target    │
│     │ ════════════════════════════   │                                      │
│     │ ✓ Evidence linked!             │                                      │
│     │   📄 baseline.pdf, pg 8        │                                      │
│     └────────────────────────────────┘                                      │
│                                                                             │
│  4. Optimistic UI: Link appears instantly, syncs in background              │
│     (No 500ms wait for "saved" confirmation)                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Alternative:** If text is selected and user presses `Cmd+L`, the focused requirement receives the link.

### 2. Evidence Scratchpad

**Problem:** Reviewers often find important information before knowing which requirement it addresses.

**Solution:** A "Scratchpad" for clipping now, categorizing later.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📋 EVIDENCE SCRATCHPAD                                          [Collapse] │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Unassigned clips (3):                                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ "Sampling conducted by AgriLab certified technician on 2024-03-15"  │   │
│  │ 📄 monitoring_report.pdf, Page 7                                    │   │
│  │ [Assign to REQ ▼] [Delete]                              Clipped 2m ago │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ "Previous land use: continuous pasture since 1987"                  │   │
│  │ 📄 baseline_report.pdf, Page 3                                      │   │
│  │ [Assign to REQ ▼] [Delete]                              Clipped 5m ago │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ⚠️ "Ownership transferred to current entity in 2019"                │   │
│  │ 📄 deed_records.pdf, Page 2                                         │   │
│  │ [Assign to REQ ▼] [Delete]                              Clipped 8m ago │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Keyboard: Cmd+C on selected PDF text → Add to scratchpad                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Workflow:**
1. Reviewer scans document, clips interesting passages (Cmd+C or drag to scratchpad)
2. Later, reviews scratchpad and assigns clips to requirements
3. Scratchpad items can be dragged to requirement cards

### 3. Keyboard Shortcuts

**Problem:** Power users (Becca) hate reaching for the mouse constantly.

**Solution:** Comprehensive keyboard navigation defined upfront.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  KEYBOARD SHORTCUTS                                                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  NAVIGATION                         ACTIONS                                 │
│  ──────────                         ───────                                 │
│  J / ↓      Next requirement        1   Set status: Covered                 │
│  K / ↑      Previous requirement    2   Set status: Partial                 │
│  H / ←      Previous document       3   Set status: Missing                 │
│  L / →      Next document           4   Set status: Flagged                 │
│  G G        Go to first req         5   Set status: Approved (override)     │
│  Shift+G    Go to last req                                                  │
│  /          Search requirements     EVIDENCE                                │
│  Tab        Toggle panels           ──────────                              │
│                                     Cmd+L    Link selection to focused req  │
│  DOCUMENT VIEWER                    Cmd+C    Clip selection to scratchpad   │
│  ───────────────                    Cmd+E    Expand evidence (Focus Mode)   │
│  Page Up    Previous page           Cmd+D    View in document               │
│  Page Down  Next page               Delete   Remove selected evidence       │
│  +/-        Zoom in/out                                                     │
│  F          Toggle Focus Mode       WORKFLOW                                │
│  Esc        Exit Focus Mode         ────────                                │
│                                     Cmd+S    Save (also auto-saves)         │
│                                     Cmd+R    Run current stage action       │
│                                     Cmd+N    Add note to focused req        │
│                                                                             │
│  ? Show this help                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4. Focus Mode

**Problem:** 23 requirements with multiple snippets creates visual noise.

**Solution:** Focus Mode expands one requirement to full panel width.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FOCUS MODE: REQ-005 Monitoring Protocol                        [Esc: Exit] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Requirement Text:                                                          │
│  "Projects shall implement a monitoring protocol that includes soil         │
│   sampling at least once per crediting period, conducted according to       │
│   the methodology's sampling requirements."                                 │
│                                                                             │
│  Source: Program Guide, Section 4.3.2                                       │
│  Validation Type: Cross-document alignment                                  │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Status: ⏳ Partial                     Confidence: 0.67                    │
│  Override: [None ▼]                                                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  EVIDENCE (2 snippets)                                                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ 1. "Soil samples were collected on 2024-03-15 at the Botany Farm      │ │
│  │     site, following the standard operating procedures outlined in     │ │
│  │     Appendix C of the methodology document."                          │ │
│  │                                                                       │ │
│  │  📄 baseline_report.pdf, Page 12, Section 3.2                         │ │
│  │  Confidence: 0.92 ⓘ                                                   │ │
│  │  Extracted: Auto (LLM) · 2 hours ago                                  │ │
│  │                                                                       │ │
│  │  [View in Document] [Edit] [Remove]                                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ 2. "Monitoring will occur annually during the crediting period."      │ │
│  │                                                                       │ │
│  │  📄 project_plan.pdf, Page 8                                          │ │
│  │  Confidence: 0.45 ⓘ "Generic statement, lacks specific dates"         │ │
│  │  Extracted: Auto (LLM) · 2 hours ago                                  │ │
│  │                                                                       │ │
│  │  [View in Document] [Edit] [Remove]                                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ANNOTATIONS                                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ [Internal] Need to verify sampling dates align with imagery dates     │ │
│  │            - Becca, 10 min ago                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  [+ Add Evidence] [+ Add Note] [Request Revision]                           │
│                                                                             │
│  ← Previous: REQ-004                              Next: REQ-006 →           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5. Optimistic UI

**Problem:** Waiting 500ms for server confirmation on every action breaks flow state.

**Solution:** Update UI immediately, sync in background.

```typescript
// Evidence linking with optimistic update
async function linkEvidence(snippetId: string, requirementId: string) {
  // 1. Update UI immediately
  updateLocalState({
    type: 'LINK_EVIDENCE',
    snippetId,
    requirementId,
    status: 'pending'  // Shows subtle indicator
  });

  // 2. Sync to server in background
  try {
    await api.linkEvidence(sessionId, snippetId, requirementId);
    updateLocalState({
      type: 'LINK_EVIDENCE_SUCCESS',
      snippetId,
      requirementId
    });
  } catch (error) {
    // 3. Rollback on failure (rare)
    updateLocalState({
      type: 'LINK_EVIDENCE_FAILED',
      snippetId,
      requirementId,
      error: error.message
    });
    showToast('Failed to save - retrying...');
  }
}
```

---

## Workflow Navigation (Soft Gating)

### Problem

The original design implies a linear 8-stage flow. Real-world reviews require jumping between stages:
- Discover a missing document in Stage 5 → need to go back to Stage 2
- Want to preview report in Stage 4 → should be possible (with warnings)

### Solution: Soft Gating

Allow free navigation between stages, but **show unresolved dependencies** instead of blocking.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE NAVIGATION WITH SOFT GATING                                          │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Current View: Cross-Validation (Stage 5)                                   │
│                                                                             │
│  [✓ Init] [✓ Discover] [✓ Map] [✓ Extract] [⏳ Validate] [○ Report] [○ Done] │
│                                                           ↑                 │
│                                                           │                 │
│                                          User clicks "Report"               │
│                                                           │                 │
│                                                           ▼                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ⚠️ Report Stage - Dependencies Not Met                              │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  You can view the Report stage, but the following issues will       │   │
│  │  appear as gaps in your report:                                     │   │
│  │                                                                     │   │
│  │  • 3 requirements have no evidence mapped                           │   │
│  │    └─ REQ-006, REQ-007, REQ-008                                     │   │
│  │  • Cross-validation has 1 unresolved warning                        │   │
│  │    └─ Date mismatch: baseline vs monitoring                         │   │
│  │                                                                     │   │
│  │  [Continue Anyway] [Go Back to Fix]                                 │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  If user continues → Report shows clearly marked gaps:                      │
│                                                                             │
│  ## Requirement REQ-006: Uncertainty Quantification                         │
│  Status: ⚠️ NOT REVIEWED - No evidence mapped                               │
│  [This requirement must be addressed before finalization]                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation

```typescript
interface StageGate {
  stage: string;
  dependencies: Dependency[];
  canProceed: boolean;
  warnings: string[];
}

function checkStageGate(session: Session, targetStage: string): StageGate {
  const deps = getStageDependencies(targetStage);
  const unmet = deps.filter(d => !isDependencyMet(session, d));

  return {
    stage: targetStage,
    dependencies: deps,
    canProceed: true,  // Always allow, but...
    warnings: unmet.map(d => d.warningMessage)  // ...show what's missing
  };
}

// Dependencies by stage
const STAGE_DEPENDENCIES = {
  'report_generation': [
    { type: 'evidence_coverage', min: 0.5, message: 'At least 50% of requirements need evidence' },
    { type: 'validation_complete', message: 'Cross-validation should be run' }
  ],
  'human_review': [
    { type: 'report_generated', message: 'Report should be generated first' }
  ],
  'completion': [
    { type: 'determination_set', required: true, message: 'Final determination is required' },
    { type: 'pending_revisions', max: 0, message: 'All revisions must be resolved' }
  ]
};
```

---

## AI & Visualization Features

### 1. Document Heatmaps

**Problem:** Hard to know if the AI missed a section entirely.

**Solution:** Heatmap on PDF scrollbar showing where evidence has been extracted.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DOCUMENT HEATMAP                                                           │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  PDF Scrollbar with Coverage Overlay:                                       │
│                                                                             │
│   Page │ Scrollbar │ Meaning                                                │
│  ──────┼───────────┼────────────────────────────────────────────────────── │
│    1   │ ░░░░░░░░░ │ No evidence extracted from this section               │
│    2   │ ░░░░░░░░░ │                                                        │
│    3   │ ░░▓▓▓░░░░ │ Some evidence extracted (moderate coverage)           │
│    4   │ ░░░░░░░░░ │                                                        │
│    5   │ ▓▓▓▓▓▓▓▓▓ │ Heavy extraction (high coverage)                      │
│    6   │ ▓▓▓▓░░░░░ │                                                        │
│    7   │ ░░░░░░░░░ │ ← COLD SECTION: May need manual review                │
│    8   │ ░░░░░░░░░ │ ←                                                      │
│    9   │ ░░▓▓░░░░░ │                                                        │
│   10   │ ░░░░░░░░░ │                                                        │
│                                                                             │
│  Legend:                                                                    │
│  ░ = No evidence    ▒ = Low coverage    ▓ = Good coverage                   │
│                                                                             │
│  Clicking a "cold" section navigates to that page for manual review.        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Fact Sheet View (Cross-Validation)

**Problem:** Stage 5 checks consistency (dates, names, areas), but text snippets are slow to compare.

**Solution:** Tabular comparison view for cross-validation results.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CROSS-VALIDATION: FACT SHEET VIEW                                          │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  DATE ALIGNMENT (120-day rule)                                              │
│  ┌─────────────────┬──────────────┬──────────────┬──────────────┬────────┐ │
│  │ Field           │ Project Plan │ Baseline Rpt │ Monitoring   │ Status │ │
│  ├─────────────────┼──────────────┼──────────────┼──────────────┼────────┤ │
│  │ Project Start   │ 2024-01-01   │ 2024-01-01   │ 2024-01-01   │ ✓      │ │
│  │ Baseline Date   │ 2024-02-15   │ 2024-02-15   │ —            │ ✓      │ │
│  │ Sampling Date   │ —            │ 2024-03-15   │ 2024-06-20   │ ⚠️ 97d │ │
│  │ Imagery Date    │ —            │ 2024-03-01   │ —            │ ✓      │ │
│  └─────────────────┴──────────────┴──────────────┴──────────────┴────────┘ │
│                                                                             │
│  LAND TENURE CONSISTENCY                                                    │
│  ┌─────────────────┬──────────────┬──────────────┬──────────────┬────────┐ │
│  │ Field           │ Project Plan │ Deed Records │ Baseline Rpt │ Status │ │
│  ├─────────────────┼──────────────┼──────────────┼──────────────┼────────┤ │
│  │ Owner Name      │ T. Mitchell  │ Thomas M.    │ T. Mitchell  │ ✓ 0.92 │ │
│  │ Area (ha)       │ 127.4        │ 127.38       │ 127.4        │ ✓      │ │
│  │ Tenure Type     │ Freehold     │ Freehold     │ Freehold     │ ✓      │ │
│  └─────────────────┴──────────────┴──────────────┴──────────────┴────────┘ │
│                                                                             │
│  PROJECT IDENTIFIER                                                         │
│  ┌─────────────────┬──────────────┬──────────────┬──────────────┬────────┐ │
│  │ Pattern         │ Occurrences  │ Documents    │ Consistent   │ Status │ │
│  ├─────────────────┼──────────────┼──────────────┼──────────────┼────────┤ │
│  │ C06-4997        │ 12           │ 5/7          │ Yes          │ ✓      │ │
│  │ 4997            │ 8            │ 4/7          │ Yes          │ ✓      │ │
│  └─────────────────┴──────────────┴──────────────┴──────────────┴────────┘ │
│                                                                             │
│  Summary: 1 warning (Sampling Date mismatch: 97 days, max allowed: 120)     │
│  [View Details] [Export to CSV]                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. AI Reasoning Tooltips

**Problem:** When AI extracts evidence with low confidence, reviewers don't know why.

**Solution:** Hover/click reveals reasoning behind confidence score.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AI REASONING TOOLTIP                                                       │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Evidence snippet displayed in checklist:                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ "Monitoring will occur annually during the crediting period."         │ │
│  │  📄 project_plan.pdf, Page 8                                          │ │
│  │  Confidence: 0.45 ⓘ  ← User hovers/clicks the ⓘ                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                         │                                                   │
│                         ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  AI Confidence Analysis                                               │ │
│  │  ─────────────────────────────────────────────────────────────────── │ │
│  │                                                                       │ │
│  │  Score: 0.45 (Low)                                                    │ │
│  │                                                                       │ │
│  │  Reasons:                                                             │ │
│  │  • Generic statement - lacks specific sampling dates                  │ │
│  │  • No mention of methodology sampling requirements                    │ │
│  │  • "Annually" is vague - doesn't specify exact timing                 │ │
│  │                                                                       │ │
│  │  Suggestion:                                                          │ │
│  │  Look for specific sampling schedule in monitoring_report.pdf         │ │
│  │  or methodology appendix.                                             │ │
│  │                                                                       │ │
│  │  Keywords searched: "sampling", "monitoring", "protocol",             │ │
│  │                     "soil samples", "crediting period"                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4. Smart Document Filtering

**Problem:** With 15+ documents, finding the right one is slow.

**Solution:** When focusing on a requirement, relevant documents bubble to top.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SMART DOCUMENT FILTERING                                                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  User clicks REQ-002 (Land Tenure)                                          │
│                                                                             │
│  Document list automatically reorders:                                      │
│                                                                             │
│  Documents (7):                        │  Relevance Indicator               │
│  ─────────────────                     │                                    │
│  ├─ 📄 deed_records.pdf          ★★★  │  ← High relevance (land tenure)   │
│  ├─ 📄 baseline_report.pdf       ★★   │  ← Medium (has area mentions)     │
│  ├─ 📄 project_plan.pdf          ★    │  ← Low (general project info)     │
│  ├─ 📄 monitoring_2024.pdf       ·    │  ← Not relevant                   │
│  ├─ 📄 ghg_emissions.pdf         ·    │                                    │
│  ├─ 📊 soil_samples.xlsx         ·    │                                    │
│  └─ 🗺️ boundary.shp              ★★   │  ← Medium (boundary = area)       │
│                                                                             │
│  Relevance is calculated based on:                                          │
│  • Document classification matches requirement category                     │
│  • Existing evidence links from this document to this requirement          │
│  • Keyword overlap between requirement and document content                │
│                                                                             │
│  [Show All] [Show Relevant Only]                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Evidence Anchoring Strategy

### The Problem

Evidence snippets must be visually highlighted in PDFs to support reviewer verification. However, PDF text selection coordinates are viewport-dependent, zoom-dependent, and can shift across screen sizes. We need a robust anchoring strategy that survives document reloads.

### Anchoring Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EVIDENCE ANCHORING: THREE-LAYER APPROACH                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LAYER 1: BOUNDING BOX COORDINATES (Primary)                                │
│  ──────────────────────────────────────────                                 │
│  Stored per highlight:                                                      │
│  {                                                                          │
│    "page": 12,                                                              │
│    "boundingRect": {                                                        │
│      "x1": 72.0,    // Left edge (PDF points from origin)                   │
│      "y1": 340.5,   // Top edge                                             │
│      "x2": 520.0,   // Right edge                                           │
│      "y2": 380.2,   // Bottom edge                                          │
│      "width": 448.0,                                                        │
│      "height": 39.7                                                         │
│    },                                                                       │
│    "rects": [       // Multiple rects for multi-line selections             │
│      { "x1": 72.0, "y1": 340.5, "x2": 520.0, "y2": 355.1 },                │
│      { "x1": 72.0, "y1": 355.1, "x2": 380.0, "y2": 380.2 }                 │
│    ]                                                                        │
│  }                                                                          │
│                                                                             │
│  Note: Coordinates use PDF "quads" system (4 points per rect),              │
│  normalized to page dimensions. react-pdf-highlighter handles this.         │
│                                                                             │
│  LAYER 2: CONTENT HASH (Fallback)                                           │
│  ────────────────────────────────                                           │
│  When coordinates fail (PDF re-export changes layout):                      │
│  {                                                                          │
│    "text_hash": "sha256:a1b2c3...",  // Hash of exact snippet text         │
│    "context_before": "collected on",  // 20 chars before snippet           │
│    "context_after": "at the site"     // 20 chars after snippet            │
│  }                                                                          │
│                                                                             │
│  Recovery algorithm:                                                        │
│  1. Try bounding box coordinates                                            │
│  2. If text at coordinates doesn't match hash, search page for text         │
│  3. Use context_before/after to disambiguate multiple matches               │
│  4. If found, update stored coordinates (self-healing)                      │
│  5. If not found, show "Evidence may have moved" warning                    │
│                                                                             │
│  LAYER 3: PAGE + TEXT REFERENCE (Manual Fallback)                           │
│  ─────────────────────────────────────────────────                          │
│  Always stored:                                                             │
│  {                                                                          │
│    "page": 12,                                                              │
│    "text": "Soil samples were collected on 2024-03-15...",                  │
│    "section": "3.2 Baseline Assessment"  // Optional                        │
│  }                                                                          │
│                                                                             │
│  Even if visual highlighting fails, reviewer can navigate to page           │
│  and manually locate the text.                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Model Update

```typescript
interface HighlightCoords {
  // Primary: Bounding box in PDF coordinate space
  page: number;
  boundingRect: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    width: number;
    height: number;
    pageNumber: number;  // Redundant but useful for multi-page highlights
  };
  rects: Array<{        // Individual character rects for multi-line
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  }>;

  // Fallback: Content hash for recovery
  textHash: string;           // SHA-256 of exact text
  contextBefore?: string;     // ~20 chars before
  contextAfter?: string;      // ~20 chars after

  // Metadata
  createdAt: string;
  lastVerified?: string;      // Last time coords were verified
  coordsStale?: boolean;      // True if text didn't match on last load
}

interface EvidenceSnippet {
  snippet_id: string;
  text: string;
  document_id: string;
  document_name: string;
  page: number;
  section: string | null;
  confidence: number;
  confidence_reason: string | null;
  extraction_method: "keyword" | "llm" | "manual" | "drag_drop";
  highlight_coordinates: HighlightCoords | null;  // Updated structure
}
```

### Annotations vs Evidence Highlights

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ANNOTATIONS vs EVIDENCE HIGHLIGHTS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  These are DIFFERENT concepts with different storage and rendering:         │
│                                                                             │
│  EVIDENCE HIGHLIGHTS (MVP)                                                  │
│  ─────────────────────────                                                  │
│  • Purpose: Mark text that supports a specific requirement                  │
│  • Linked to: requirement_id                                                │
│  • Color: Blue (consistent across all evidence)                             │
│  • Stored in: evidence.json → evidence_snippets[].highlight_coordinates     │
│  • Behavior: Click highlight → jumps to linked requirement in checklist     │
│  • Created by: Drag-drop, Cmd+L, or AI extraction                           │
│                                                                             │
│  ANNOTATIONS (Future)                                                       │
│  ─────────────────────                                                      │
│  • Purpose: Free-form comments on document content                          │
│  • Linked to: document_id + coordinates (not requirements)                  │
│  • Color: Yellow (internal), Red (flagged), Green (verified)                │
│  • Stored in: annotations.json → separate from evidence                     │
│  • Behavior: Click annotation → shows comment popup                         │
│  • Created by: Manual annotation tool                                       │
│                                                                             │
│  For MVP: Only evidence highlights. Annotations deferred to v1.1.           │
│                                                                             │
│  Rendering distinction:                                                     │
│  ┌──────────────────────────────────────────┐                               │
│  │ PDF Viewer                               │                               │
│  │                                          │                               │
│  │ "The project area covers ▓▓▓▓▓▓▓▓▓▓▓▓"  │  ← Blue = evidence highlight │
│  │                                          │                               │
│  │ "Sampling methodology ████████████████"  │  ← Yellow = annotation        │
│  │                        ↑                 │     (future)                  │
│  │                     "Need to verify"     │                               │
│  │                                          │                               │
│  └──────────────────────────────────────────┘                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Manual Override Interaction

When a reviewer manually overrides a requirement's status, the system must handle the interaction with auto-extracted evidence gracefully:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MANUAL OVERRIDE + AUTO STATUS INTERACTION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCENARIO: AI extracted weak evidence (confidence 0.45)                     │
│            Reviewer manually marks as "Covered"                             │
│                                                                             │
│  BEHAVIOR:                                                                  │
│  1. Override creates audit entry:                                           │
│     {                                                                       │
│       "requirement_id": "REQ-005",                                          │
│       "previous_status": "partial",                                         │
│       "previous_confidence": 0.45,                                          │
│       "override_status": "covered",                                         │
│       "override_by": "becca@regen.network",                                 │
│       "override_at": "2024-01-15T10:30:00Z",                                │
│       "override_reason": "Verified manually - date matches imagery"         │
│     }                                                                       │
│                                                                             │
│  2. Status display shows BOTH:                                              │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ REQ-005: Monitoring Protocol                                      │  │
│     │                                                                   │  │
│     │ Status: ✓ Covered (Manual Override)                               │  │
│     │ Auto-detected: ⚠️ Partial (0.45)                                  │  │
│     │                                                                   │  │
│     │ Override reason: "Verified manually - date matches imagery"       │  │
│     │ Overridden by: Becca, 10 minutes ago                              │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  3. If new evidence is added AFTER override:                                │
│     • New evidence appears in list                                          │
│     • Auto-status recalculates but does NOT override manual status          │
│     • UI shows: "New evidence found - review override?"                     │
│     • Reviewer can keep override or remove it                               │
│                                                                             │
│  4. Override can be removed:                                                │
│     • "Clear Override" button reverts to auto-calculated status             │
│     • Creates audit entry for removal                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Batch Processing Architecture (111 Farms)

### Problem

Processing 111 farms individually would take 111 × 90 minutes = 166 hours.
Many farms share common documentation (methodology, proponent structure, legal templates).

### Solution: Project Templates & Inheritance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PROJECT TEMPLATES & INHERITANCE                                            │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  TEMPLATE HIERARCHY                                                         │
│                                                                             │
│  Czech Farm Cluster (Template)                                              │
│  ├── Shared Documents:                                                      │
│  │   • Methodology: Soil Carbon v1.2.2 ✓                                    │
│  │   • Legal Structure: CZ Agricultural Co-op ✓                             │
│  │   • Regional Baseline Study ✓                                            │
│  │                                                                          │
│  ├── Pre-verified Requirements (inherited by all farms):                    │
│  │   • REQ-001 Methodology version ✓                                        │
│  │   • REQ-010 Additionality (regional) ✓                                   │
│  │   • REQ-015 Buffer pool contribution ✓                                   │
│  │                                                                          │
│  └── Child Projects (111 farms):                                            │
│      ├── Farm CZ-001: Needs only farm-specific verification                 │
│      │   • Soil samples ○                                                   │
│      │   • Boundary shapefile ○                                             │
│      │   • Individual land tenure ○                                         │
│      │                                                                       │
│      ├── Farm CZ-002: Needs only farm-specific verification                 │
│      │   • Soil samples ○                                                   │
│      │   • Boundary shapefile ○                                             │
│      │   • Individual land tenure ○                                         │
│      │                                                                       │
│      └── ... (109 more farms)                                               │
│                                                                             │
│  TIME SAVINGS:                                                              │
│  • Template verification: 2 hours (one time)                                │
│  • Per-farm verification: 20-30 minutes (farm-specific only)                │
│  • Total: 2 + (111 × 0.5) = ~57 hours (vs 166 hours)                       │
│  • Savings: 65%                                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Template Creation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CREATE PROJECT TEMPLATE                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Template Name: Czech Farm Cluster 2024                                     │
│  Methodology: [Soil Carbon v1.2.2 ▼]                                        │
│                                                                             │
│  SHARED DOCUMENTS                                                           │
│  Upload documents that apply to ALL projects in this cluster:               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  📄 methodology_v1.2.2.pdf                                            │ │
│  │  📄 czech_agricultural_coop_legal_structure.pdf                       │ │
│  │  📄 regional_baseline_study_2024.pdf                                  │ │
│  │  [+ Add More Documents]                                               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  INHERITED REQUIREMENTS                                                     │
│  Select requirements that will be pre-verified for all child projects:      │
│                                                                             │
│  [✓] REQ-001 Methodology version                                            │
│  [✓] REQ-010 Additionality demonstration                                    │
│  [✓] REQ-015 Buffer pool contribution                                       │
│  [✓] REQ-020 Safeguards policy                                              │
│  [ ] REQ-002 Land tenure (farm-specific)                                    │
│  [ ] REQ-005 Monitoring protocol (farm-specific)                            │
│  ...                                                                        │
│                                                                             │
│  [Create Template] [Cancel]                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Bulk Dashboard Actions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BULK ACTIONS                                                               │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Czech Farm Cluster (111 projects)                    [☐ Select All]        │
│                                                                             │
│  [☑] Farm CZ-001    Stage 3/8    ⏳ In Progress                             │
│  [☑] Farm CZ-002    Stage 3/8    ⏳ In Progress                             │
│  [☑] Farm CZ-003    Stage 2/8    ⏳ Discovery                               │
│  [☐] Farm CZ-004    Stage 5/8    ✓ Validated                                │
│  [☑] Farm CZ-005    Stage 1/8    ○ Not Started                              │
│  ... (106 more)                                                             │
│                                                                             │
│  Selected: 4 projects                                                       │
│                                                                             │
│  BULK ACTIONS:                                                              │
│  [▶ Run Discovery]  [▶ Run Evidence Extraction]  [▶ Run Validation]        │
│  [📤 Export Reports]  [👤 Assign to Reviewer]  [🗑️ Delete Selected]         │
│                                                                             │
│  FILTERS:                                                                   │
│  Stage: [All ▼]  Status: [All ▼]  Reviewer: [All ▼]  [Apply]               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### API Extensions for Templates

```typescript
// New endpoints needed for template support
POST /templates
Body: { name, methodology, shared_documents[], inherited_requirements[] }
Response: { template_id, ... }

GET /templates
Response: { templates: Template[] }

POST /templates/{id}/projects
Body: { project_names: string[] }  // Batch create from template
Response: { created_projects: Session[] }

GET /templates/{id}/projects
Response: { projects: Session[] }

// Session model extension
interface Session {
  // ... existing fields ...
  parent_template_id: string | null;
  inherited_evidence: {
    requirement_id: string;
    inherited_from: string;  // template_id
    evidence_snippets: EvidenceSnippet[];
  }[];
}
```

---

## Collaboration Features

### 1. Internal vs External Comments

**Problem:** Reviewers need a safe space to deliberate without accidentally exposing internal notes to proponents.

**Solution:** Distinct UI styles and explicit confirmation for external communications.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INTERNAL vs EXTERNAL COMMENTS                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  INTERNAL NOTES (Yellow - Private to Team)                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ 🔒 INTERNAL                                                            │ │
│  │ ─────────────────────────────────────────────────────────────────────│ │
│  │ "This sampling date looks suspicious - need to verify with            │ │
│  │  imagery before approving. The monitoring report says 2024-03-15     │ │
│  │  but the satellite image metadata shows 2024-06-20."                  │ │
│  │                                                                       │ │
│  │ - Becca, 10 minutes ago                                               │ │
│  │                                                                       │ │
│  │ [Reply] [Delete]                                    Only visible to   │ │
│  │                                                     registry team     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  REVISION REQUEST (Red/Blue - Sent to Proponent)                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ 📤 SENT TO PROPONENT                                                   │ │
│  │ ─────────────────────────────────────────────────────────────────────│ │
│  │ "Please provide documentation clarifying the soil sampling date.      │ │
│  │  The monitoring report indicates 2024-03-15, but we need to verify   │ │
│  │  this aligns with project imagery."                                   │ │
│  │                                                                       │ │
│  │ Priority: High                                                        │ │
│  │ Sent: 2024-01-15 by Becca                                             │ │
│  │ Status: ⏳ Awaiting Response                                          │ │
│  │                                                                       │ │
│  │ [View Response] [Resend] [Resolve]                  Visible to        │ │
│  │                                                     proponent         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CREATING A NEW COMMENT:                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Add comment to REQ-005:                                               │ │
│  │                                                                       │ │
│  │ [____________________________________________]                         │ │
│  │                                                                       │ │
│  │ Type: ( ) 🔒 Internal Note    (●) 📤 Revision Request                │ │
│  │                                                                       │ │
│  │ [Cancel]                         [Post Internal] [Send to Proponent] │ │
│  │                                                                       │ │
│  │ ⚠️ "Send to Proponent" will be visible to the project developer      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Revision Snapshotting

**Problem:** When a proponent uploads new documents, it's hard to see what changed.

**Solution:** Snapshot evidence state when revision is requested, highlight deltas.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  REVISION SNAPSHOT & DIFF                                                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  REQ-005: Monitoring Protocol                                               │
│                                                                             │
│  REVISION HISTORY                                                           │
│  ─────────────────                                                          │
│                                                                             │
│  📸 Snapshot: 2024-01-15 (Revision Requested)                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Evidence at time of request:                                          │ │
│  │ • "Monitoring will occur annually" (project_plan.pdf, pg 8)           │ │
│  │ • Confidence: 0.45                                                    │ │
│  │ • Status: Partial                                                     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  📄 Response: 2024-01-18 (Proponent uploaded new document)                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ NEW: monitoring_schedule_2024.pdf                                     │ │
│  │                                                                       │ │
│  │ CHANGES DETECTED:                                                     │ │
│  │ + Added: "Soil sampling conducted March 15, 2024 by AgriLab"          │ │
│  │ + Added: "Follow-up sampling scheduled September 2024"                │ │
│  │ + Added: Sampling methodology reference (Appendix C)                  │ │
│  │                                                                       │ │
│  │ NEW Evidence Auto-Extracted:                                          │ │
│  │ • "Soil sampling conducted March 15, 2024..." (pg 2)                  │ │
│  │ • Confidence: 0.91                                                    │ │
│  │                                                                       │ │
│  │ [View Document] [Accept New Evidence] [Request Further Revision]      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CURRENT STATE (After revision)                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Evidence: 2 snippets                                                  │ │
│  │ • Original: "Monitoring will occur annually" (0.45)                   │ │
│  │ • NEW: "Soil sampling conducted March 15, 2024..." (0.91) ← ADDED     │ │
│  │                                                                       │ │
│  │ Status: Partial → Covered ✓                                           │ │
│  │ Confidence: 0.45 → 0.91                                               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## RBAC & Permissions Model

### Role Definitions (MVP)

| Role | Description | Example User |
|------|-------------|--------------|
| **Reviewer** | Conducts project reviews, extracts evidence, makes determinations | Becca (soil scientist) |
| **Proponent** | Submits projects, responds to revisions, views public status | Thomas (farm owner) |
| **Admin** | Manages users, templates, assigns reviews, exports metrics | Registry administrator |

### Permission Matrix

| Action | Reviewer | Proponent | Admin |
|--------|----------|-----------|-------|
| **Sessions** | | | |
| Create session | ✓ | ✗ | ✓ |
| View own sessions | ✓ | ✓ (limited) | ✓ |
| View all sessions | ✗ | ✗ | ✓ |
| Delete session | ✗ | ✗ | ✓ |
| **Documents** | | | |
| Upload documents | ✓ | ✓ (own project) | ✓ |
| View documents | ✓ | ✓ (own project) | ✓ |
| Delete documents | ✓ | ✗ | ✓ |
| **Evidence** | | | |
| Extract/link evidence | ✓ | ✗ | ✓ |
| View evidence | ✓ | ✗ | ✓ |
| Override status | ✓ | ✗ | ✓ |
| **Comments** | | | |
| Add internal note | ✓ | ✗ | ✓ |
| View internal notes | ✓ | ✗ | ✓ |
| Send revision request | ✓ | ✗ | ✓ |
| Respond to revision | ✗ | ✓ | ✓ |
| **Reports** | | | |
| Generate report | ✓ | ✗ | ✓ |
| View report | ✓ | ✓ (final only) | ✓ |
| Export report | ✓ | ✗ | ✓ |
| **Templates** | | | |
| Create template | ✗ | ✗ | ✓ |
| Use template | ✓ | ✗ | ✓ |
| Modify template | ✗ | ✗ | ✓ |
| **Admin** | | | |
| Assign reviewer | ✗ | ✗ | ✓ |
| View metrics | ✗ | ✗ | ✓ |
| Manage users | ✗ | ✗ | ✓ |

### Proponent View Restrictions

Proponents have a strictly limited view to prevent exposure of internal deliberations:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PROPONENT VIEW: What They CAN See                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ✓ Project name and metadata                                                │
│  ✓ Overall review stage (Stage 4/8)                                         │
│  ✓ Documents they uploaded                                                  │
│  ✓ Revision requests (public comments only)                                 │
│  ✓ Final determination (when completed)                                     │
│  ✓ Final report (when released)                                             │
│                                                                             │
│  PROPONENT VIEW: What They CANNOT See                                       │
│  ─────────────────────────────────────                                      │
│                                                                             │
│  ✗ Individual requirement status                                            │
│  ✗ Evidence snippets and confidence scores                                  │
│  ✗ Internal notes and deliberations                                         │
│  ✗ Cross-validation results                                                 │
│  ✗ Reviewer name (until determination)                                      │
│  ✗ Draft reports                                                            │
│  ✗ Override history                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation

```typescript
// middleware/auth.ts
interface User {
  id: string;
  email: string;
  role: "reviewer" | "proponent" | "admin";
  assigned_projects?: string[];  // For proponents: projects they own
}

// API route protection
function requireRole(...allowedRoles: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    const user = req.user;
    if (!allowedRoles.includes(user.role)) {
      return res.status(403).json({ error: "Forbidden" });
    }
    next();
  };
}

// Example route protection
app.post("/sessions", requireRole("reviewer", "admin"), createSession);
app.get("/sessions/:id", requireProjectAccess, getSession);  // Custom check
app.post("/sessions/:id/revisions", requireRole("reviewer", "admin"), createRevision);
app.post("/sessions/:id/revisions/:rid/respond", requireRole("proponent"), respondToRevision);
```

---

## Web Application Design

### Information Architecture

```
Registry Review App
├── Dashboard
│   ├── Active Reviews (cards with progress)
│   ├── Quick Stats (reviews completed, avg time)
│   ├── Recent Activity
│   └── Bulk Actions Bar (when items selected)
├── Templates (NEW)
│   ├── Template List
│   ├── Create Template Wizard
│   └── Template Detail (shared docs, inherited reqs)
├── Review Workspace (main interface)
│   ├── Header
│   │   ├── Project Name & ID
│   │   ├── Template Badge (if from template)
│   │   ├── Stage Progress Bar (soft-gated)
│   │   └── Actions (Save, Export, Complete)
│   ├── Left Panel: Document Viewer
│   │   ├── Document Tabs
│   │   ├── PDF Viewer with Highlighting
│   │   │   ├── Heatmap Scrollbar (NEW)
│   │   │   └── Drag-and-Drop Source
│   │   └── Document List (Smart Filtered)
│   ├── Right Panel: Checklist & Evidence
│   │   ├── Scratchpad (Collapsible) (NEW)
│   │   ├── Category Accordion
│   │   ├── Requirement Cards (Drag-and-Drop Targets)
│   │   │   ├── AI Reasoning Tooltips (NEW)
│   │   │   └── Focus Mode Toggle (NEW)
│   │   └── Validation Summary (Fact Sheet View) (NEW)
│   └── Footer
│       ├── Stage Navigation (Soft-Gated)
│       └── Keyboard Shortcut Hint
├── Cross-Validation View (NEW)
│   ├── Fact Sheet Tables
│   ├── Date Alignment Matrix
│   ├── Land Tenure Comparison
│   └── Project ID Occurrences
├── Reports
│   ├── Generated Reports List
│   ├── Report Viewer (Shows Gaps)
│   └── Export Options (PDF, JSON, Markdown, CSV)
├── Revisions (Proponent View)
│   ├── Pending Revisions
│   ├── Upload Responses
│   ├── Revision History with Snapshots (NEW)
│   └── Communication Thread (Internal/External) (NEW)
└── Settings
    ├── User Profile
    ├── Keyboard Shortcuts Customization
    ├── Notifications
    └── API Keys (for integrations)
```

### Component Hierarchy (Updated)

```
App
├── AppLayout
│   ├── TopNav
│   │   ├── Logo
│   │   ├── ProjectSelector
│   │   ├── TemplateIndicator (NEW)
│   │   └── UserMenu
│   └── MainContent
│
├── DashboardPage
│   ├── StatsCards
│   ├── BulkActionsBar (NEW)
│   ├── TemplateSelector (NEW)
│   ├── ActiveReviewsList
│   │   └── ReviewCard (with checkbox for bulk select)
│   └── RecentActivityFeed
│
├── WorkspacePage
│   ├── WorkspaceHeader
│   │   ├── ProjectInfo
│   │   ├── TemplateInheritanceBadge (NEW)
│   │   ├── SoftGatedStageProgress (NEW)
│   │   └── ActionButtons
│   ├── KeyboardShortcutHelper (NEW)
│   ├── SplitPane
│   │   ├── DocumentPanel
│   │   │   ├── DocumentTabs
│   │   │   ├── PDFViewerWithHighlighter (NEW: react-pdf-highlighter)
│   │   │   │   ├── HeatmapScrollbar (NEW)
│   │   │   │   ├── PageNavigation
│   │   │   │   ├── ZoomControls
│   │   │   │   ├── PersistentHighlightLayer (NEW)
│   │   │   │   └── DragSourceHandler (NEW)
│   │   │   └── SmartFilteredDocumentList (NEW)
│   │   └── ChecklistPanel
│   │       ├── EvidenceScratchpad (NEW)
│   │       ├── ChecklistHeader
│   │       │   ├── FilterControls
│   │       │   └── ProgressSummary
│   │       ├── CategoryAccordion
│   │       │   └── RequirementCard (DropTarget) (NEW)
│   │       │       ├── RequirementHeader
│   │       │       ├── StatusBadge
│   │       │       ├── InheritedBadge (NEW: from template)
│   │       │       ├── EvidenceList
│   │       │       │   └── EvidenceSnippetWithReasoning (NEW)
│   │       │       ├── AIReasoningTooltip (NEW)
│   │       │       ├── FocusModeButton (NEW)
│   │       │       └── ReviewControls
│   │       └── ValidationSummary
│   ├── FocusModeOverlay (NEW)
│   └── SoftGatedStageNavigator (NEW)
│
├── CrossValidationPage (NEW)
│   ├── FactSheetView
│   │   ├── DateAlignmentTable
│   │   ├── LandTenureTable
│   │   └── ProjectIDTable
│   └── ValidationDetails
│
├── TemplatePage (NEW)
│   ├── TemplateList
│   ├── CreateTemplateWizard
│   │   ├── SharedDocumentUploader
│   │   ├── InheritedRequirementSelector
│   │   └── TemplatePreview
│   └── TemplateDetail
│       ├── SharedDocuments
│       ├── InheritedRequirements
│       └── ChildProjectsList
│
└── RevisionsPage
    ├── RevisionsList
    ├── RevisionSnapshot (NEW)
    ├── DiffViewer (NEW)
    └── InternalExternalComments (NEW)
```

---

## Technical Architecture

### Frontend Stack (Updated)

```
Frontend
├── Framework: Next.js 14+ (App Router)
├── Language: TypeScript
├── Styling: Tailwind CSS + shadcn/ui components
├── PDF Viewer: react-pdf-highlighter (NOT raw PDF.js)  ← UPDATED
│   └── Handles persistent highlighting coordinate math
├── Drag-and-Drop: @dnd-kit/core  ← NEW
├── State Management: Zustand + React Query
│   └── Optimistic updates for evidence linking  ← NEW
├── Keyboard Shortcuts: react-hotkeys-hook  ← NEW
├── API Client: Generated from OpenAPI spec
└── Deployment: Vercel or self-hosted
```

**Rationale Updates:**
- **react-pdf-highlighter** over raw PDF.js: Handles the complex coordinate math for persistent text highlighting across screen sizes
- **@dnd-kit/core**: Modern drag-and-drop with accessibility support
- **Optimistic UI pattern**: Critical for maintaining flow state during evidence linking

### Optimistic UI Pattern (Detail)

```typescript
// stores/evidence.ts
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

interface EvidenceStore {
  // Local state (optimistic)
  evidence: Map<string, Evidence[]>;  // requirementId -> evidence[]
  pendingLinks: Set<string>;  // snippetIds being synced
  failedLinks: Map<string, string>;  // snippetId -> error message

  // Actions
  linkEvidence: (snippetId: string, requirementId: string) => Promise<void>;
  unlinkEvidence: (snippetId: string, requirementId: string) => Promise<void>;
}

export const useEvidenceStore = create<EvidenceStore>()(
  immer((set, get) => ({
    evidence: new Map(),
    pendingLinks: new Set(),
    failedLinks: new Map(),

    linkEvidence: async (snippetId, requirementId) => {
      // 1. Optimistic update - instant UI feedback
      set(state => {
        state.pendingLinks.add(snippetId);
        const reqEvidence = state.evidence.get(requirementId) || [];
        reqEvidence.push({
          snippet_id: snippetId,
          status: 'pending',
          // ... other fields
        });
        state.evidence.set(requirementId, reqEvidence);
      });

      // 2. Sync to server
      try {
        await api.evidence.link(snippetId, requirementId);

        // 3. Confirm success
        set(state => {
          state.pendingLinks.delete(snippetId);
          const reqEvidence = state.evidence.get(requirementId);
          const snippet = reqEvidence?.find(e => e.snippet_id === snippetId);
          if (snippet) snippet.status = 'confirmed';
        });
      } catch (error) {
        // 4. Rollback on failure
        set(state => {
          state.pendingLinks.delete(snippetId);
          state.failedLinks.set(snippetId, error.message);

          // Remove the optimistically added evidence
          const reqEvidence = state.evidence.get(requirementId);
          if (reqEvidence) {
            state.evidence.set(
              requirementId,
              reqEvidence.filter(e => e.snippet_id !== snippetId)
            );
          }
        });

        // Show retry toast
        toast.error('Failed to link evidence. Tap to retry.', {
          action: () => get().linkEvidence(snippetId, requirementId)
        });
      }
    }
  }))
);
```

### Long-Running Operations as Jobs

Evidence extraction and cross-validation can take 30-60 seconds. These operations should be modeled as background jobs, not synchronous API calls.

```typescript
// Job-based API for long-running operations
interface Job {
  job_id: string;
  type: "evidence_extraction" | "cross_validation" | "report_generation" | "batch_create";
  status: "queued" | "running" | "completed" | "failed";
  progress: number;           // 0-100
  started_at: string | null;
  completed_at: string | null;
  result?: any;               // Job-specific result
  error?: string;             // If failed
}

// API Pattern
POST /sessions/{id}/evidence/extract
Response: { job_id: "job_123", status: "queued" }

GET /jobs/{job_id}
Response: { job_id: "job_123", status: "running", progress: 45 }

// Frontend polling (with exponential backoff)
async function pollJob(jobId: string): Promise<Job> {
  let delay = 500;
  while (true) {
    const job = await api.getJob(jobId);
    if (job.status === "completed" || job.status === "failed") {
      return job;
    }
    // Update progress UI
    setProgress(job.progress);
    // Wait with exponential backoff (max 5 sec)
    await sleep(delay);
    delay = Math.min(delay * 1.5, 5000);
  }
}
```

**Job Progress UI:**
```
┌─────────────────────────────────────────────────────────────────┐
│  Extracting Evidence...                                         │
│                                                                 │
│  ████████████████████░░░░░░░░░░░░░░░░░░░░ 45%                  │
│                                                                 │
│  Processing: baseline_report.pdf (3 of 7 documents)             │
│  Snippets found: 12                                             │
│                                                                 │
│  [Cancel]                                                       │
└─────────────────────────────────────────────────────────────────┘
```

### PDF File Serving Strategy

PDFs should be served efficiently to avoid memory bloat and enable progressive loading.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PDF FILE SERVING: AVOID BASE64, USE STREAMING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ❌ BAD: Base64 in JSON                                                     │
│  GET /documents/{id}                                                        │
│  Response: { "content": "JVBERi0xLjQKJ..." }  // 1.3x size, blocks parsing │
│                                                                             │
│  ✓ GOOD: Direct binary streaming with range request support                 │
│  GET /documents/{id}/content                                                │
│  Headers:                                                                   │
│    Content-Type: application/pdf                                            │
│    Accept-Ranges: bytes                                                     │
│    Content-Length: 2457600                                                  │
│  Response: <binary PDF data>                                                │
│                                                                             │
│  Benefits:                                                                  │
│  • PDF.js can stream pages progressively                                    │
│  • Range requests enable fast page jumps                                    │
│  • No JSON parsing overhead for large files                                 │
│  • Browser caching works correctly                                          │
│                                                                             │
│  Implementation:                                                            │
│  • Backend: Return FileResponse with Content-Disposition                    │
│  • Frontend: Pass URL directly to react-pdf-highlighter                     │
│  • Caching: Set Cache-Control headers for immutable PDFs                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```python
# Backend implementation (FastAPI)
from fastapi.responses import FileResponse

@app.get("/sessions/{session_id}/documents/{doc_id}/content")
async def get_document_content(session_id: str, doc_id: str):
    document = await get_document(session_id, doc_id)
    return FileResponse(
        path=document.file_path,
        media_type="application/pdf",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=31536000, immutable"  # PDFs don't change
        }
    )
```

### API Client Generation

Generate TypeScript types from the existing OpenAPI spec to ensure frontend/backend type safety.

```bash
# Generate types from OpenAPI spec
npx openapi-typescript http://localhost:8080/openapi.json -o src/lib/api/schema.ts

# Or from static file
npx openapi-typescript ./openapi.json -o src/lib/api/schema.ts
```

```typescript
// Generated types usage
import type { paths, components } from './schema';

type Session = components['schemas']['Session'];
type EvidenceSnippet = components['schemas']['EvidenceSnippet'];

// Type-safe API client
import createClient from 'openapi-fetch';
import type { paths } from './schema';

const client = createClient<paths>({ baseUrl: 'https://api.example.com' });

// Fully typed - parameters and response
const { data, error } = await client.GET('/sessions/{session_id}', {
  params: { path: { session_id: 'abc123' } }
});
// data is typed as Session
```

**Tooling Recommendation:**
- **openapi-typescript**: Generate types from OpenAPI spec
- **openapi-fetch**: Lightweight fetch wrapper with full type inference
- Alternative: **orval** for React Query integration with generated hooks

### Data Flow (Updated)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Web Frontend  │────▶│   REST API      │────▶│   MCP Server    │
│   (Next.js)     │◀────│   (FastAPI)     │◀────│   (FastMCP)     │
│                 │     │                 │     │                 │
│  Optimistic UI  │     │                 │     │                 │
│  Local State    │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Browser State  │     │  File Storage   │     │  LLM (Claude)   │
│  ├─ Zustand     │     │  sessions/      │     │  Evidence       │
│  ├─ React Query │     │  templates/     │     │  Extraction     │
│  └─ IndexedDB   │     │  cache/         │     │                 │
│     (offline)   │     │  snapshots/     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### File Structure (Updated)

```
registry-review-web/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                      # Dashboard
│   ├── templates/
│   │   ├── page.tsx                  # Template list
│   │   ├── new/page.tsx              # Create template
│   │   └── [id]/page.tsx             # Template detail
│   ├── reviews/
│   │   ├── page.tsx
│   │   ├── new/page.tsx
│   │   └── [id]/
│   │       ├── page.tsx              # Workspace
│   │       ├── validation/page.tsx   # Fact sheet view
│   │       └── report/page.tsx
│   ├── revisions/
│   │   └── [id]/page.tsx
│   └── settings/
│       └── page.tsx
├── components/
│   ├── ui/                           # shadcn/ui
│   ├── workspace/
│   │   ├── DocumentPanel.tsx
│   │   ├── PDFHighlighter.tsx        # Wrapper for react-pdf-highlighter
│   │   ├── HeatmapScrollbar.tsx      # NEW
│   │   ├── DragDropProvider.tsx      # NEW
│   │   ├── ChecklistPanel.tsx
│   │   ├── EvidenceScratchpad.tsx    # NEW
│   │   ├── RequirementCard.tsx
│   │   ├── AIReasoningTooltip.tsx    # NEW
│   │   ├── FocusModeOverlay.tsx      # NEW
│   │   ├── SoftGatedStageNav.tsx     # NEW
│   │   └── SmartDocumentList.tsx     # NEW
│   ├── validation/
│   │   ├── FactSheetView.tsx         # NEW
│   │   ├── DateAlignmentTable.tsx    # NEW
│   │   └── LandTenureTable.tsx       # NEW
│   ├── templates/
│   │   ├── TemplateCard.tsx          # NEW
│   │   ├── CreateTemplateWizard.tsx  # NEW
│   │   └── InheritedReqSelector.tsx  # NEW
│   ├── collaboration/
│   │   ├── InternalNote.tsx          # NEW
│   │   ├── RevisionRequest.tsx       # NEW
│   │   └── SnapshotDiff.tsx          # NEW
│   ├── dashboard/
│   │   ├── StatsCards.tsx
│   │   ├── BulkActionsBar.tsx        # NEW
│   │   └── ReviewCard.tsx
│   └── common/
│       ├── TopNav.tsx
│       ├── KeyboardShortcuts.tsx     # NEW
│       └── ProgressBar.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts
│   │   ├── sessions.ts
│   │   ├── templates.ts              # NEW
│   │   ├── evidence.ts
│   │   └── types.ts
│   ├── stores/
│   │   ├── evidence.ts               # Optimistic UI store
│   │   ├── scratchpad.ts             # NEW
│   │   └── workspace.ts
│   ├── hooks/
│   │   ├── useSession.ts
│   │   ├── useKeyboardShortcuts.ts   # NEW
│   │   ├── useDragDrop.ts            # NEW
│   │   └── useOptimisticEvidence.ts  # NEW
│   └── utils/
│       ├── pdf.ts
│       ├── heatmap.ts                # NEW
│       └── diff.ts                   # NEW
├── styles/
│   └── globals.css
└── ...config files
```

---

## Data Handling & Compliance

### Document Storage

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DATA STORAGE ARCHITECTURE                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SESSION DATA (File-based)                                                  │
│  ─────────────────────────                                                  │
│  Location: /data/sessions/{session_id}/                                     │
│  Contents:                                                                  │
│  ├── session.json      # Metadata, status, workflow progress               │
│  ├── documents.json    # Document inventory and classification             │
│  ├── evidence.json     # Evidence snippets with highlight coords           │
│  ├── validation.json   # Cross-validation results                          │
│  ├── overrides.json    # Manual reviewer overrides with audit trail        │
│  ├── annotations.json  # Internal notes (future)                           │
│  ├── revisions.json    # Revision request/response history                 │
│  ├── snapshots/        # Point-in-time snapshots for revisions             │
│  │   ├── 2024-01-15_revision_001.json                                      │
│  │   └── 2024-01-18_revision_002.json                                      │
│  └── uploads/          # Original PDF files                                │
│      ├── baseline_report.pdf                                               │
│      ├── monitoring_2024.pdf                                               │
│      └── ...                                                               │
│                                                                             │
│  TEMPLATE DATA                                                              │
│  ─────────────                                                              │
│  Location: /data/templates/{template_id}/                                   │
│  Contents:                                                                  │
│  ├── template.json     # Template metadata, inherited requirements         │
│  ├── shared_docs/      # Shared documents (referenced by child sessions)   │
│  └── evidence.json     # Pre-verified evidence for inherited requirements  │
│                                                                             │
│  IMPORTANT: Child sessions reference template files, not copy them.        │
│  This saves storage and ensures consistency.                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Retention Policy

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| Active sessions | Indefinite | Active work |
| Completed sessions | 7 years | Audit compliance |
| Deleted sessions | 90 days soft delete | Accidental deletion recovery |
| Uploaded PDFs | Same as session | Tied to session lifecycle |
| Audit logs | 7 years | Compliance requirement |
| Templates | Indefinite | Referenced by child sessions |
| User data | Account lifetime + 30 days | GDPR compliance |

### Sensitive Data Handling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SENSITIVE DATA CLASSIFICATION                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HIGH SENSITIVITY (Access restricted to reviewer + admin)                   │
│  • Internal notes and deliberations                                         │
│  • Override reasons and audit trails                                        │
│  • Cross-validation detailed results                                        │
│  • Draft reports                                                            │
│  • Evidence confidence scores                                               │
│                                                                             │
│  MEDIUM SENSITIVITY (Shared with proponent on request)                      │
│  • Uploaded project documents                                               │
│  • Revision requests and responses                                          │
│  • Final determination                                                      │
│  • Published reports                                                        │
│                                                                             │
│  LOW SENSITIVITY (Public after approval)                                    │
│  • Project name and basic metadata                                          │
│  • Final approval status                                                    │
│  • Methodology reference                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Audit Trail Requirements

Every state-changing action must be logged:

```typescript
interface AuditEntry {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  action: AuditAction;
  session_id: string;
  entity_type: "session" | "document" | "evidence" | "requirement" | "revision";
  entity_id: string;
  previous_value?: any;  // For updates
  new_value?: any;       // For creates/updates
  ip_address?: string;
  user_agent?: string;
}

type AuditAction =
  | "session.created"
  | "session.deleted"
  | "document.uploaded"
  | "document.deleted"
  | "evidence.linked"
  | "evidence.unlinked"
  | "requirement.status_changed"
  | "requirement.override_set"
  | "requirement.override_cleared"
  | "revision.requested"
  | "revision.responded"
  | "revision.resolved"
  | "report.generated"
  | "session.completed";
```

### Backup Strategy

- **Hourly**: Incremental backup of changed session files
- **Daily**: Full backup of all data
- **Weekly**: Offsite backup replication
- **Point-in-time recovery**: Supported via file versioning

### GDPR Considerations (Future)

For EU deployment:
- User data export on request (30 days)
- Right to deletion (with audit trail preservation caveat)
- Data processing agreements with proponents
- Cookie consent for analytics (if added)

---

## Implementation Roadmap (Reordered to De-Risk PDF)

**Key Change:** PDF handling moved to Phase 1 to de-risk the highest-uncertainty component early. If react-pdf-highlighter doesn't work, we discover it in Week 1-2, not Week 3-4.

### Phase 1: PDF Viewer & Foundation (Week 1-2)

**Goal:** Prove PDF rendering and highlighting works with real project documents

**Tasks:**
- [ ] Initialize Next.js project with TypeScript
- [ ] Configure Tailwind CSS and shadcn/ui
- [ ] Integrate **react-pdf-highlighter** immediately
- [ ] Test PDF rendering with 5+ real project PDFs (different sizes, layouts)
- [ ] Implement basic text selection and highlighting
- [ ] Verify highlight coordinate persistence across page reload
- [ ] Set up binary PDF streaming endpoint (not base64)
- [ ] Set up API client with openapi-typescript type generation

**EXIT CRITERIA (Must pass before Phase 2):**
- [ ] 5 different PDFs render correctly
- [ ] Highlights persist after page reload
- [ ] PDFs load via streaming (not base64)
- [ ] No memory issues with 50+ page PDF
- [ ] Text selection works on scanned vs native PDFs

**Risk Mitigation:** If react-pdf-highlighter fails, evaluate alternatives:
- mozilla/pdf.js with custom highlight layer
- @phuocng/react-pdf-viewer
- Fallback: page + text reference only (no visual highlights)

**Deliverable:** PDF viewer proof-of-concept with persistent highlights

---

### Phase 2: Core Workspace (Week 3-4)

**Goal:** Basic workspace layout with session management

**Tasks:**
- [ ] Implement Dashboard page with session list
- [ ] Implement basic session CRUD
- [ ] Create split-pane workspace layout
- [ ] Add document list sidebar
- [ ] Implement page navigation controls
- [ ] Add zoom controls
- [ ] Set up Zustand stores with optimistic update pattern
- [ ] Add keyboard shortcut infrastructure (react-hotkeys-hook)

**EXIT CRITERIA:**
- [ ] Can create/open/delete sessions
- [ ] Workspace shows PDF on left, empty checklist on right
- [ ] J/K navigation between documents works
- [ ] Page up/down navigation works
- [ ] Zoom in/out works

**Deliverable:** Working workspace shell with session management

---

### Phase 3: Evidence Linking (Week 5-6)

**Goal:** Drag-and-drop evidence workflow

**Tasks:**
- [ ] Implement checklist panel with category accordion
- [ ] Create requirement cards from API data
- [ ] Implement **drag-and-drop** from PDF to requirements (@dnd-kit/core)
- [ ] Add **evidence scratchpad** panel
- [ ] Display linked evidence snippets
- [ ] Implement **Focus Mode** overlay (F key)
- [ ] Add keyboard shortcuts for status updates (1-5 keys)
- [ ] Implement optimistic UI for linking

**EXIT CRITERIA:**
- [ ] Can drag text from PDF to requirement card
- [ ] Evidence appears instantly (optimistic UI)
- [ ] Evidence persists on page reload
- [ ] Scratchpad holds clipped text (Cmd+C)
- [ ] Focus Mode expands single requirement
- [ ] Keyboard 1-5 changes status, J/K navigates

**Deliverable:** Complete drag-drop evidence workflow

---

### Phase 4: Validation & Cross-Issues Panel (Week 7-8)

**Goal:** Cross-validation with tabular views and issues integration

**Tasks:**
- [ ] Implement **Fact Sheet View** for cross-validation
- [ ] Create Date Alignment comparison table
- [ ] Create Land Tenure comparison table
- [ ] Create Project ID occurrence table
- [ ] Add **Cross-Validation Issues Panel** in workspace sidebar
- [ ] Clicking issue jumps to relevant requirement + document
- [ ] Add validation warnings inline in checklist
- [ ] Implement **soft-gating** for stage navigation
- [ ] Add AI reasoning tooltips to evidence snippets
- [ ] Add heatmap scrollbar to PDF viewer

**EXIT CRITERIA:**
- [ ] Fact sheet tables render from API data
- [ ] Issues panel shows validation warnings
- [ ] Clicking issue navigates to requirement
- [ ] Soft gate shows warnings but allows navigation
- [ ] Heatmap shows evidence coverage

**Deliverable:** Scannable cross-validation with navigation

---

### Phase 5: RBAC & Proponent Flow (Week 9-10)

**Goal:** Basic auth and proponent revision response

**Tasks:**
- [ ] Implement session-based authentication
- [ ] Add role-based access control (reviewer/proponent/admin)
- [ ] Create proponent dashboard (limited view)
- [ ] Implement revision request flow
- [ ] Build proponent upload response UI
- [ ] Add notification email triggers (stub)
- [ ] Implement **internal vs external** comment distinction
- [ ] Create revision snapshotting

**EXIT CRITERIA:**
- [ ] Proponent cannot see internal notes
- [ ] Proponent can upload revision response
- [ ] Internal notes have yellow background (distinct)
- [ ] Revision request creates notification
- [ ] Snapshot created on revision request

**Deliverable:** Multi-user flow with proponent collaboration

---

### Phase 6: Templates & Batch (Week 11-12)

**Goal:** Template system for 111 farms use case

**Tasks:**
- [ ] Implement Template CRUD pages
- [ ] Create template wizard (shared docs, inherited reqs)
- [ ] Add template inheritance to session model
- [ ] Implement **bulk actions** on dashboard
- [ ] Add batch project creation from template (CSV upload)
- [ ] Show inherited requirements with "From Template" badge
- [ ] Inherited evidence is read-only
- [ ] Bulk export reports as ZIP

**EXIT CRITERIA:**
- [ ] Can create template with shared documents
- [ ] Can batch-create 10 projects from template
- [ ] Inherited requirements show as pre-filled
- [ ] Inherited evidence cannot be edited
- [ ] Bulk export generates ZIP with 10 reports

**Deliverable:** Can process farm clusters efficiently

---

### Phase 7: Polish & Production (Week 13-14)

**Goal:** Production-ready MVP

**Tasks:**
- [ ] Performance optimization (lazy loading, virtualization)
- [ ] Error handling and recovery
- [ ] Job progress UI for long-running operations
- [ ] Mobile responsiveness improvements
- [ ] Keyboard shortcut customization
- [ ] User onboarding flow (first-time hints)
- [ ] Documentation and help system
- [ ] Audit log viewer

**EXIT CRITERIA:**
- [ ] 50+ page PDF loads in <3 seconds
- [ ] Evidence extraction shows progress bar
- [ ] Error states have retry options
- [ ] Help modal shows keyboard shortcuts
- [ ] No console errors in production build

**Deliverable:** Production-ready application

---

### Contingency: Phase 8 (If Needed)

Reserved for:
- Bug fixes discovered in user testing
- Performance issues with 111 farms scale
- Integration issues with existing ChatGPT workflow
- Accessibility improvements

---

## Success Metrics (Updated)

### Quantitative

| Metric | Current | Target | With Templates |
|--------|---------|--------|----------------|
| Review time (individual) | 6-8 hours | 60-90 min | 60-90 min |
| Review time (cluster farm) | 6-8 hours | 60-90 min | **20-30 min** |
| Evidence linking speed | N/A | <2 sec/link | <0.5 sec (drag-drop) |
| Keyboard navigation coverage | N/A | 80% of actions | 80%+ |
| Requirement coverage (auto) | ~70% | 95%+ | 95%+ |
| User errors | Unknown | <5% | <5% |
| Training time | N/A | <1 hour | <1 hour |
| 111 farms total time | 832 hours | 166 hours | **~57 hours** |

### Qualitative

- Reviewers prefer drag-drop over popup menus
- Scratchpad matches "find first, sort later" mental model
- Fact Sheet view preferred over text snippets for validation
- Internal/external comment distinction prevents accidental exposure
- Templates significantly reduce per-farm time in clusters
- AI reasoning tooltips build trust in automated extraction

---

## Open Questions (Updated)

### Resolved in v1.2

1. ~~**Real-time updates:** Polling sufficient for MVP or invest in WebSocket early?~~ → Use optimistic UI + polling for MVP
2. ~~**PDF annotations:** Store annotations in backend or browser-only for MVP?~~ → Backend storage with react-pdf-highlighter; annotations deferred to v1.1
3. ~~**Batch processing:** How to handle 111 farms efficiently in UI?~~ → Templates + bulk actions
4. ~~**Evidence anchoring:** How to persist highlight coordinates?~~ → Three-layer approach (bbox → content hash → page+text)
5. ~~**Long-running operations:** Synchronous or async?~~ → Job-based API with polling
6. ~~**PDF file serving:** Base64 or streaming?~~ → Binary streaming with range request support
7. ~~**API types:** Manual or generated?~~ → openapi-typescript with openapi-fetch
8. ~~**RBAC model:** What permissions?~~ → Reviewer/Proponent/Admin with explicit permission matrix

### Still Open

1. **Authentication provider:** Start with simple session-based auth or integrate with existing Regen identity system?
2. **Offline support:** Needed for field reviewers with poor connectivity? (Consider for Phase 8)
3. **Template versioning:** What happens when a template is updated after child projects are created? Options:
   - Freeze inherited evidence at creation time
   - Allow opt-in sync with template updates
   - Version templates and track which version each child uses
4. **Multi-reviewer:** Should multiple reviewers be able to work on the same project simultaneously? (Deferred to Future)
5. **Proponent notifications:** Email only, or in-app notifications? What service for email (SendGrid, Postmark)?
6. **Scanned PDFs:** How to handle PDFs without embedded text? Options:
   - OCR on upload (adds processing time)
   - Warn user "this PDF has no searchable text"
   - Support manual text entry for evidence

---

## Conclusion

This planning document (v1.2) incorporates two rounds of feedback that transforms the Registry Review Web Application from concept to production-ready specification. Key architectural decisions:

### UX Improvements (v1.1)

1. **Drag-and-drop evidence linking** eliminates tedious popup menus
2. **Evidence scratchpad** matches the "find first, sort later" cognitive model
3. **Keyboard shortcuts** enable power-user flow state
4. **Soft gating** allows non-linear workflow navigation
5. **Fact Sheet views** make cross-validation instantly scannable
6. **AI reasoning tooltips** build trust in automated extraction
7. **Project templates** enable 65% time savings for farm clusters
8. **Internal/external comments** prevent accidental exposure of deliberations
9. **Revision snapshotting** clearly shows what changed

### Architectural Improvements (v1.2)

10. **MVP scope explicitly defined** with feature priority matrix
11. **End-to-end user journeys** with acceptance criteria
12. **Evidence anchoring strategy** with three-layer fallback (bbox → hash → page)
13. **RBAC model** with explicit permission matrix
14. **Long-running operations as jobs** with progress polling
15. **PDF streaming** (not base64) for efficient loading
16. **API client generation** from OpenAPI spec
17. **Data handling policy** with retention and classification
18. **Phase reordering** to de-risk PDF handling in Week 1
19. **Exit criteria per phase** to ensure quality gates

### Projected Outcomes

With these enhancements, the application can realistically achieve:
- **60-90 minutes** per individual review (down from 6-8 hours)
- **20-30 minutes** per farm in a cluster (with templates)
- **~57 hours** to process 111 Czech farms (down from 832 hours)

### Next Steps

1. **Review and approve** this planning document (v1.2)
2. **Create Next.js repository** with initial scaffolding
3. **Begin Phase 1** with react-pdf-highlighter proof-of-concept
4. **Test with 5+ real PDFs** before proceeding to Phase 2
5. **Schedule weekly check-ins** with Becca for user feedback

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | January 2026 | Initial planning document |
| v1.1 | January 2026 | UX feedback: drag-drop, scratchpad, soft gating, templates |
| v1.2 | January 2026 | Architectural feedback: MVP scope, user journeys, evidence anchoring, RBAC, data handling, phase reordering |
