"""Registry Review MCP Server - automated carbon credit project registry review workflows."""

import json
import logging
import sys
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .config.settings import settings
from .models import errors as mcp_errors
from .tools import session_tools, document_tools, evidence_tools, validation_tools, report_tools, upload_tools, mapping_tools
from .utils.tool_helpers import with_error_handling
from .prompts import (
    A_initialize,
    B_document_discovery,
    C_requirement_mapping,
    D_evidence_extraction,
    E_cross_validation,
    F_report_generation,
    G_human_review,
    H_completion,
)

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
    methodology: str = "soil-carbon-v1.2.2",
    documents_path: str | None = None,
    project_id: str | None = None,
    proponent: str | None = None,
    crediting_period: str | None = None,
) -> str:
    """Create a new registry review session.

    Stage 1: Initialize (metadata only)
    Creates session with project information. Documents can be added later.

    Note: documents_path is deprecated - use add_documents() tool instead.
    """
    result = await session_tools.create_session(
        project_name=project_name,
        documents_path=documents_path,
        methodology=methodology,
        project_id=project_id,
        proponent=proponent,
        crediting_period=crediting_period,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
@with_error_handling("load_session")
async def load_session(session_id: str) -> str:
    """Load an existing review session."""
    session_data = await session_tools.load_session(session_id)
    return json.dumps(session_data, indent=2)


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
    return json.dumps(result, indent=2)


@mcp.tool()
@with_error_handling("list_sessions")
async def list_sessions() -> str:
    """List all review sessions with complete field details"""
    sessions = await session_tools.list_sessions()
    return json.dumps(sessions, indent=2)


@mcp.tool()
@with_error_handling("list_example_projects")
async def list_example_projects() -> str:
    """List example projects available in the examples directory for testing/demo purposes"""
    result = await session_tools.list_example_projects()
    return json.dumps(result, indent=2)


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

    return json.dumps({
        "session": session_result,
        "discovery": discovery_result
    }, indent=2)


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
    return json.dumps(result, indent=2)


@mcp.tool()
@with_error_handling("add_documents")
async def add_documents(
    session_id: str,
    source: dict,
    check_duplicates: bool = True,
) -> str:
    """Add document sources to session.

    Stage 1b: Add sources before discovery

    Args:
        session_id: Existing session ID
        source: Document source specification. Supported types:
            - Upload: {"type": "upload", "files": [{"filename": "...", "content_base64": "..."}]}
            - Path: {"type": "path", "path": "/absolute/path/to/documents"}
        check_duplicates: Detect existing sessions with similar content (default: True)

    Returns:
        Result with source details and optional duplicate warning
    """
    result = await document_tools.add_documents(
        session_id=session_id,
        source=source,
        check_duplicates=check_duplicates,
    )
    return json.dumps(result, indent=2)


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
    """Create session from uploaded files (base64 or path format)."""
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
    return json.dumps(result, indent=2)


@mcp.tool()
@with_error_handling("upload_additional_files")
async def upload_additional_files(
    session_id: str,
    files: list[dict],
) -> str:
    """Add files to existing session (base64 or path format)."""
    result = await upload_tools.upload_additional_files(
        session_id=session_id,
        files=files,
    )
    return json.dumps(result, indent=2)


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
    """Create session, upload files, and extract evidence in one step."""
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
    return json.dumps(result, indent=2)


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
    return json.dumps(results, indent=2)


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

    return json.dumps(results, indent=2)


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
    return json.dumps(results, indent=2)


# ============================================================================
# Requirement Mapping Tools (Stage 3)
# ============================================================================


@mcp.tool()
@with_error_handling("map_all_requirements")
async def map_all_requirements(session_id: str) -> str:
    """Map all requirements to documents using semantic matching.

    Args:
        session_id: Unique session identifier

    Returns:
        Summary of mapping results with statistics
    """
    results = await mapping_tools.map_all_requirements(session_id)
    return json.dumps(results, indent=2)


@mcp.tool()
@with_error_handling("confirm_mapping")
async def confirm_mapping(
    session_id: str,
    requirement_id: str,
    document_ids: list[str]
) -> str:
    """Confirm or manually set document mappings for a requirement.

    Args:
        session_id: Unique session identifier
        requirement_id: Requirement ID (e.g., "REQ-002")
        document_ids: List of document IDs to map

    Returns:
        Updated mapping information
    """
    result = await mapping_tools.confirm_mapping(session_id, requirement_id, document_ids)
    return json.dumps(result, indent=2)


@mcp.tool()
@with_error_handling("remove_mapping")
async def remove_mapping(
    session_id: str,
    requirement_id: str,
    document_id: str
) -> str:
    """Remove a document from a requirement mapping.

    Args:
        session_id: Unique session identifier
        requirement_id: Requirement ID (e.g., "REQ-002")
        document_id: Document ID to remove

    Returns:
        Updated mapping information
    """
    result = await mapping_tools.remove_mapping(session_id, requirement_id, document_id)
    return json.dumps(result, indent=2)


@mcp.tool()
@with_error_handling("get_mapping_status")
async def get_mapping_status(session_id: str) -> str:
    """Get current mapping status and statistics.

    Args:
        session_id: Unique session identifier

    Returns:
        Complete mapping status with statistics
    """
    result = await mapping_tools.get_mapping_status(session_id)
    return json.dumps(result, indent=2)


# ============================================================================
# Evidence Extraction Tools (Stage 4)
# ============================================================================


@mcp.tool()
@with_error_handling("extract_evidence")
async def extract_evidence(session_id: str) -> str:
    """Extract evidence for all requirements from mapped documents.

    This tool extracts evidence snippets with page citations from documents
    that have been mapped to requirements in Stage 3.

    Args:
        session_id: Unique session identifier

    Returns:
        Summary of evidence extraction results with coverage statistics
    """
    from .tools.evidence_tools import extract_all_evidence
    results = await extract_all_evidence(session_id)
    return json.dumps(results, indent=2)


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
    return json.dumps(result, indent=2)


# ============================================================================
# Prompts
# ============================================================================


@mcp.prompt()
def list_capabilities() -> list[TextContent]:
    """List all MCP server capabilities, tools, and workflow prompts"""
    from pathlib import Path

    # Load capabilities from external markdown file
    capabilities_path = Path(__file__).parent.parent.parent / "CAPABILITIES.md"

    try:
        capabilities = capabilities_path.read_text()
        # Add dynamic timestamp
        capabilities += f"\n\n**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
    except FileNotFoundError:
        capabilities = "# Regen Registry Review MCP Server\n\n**Error:** CAPABILITIES.md not found. See documentation for details."

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


@mcp.prompt(name="C-requirement-mapping")
async def requirement_mapping(project: str = "") -> list[TextContent]:
    """Map documents to checklist requirements - provide session ID (optional, auto-selects latest)"""
    session_id = project if project else None
    return await C_requirement_mapping.requirement_mapping_prompt(session_id)


@mcp.prompt(name="D-evidence-extraction")
async def evidence_extraction(project: str = "") -> list[TextContent]:
    """Extract evidence from mapped documents - provide session ID (optional, auto-selects latest)"""
    session_id = project if project else None
    result = await D_evidence_extraction.evidence_extraction(session_id)
    return [TextContent(type="text", text=result)]


@mcp.prompt(name="E-cross-validation")
async def cross_validation(project: str = "") -> list[TextContent]:
    """Validate consistency across documents (dates, land tenure, project IDs) - provide session ID (optional)"""
    session_id = project if project else None
    return await E_cross_validation.cross_validation_prompt(session_id)


@mcp.prompt(name="F-report-generation")
async def report_generation(project: str = "") -> list[TextContent]:
    """Generate complete review report in Markdown and JSON formats - provide session ID (optional)"""
    session_id = project if project else None
    return await F_report_generation.report_generation_prompt(session_id)


@mcp.prompt(name="G-human-review")
async def human_review(project: str = "") -> list[TextContent]:
    """Review flagged validation items requiring human judgment - provide session ID (optional)"""
    session_id = project if project else None
    return await G_human_review.human_review_prompt(session_id)


@mcp.prompt(name="H-completion")
async def completion(project: str = "") -> list[TextContent]:
    """Complete and finalize the review session with final assessment - provide session ID (optional)"""
    session_id = project if project else None
    return await H_completion.complete_prompt(session_id)


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
