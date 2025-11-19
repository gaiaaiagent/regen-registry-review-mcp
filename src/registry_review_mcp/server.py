"""Registry Review MCP Server - automated carbon credit project registry review workflows."""

import logging
import sys
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .config.settings import settings
from .models import errors as mcp_errors
from .tools import session_tools, document_tools, evidence_tools, validation_tools, report_tools, upload_tools
from .utils.tool_helpers import (
    with_error_handling,
    format_success,
    format_error,
    format_list,
    format_sessions_list,
    format_session_created,
    format_session_loaded,
    format_documents_discovered,
    format_evidence_extracted,
    format_review_started,
    format_upload_result,
    format_pdf_extraction,
    format_gis_metadata,
    format_requirement_mapping,
    ResponseBuilder,
)
from .prompts import A_initialize, B_document_discovery, C_evidence_extraction, D_cross_validation, E_report_generation, F_human_review, G_complete

# ============================================================================
# Logging Setup (CRITICAL: Must write to stderr, NOT stdout)
# ============================================================================

logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format,
    stream=sys.stderr,  # CRITICAL: stderr only for MCP protocol
)
logger = logging.getLogger(__name__)

# ============================================================================
# MCP Server Initialization
# ============================================================================

mcp = FastMCP("Regen Registry Review")

logger.info("Initializing Registry Review MCP Server v2.0.0")

# ============================================================================
# Session Management Tools
# ============================================================================


@mcp.tool()
@with_error_handling("create_session")
async def create_session(
    project_name: str,
    documents_path: str,
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
    proponent: str | None = None,
    crediting_period: str | None = None,
) -> str:
    """Create a new registry review session."""
    result = await session_tools.create_session(
        project_name=project_name,
        documents_path=documents_path,
        methodology=methodology,
        project_id=project_id,
        proponent=proponent,
        crediting_period=crediting_period,
    )
    return format_session_created(result)


@mcp.tool()
@with_error_handling("load_session")
async def load_session(session_id: str) -> str:
    """Load an existing review session."""
    session_data = await session_tools.load_session(session_id)
    return format_session_loaded(session_data)


@mcp.tool()
@with_error_handling("update_session_state")
async def update_session_state(
    session_id: str,
    status: str | None = None,
    workflow_stage: str | None = None,
    workflow_status: str | None = None,
) -> str:
    """Update session state."""
    updates: dict = {}
    if status:
        updates["status"] = status
    if workflow_stage and workflow_status:
        updates[f"workflow_progress.{workflow_stage}"] = workflow_status

    result = await session_tools.update_session_state(session_id, updates)
    return format_success("Session Updated", {"session_id": session_id, "updated": result.get('updated_at')})


@mcp.tool()
@with_error_handling("list_sessions")
async def list_sessions() -> str:
    """List all review sessions with complete field details"""
    sessions = await session_tools.list_sessions()
    return format_sessions_list(sessions)


@mcp.tool()
@with_error_handling("list_example_projects")
async def list_example_projects() -> str:
    """List example projects available in the examples directory for testing/demo purposes"""
    result = await session_tools.list_example_projects()

    if result["projects_found"] == 0:
        return format_error(Exception(result['message']))

    projects = [
        {
            "name": p['name'],
            "path": p['path'],
            "file_count": p['file_count']
        }
        for p in result["projects"]
    ]

    return (
        format_list(projects, result['message'])
        + "\n\nTo initialize an example project:\n/initialize Project Name, /path/from/above"
    )


@mcp.tool()
@with_error_handling("start_review")
async def start_review(
    project_name: str,
    documents_path: str,
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
) -> str:
    """Quick-start: Create session and discover documents in one step.

    This is a convenience tool that combines create_session and discover_documents
    for a streamlined workflow.

    Args:
        project_name: Name of the project being reviewed
        documents_path: Absolute path to directory containing project documents
        methodology: Methodology identifier (default: soil-carbon-v1.2.2)
        project_id: Project ID if known (e.g., C06-4997)

    Returns:
        Combined session creation and document discovery results
    """
    session_result = await session_tools.create_session(
        project_name=project_name,
        documents_path=documents_path,
        methodology=methodology,
        project_id=project_id,
    )

    discovery_result = await document_tools.discover_documents(session_result["session_id"])

    return format_review_started(session_result, discovery_result)


