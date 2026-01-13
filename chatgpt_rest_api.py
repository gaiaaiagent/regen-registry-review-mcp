#!/usr/bin/env python3
"""REST API wrapper for ChatGPT Custom GPT integration.

This provides HTTP endpoints that wrap the MCP server's functionality,
allowing ChatGPT to interact via Custom GPT Actions.
"""

import sys
import uuid
import secrets
import base64
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI, HTTPException, File, UploadFile, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import uvicorn

from registry_review_mcp.tools import (
    session_tools,
    document_tools,
    mapping_tools,
    evidence_tools,
    upload_tools,
    human_review_tools,
)
from registry_review_mcp.config.settings import settings

# Start session monitoring if enabled
if settings.monitor_sessions:
    from registry_review_mcp.utils.session_monitor import start_session_monitor
    start_session_monitor(settings.sessions_dir)

# ============================================================================
# Status Derivation Helper
# ============================================================================


def get_derived_status(workflow_progress: dict | None) -> str:
    """Derive human-readable status from workflow_progress.

    The session.status field is set once at creation and never updated,
    while workflow_progress tracks actual stage completion. This function
    returns a status string that reflects the actual progress.
    """
    if not workflow_progress:
        return "Initialized"

    # Check stages in reverse order (most advanced first)
    stages = [
        ("completion", "Completed"),
        ("human_review", "In Human Review"),
        ("report_generation", "Report Generated"),
        ("cross_validation", "Validated"),
        ("evidence_extraction", "Evidence Extracted"),
        ("requirement_mapping", "Requirements Mapped"),
        ("document_discovery", "Documents Discovered"),
        ("initialize", "Initialized"),
    ]

    for stage_key, status_label in stages:
        if workflow_progress.get(stage_key) == "completed":
            return status_label

    return "Initialized"


def apply_derived_status(session: dict) -> dict:
    """Apply derived status to a session dict, replacing the static status field."""
    if "workflow_progress" in session:
        session["status"] = get_derived_status(session["workflow_progress"])
    return session


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Registry Review API",
    description="Carbon credit project registry review tools for ChatGPT",
    version="1.0.0",
    servers=[
        {"url": "https://regen.gaiaai.xyz/api/registry", "description": "Production endpoint"}
    ],
)

# Enable CORS for ChatGPT and browser uploads
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chat.openai.com", "https://chatgpt.com", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for pending uploads (use Redis/database in production)
pending_uploads: dict[str, dict] = {}


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateSessionRequest(BaseModel):
    project_name: str = Field(..., description="Name of the project to review")
    methodology: str = Field(
        default="soil-carbon-v1.2.2",
        description="Methodology identifier (default: soil-carbon-v1.2.2)",
    )
    project_id: str | None = Field(None, description="Optional project ID (e.g., C06-4997)")


class SessionResponse(BaseModel):
    session_id: str
    project_name: str
    methodology: str
    created_at: str
    requirements_total: int
    message: str


class DiscoverRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to discover documents for")


class MapRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to map requirements for")


class EvidenceRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to extract evidence for")


class UploadFileRequest(BaseModel):
    filename: str = Field(..., description="Name of the file being uploaded")
    content_base64: str = Field(..., description="Base64-encoded file content")


class StartExampleReviewRequest(BaseModel):
    example_name: str = Field(..., description="Name of example project (e.g., '22-23')")
    project_name: str | None = Field(None, description="Custom project name (optional)")


class StartReviewWithFilesRequest(BaseModel):
    project_name: str = Field(..., description="Name of the project to review")
    files: list[UploadFileRequest] = Field(..., description="List of files to upload (base64 encoded)")
    methodology: str = Field(default="soil-carbon-v1.2.2", description="Methodology identifier")


class GenerateUploadUrlRequest(BaseModel):
    project_name: str = Field(..., description="Name of the project to review")
    methodology: str = Field(default="soil-carbon-v1.2.2", description="Methodology identifier")
    session_id: str | None = Field(None, description="Existing session ID to add files to (optional)")


class SetOverrideRequest(BaseModel):
    requirement_id: str = Field(..., description="Requirement ID (e.g., 'REQ-001')")
    override_status: str = Field(
        ..., description="Decision status: approved, rejected, needs_revision, conditional, pending"
    )
    notes: str | None = Field(None, description="Optional notes explaining the decision")
    reviewer: str = Field(default="user", description="Identifier of the reviewer")


class AddAnnotationRequest(BaseModel):
    requirement_id: str = Field(..., description="Requirement ID (e.g., 'REQ-001')")
    note: str = Field(..., description="The annotation text")
    annotation_type: str = Field(
        default="note", description="Type: note, question, concern, clarification"
    )
    reviewer: str = Field(default="user", description="Identifier of the reviewer")


class SetDeterminationRequest(BaseModel):
    determination: str = Field(
        ..., description="Final decision: approve, conditional, reject, hold"
    )
    notes: str = Field(..., description="Required explanation of the determination")
    conditions: str | None = Field(None, description="For conditional approvals")
    reviewer: str = Field(default="user", description="Identifier of the reviewer")


class RevisionRequest(BaseModel):
    requirement_id: str = Field(..., description="Requirement ID (e.g., 'REQ-001')")
    description: str = Field(..., description="What revision is needed from proponent")
    priority: str = Field(default="medium", description="Priority: critical, high, medium, low")
    requested_by: str = Field(default="user", description="Identifier of the requester")


class ResolveRevisionRequest(BaseModel):
    resolution_notes: str = Field(..., description="Notes about how the revision was resolved")
    resolved_by: str = Field(default="user", description="Identifier of the resolver")


# ============================================================================
# Agent Chat Models
# ============================================================================


class AgentContext(BaseModel):
    focused_requirement_id: Optional[str] = Field(None, description="Currently focused requirement ID")
    visible_document_id: Optional[str] = Field(None, description="Currently visible document ID")
    visible_page: Optional[int] = Field(None, description="Currently visible page number")


class AgentChatRequest(BaseModel):
    message: str = Field(..., description="User message to the agent")
    context: Optional[AgentContext] = Field(None, description="Current workspace context")


class AgentAction(BaseModel):
    type: str = Field(..., description="Action type: navigate, extract, validate, etc.")
    label: str = Field(..., description="Button label for UI")
    params: dict = Field(default_factory=dict, description="Action parameters")


