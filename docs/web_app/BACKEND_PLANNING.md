# Backend Planning

## Overview

The backend extends the existing MCP server and REST API with an embedded AI agent that powers the chat panel in the web application.

---

## Table of Contents

1. [Existing Architecture](#existing-architecture)
2. [AI Agent](#ai-agent)
3. [API Extensions](#api-extensions)
4. [Google Drive Integration](#google-drive-integration)
5. [Notifications](#notifications)
6. [Data Models](#data-models)
7. [Evidence Anchoring](#evidence-anchoring)
8. [Long-Running Operations](#long-running-operations)
9. [PDF File Serving](#pdf-file-serving)
10. [Authentication](#authentication)
11. [RBAC & Permissions](#rbac--permissions)
12. [Data Handling & Compliance](#data-handling--compliance)

---

## Existing Architecture

### MCP Server

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
│   ├── human_review_tools.py    # Overrides, annotations
│   ├── report_tools.py          # Report generation
│   └── upload_tools.py          # File upload handling
├── extractors/                  # Content extraction
│   ├── marker_extractor.py      # PDF → Markdown via marker
│   ├── llm_extractors.py        # LLM-powered field extraction
│   └── fast_extractor.py        # Quick regex-based extraction
└── models/                      # Pydantic schemas
    ├── schemas.py               # Session, Document, Requirement
    ├── evidence.py              # EvidenceSnippet, RequirementFinding
    ├── validation.py            # DateAlignment, LandTenure
    └── report.py                # ReviewReport, ReportSummary
```

### REST API (Existing)

**File:** `chatgpt_rest_api.py`
**Framework:** FastAPI
**Deployment:** `https://regen.gaiaai.xyz/registry`

Key endpoint categories:
- Sessions: create/list/get/delete (status derived from workflow progress)
- Uploads: base64 upload to session, plus two-step upload URL workflow
- Discovery: discover documents + conversion status (extraction pipeline visibility)
- Mapping: map requirements, mapping status, mapping matrix, confirm-all-mappings
- Evidence: extract evidence, evidence matrix (table view)
- Validation: run cross-validation
- Reports: generate report (markdown/json)
- Human Review: overrides, annotations, determination, revisions, audit log

**Web app gaps to plan explicitly (not exposed yet):**
- Stream PDFs as binary for the viewer (`/sessions/{id}/documents/{doc_id}/content`)
- List documents and return per-document metadata/paths (beyond matrix views)
- Edit mappings per requirement (confirm/remove) from the UI
- Manual evidence CRUD (drag-drop evidence + highlight persistence)
- Job API for long-running operations (progress + cancel)

---

## AI Agent

### Overview

The AI agent is a conversational assistant embedded in the web application via a chat panel. It can:

1. **Explain** - Answer questions about requirements, methodology, evidence
2. **Find** - Search documents for specific information
3. **Extract** - Run automated evidence extraction on demand
4. **Suggest** - Recommend which documents to check for a requirement
5. **Automate** - Run multi-step workflows (e.g., "extract evidence for all GHG requirements")

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AI AGENT ARCHITECTURE                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FRONTEND (Chat Panel)                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  User: "Why is REQ-005 marked as partial?"                            │ │
│  │                                                                       │ │
│  │  Agent: "REQ-005 requires a monitoring protocol with specific         │ │
│  │  sampling dates. I found one snippet mentioning 'annual monitoring'   │ │
│  │  but it lacks the exact dates required by the methodology.            │ │
│  │                                                                       │ │
│  │  I can search the monitoring_report.pdf for sampling dates if you     │ │
│  │  want. [Search Now]"                                                  │ │
│  │                                                                       │ │
│  │  [____________________________________] [Send]                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              ▼                                              │
│  BACKEND (Agent Service)                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │ │
│  │  │   Claude    │───▶│   Tools     │───▶│   MCP       │              │ │
│  │  │   (LLM)     │    │   Router    │    │   Server    │              │ │
│  │  └─────────────┘    └─────────────┘    └─────────────┘              │ │
│  │         │                                      │                      │ │
│  │         │           Available Tools:           │                      │ │
│  │         │           • search_documents         │                      │ │
│  │         │           • extract_evidence         │                      │ │
│  │         │           • explain_requirement      │                      │ │
│  │         │           • run_validation           │                      │ │
│  │         │           • get_session_status       │                      │ │
│  │         │           • navigate_to_page         │                      │ │
│  │         ▼                                      ▼                      │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │                    Session Context                              │ │ │
│  │  │  • Current session state                                        │ │ │
│  │  │  • Focused requirement                                          │ │ │
│  │  │  • Visible document + page                                      │ │ │
│  │  │  • User role (reviewer/proponent/admin)                         │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Agent Modes by User Role

| Role | Agent Capabilities |
|------|-------------------|
| **Reviewer** | Full access: explain, search, extract, validate, automate |
| **Proponent** | Limited: explain revision requests, suggest what to upload, answer methodology questions |
| **Admin** | Reviewer access + metrics queries, bulk operations |

### Guardrails (Recommended)

- **No autonomous writes:** the agent may propose actions, but the UI must require explicit user confirmation for any state change.
- **Read-first behavior:** prefer read-only tools (search/explain/summarize) before triggering expensive mutations (extract/validate/report).
- **Audit clarity:** log suggested actions separately (actor=`agent`) and attribute executed writes to the authenticated user.
- **Role-aware redaction:** the proponent-facing agent must never access internal notes, evidence confidence, or reviewer deliberations.

### Agent Tools

```python
# Agent tool definitions (pseudo-code)

@tool
def search_documents(query: str, document_ids: list[str] | None = None) -> list[SearchResult]:
    """Search document content for specific information."""
    # MVP: keyword search over extracted markdown (fast/hq); vector search later if needed
    pass

@tool
def extract_evidence(requirement_id: str, document_ids: list[str] | None = None) -> list[EvidenceSnippet]:
    """Extract evidence for a specific requirement from documents."""
    # Wraps existing LLM extractor
    pass

@tool
def explain_requirement(requirement_id: str) -> str:
    """Explain what a requirement means and what evidence is needed."""
    # Uses methodology context + requirement text
    pass

@tool
def explain_confidence(snippet_id: str) -> str:
    """Explain why an evidence snippet has its confidence score."""
    # Retrieves stored confidence_reason or generates explanation
    pass

@tool
def run_validation(validation_type: str) -> ValidationResult:
    """Run a specific cross-validation check."""
    # Wraps existing validation tools
    pass

@tool
def get_session_status() -> SessionSummary:
    """Get current session progress and statistics."""
    pass

@tool
def navigate_to(document_id: str, page: int) -> None:
    """Navigate the document viewer to a specific page."""
    # Sends event to frontend via WebSocket or polling
    pass

@tool
def link_evidence(snippet_id: str, requirement_id: str) -> None:
    """Link an evidence snippet to a requirement."""
    pass

@tool
def set_requirement_status(requirement_id: str, status: str, reason: str) -> None:
    """Set the status of a requirement with a reason."""
    pass
```

### Conversation Examples

**Example 1: Explanation**
```
User: Why is REQ-005 marked as partial?

Agent: REQ-005 requires documentation of a monitoring protocol including
specific sampling dates.

I found 1 evidence snippet from project_plan.pdf (page 8) that says
"Monitoring will occur annually" - but this is vague and doesn't include
the specific dates required by the methodology.

To mark this as Covered, you need evidence showing:
- Exact sampling dates (e.g., "March 15, 2024")
- Reference to the methodology's sampling requirements

Would you like me to search the monitoring report for sampling dates?
```

**Example 2: Automated Search**
```
User: Find all mentions of sampling dates across all documents

Agent: I'll search all 7 documents for sampling date references...

Found 4 mentions:
1. baseline_report.pdf, p.12: "Soil samples collected on 2024-03-15"
2. monitoring_report.pdf, p.3: "Sampling schedule: March and September 2024"
3. monitoring_report.pdf, p.7: "Follow-up sampling completed 2024-09-20"
4. project_plan.pdf, p.8: "Annual sampling during crediting period"

The most relevant for REQ-005 appears to be #1 and #2.
Would you like me to link these to REQ-005?
```

**Example 3: Bulk Automation**
```
User: Extract evidence for all GHG Accounting requirements

Agent: I'll extract evidence for the 5 GHG Accounting requirements
(REQ-004 through REQ-008)...

[Progress: ████████████░░░░░░░░ 60%]
Processing REQ-006: Uncertainty quantification...

Done! Results:
- REQ-004 Baseline calculation: 3 snippets found (confidence: 0.89)
- REQ-005 Monitoring protocol: 2 snippets found (confidence: 0.67)
- REQ-006 Uncertainty: 1 snippet found (confidence: 0.72)
- REQ-007 Leakage: 0 snippets found ⚠️
- REQ-008 Permanence: 2 snippets found (confidence: 0.85)

REQ-007 needs manual review - no leakage assessment found in documents.
```

**Example 4: Proponent Help**
```
User (Proponent): I received a revision request but I don't understand
what's being asked for

Agent: The reviewer requested clarification on the soil sampling date.

The issue: Your monitoring report mentions "annual monitoring" but doesn't
specify the exact date when soil samples were collected.

To resolve this, you should upload documentation showing:
- The specific date(s) of soil sampling
- Who conducted the sampling (lab name or certifying body)
- Reference to the methodology's sampling protocol

Do you have a sampling schedule or lab report you can upload?
```

### API Endpoints for Agent

```
POST /sessions/{session_id}/agent/chat
Body: {
  "message": "Why is REQ-005 marked as partial?",
  "context": {
    "focused_requirement": "REQ-005",
    "visible_document": "baseline_report.pdf",
    "visible_page": 12
  }
}
Response: {
  "response": "REQ-005 requires...",
  "actions": [
    {
      "type": "suggestion",
      "label": "Search monitoring report",
      "action": "search_documents",
      "params": { "query": "sampling date", "document_ids": ["doc_002"] }
    }
  ],
  "sources": [
    { "document": "project_plan.pdf", "page": 8, "snippet": "..." }
  ]
}

GET /sessions/{session_id}/agent/history
Response: {
  "messages": [
    { "role": "user", "content": "...", "timestamp": "..." },
    { "role": "assistant", "content": "...", "timestamp": "..." }
  ]
}
```

---

## API Extensions

### New Endpoints for Web App

```
# Templates (for batch processing)
POST   /templates                    # Create template
GET    /templates                    # List templates
GET    /templates/{id}               # Get template details
POST   /templates/{id}/versions      # Create a new immutable template version
DELETE /templates/{id}               # Delete template
POST   /templates/{id}/projects      # Batch create projects from template

# Workspace (missing today; required for the web UI)
GET    /sessions/{id}/workspace                  # One-shot workspace hydration (recommended)
GET    /sessions/{id}/documents                 # List documents + metadata for viewer/sidebar
GET    /sessions/{id}/search?query=...          # MVP: keyword search over extracted markdown
POST   /sessions/{id}/mappings/{requirement_id} # Confirm/set mapping for one requirement
DELETE /sessions/{id}/mappings/{requirement_id}/{doc_id} # Remove one doc from a requirement
POST   /sessions/{id}/evidence/manual           # Create manual/drag-drop evidence with highlight anchor
GET    /sessions/{id}/evidence/manual           # List manual evidence (scratchpad + assigned)
DELETE /sessions/{id}/evidence/manual/{clip_id} # Remove manual evidence
GET    /sessions/{id}/validation                # Read validation.json (for fact sheets)
POST   /sessions/{id}/complete                  # Finalize + lock session (Stage 8)

# Uploads (web UI friendly)
POST   /sessions/{id}/upload/multipart          # multipart/form-data (avoid base64 for web)

# Google Drive Integration (preferred over manual upload)
GET    /gdrive/folders                          # List accessible folders
GET    /gdrive/folders/{folder_id}/files        # List files in folder
POST   /sessions/{id}/import/gdrive             # Import files from Google Drive to session
       Body: { "file_ids": ["...", "..."] }

# Notifications
POST   /notifications/email                     # Send email via Mailjet
GET    /users/{id}/notifications                # List in-app notifications
PATCH  /users/{id}/notifications/{nid}/read     # Mark notification as read

# Jobs (for long-running operations)
GET    /jobs/{job_id}                # Get job status
DELETE /jobs/{job_id}                # Cancel job

# Agent
POST   /sessions/{id}/agent/chat     # Send message to agent
GET    /sessions/{id}/agent/history  # Get conversation history

# Binary file serving
GET    /sessions/{id}/documents/{doc_id}/content  # Stream PDF binary
```

### Workspace Snapshot Endpoint (Recommended)

The frontend will be dramatically simpler (and less error-prone) if it can hydrate the entire workspace with one request.

```
GET /sessions/{id}/workspace
Response: {
  "session": {...},              # session.json
  "documents": {...},            # documents.json
  "checklist": {...},            # requirements for the methodology (read-only)
  "mappings": {...},             # mappings.json
  "evidence_ai": {...},          # evidence.json (regeneratable)
  "evidence_manual": {...},      # manual_evidence.json (never regenerated)
  "annotations": {...},          # annotations.json
  "revisions": {...},            # revisions.json
  "determination": {...},        # determination.json
  "audit_summary": {...},        # derived from audit_log.json
  "artifacts": {...}             # freshness flags (from session.json)
}
```

Practical add-ons:
- `?include=` and `?exclude=` for payload control.
- `ETag` headers so the UI can revalidate cheaply and avoid unnecessary refreshes.

### API Client Generation

Generate TypeScript types from OpenAPI spec:

```bash
npx openapi-typescript http://localhost:8080/openapi.json -o src/lib/api/schema.ts
```

Use with openapi-fetch for type-safe API calls:

```typescript
import createClient from 'openapi-fetch';
import type { paths } from './schema';

const client = createClient<paths>({ baseUrl: '/api' });

const { data, error } = await client.GET('/sessions/{session_id}', {
  params: { path: { session_id: 'abc123' } }
});
```

---

## Google Drive Integration

### Overview

Reviewers already use a shared Google Drive for project documents. Connecting directly to Google Drive minimizes manual uploads and keeps documents in their natural location.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GOOGLE DRIVE INTEGRATION                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User Flow:                                                                 │
│  1. Reviewer clicks "Import from Google Drive"                              │
│  2. Folder picker shows accessible folders                                  │
│  3. Reviewer selects project folder or individual files                     │
│  4. Backend downloads files to session uploads/                             │
│  5. Document discovery runs automatically                                   │
│                                                                             │
│  Benefits:                                                                  │
│  • No manual download/upload cycle                                          │
│  • Documents stay in familiar location for proponents                       │
│  • Can refresh from Drive if proponent updates a file                       │
│                                                                             │
│  Authentication:                                                            │
│  • Use same Google OAuth as sign-in                                         │
│  • Request Drive read-only scope during auth                                │
│  • Only access folders explicitly shared with the user                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# Google Drive service (using google-api-python-client)
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class GoogleDriveService:
    def __init__(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    def list_folders(self) -> list[dict]:
        """List folders accessible to user."""
        results = self.service.files().list(
            q="mimeType='application/vnd.google-apps.folder'",
            fields="files(id, name, parents)"
        ).execute()
        return results.get('files', [])

    def list_files(self, folder_id: str) -> list[dict]:
        """List files in a folder."""
        results = self.service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/pdf'",
            fields="files(id, name, mimeType, size, modifiedTime)"
        ).execute()
        return results.get('files', [])

    def download_file(self, file_id: str, destination: Path) -> None:
        """Download a file to local path."""
        request = self.service.files().get_media(fileId=file_id)
        with open(destination, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
```

---

## Notifications

### Overview

Notifications keep proponents and reviewers informed about review progress. Uses Mailjet for email (already configured) plus in-app notifications.

### Notification Events

| Event | Recipients | Email | In-App |
|-------|------------|-------|--------|
| Revision requested | Proponent | Yes | Yes |
| Revision response uploaded | Reviewer | Yes | Yes |
| Review completed | Proponent | Yes | Yes |
| Project assigned | Reviewer | Yes | Yes |
| Approaching deadline | Reviewer, Admin | Yes | Yes |

### Email Templates (Mailjet)

```python
# Notification service
from mailjet_rest import Client

class NotificationService:
    def __init__(self):
        self.mailjet = Client(
            auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY)
        )

    def send_revision_request(self, proponent_email: str, project_name: str, requirement: str, message: str):
        """Notify proponent of revision request."""
        self.mailjet.send.create(data={
            'Messages': [{
                'From': {'Email': 'registry@regen.network', 'Name': 'Regen Registry'},
                'To': [{'Email': proponent_email}],
                'Subject': f'Revision Requested: {project_name}',
                'HTMLPart': f'''
                    <h2>Revision Requested</h2>
                    <p>A revision has been requested for <strong>{project_name}</strong>.</p>
                    <p><strong>Requirement:</strong> {requirement}</p>
                    <p><strong>Message:</strong> {message}</p>
                    <p><a href="https://registry.regen.network/revisions/...">View and Respond</a></p>
                '''
            }]
        })
```

### In-App Notifications

```typescript
interface Notification {
  id: string;
  user_id: string;
  type: "revision_requested" | "revision_responded" | "review_completed" | "project_assigned";
  title: string;
  message: string;
  link: string;
  read: boolean;
  created_at: string;
}
```

---

## Data Models

### Session (Extended)

```typescript
interface Session {
  session_id: string;
  created_at: string;
  updated_at: string;
  status: "active" | "completed" | "archived";

  // Template support
  parent_template_id: string | null;
  template_version_id: string | null; // Immutable template version reference

  project_metadata: {
    project_name: string;
    project_id: string | null;
    methodology: string;
    proponent: string | null;
    crediting_period: string | null;
    cluster_id: string | null;  // For batch grouping
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

  // Derived artifact freshness (prevents silent inconsistencies)
  artifacts: {
    versions: {
      documents: number;
      mappings: number;
      evidence_ai: number;
      evidence_manual: number;
      validation: number;
      report: number;
    };
    stale: {
      mappings: boolean;
      evidence_ai: boolean;
      validation: boolean;
      report: boolean;
    };
    derived_from: {
      mappings_from_documents: number;
      evidence_ai_from_mappings: number;
      validation_from_evidence_ai: number;
      report_from_validation: number;
    };
  };

  // RBAC
  assigned_reviewer: string | null;
  proponent_email: string | null;
}
```

### Evidence Snippet (Extended)

**Important:** AI-generated evidence and manual/drag-drop evidence should not share the same storage file.
- **AI extraction** writes `evidence.json` and may regenerate it freely.
- **Manual evidence** (scratchpad + drag-drop highlights) should live in a separate file (e.g., `manual_evidence.json`) to prevent accidental overwrite.

```typescript
interface EvidenceSnippet {
  snippet_id: string;
  text: string;
  document_id: string;
  document_name: string;
  page: number | null;
  section: string | null;

  // Confidence
  confidence: number;
  confidence_reason: string | null;  // AI explanation

  // Extraction metadata
  extraction_method: "keyword" | "llm" | "manual" | "drag_drop";
  extracted_at: string;
  extracted_by: string | null;  // User ID for manual/drag_drop

  // Highlight coordinates (see Evidence Anchoring section)
  highlight_coordinates: HighlightCoords | null;
}
```

### Manual Evidence (Scratchpad + Drag-Drop)

```typescript
interface ManualEvidenceClip {
  clip_id: string;
  text: string;
  document_id: string;
  document_name: string;
  page: number | null;
  highlight_coordinates: HighlightCoords | null;

  // Scratchpad assignment
  assigned_requirement_id: string | null;

  // Attribution
  created_at: string;
  created_by: string; // user_id or email
  source: "drag_drop" | "manual";
}
```

---

## Evidence Anchoring

### Three-Layer Approach

Evidence highlights must persist across page reloads and screen sizes.

**Layer 1: Bounding Box Coordinates (Primary)**
```typescript
interface HighlightCoords {
  page: number;
  boundingRect: {
    x1: number;  // PDF points from origin
    y1: number;
    x2: number;
    y2: number;
    width: number;
    height: number;
  };
  rects: Array<{  // For multi-line selections
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  }>;
}
```

**Layer 2: Content Hash (Fallback)**
```typescript
{
  textHash: string;         // SHA-256 of exact text
  contextBefore: string;    // ~20 chars before
  contextAfter: string;     // ~20 chars after
}
```

**Layer 3: Page + Text Reference (Manual Fallback)**

Always stored as baseline - even if visual highlighting fails, user can navigate to page and find text.

### Recovery Algorithm

1. Try bounding box coordinates
2. If text at coordinates doesn't match hash, search page for text
3. Use context to disambiguate multiple matches
4. If found, update stored coordinates (self-healing)
5. If not found, show "Evidence may have moved" warning

---

## Long-Running Operations

Evidence extraction and cross-validation can take 30-60 seconds. Model as background jobs:

```typescript
interface Job {
  job_id: string;
  type: "evidence_extraction" | "cross_validation" | "report_generation" | "batch_create";
  status: "queued" | "running" | "completed" | "failed";
  progress: number;  // 0-100
  started_at: string | null;
  completed_at: string | null;
  result?: any;
  error?: string;
}
```

### API Pattern

```
POST /sessions/{id}/evidence/extract
Response: { "job_id": "job_123", "status": "queued" }

GET /jobs/job_123
Response: { "job_id": "job_123", "status": "running", "progress": 45 }
```

### Frontend Polling

Poll with exponential backoff (500ms → 5s max). Show progress bar during operation.

### MVP vs Production Note

- **MVP:** it’s acceptable for evidence/validation/report endpoints to run synchronously with a spinner, while PDF conversion uses `GET /sessions/{id}/conversion-status`.
- **Production:** if job IDs are exposed to the frontend, job state should be persisted (file or DB). In-memory jobs will break across server restarts and deployments.

---

## PDF File Serving

Serve PDFs as binary streams, not base64 in JSON:

```python
from fastapi.responses import FileResponse

@app.get("/sessions/{session_id}/documents/{doc_id}/content")
async def get_document_content(session_id: str, doc_id: str):
    document = await get_document(session_id, doc_id)
    return FileResponse(
        path=document.file_path,
        media_type="application/pdf",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=31536000, immutable"
        }
    )
```

Benefits:
- PDF.js can stream pages progressively
- Range requests enable fast page jumps
- Browser caching works correctly

---

## Authentication

**Approach:** Sign in with Google (reuse the same Regen Google Workspace identity model as `regen-koi-mcp`).

- **Frontend:** Auth.js/NextAuth Google provider, session cookie for the web app
- **Backend:** FastAPI auth dependency validates the session/JWT and attaches `user_id`, `user_email`, and `role`
- **Role assignment:** reviewer/admin via allowlist (e.g., `@regen.network`), proponent via per-session invitation/ownership

---

## RBAC & Permissions

### Role Definitions

| Role | Description |
|------|-------------|
| **Reviewer** | Conducts reviews, extracts evidence, makes determinations |
| **Proponent** | Submits projects, responds to revisions, views public status |
| **Admin** | Manages users, templates, assigns reviews, exports metrics |

### Permission Matrix

| Action | Reviewer | Proponent | Admin |
|--------|----------|-----------|-------|
| Create session | Yes | No | Yes |
| View own sessions | Yes | Limited | Yes |
| View all sessions | No | No | Yes |
| Upload documents | Yes | Own project | Yes |
| Extract/link evidence | Yes | No | Yes |
| View evidence | Yes | No | Yes |
| Add internal note | Yes | No | Yes |
| View internal notes | Yes | No | Yes |
| Send revision request | Yes | No | Yes |
| Respond to revision | No | Yes | Yes |
| Generate report | Yes | No | Yes |
| View final report | Yes | Yes | Yes |
| Create template | No | No | Yes |
| Use template | Yes | No | Yes |
| Assign reviewer | No | No | Yes |

### Proponent View Restrictions

Proponents can see:
- Project name and metadata
- Overall review stage
- Documents they uploaded
- Revision requests (public comments only)
- Final determination and report

Proponents cannot see:
- Individual requirement status
- Evidence snippets and confidence scores
- Internal notes
- Cross-validation results
- Draft reports

---

## Data Handling & Compliance

### Storage Structure

```
{DATA_DIR}/
├── sessions/{session_id}/          # `REGISTRY_REVIEW_SESSIONS_DIR` (defaults to XDG `settings.sessions_dir`)
│   ├── session.json
│   ├── documents.json
│   ├── mappings.json
│   ├── evidence.json
│   ├── manual_evidence.json        # scratchpad + drag-drop clips (never regenerated)
│   ├── validation.json
│   ├── annotations.json            # overrides + internal notes
│   ├── revisions.json
│   ├── determination.json
│   ├── audit_log.json
│   ├── report.md
│   ├── report.json
│   ├── snapshots/
│   └── uploads/
└── templates/{template_id}/        # New for web app (not implemented yet)
    ├── template.json               # logical template metadata
    └── versions/{version_id}/      # immutable version snapshots
        ├── template_version.json
        ├── shared_docs/
        ├── evidence.json
        └── manual_evidence.json
```

### Retention Policy

| Data Type | Retention |
|-----------|-----------|
| Active sessions | Indefinite |
| Completed sessions | 7 years |
| Deleted sessions | 90 days soft delete |
| Audit logs | 7 years |
| Templates | Indefinite |

### Audit Trail

Every state-changing action is logged:

```typescript
interface AuditEntry {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  action: string;  // e.g., "evidence.linked", "requirement.status_changed"
  session_id: string;
  entity_type: string;
  entity_id: string;
  previous_value?: any;
  new_value?: any;
}
```