@mcp.tool()
@with_error_handling("delete_session")
async def delete_session(session_id: str) -> str:
    """Delete a review session and all its data.

    Args:
        session_id: Unique session identifier

    Returns:
        Confirmation message
    """
    result = await session_tools.delete_session(session_id)
    return format_success(result["message"])


# ============================================================================
# File Upload Tools
# ============================================================================


@mcp.tool()
@with_error_handling("create_session_from_uploads")
async def create_session_from_uploads(
    project_name: str,
    files: list[dict],
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
    proponent: str | None = None,
    crediting_period: str | None = None,
    deduplicate: bool = True,
    force_new_session: bool = False,
) -> str:
    """Create a new registry review session from uploaded file content.

    Accepts file content in two flexible formats:
    1. Base64 format: {"filename": "doc.pdf", "content_base64": "JVBERi0..."}
    2. Path format: {"filename": "doc.pdf", "path": "/absolute/path/to/file.pdf"}

    Ideal for web applications, chat interfaces, and APIs where files are
    uploaded dynamically or stored on the server filesystem.

    Args:
        project_name: Name of the project being reviewed
        files: List of file objects. Each file must have:
            - filename OR name (required): Name of the file (e.g., "ProjectPlan.pdf")
            - content_base64 OR path (required): Either base64-encoded content or absolute file path
            - mime_type (optional): MIME type (e.g., "application/pdf")
        methodology: Methodology identifier (default: soil-carbon-v1.2.2)
        project_id: Project ID if known (e.g., C06-4997)
        proponent: Name of project proponent
        crediting_period: Crediting period description (e.g., "2022-2032")
        deduplicate: Automatically remove duplicate files by filename and content hash (default: True)
        force_new_session: Force creation of new session even if existing session detected (default: False)

    Returns:
        Success message with session details and document discovery results.
        If existing session detected, returns that session's information.

    Examples:
        # Base64 format
        files = [{"filename": "plan.pdf", "content_base64": "JVBERi0xLjQK..."}]

        # Path format (e.g., from ElizaOS uploads)
        files = [{"name": "plan.pdf", "path": "/media/uploads/agents/abc/plan.pdf"}]

        create_session_from_uploads("My Project", files)
    """
    result = await upload_tools.create_session_from_uploads(
        project_name=project_name,
        files=files,
        methodology=methodology,
        project_id=project_id,
        proponent=proponent,
        crediting_period=crediting_period,
        deduplicate=deduplicate,
        force_new_session=force_new_session,
    )

    # Handle existing session case with special formatting
    if result.get("existing_session_detected"):
        progress = result.get("workflow_progress", {})
        progress_text = []
        for stage, status in progress.items():
            icon = "✓" if status == "completed" else "⏳" if status == "in_progress" else "○"
            progress_text.append(f"  {icon} {stage}: {status}")
        progress_summary = "\n".join(progress_text) if progress_text else "  (No progress recorded)"

        return f"""ℹ️ Existing Session Found

Session ID: {result['session_id']}
Project: {result['project_name']}
Created: {result.get('session_created', 'Unknown')}

{result.get('message', 'Returning existing session.')}

Workflow Progress:
{progress_summary}

To create a new session anyway, set force_new_session=True.
"""

    return format_upload_result(result)


@mcp.tool()
@with_error_handling("upload_additional_files")
async def upload_additional_files(
    session_id: str,
    files: list[dict],
) -> str:
    """Add additional files to an existing session.

    Accepts file content in two flexible formats:
    1. Base64 format: {"filename": "doc.pdf", "content_base64": "JVBERi0..."}
    2. Path format: {"filename": "doc.pdf", "path": "/absolute/path/to/file.pdf"}

    Adds files to an existing session's document directory and re-runs document discovery.
    Useful for iterative document submission.

    Args:
        session_id: Existing session identifier
        files: List of file objects. Each file must have:
            - filename OR name (required): Name of the file
            - content_base64 OR path (required): Either base64-encoded content or absolute file path
            - mime_type (optional): MIME type

    Returns:
        Success message with updated document discovery results

    Examples:
        # Base64 format
        upload_additional_files("session-abc123",
            [{"filename": "Baseline.pdf", "content_base64": "JVBERi0..."}])

        # Path format
        upload_additional_files("session-abc123",
            [{"name": "Baseline.pdf", "path": "/media/uploads/agents/abc/baseline.pdf"}])
    """
    result = await upload_tools.upload_additional_files(
        session_id=session_id,
        files=files,
    )

    return format_upload_result(result)