class AgentSource(BaseModel):
    document_id: str = Field(..., description="Document ID")
    document_name: str = Field(..., description="Document filename")
    page: Optional[int] = Field(None, description="Page number")
    text: Optional[str] = Field(None, description="Relevant excerpt")


class AgentChatResponse(BaseModel):
    message: str = Field(..., description="Agent's text response")
    actions: List[AgentAction] = Field(default_factory=list, description="Proposed actions as buttons")
    sources: List[AgentSource] = Field(default_factory=list, description="Referenced documents/pages")


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Registry Review API",
        "version": "1.0.0",
        "description": "Carbon credit project registry review tools",
        "endpoints": {
            "sessions": "/sessions",
            "examples": "/examples",
            "discover": "/sessions/{session_id}/discover",
            "map": "/sessions/{session_id}/map",
            "evidence": "/sessions/{session_id}/evidence",
        },
    }


@app.post("/sessions", response_model=SessionResponse, summary="Create review session")
async def create_session(request: CreateSessionRequest):
    """Create a new registry review session.

    This initializes a session with project metadata. Documents can be added later.
    """
    try:
        result = await session_tools.create_session(
            project_name=request.project_name,
            methodology=request.methodology,
            project_id=request.project_id,
        )
        return SessionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions", summary="List all sessions")
async def list_sessions():
    """List all registry review sessions.

    Returns a list of all sessions with their current status.
    Status is derived from workflow_progress to reflect actual progress.
    """
    try:
        sessions = await session_tools.list_sessions()
        # Apply derived status to each session
        sessions = [apply_derived_status(s) for s in sessions]
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}", summary="Get session details")
async def get_session(session_id: str):
    """Get detailed information about a specific session.

    Returns complete session state including workflow progress and documents.
    Status is derived from workflow_progress to reflect actual progress.
    """
    try:
        session = await session_tools.load_session(session_id)
        return apply_derived_status(session)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/examples", summary="List example projects")