@mcp.tool()
@with_error_handling("start_review_from_uploads")
async def start_review_from_uploads(
    project_name: str,
    files: list[dict],
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
    proponent: str | None = None,
    crediting_period: str | None = None,
    auto_extract: bool = True,
    deduplicate: bool = True,
    force_new_session: bool = False,
) -> str:
    """One-step tool to create session, upload files, and optionally extract evidence.

    This is the recommended tool for new integrations - it combines session creation,
    document discovery, and evidence extraction into a single streamlined operation.

    Accepts file content in two flexible formats:
    1. Base64 format: {"filename": "doc.pdf", "content_base64": "JVBERi0..."}
    2. Path format: {"filename": "doc.pdf", "path": "/absolute/path/to/file.pdf"}

    Args:
        project_name: Name of the project being reviewed
        files: List of file objects. Each file must have:
            - filename OR name (required): Name of the file
            - content_base64 OR path (required): Either base64-encoded content or absolute file path
            - mime_type (optional): MIME type
        methodology: Methodology identifier (default: soil-carbon-v1.2.2)
        project_id: Project ID if known (e.g., C06-4997)
        proponent: Name of project proponent
        crediting_period: Crediting period description (e.g., "2022-2032")
        auto_extract: Automatically run evidence extraction (default: True)
        deduplicate: Automatically remove duplicate files by filename and content hash (default: True)
        force_new_session: Force creation of new session even if existing session detected (default: False)

    Returns:
        Combined results from session creation and evidence extraction.
        If existing session detected, returns that session's information.

    Examples:
        # Base64 format
        start_review_from_uploads("Botany Farm 2022", [
            {"filename": "ProjectPlan.pdf", "content_base64": "JVBERi0..."},
            {"filename": "Baseline.pdf", "content_base64": "JVBERi0..."}
        ])

        # Path format (e.g., from ElizaOS)
        start_review_from_uploads("Botany Farm 2022", [
            {"name": "ProjectPlan.pdf", "path": "/media/uploads/agents/abc/plan.pdf"},
            {"name": "Baseline.pdf", "path": "/media/uploads/agents/abc/baseline.pdf"}
        ])
    """
    result = await upload_tools.start_review_from_uploads(
        project_name=project_name,
        files=files,
        methodology=methodology,
        project_id=project_id,
        proponent=proponent,
        crediting_period=crediting_period,
        auto_extract=auto_extract,
        deduplicate=deduplicate,
        force_new_session=force_new_session,
    )

    # Build response from session creation part
    session_result = result["session_creation"]
    output = format_upload_result(session_result)

    # Add evidence extraction results if present
    if "evidence_extraction" in result:
        evidence = result["evidence_extraction"]

        if evidence.get("success") is False:
            output += f"\n\n⚠️  Evidence Extraction Failed:\n{evidence.get('message', 'Unknown error')}\n\nYou can run extract_evidence(\"{session_result['session_id']}\") manually to retry."
        else:
            output += f"\n\nEvidence Extraction Complete:\n"
            output += f"  Total Requirements: {evidence.get('requirements_total', 0)}\n"
            output += f"  ✅ Covered: {evidence.get('requirements_covered', 0)}\n"
            output += f"  ⚠️  Partial: {evidence.get('requirements_partial', 0)}\n"
            output += f"  ❌ Missing: {evidence.get('requirements_missing', 0)}\n"
            output += f"  Overall Coverage: {evidence.get('overall_coverage', 0) * 100:.1f}%"

    return output


# ============================================================================
# Document Processing Tools
# ============================================================================


@mcp.tool()
@with_error_handling("discover_documents")
async def discover_documents(session_id: str) -> str:
    """Discover and classify all documents in the project directory.

    Args:
        session_id: Unique session identifier

    Returns:
        Summary of discovered documents with classifications
    """
    results = await document_tools.discover_documents(session_id)
    return format_documents_discovered(results)


@mcp.tool()
@with_error_handling("extract_pdf_text")
async def extract_pdf_text(
    filepath: str,
    start_page: int | None = None,
    end_page: int | None = None,
    extract_tables: bool = False,
) -> str:
    """Extract text content from a PDF file.

    Args:
        filepath: Absolute path to PDF file
        start_page: Optional starting page (1-indexed)
        end_page: Optional ending page (1-indexed)
        extract_tables: Whether to extract tables

    Returns:
        Extracted text content with metadata
    """
    page_range = (start_page, end_page) if start_page and end_page else None
    results = await document_tools.extract_pdf_text(
        filepath, page_range, extract_tables
    )

    return format_pdf_extraction(results)


@mcp.tool()
@with_error_handling("extract_gis_metadata")
async def extract_gis_metadata(filepath: str) -> str:
    """Extract metadata from a GIS shapefile or GeoJSON.

    Args:
        filepath: Absolute path to GIS file (.shp or .geojson)

    Returns:
        GIS metadata including CRS, bounds, feature count
    """
    results = await document_tools.extract_gis_metadata(filepath)
    return format_gis_metadata(results)


# ============================================================================
# Evidence Extraction Tools (Phase 3)
# ============================================================================


@mcp.tool()
@with_error_handling("extract_evidence")
async def extract_evidence(session_id: str) -> str:
    """Extract evidence for all requirements from discovered documents.

    This tool maps each requirement in the checklist to relevant documents,
    extracts evidence snippets with page citations, and calculates coverage statistics.

    Args:
        session_id: Unique session identifier

    Returns:
        Summary of evidence extraction results with coverage statistics
    """
    results = await evidence_tools.extract_all_evidence(session_id)
    return format_evidence_extracted(results)


@mcp.tool()
@with_error_handling("map_requirement")
async def map_requirement(session_id: str, requirement_id: str) -> str:
    """Map a single requirement to documents and extract evidence.

    Args:
        session_id: Unique session identifier
        requirement_id: Requirement ID (e.g., "REQ-002", "REQ-007")

    Returns:
        Evidence details for the specific requirement
    """
    result = await evidence_tools.map_requirement(session_id, requirement_id)
    return format_requirement_mapping(result)


# ============================================================================
# Prompts
# ============================================================================


@mcp.prompt()
def list_capabilities() -> list[TextContent]:
    """List all MCP server capabilities, tools, and workflow prompts"""
    capabilities = f"""# Regen Registry Review MCP Server

**Version:** 2.0.0
**Purpose:** Automate carbon credit project registry review workflows

## Capabilities

### Tools Available

**Session Management:**
- `start_review` - Quick-start: Create session and discover documents in one step
- `create_session` - Create new review session
- `load_session` - Load existing session
- `update_session_state` - Update session progress
- `list_sessions` - List all sessions
- `delete_session` - Delete a session

**Document Processing (Phase 2):**
- `discover_documents` - Scan and classify project documents
- `extract_pdf_text` - Extract text from PDF files
- `extract_gis_metadata` - Extract GIS shapefile metadata

**Evidence Extraction (Phase 3):**
- `extract_evidence` - Map all requirements to documents and extract evidence
- `map_requirement` - Map a single requirement to documents with evidence snippets

**Validation & Reporting (Phase 4):**
- `cross_validation` - Validate dates, land tenure, and project IDs across documents
- `generate_report` - Create comprehensive Markdown and JSON reports

### Workflows (7 Sequential Stages)

1. **Initialize** (`/initialize`) - Create session and load checklist
2. **Document Discovery** (`/document-discovery`) - Scan and classify all documents
3. **Evidence Extraction** (`/evidence-extraction`) - Map requirements to evidence
4. **Cross-Validation** (`/cross-validation`) - Verify consistency across documents
5. **Report Generation** (`/report-generation`) - Generate structured review report
6. **Human Review** (`/human-review`) - Present flagged items for decision
7. **Complete** (`/complete`) - Finalize and export report

### Supported Methodology

- Soil Carbon v1.2.2 (GHG Benefits in Managed Crop and Grassland Systems)
- Additional methodologies: Coming in Phase 3+

### File Types Supported

- PDF documents (text and tables)
- GIS shapefiles (.shp, .shx, .dbf, .geojson)
- Imagery files (.tif, .tiff) - metadata only

## Getting Started

**Quick Start (Recommended):**
```
start_review(
    project_name="Botany Farm",
    documents_path="/absolute/path/to/documents",
    methodology="soil-carbon-v1.2.2"
)
```
This creates a session and discovers all documents in one step.

**Or use the prompts directly:**
```
/document-discovery
/evidence-extraction
```
These will auto-select your most recent session, or guide you to create one if none exists.

**Manual workflow:**
1. Create a session with `create_session`
2. Discover documents with `discover_documents` or `/document-discovery` prompt
3. Extract evidence with `extract_evidence` or `/evidence-extraction` prompt

## Status

- **Phase 1 (Foundation):** ✅ Complete (Session management, infrastructure)
- **Phase 2 (Document Processing):** ✅ Complete (Document discovery, classification, PDF/GIS extraction)
- **Phase 3 (Evidence Extraction):** ✅ Complete (Requirement mapping, evidence snippets, coverage analysis)
- **Phase 4 (Validation & Reporting):** ✅ Complete (Cross-validation, report generation, LLM-native extraction)
- **Phase 5 (Integration & Polish):** 🚧 In Progress (All 7 prompts complete, testing in progress)

**Test Coverage:** 120/120 tests passing (100%)
**LLM Extraction:** 80%+ recall with caching and cost tracking
**Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}
"""

    return [TextContent(type="text", text=capabilities)]