async def list_examples():
    """List available example projects for testing.

    Returns a list of example projects that can be used to test the review workflow.
    """
    try:
        examples = await session_tools.list_example_projects()
        return examples
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/discover", summary="Discover documents")
async def discover_documents(session_id: str):
    """Discover and classify all documents in the project.

    Scans the project directory and classifies documents by type
    (monitoring plan, verification report, GIS data, etc.).
    """
    try:
        result = await document_tools.discover_documents(session_id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/map", summary="Map requirements to documents")
async def map_requirements(session_id: str):
    """Map registry requirements to discovered documents.

    Uses semantic matching to identify which documents address which
    checklist requirements.
    """
    try:
        result = await mapping_tools.map_all_requirements(session_id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/mapping-status", summary="Get mapping status")
async def get_mapping_status(session_id: str):
    """Get current requirement mapping status.

    Returns statistics about which requirements are mapped and coverage levels.
    """
    try:
        result = await mapping_tools.get_mapping_status(session_id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/mapping-matrix", summary="Get mapping matrix view")
async def get_mapping_matrix(session_id: str):
    """Get a visual matrix view of document-to-requirement mappings.

    Returns a structured matrix showing which documents map to which requirements,
    with confidence indicators and status. Use this to review mappings before
    proceeding to evidence extraction.
    """
    try:
        result = await mapping_tools.get_mapping_matrix(session_id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/confirm-all-mappings", summary="Confirm all mappings")
async def confirm_all_mappings(session_id: str):
    """Confirm all suggested mappings in bulk.

    Use this after reviewing the mapping matrix to accept all agent suggestions.
    This marks all suggested mappings as confirmed and enables evidence extraction.
    """
    try:
        result = await mapping_tools.confirm_all_mappings(session_id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/conversion-status", summary="Get PDF conversion status")
async def get_conversion_status(session_id: str):
    """Get PDF conversion status and progress.

    Returns comprehensive status of dual-track PDF extraction:
    - Fast extraction (PyMuPDF): immediate, 75-90% quality
    - High-quality extraction (Marker): background, 100% quality

    Includes progress percentages, ETAs, and per-document status.
    Use this to show users transparent progress during long conversions.
    """
    try:
        from registry_review_mcp.services.document_processor import get_conversion_status as get_status

        status = get_status(session_id)

        return {
            "session_id": status.session_id,
            "total_documents": status.total_documents,
            "pdfs_total": status.pdfs_total,
            "fast_complete": status.fast_complete,
            "hq_complete": status.hq_complete,
            "hq_converting": status.hq_converting,
            "hq_queued": status.hq_queued,
            "overall_progress": status.overall_progress,
            "estimated_completion": status.estimated_completion,
            "message": status.message,
            "documents": [
                {
                    "document_id": d.document_id,
                    "filename": d.filename,
                    "fast_status": d.fast_status,
                    "hq_status": d.hq_status,
                    "hq_progress": d.hq_progress,
                    "preferred_quality": d.preferred_quality,
                    "has_content": d.has_content,
                }
                for d in status.documents
            ],
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/evidence", summary="Extract evidence")
async def extract_evidence(session_id: str):
    """Extract evidence for all requirements from mapped documents.

    Analyzes documents and extracts specific evidence snippets with
    page citations for each requirement.
    """
    try:
        from registry_review_mcp.tools.evidence_tools import extract_all_evidence

        result = await extract_all_evidence(session_id)

        # Add workflow guidance for ChatGPT
        result["next_steps"] = {
            "recommended": {
                "action": "Run cross-validation",
                "endpoint": f"/sessions/{session_id}/validate",
                "description": "Check consistency across documents (dates, IDs, tenure claims)",
            },
            "optional": [
                {
                    "action": "Review evidence matrix",
                    "endpoint": f"/sessions/{session_id}/review-status",
                    "description": "Examine specific requirement evidence in detail",
                },
            ],
            "not_ready": [
                {
                    "action": "Generate report",
                    "reason": "Cross-validation must complete first",
                },
            ],
        }
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/evidence-matrix", summary="Get evidence matrix")
async def get_evidence_matrix(session_id: str):
    """Get structured evidence matrix for display.

    USE THIS ENDPOINT when user asks for "evidence matrix" or "checklist".
    This is the primary endpoint for viewing extracted evidence.

    Returns a standardized matrix with ALL columns:
    - requirement_id: Unique requirement identifier (e.g., REQ-001)
    - category: Requirement category (e.g., "Land Tenure")
    - status: Evidence status (covered/partial/missing)
    - confidence: Confidence score (0.0-1.0)
    - source_document: Document where evidence was found
    - page: Page number in source document
    - section: Section header where evidence appears
    - extracted_value: THE SPECIFIC VALUE for the registry checklist (e.g., "January 1, 2022", "Nicholas Denman")
    - validation_type: Type of validation (auto vs human judgment)
    - human_review_required: Whether human review is needed

    IMPORTANT: Always display ALL columns including 'extracted_value' which contains
    the specific answer to enter in the registry checklist's "Submitted Material" column.
    """
    try:
        from registry_review_mcp.utils.state import StateManager
        import json

        state_manager = StateManager(session_id)

        # Load evidence data
        evidence_path = state_manager.session_dir / "evidence.json"
        if not evidence_path.exists():
            raise HTTPException(
                status_code=400,
                detail="Evidence not yet extracted. Run evidence extraction first.",
            )

        with open(evidence_path) as f:
            evidence_data = json.load(f)

        # Load checklist for validation_type mapping
        session_data = state_manager.read_json("session.json")
        methodology = session_data.get("project_metadata", {}).get(
            "methodology", "soil-carbon-v1.2.2"
        )
        checklist_path = settings.get_checklist_path(methodology)

        validation_types = {}
        if checklist_path.exists():
            with open(checklist_path) as f:
                checklist = json.load(f)
            for req in checklist.get("requirements", []):
                validation_types[req["requirement_id"]] = req.get(
                    "validation_type", "manual"
                )

        # Build matrix rows
        matrix = []
        auto_validated = 0
        human_review_required = 0

        for req_evidence in evidence_data.get("evidence", []):
            req_id = req_evidence.get("requirement_id", "")
            validation_type = validation_types.get(req_id, "manual")
            is_auto = validation_type in [
                "document_presence",
                "cross_document",
                "date_alignment",
                "structured_field",
            ]

            if is_auto:
                auto_validated += 1
            else:
                human_review_required += 1

            # Get best evidence snippet for this requirement
            snippets = req_evidence.get("evidence_snippets", [])
            best_snippet = snippets[0] if snippets else None

            matrix.append(
                {
                    "requirement_id": req_id,
                    "category": req_evidence.get("category", ""),
                    "requirement_text": req_evidence.get("requirement_text", "")[:200],
                    "validation_type": validation_type,
                    "auto_validatable": is_auto,
                    "status": req_evidence.get("status", "missing"),
                    "confidence": req_evidence.get("confidence", 0.0),
                    "source_document": (
                        best_snippet.get("document_name", "") if best_snippet else ""
                    ),
                    "page": best_snippet.get("page") if best_snippet else None,
                    "section": best_snippet.get("section", "") if best_snippet else "",
                    "extracted_value": (
                        best_snippet.get("extracted_value", "") if best_snippet else ""
                    ),
                    "evidence_text": (
                        best_snippet.get("text", "")[:300] if best_snippet else ""
                    ),
                    "evidence_count": len(snippets),
                    "human_review_required": not is_auto,
                }
            )

        return {
            "session_id": session_id,
            "matrix": matrix,
            "summary": {
                "total_requirements": len(matrix),
                "auto_validatable": auto_validated,
                "human_review_required": human_review_required,
                "covered": sum(1 for r in matrix if r["status"] == "covered"),
                "partial": sum(1 for r in matrix if r["status"] == "partial"),
                "missing": sum(1 for r in matrix if r["status"] == "missing"),
                "coverage": evidence_data.get("overall_coverage", 0.0),
            },
            "columns": [
                "requirement_id",
                "category",
                "status",
                "confidence",
                "source_document",
                "page",
                "section",
                "extracted_value",
                "validation_type",
                "human_review_required",
            ],
            "display_hint": "ALWAYS render as table with ALL columns: ID | Category | Status | Confidence | Source | Page | Section | Value | Type | Review. The 'extracted_value' column contains the specific answer for the registry checklist.",
        }
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/validate", summary="Cross-validate evidence")
async def cross_validate(session_id: str):
    """Run cross-document validation checks.

    Stage 5: Validates consistency across all extracted evidence:
    - Date alignment (sampling vs imagery dates within 120 days)
    - Land tenure consistency (owner names, areas across documents)
    - Project ID validation (consistent across all documents)

    Returns validation results with pass/fail/warning status.
    """
    try:
        from registry_review_mcp.tools import validation_tools

        result = await validation_tools.cross_validate(session_id)

        # Add clear warning for zero-validation cases
        summary = result.get("summary", {})
        total_validations = summary.get("total_validations", 0)
        diagnostics = summary.get("extraction_diagnostics", {})

        if total_validations == 0:
            # Build explanation of why no validations ran
            reasons = []
            if diagnostics:
                if not diagnostics.get("date_validation_possible"):
                    reasons.append(
                        f"Date validation: {diagnostics.get('date_validation_reason', 'insufficient data')}"
                    )
                if not diagnostics.get("tenure_validation_possible"):
                    reasons.append(
                        f"Tenure validation: {diagnostics.get('tenure_validation_reason', 'insufficient data')}"
                    )
                if not diagnostics.get("project_id_validation_possible"):
                    reasons.append(
                        f"Project ID validation: {diagnostics.get('project_id_validation_reason', 'insufficient data')}"
                    )

            result["warning"] = {
                "status": "NO_VALIDATIONS_RAN",
                "message": "Zero automated validations were performed. This does NOT mean the documents are validated.",
                "reasons": reasons,
                "recommendation": "All requirements require human review when automated validation cannot extract structured data.",
            }

        # Add workflow guidance for ChatGPT
        result["next_steps"] = {
            "recommended": {
                "action": "Generate review report",
                "endpoint": f"/sessions/{session_id}/report",
                "description": "Create structured summary for registry submission",
            },
            "optional": [
                {
                    "action": "View evidence matrix",
                    "endpoint": f"/sessions/{session_id}/evidence-matrix",
                    "description": "See structured view of all evidence with validation status",
                },
                {
                    "action": "Review validation details",
                    "endpoint": f"/sessions/{session_id}/review-status",
                    "description": "Examine specific validation results",
                },
            ],
        }
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/report", summary="Generate review report")
async def generate_report(session_id: str, format: str = "markdown", request: Request = None):
    """Generate complete review report.

    Stage 6: Creates review report with:
    - Executive summary with coverage statistics
    - Per-requirement findings with evidence citations
    - Cross-validation results
    - Items flagged for human review

    Args:
        format: Output format - "markdown", "json", or "checklist" (default: markdown)
                "checklist" generates a populated registry submission form

    Returns report generation result with path to saved file.
    For checklist format, includes download_url for direct file download.
    """
    try:
        from registry_review_mcp.tools import report_tools

        result = await report_tools.generate_review_report(
            session_id=session_id,
            format=format,
        )

        # Add download URL for all file formats
        if request and format in ("markdown", "checklist", "docx"):
            # Use X-Forwarded-Host if available, otherwise fall back to Host header
            forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
            forwarded_proto = request.headers.get("x-forwarded-proto", "https")
            if forwarded_host:
                base_url = f"{forwarded_proto}://{forwarded_host}/api/registry"
            else:
                base_url = str(request.base_url).rstrip("/")

            if format == "markdown":
                result["download_url"] = f"{base_url}/sessions/{session_id}/report/download"
                result["download_instructions"] = (
                    f"Download your review report (Markdown): {result['download_url']}"
                )
            elif format == "checklist":
                result["download_url"] = f"{base_url}/sessions/{session_id}/checklist/download"
                result["download_instructions"] = (
                    f"Download your populated checklist (Markdown): {result['download_url']}"
                )
            else:  # docx
                result["download_url"] = f"{base_url}/sessions/{session_id}/checklist/download-docx"
                result["download_instructions"] = (
                    f"Download your populated checklist (Word): {result['download_url']}"
                )

        # Add workflow guidance for ChatGPT
        result["next_steps"] = {
            "recommended": {
                "action": "Human review",
                "endpoint": f"/sessions/{session_id}/review-status",
                "description": "Review flagged items and add expert annotations",
            },
            "optional": [
                {
                    "action": "Set requirement overrides",
                    "endpoint": f"/sessions/{session_id}/override",
                    "description": "Override agent assessments with expert judgment",
                },
                {
                    "action": "Request revisions from proponent",
                    "endpoint": f"/sessions/{session_id}/revisions",
                    "description": "Request additional documentation or clarification",
                },
            ],
            "final": {
                "action": "Set final determination",
                "endpoint": f"/sessions/{session_id}/determination",
                "description": "Record official decision (approve/conditional/reject/hold)",
            },
        }
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Report Download Endpoint
# ============================================================================


@app.get("/sessions/{session_id}/report/download", summary="Download report")
async def download_report(session_id: str):
    """Download the review report as Markdown.

    Returns the report.md file for direct download.
    Generate the report first with POST /sessions/{session_id}/report?format=markdown
    """
    try:
        from registry_review_mcp.utils.state import StateManager

        state_manager = StateManager(session_id)

        # Validate session exists first
        if not state_manager.exists():
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        report_path = state_manager.session_dir / "report.md"

        if not report_path.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Report not found. Generate it first with "
                    f"POST /sessions/{session_id}/report?format=markdown"
                ),
            )

        # Sanitize session_id for safe filename
        safe_id = "".join(c for c in session_id[:12] if c.isalnum() or c in "-_")

        return FileResponse(
            path=report_path,
            filename=f"report_{safe_id}.md",
            media_type="text/markdown",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/checklist/download", summary="Download checklist")
async def download_checklist(session_id: str):
    """Download the populated registry checklist.

    Returns the checklist.md file for direct download.
    Generate the checklist first with POST /sessions/{session_id}/report?format=checklist
    """
    try:
        from registry_review_mcp.utils.state import StateManager

        state_manager = StateManager(session_id)

        # Validate session exists first
        if not state_manager.exists():
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        checklist_path = state_manager.session_dir / "checklist.md"

        if not checklist_path.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Checklist not found. Generate it first with "
                    f"POST /sessions/{session_id}/report?format=checklist"
                ),
            )

        # Sanitize session_id for safe filename
        safe_id = "".join(c for c in session_id[:12] if c.isalnum() or c in "-_")

        return FileResponse(
            path=checklist_path,
            filename=f"checklist_{safe_id}.md",
            media_type="text/markdown",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/checklist/download-docx", summary="Download DOCX checklist")
async def download_checklist_docx(session_id: str):
    """Download the populated registry checklist as a Word document.

    Returns the checklist.docx file for direct download.
    Generate the checklist first with POST /sessions/{session_id}/report?format=docx
    System-generated text appears in blue.
    """
    try:
        from registry_review_mcp.utils.state import StateManager

        state_manager = StateManager(session_id)

        # Validate session exists first
        if not state_manager.exists():
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        docx_path = state_manager.session_dir / "checklist.docx"

        if not docx_path.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    f"DOCX checklist not found. Generate it first with "
                    f"POST /sessions/{session_id}/report?format=docx"
                ),
            )

        # Sanitize session_id for safe filename
        safe_id = "".join(c for c in session_id[:12] if c.isalnum() or c in "-_")

        return FileResponse(
            path=docx_path,
            filename=f"checklist_{safe_id}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Human Review Tools (Stage 7)
# ============================================================================


@app.get("/sessions/{session_id}/review-status", summary="Get review status")
async def get_review_status(session_id: str, requirement_id: str | None = None):
    """Get human review status for requirements.

    Returns overrides and annotations for all or specific requirements.
    """
    try:
        result = await human_review_tools.get_requirement_review_status(
            session_id=session_id,
            requirement_id=requirement_id,
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/override", summary="Set requirement override")
async def set_override(session_id: str, request: SetOverrideRequest):
    """Set human override status for a requirement.

    This allows the reviewer to override agent assessments with expert judgment.
    The override is recorded with timestamp and attribution.
    """
    try:
        result = await human_review_tools.set_requirement_override(
            session_id=session_id,
            requirement_id=request.requirement_id,
            override_status=request.override_status,
            notes=request.notes,
            reviewer=request.reviewer,
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}/override/{requirement_id}", summary="Clear override")
async def clear_override(session_id: str, requirement_id: str, reviewer: str = "user"):
    """Clear an override for a requirement.

    This removes the override status, reverting to agent assessment.
    """
    try:
        result = await human_review_tools.clear_requirement_override(
            session_id=session_id,
            requirement_id=requirement_id,
            reviewer=reviewer,
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/annotation", summary="Add annotation")
async def add_annotation(session_id: str, request: AddAnnotationRequest):
    """Add an annotation/note to a requirement.

    Annotations are separate from overrides and allow the reviewer to
    capture observations, questions, or concerns without making a decision.
    """
    try:
        result = await human_review_tools.add_annotation(
            session_id=session_id,
            requirement_id=request.requirement_id,
            note=request.note,
            annotation_type=request.annotation_type,
            reviewer=request.reviewer,
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/determination", summary="Get final determination")
async def get_determination(session_id: str):
    """Get the final determination for a session.

    Returns the current determination status and details.
    """
    try:
        result = await human_review_tools.get_final_determination(session_id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/determination", summary="Set final determination")
async def set_determination(session_id: str, request: SetDeterminationRequest):
    """Set the final determination for the review.

    This is the official decision on whether the project should be approved,
    conditionally approved, rejected, or placed on hold.
    """
    try:
        result = await human_review_tools.set_final_determination(
            session_id=session_id,
            determination=request.determination,
            notes=request.notes,
            conditions=request.conditions,
            reviewer=request.reviewer,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}/determination", summary="Clear determination")
async def clear_determination(session_id: str, reviewer: str = "user"):
    """Clear the final determination.

    This allows the determination to be reconsidered.
    """
    try:
        result = await human_review_tools.clear_final_determination(
            session_id=session_id,
            reviewer=reviewer,
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Revision Request Endpoints (Stage 7)
# ============================================================================


@app.get("/sessions/{session_id}/revisions", summary="Get revision requests")
async def get_revisions(session_id: str, status: str | None = None):
    """Get all revision requests for a session.

    Returns a list of revision requests with summary statistics.
    """
    try:
        result = await human_review_tools.get_revision_requests(
            session_id=session_id,
            status_filter=status,
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/revisions", summary="Request revision")
async def request_revision(session_id: str, request: RevisionRequest):
    """Request revision from project proponent for a requirement.

    Marks a requirement as pending proponent revision.
    """
    try:
        result = await human_review_tools.request_revision(
            session_id=session_id,
            requirement_id=request.requirement_id,
            description=request.description,
            priority=request.priority,
            requested_by=request.requested_by,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/revisions/summary", summary="Get revision summary")
async def get_revision_summary(session_id: str):
    """Generate a summary of revision requests for the project proponent.

    Returns a formatted markdown summary that can be shared.
    """
    try:
        result = await human_review_tools.generate_revision_summary(session_id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/revisions/{requirement_id}/resolve", summary="Resolve revision")
async def resolve_revision(session_id: str, requirement_id: str, request: ResolveRevisionRequest):
    """Mark a revision request as resolved.

    Call this after receiving and processing revised documents.
    """
    try:
        result = await human_review_tools.resolve_revision(
            session_id=session_id,
            requirement_id=requirement_id,
            resolution_notes=request.resolution_notes,
            resolved_by=request.resolved_by,
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/audit-log", summary="Get audit log")
async def get_audit_log(
    session_id: str,
    action_filter: str | None = None,
    actor_filter: str | None = None,
    limit: int = 100,
):
    """Get the audit log for a session.

    Returns a chronological list of all actions taken during the review,
    with optional filtering by action type or actor.
    """
    try:
        result = await human_review_tools.get_audit_log(
            session_id=session_id,
            action_filter=action_filter,
            actor_filter=actor_filter,
            limit=limit,
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}", summary="Delete session")
async def delete_session(session_id: str):
    """Delete a review session and all its data.

    Permanently removes the session and all associated files.
    """
    try:
        result = await session_tools.delete_session(session_id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Agent Chat Endpoint
# ============================================================================


def build_agent_tools_description() -> str:
    """Build description of available tools for the agent."""
    return """You have access to these tools for the registry review workspace:

1. search_documents(query: str) - Search across all session documents for relevant content
2. get_requirement_status(requirement_id: str) - Get current status and evidence for a requirement
3. navigate_to_page(document_id: str, page: int) - Suggest navigation to a specific page
4. summarize_gaps() - List all requirements that are missing evidence
5. get_document_list() - Get list of all documents in the session
6. explain_evidence(requirement_id: str) - Explain what evidence was found for a requirement

When you want to suggest an action to the user, respond with a JSON block containing proposed actions.
Actions will be shown as buttons the user can click to execute them."""


def build_session_context(session_data: dict, evidence_data: dict | None, documents_data: dict | None) -> str:
    """Build context string about the current session state."""
    project_name = session_data.get("project_metadata", {}).get("project_name", "Unknown")
    methodology = session_data.get("project_metadata", {}).get("methodology", "Unknown")
    workflow = session_data.get("workflow_progress", {})

    context_parts = [
        f"Project: {project_name}",
        f"Methodology: {methodology}",
        f"Workflow Status: {get_derived_status(workflow)}",
    ]

    if documents_data:
        docs = documents_data.get("documents", [])
        context_parts.append(f"Documents: {len(docs)} files")
        doc_names = [d.get("filename", "unknown") for d in docs[:5]]
        context_parts.append(f"Document names: {', '.join(doc_names)}")

    if evidence_data:
        evidence_list = evidence_data.get("evidence", [])
        covered = sum(1 for e in evidence_list if e.get("status") == "covered")
        partial = sum(1 for e in evidence_list if e.get("status") == "partial")
        missing = sum(1 for e in evidence_list if e.get("status") == "missing")
        context_parts.append(f"Evidence: {covered} covered, {partial} partial, {missing} missing")

    return "\n".join(context_parts)


def build_focused_context(context: AgentContext | None, evidence_data: dict | None, documents_data: dict | None) -> str:
    """Build context about what the user is currently looking at."""
    if not context:
        return "User context: Not specified"

    parts = []
    if context.focused_requirement_id:
        parts.append(f"Focused requirement: {context.focused_requirement_id}")
        if evidence_data:
            for ev in evidence_data.get("evidence", []):
                if ev.get("requirement_id") == context.focused_requirement_id:
                    parts.append(f"  Status: {ev.get('status', 'unknown')}")
                    parts.append(f"  Confidence: {ev.get('confidence', 0):.0%}")
                    snippets = ev.get("evidence_snippets", [])
                    if snippets:
                        parts.append(f"  Evidence snippets: {len(snippets)}")
                        for snip in snippets[:2]:
                            parts.append(f"    - {snip.get('document_name', 'unknown')}, page {snip.get('page', '?')}")
                    break

    if context.visible_document_id:
        parts.append(f"Viewing document: {context.visible_document_id}")
        if documents_data:
            for doc in documents_data.get("documents", []):
                if doc.get("document_id") == context.visible_document_id:
                    parts.append(f"  Filename: {doc.get('filename', 'unknown')}")
                    break

    if context.visible_page:
        parts.append(f"Current page: {context.visible_page}")

    return "\n".join(parts) if parts else "User context: General view"


def parse_agent_response(response_text: str, evidence_data: dict | None, documents_data: dict | None) -> AgentChatResponse:
    """Parse the agent's response and extract actions and sources."""
    message = response_text
    actions: List[AgentAction] = []
    sources: List[AgentSource] = []

    # Look for JSON action blocks in the response
    import re
    action_pattern = r'```json\s*(\{[^`]+\})\s*```'
    matches = re.findall(action_pattern, response_text, re.DOTALL)

    for match in matches:
        try:
            action_data = json.loads(match)
            if "actions" in action_data:
                for act in action_data["actions"]:
                    actions.append(AgentAction(
                        type=act.get("type", "unknown"),
                        label=act.get("label", "Action"),
                        params=act.get("params", {})
                    ))
            # Remove the JSON block from the message
            message = message.replace(f"```json\n{match}\n```", "").strip()
            message = message.replace(f"```json{match}```", "").strip()
        except json.JSONDecodeError:
            pass

    # Extract document references from the response
    if documents_data:
        doc_map = {d.get("filename", "").lower(): d for d in documents_data.get("documents", [])}
        for doc in documents_data.get("documents", []):
            filename = doc.get("filename", "")
            if filename.lower() in response_text.lower():
                sources.append(AgentSource(
                    document_id=doc.get("document_id", ""),
                    document_name=filename,
                    page=None,
                    text=None
                ))

    # Extract page references
    page_pattern = r'page\s+(\d+)'
    page_matches = re.findall(page_pattern, response_text, re.IGNORECASE)
    for page_num in page_matches:
        if sources:
            sources[0].page = int(page_num)
            break

    return AgentChatResponse(
        message=message,
        actions=actions,
        sources=sources
    )


@app.post("/sessions/{session_id}/agent/chat", response_model=AgentChatResponse, summary="Chat with AI agent")
async def agent_chat(session_id: str, request: AgentChatRequest):
    """Conversational AI agent for the review workspace.

    Receives user message plus context (focused requirement, visible document/page).
    Calls Claude API with session-aware tools.
    Returns response with proposed actions that the user can execute.

    This is a human-in-the-loop design: the agent proposes actions, but the user
    must confirm before any action is executed.
    """
    from anthropic import AsyncAnthropic

    try:
        state_manager = StateManager(session_id)
        session_data = state_manager.read_json("session.json")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Load evidence and documents if available
    evidence_data = None
    documents_data = None

    try:
        evidence_data = state_manager.read_json("evidence.json")
    except FileNotFoundError:
        pass

    try:
        documents_data = state_manager.read_json("documents.json")
    except FileNotFoundError:
        pass

    # Build system prompt with session context
    session_context = build_session_context(session_data, evidence_data, documents_data)
    focused_context = build_focused_context(request.context, evidence_data, documents_data)
    tools_description = build_agent_tools_description()

    system_prompt = f"""You are an AI assistant helping a carbon credit registry reviewer analyze project documents.

CURRENT SESSION STATE:
{session_context}

USER'S CURRENT VIEW:
{focused_context}

AVAILABLE TOOLS:
{tools_description}

GUIDELINES:
1. Be helpful and concise. Focus on what the user is asking about.
2. Reference specific documents and page numbers when discussing evidence.
3. When suggesting actions, include a JSON block with the action details.
4. For navigation suggestions, use: {{"actions": [{{"type": "navigate", "label": "View in Document", "params": {{"document_id": "...", "page": N}}}}]}}
5. For validation actions, use: {{"actions": [{{"type": "validate", "label": "Run Validation", "params": {{}}}}]}}
6. For extraction actions, use: {{"actions": [{{"type": "extract", "label": "Extract Evidence", "params": {{"requirement_id": "..."}}}}]}}
7. Keep responses focused and actionable for a professional reviewer.
8. If asked about requirements, reference their IDs (e.g., REQ-001, REQ-002).
9. When evidence is found, mention the confidence level and source document."""

    # Build messages with evidence context if discussing specific requirements
    user_message = request.message

    if request.context and request.context.focused_requirement_id and evidence_data:
        req_id = request.context.focused_requirement_id
        for ev in evidence_data.get("evidence", []):
            if ev.get("requirement_id") == req_id:
                snippets = ev.get("evidence_snippets", [])
                if snippets:
                    evidence_context = f"\n\nEvidence for {req_id}:\n"
                    for snip in snippets[:3]:
                        evidence_context += f"- {snip.get('document_name', 'unknown')}, page {snip.get('page', '?')}: \"{snip.get('text', '')[:200]}...\"\n"
                    user_message = f"{request.message}\n{evidence_context}"
                break

    # Call Claude API
    try:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        response = await client.messages.create(
            model=settings.get_active_llm_model(),
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        response_text = response.content[0].text

        # Parse the response to extract actions and sources
        result = parse_agent_response(response_text, evidence_data, documents_data)
        return result

    except Exception as e:
        logger.error(f"Agent chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# Import StateManager after sys.path is set up
from registry_review_mcp.utils.state import StateManager


@app.post("/sessions/{session_id}/upload", summary="Upload file to session")
async def upload_file(session_id: str, request: UploadFileRequest):
    """Upload a file to an existing session.

    Accepts base64-encoded file content and adds it to the session's documents.
    Note: Session must have been created with documents (e.g., via /start-example-review
    or /start-review-with-files). Use /start-review-with-files for new reviews.
    """
    try:
        files = [{"filename": request.filename, "content_base64": request.content_base64}]
        result = await upload_tools.upload_additional_files(session_id, files)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/start-review-with-files", summary="Start review with uploaded files")
async def start_review_with_files(request: StartReviewWithFilesRequest):
    """Start a new review by uploading files directly.

    Creates a session, saves uploaded files, discovers documents, and begins processing.
    This is the primary endpoint for ChatGPT file uploads.

    Files must be base64-encoded. Returns session details and discovery results.
    """
    try:
        files = [{"filename": f.filename, "content_base64": f.content_base64} for f in request.files]
        result = await upload_tools.start_review_from_uploads(
            project_name=request.project_name,
            files=files,
            methodology=request.methodology,
            auto_extract=False,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/start-example-review", summary="Start review with example project")
async def start_example_review(request: StartExampleReviewRequest):
    """Start a review using an example project.

    Creates a new session with documents from an example project directory,
    then automatically discovers and classifies the documents.

    Available examples: '22-23', '23-24' (crediting periods)
    """
    try:
        examples = await session_tools.list_example_projects()
        project_list = examples.get("projects", [])

        matching = [p for p in project_list if request.example_name in p.get("name", "")]
        if not matching:
            available = [p.get("name") for p in project_list]
            raise HTTPException(
                status_code=404,
                detail=f"Example '{request.example_name}' not found. Available: {available}"
            )

        example = matching[0]
        project_name = request.project_name or f"Review of {example['name']}"

        session_result = await session_tools.create_session(
            project_name=project_name,
            documents_path=example["path"],
        )

        discovery_result = await document_tools.discover_documents(session_result["session_id"])

        return {
            "session": session_result,
            "discovery": discovery_result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Two-Step Upload Endpoints (ChatGPT File Upload Workaround)
# ============================================================================


@app.post("/generate-upload-url", summary="Generate secure upload URL")
async def generate_upload_url(request: GenerateUploadUrlRequest, http_request: Request):
    """Generate a secure URL where the user can upload files directly.

    This is Step 1 of the two-step upload pattern for ChatGPT integration.
    ChatGPT calls this endpoint, then instructs the user to click the URL
    and upload their files. After upload, call /process-upload/{upload_id}.
    """
    upload_id = str(uuid.uuid4())[:12]
    token = secrets.token_urlsafe(16)

    pending_uploads[upload_id] = {
        "project_name": request.project_name,
        "methodology": request.methodology,
        "session_id": request.session_id,  # Optional: add to existing session
        "token": token,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        "status": "pending",
        "files": [],
    }

    # Use X-Forwarded-Host if available, otherwise fall back to Host header
    forwarded_host = http_request.headers.get("x-forwarded-host") or http_request.headers.get("host")
    forwarded_proto = http_request.headers.get("x-forwarded-proto", "https")
    if forwarded_host:
        base_url = f"{forwarded_proto}://{forwarded_host}/api/registry"
    else:
        base_url = str(http_request.base_url).rstrip("/")
    upload_url = f"{base_url}/upload/{upload_id}?token={token}"

    response = {
        "upload_id": upload_id,
        "upload_url": upload_url,
        "expires_in": "24 hours",
        "instructions": f"Please click the link to upload your project files: {upload_url}",
        "next_step": f"After uploading, tell the assistant 'I uploaded my files' and it will call /process-upload/{upload_id}",
    }

    if request.session_id:
        response["session_id"] = request.session_id
        response["mode"] = "add_to_existing"
        response["instructions"] = f"Adding files to existing session {request.session_id}. {response['instructions']}"
    else:
        response["mode"] = "create_new"

    return response


@app.get("/upload/{upload_id}", response_class=HTMLResponse, summary="File upload form")
async def upload_form(upload_id: str, token: str = Query(...)):
    """Serve HTML form for file upload.

    Users are directed here from ChatGPT to upload their files directly.
    """
    session = pending_uploads.get(upload_id)
    if not session or session["token"] != token:
        return HTMLResponse(
            content="<h1>Invalid or expired upload link</h1><p>Please request a new upload URL from ChatGPT.</p>",
            status_code=403,
        )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload Documents - Registry Review</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                   max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; margin-bottom: 10px; }}
            .project-name {{ color: #666; margin-bottom: 20px; }}
            .upload-area {{ border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0;
                          border-radius: 8px; transition: all 0.3s; }}
            .upload-area:hover {{ border-color: #4CAF50; background: #f9fff9; }}
            .upload-area.dragover {{ border-color: #4CAF50; background: #e8f5e9; }}
            input[type="file"] {{ display: none; }}
            .upload-btn {{ background: #4CAF50; color: white; padding: 12px 30px; border: none;
                          border-radius: 5px; cursor: pointer; font-size: 16px; }}
            .upload-btn:hover {{ background: #45a049; }}
            .file-list {{ margin: 20px 0; text-align: left; }}
            .file-item {{ padding: 10px; background: #f0f0f0; margin: 5px 0; border-radius: 5px;
                         display: flex; justify-content: space-between; }}
            .submit-btn {{ background: #2196F3; color: white; padding: 15px 40px; border: none;
                          border-radius: 5px; cursor: pointer; font-size: 18px; width: 100%; margin-top: 20px; }}
            .submit-btn:hover {{ background: #1976D2; }}
            .submit-btn:disabled {{ background: #ccc; cursor: not-allowed; }}
            .success {{ background: #e8f5e9; padding: 20px; border-radius: 8px; margin-top: 20px; }}
            .success h2 {{ color: #4CAF50; }}
            #status {{ margin-top: 15px; padding: 10px; border-radius: 5px; }}
            .uploading {{ background: #fff3e0; color: #e65100; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Upload Project Documents</h1>
            <p class="project-name">Project: <strong>{session['project_name']}</strong></p>

            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-area" id="dropZone">
                    <p>Drag & drop files here or click to browse</p>
                    <input type="file" id="fileInput" name="files" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.shp,.geojson">
                    <br><br>
                    <button type="button" class="upload-btn" onclick="document.getElementById('fileInput').click()">
                        Select Files
                    </button>
                </div>

                <div class="file-list" id="fileList"></div>

                <button type="submit" class="submit-btn" id="submitBtn" disabled>
                    Upload Files
                </button>

                <div id="status"></div>
            </form>

            <div id="success" class="success" style="display: none;">
                <h2>✅ Upload Complete!</h2>
                <p>Your files have been uploaded successfully.</p>
                <p><strong>Return to ChatGPT</strong> and say: "I uploaded my files"</p>
                <p>The assistant will then process your documents.</p>
            </div>
        </div>

        <script>
            const dropZone = document.getElementById('dropZone');
            const fileInput = document.getElementById('fileInput');
            const fileList = document.getElementById('fileList');
            const submitBtn = document.getElementById('submitBtn');
            const uploadForm = document.getElementById('uploadForm');
            const status = document.getElementById('status');
            const successDiv = document.getElementById('success');

            let selectedFiles = [];

            // Drag and drop handlers
            dropZone.addEventListener('dragover', (e) => {{
                e.preventDefault();
                dropZone.classList.add('dragover');
            }});

            dropZone.addEventListener('dragleave', () => {{
                dropZone.classList.remove('dragover');
            }});

            dropZone.addEventListener('drop', (e) => {{
                e.preventDefault();
                dropZone.classList.remove('dragover');
                handleFiles(e.dataTransfer.files);
            }});

            fileInput.addEventListener('change', (e) => {{
                handleFiles(e.target.files);
            }});

            function handleFiles(files) {{
                for (let file of files) {{
                    if (!selectedFiles.find(f => f.name === file.name)) {{
                        selectedFiles.push(file);
                    }}
                }}
                updateFileList();
            }}

            function updateFileList() {{
                fileList.innerHTML = selectedFiles.map((file, i) => `
                    <div class="file-item">
                        <span>${{file.name}} (${{(file.size / 1024).toFixed(1)}} KB)</span>
                        <button type="button" onclick="removeFile(${{i}})" style="background:none;border:none;cursor:pointer;">❌</button>
                    </div>
                `).join('');
                submitBtn.disabled = selectedFiles.length === 0;
            }}

            function removeFile(index) {{
                selectedFiles.splice(index, 1);
                updateFileList();
            }}

            uploadForm.addEventListener('submit', async (e) => {{
                e.preventDefault();

                if (selectedFiles.length === 0) return;

                submitBtn.disabled = true;
                status.innerHTML = '<div class="uploading">⏳ Uploading files... Please wait.</div>';

                const formData = new FormData();
                selectedFiles.forEach(file => formData.append('files', file));

                try {{
                    const response = await fetch(window.location.pathname + window.location.search, {{
                        method: 'POST',
                        body: formData
                    }});

                    if (response.ok) {{
                        const result = await response.json();
                        uploadForm.style.display = 'none';
                        successDiv.style.display = 'block';
                    }} else {{
                        const error = await response.json();
                        status.innerHTML = `<div style="background:#ffebee;color:#c62828;padding:10px;border-radius:5px;">
                            ❌ Upload failed: ${{error.detail || 'Unknown error'}}</div>`;
                        submitBtn.disabled = false;
                    }}
                }} catch (err) {{
                    status.innerHTML = `<div style="background:#ffebee;color:#c62828;padding:10px;border-radius:5px;">
                        ❌ Upload failed: ${{err.message}}</div>`;
                    submitBtn.disabled = false;
                }}
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/upload/{upload_id}", summary="Handle file upload")
async def handle_file_upload(
    upload_id: str,
    token: str = Query(...),
    files: List[UploadFile] = File(...),
):
    """Handle direct file uploads from the browser form.

    Files are saved and associated with the pending upload session.
    """
    session = pending_uploads.get(upload_id)
    if not session or session["token"] != token:
        raise HTTPException(status_code=403, detail="Invalid or expired upload token")

    if session["status"] == "uploaded":
        raise HTTPException(status_code=400, detail="Files already uploaded for this session")

    saved_files = []
    for file in files:
        content = await file.read()
        content_b64 = base64.b64encode(content).decode("utf-8")
        saved_files.append({
            "filename": file.filename,
            "content_base64": content_b64,
            "size_bytes": len(content),
        })

    session["files"] = saved_files
    session["status"] = "uploaded"
    session["uploaded_at"] = datetime.now().isoformat()

    return {
        "success": True,
        "upload_id": upload_id,
        "files_uploaded": len(saved_files),
        "filenames": [f["filename"] for f in saved_files],
        "message": "Files uploaded successfully. Return to ChatGPT and say 'I uploaded my files'.",
    }


@app.post("/process-upload/{upload_id}", summary="Process uploaded files")
async def process_uploaded_files(upload_id: str):
    """Process files after user uploads them via the upload URL.

    This is Step 2 of the two-step upload pattern. ChatGPT calls this
    after the user confirms they uploaded files.
    """
    session = pending_uploads.get(upload_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Upload session {upload_id} not found")

    if session["status"] == "pending":
        raise HTTPException(
            status_code=400,
            detail="No files uploaded yet. Please upload files first using the upload URL.",
        )

    if session["status"] == "processed":
        raise HTTPException(
            status_code=400,
            detail=f"Files already processed. Session ID: {session.get('session_id')}",
        )

    files = session.get("files", [])
    if not files:
        raise HTTPException(status_code=400, detail="No files found in upload session")

    try:
        existing_session_id = session.get("session_id")
        file_list = [{"filename": f["filename"], "content_base64": f["content_base64"]} for f in files]

        if existing_session_id:
            # Add files to existing session
            result = await upload_tools.upload_additional_files(
                session_id=existing_session_id,
                files=file_list,
            )
            session["status"] = "processed"
            # Run discovery on the updated session
            discovery_result = await document_tools.discover_documents(existing_session_id)
            return {
                "success": True,
                "upload_id": upload_id,
                "session_id": existing_session_id,
                "files_processed": len(files),
                "files_added": result.get("files_added", len(files)),
                "discovery": {
                    "documents_found": discovery_result.get("documents_found", 0),
                    "classification_summary": discovery_result.get("classification_summary", {}),
                },
            }
        else:
            # Create new session with files
            result = await upload_tools.start_review_from_uploads(
                project_name=session["project_name"],
                files=file_list,
                methodology=session["methodology"],
                auto_extract=False,
            )
            session["status"] = "processed"
            session["session_id"] = result.get("session_creation", {}).get("session_id")
            return {
                "success": True,
                "upload_id": upload_id,
                "session_id": session["session_id"],
                "files_processed": len(files),
                "result": result,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/upload-status/{upload_id}", summary="Check upload status")
async def check_upload_status(upload_id: str):
    """Check the status of an upload session."""
    session = pending_uploads.get(upload_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Upload session {upload_id} not found")

    return {
        "upload_id": upload_id,
        "project_name": session["project_name"],
        "status": session["status"],
        "files_count": len(session.get("files", [])),
        "created_at": session["created_at"],
        "session_id": session.get("session_id"),
    }


# ============================================================================
# Server Entry Point
# ============================================================================


def main():
    """Run the REST API server"""
    print("=" * 70)
    print("Registry Review REST API for ChatGPT")
    print("=" * 70)
    print("Host:     localhost")
    print("Port:     8003")
    print("Endpoint: http://localhost:8003")
    print("Docs:     http://localhost:8003/docs")
    print("=" * 70)
    print("")
    print("Next Steps:")
    print("1. Create tunnel: ssh -R 80:localhost:8001 nokey@localhost.run")
    print("2. Create Custom GPT in ChatGPT")
    print("3. Add Action using OpenAPI schema from /docs")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")


if __name__ == "__main__":
    main()