@mcp.prompt(name="list-sessions")
async def list_sessions_prompt() -> list[TextContent]:
    """List all active review sessions with project names, progress, and workflow status"""
    result = await list_sessions()
    return [TextContent(type="text", text=result)]


@mcp.prompt(name="list-projects")
async def list_projects_prompt() -> list[TextContent]:
    """List available example projects in the examples directory for quick testing"""
    result = await list_example_projects()
    return [TextContent(type="text", text=result)]


@mcp.prompt(name="A-initialize")
async def initialize(project: str) -> list[TextContent]:
    """Initialize new review session - provide 'project name, /path/to/documents' (comma-separated)"""
    parts = [p.strip() for p in project.split(",", 1)]
    project_name = parts[0] if len(parts) > 0 else None
    documents_path = parts[1] if len(parts) > 1 else None
    return await A_initialize.initialize_prompt(project_name, documents_path)


@mcp.prompt(name="B-document-discovery")
async def document_discovery(project: str = "") -> list[TextContent]:
    """Discover and classify project documents - provide session ID or project name (optional, auto-selects latest)"""
    session_id = project if project and not "," in project else None
    project_name = None
    documents_path = None
    if "," in project:
        parts = [p.strip() for p in project.split(",", 1)]
        project_name = parts[0]
        documents_path = parts[1] if len(parts) > 1 else None
    return await B_document_discovery.document_discovery_prompt(project_name, documents_path, session_id)


@mcp.prompt(name="C-evidence-extraction")
async def evidence_extraction(project: str = "") -> list[TextContent]:
    """Extract evidence from documents and map to requirements - provide session ID (optional, auto-selects latest)"""
    session_id = project if project else None
    result = await C_evidence_extraction.evidence_extraction(session_id)
    return [TextContent(type="text", text=result)]


@mcp.prompt(name="D-cross-validation")
async def cross_validation(project: str = "") -> list[TextContent]:
    """Validate consistency across documents (dates, land tenure, project IDs) - provide session ID (optional)"""
    session_id = project if project else None
    return await D_cross_validation.cross_validation_prompt(session_id)


@mcp.prompt(name="E-report-generation")
async def report_generation(project: str = "") -> list[TextContent]:
    """Generate complete review report in Markdown and JSON formats - provide session ID (optional)"""
    session_id = project if project else None
    return await E_report_generation.report_generation_prompt(session_id)


@mcp.prompt(name="F-human-review")
async def human_review(project: str = "") -> list[TextContent]:
    """Review flagged validation items requiring human judgment - provide session ID (optional)"""
    session_id = project if project else None
    return await F_human_review.human_review_prompt(session_id)


@mcp.prompt(name="G-complete")
async def complete(project: str = "") -> list[TextContent]:
    """Complete and finalize the review session with final assessment - provide session ID (optional)"""
    session_id = project if project else None
    return await G_complete.complete_prompt(session_id)


# ============================================================================
# Entry Point
# ============================================================================


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Registry Review MCP Server")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info(f"Log level: {settings.log_level}")

    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
