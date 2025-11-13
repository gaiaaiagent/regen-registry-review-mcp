"""Registry Review MCP Server.

Main entry point for the Model Context Protocol server providing automated
registry review workflows for carbon credit project registration.
"""

import logging
import sys
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .config.settings import settings
from .models import errors as mcp_errors
from .tools import session_tools, document_tools, evidence_tools, validation_tools, report_tools
from .prompts import initialize, document_discovery, evidence_extraction, cross_validation, report_generation

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
async def create_session(
    project_name: str,
    documents_path: str,
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
    proponent: str | None = None,
    crediting_period: str | None = None,
) -> str:
    """Create a new registry review session.

    Args:
        project_name: Name of the project being reviewed
        documents_path: Absolute path to directory containing project documents
        methodology: Methodology identifier (default: soil-carbon-v1.2.2)
        project_id: Project ID if known (e.g., C06-4997)
        proponent: Name of project proponent
        crediting_period: Crediting period description (e.g., "2022-2032")

    Returns:
        JSON string with session details and instructions for next steps
    """
    try:
        logger.info(f"Creating session for project: {project_name}")

        result = await session_tools.create_session(
            project_name=project_name,
            documents_path=documents_path,
            methodology=methodology,
            project_id=project_id,
            proponent=proponent,
            crediting_period=crediting_period,
        )

        logger.info(f"Session created: {result['session_id']}")

        return f"""✓ Session Created Successfully

Session ID: {result['session_id']}
Project: {result['project_name']}
Methodology: {result['methodology']}
Documents Path: {result['documents_path']}
Created: {result['created_at']}

Next Step: Run document discovery
    - Use the /document-discovery prompt to scan and classify all project documents
    - Or call the discover_documents tool directly with session_id: {result['session_id']}
"""

    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def load_session(session_id: str) -> str:
    """Load an existing review session.

    Args:
        session_id: Unique session identifier

    Returns:
        JSON string with complete session data
    """
    try:
        logger.info(f"Loading session: {session_id}")

        session_data = await session_tools.load_session(session_id)

        # Format workflow progress
        progress = session_data.get("workflow_progress", {})
        progress_status = "\n".join(
            f"  - {stage}: {status}" for stage, status in progress.items()
        )

        # Format statistics
        stats = session_data.get("statistics", {})

        return f"""✓ Session Loaded

Session ID: {session_id}
Project: {session_data.get('project_metadata', {}).get('project_name')}
Status: {session_data.get('status')}
Created: {session_data.get('created_at')}
Updated: {session_data.get('updated_at')}

Workflow Progress:
{progress_status}

Statistics:
  - Documents Found: {stats.get('documents_found', 0)}
  - Requirements Total: {stats.get('requirements_total', 0)}
  - Requirements Covered: {stats.get('requirements_covered', 0)}
  - Requirements Partial: {stats.get('requirements_partial', 0)}
  - Requirements Missing: {stats.get('requirements_missing', 0)}
"""

    except mcp_errors.SessionNotFoundError as e:
        logger.warning(f"Session not found: {session_id}")
        return f"✗ Session not found: {session_id}\n\nUse list_sessions to see available sessions."

    except Exception as e:
        logger.error(f"Failed to load session: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def update_session_state(
    session_id: str,
    status: str | None = None,
    workflow_stage: str | None = None,
    workflow_status: str | None = None,
) -> str:
    """Update session state.

    Args:
        session_id: Unique session identifier
        status: Overall session status
        workflow_stage: Workflow stage to update (e.g., "document_discovery")
        workflow_status: Status for the workflow stage (pending/in_progress/completed)

    Returns:
        Confirmation message
    """
    try:
        logger.info(f"Updating session: {session_id}")

        updates: dict = {}

        if status:
            updates["status"] = status

        if workflow_stage and workflow_status:
            updates[f"workflow_progress.{workflow_stage}"] = workflow_status

        result = await session_tools.update_session_state(session_id, updates)

        return f"""✓ Session Updated

Session ID: {session_id}
Updated: {result.get('updated_at')}
"""

    except mcp_errors.SessionNotFoundError:
        return f"✗ Session not found: {session_id}"

    except Exception as e:
        logger.error(f"Failed to update session: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def list_sessions() -> str:
    """List all available review sessions.

    Returns:
        Formatted list of sessions with metadata
    """
    try:
        logger.info("Listing all sessions")

        sessions = await session_tools.list_sessions()

        if not sessions:
            return "No sessions found.\n\nCreate a new session using the create_session tool."

        session_list = []
        for idx, session in enumerate(sessions, 1):
            session_list.append(
                f"{idx}. {session['session_id']}\n"
                f"   Project: {session.get('project_name', 'Unknown')}\n"
                f"   Created: {session.get('created_at', 'Unknown')}\n"
                f"   Status: {session.get('status', 'Unknown')}"
            )

        return f"✓ Found {len(sessions)} session(s)\n\n" + "\n\n".join(session_list)

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"


@mcp.tool()
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
    try:
        logger.info(f"Starting review for project: {project_name}")

        # Create session
        session_result = await session_tools.create_session(
            project_name=project_name,
            documents_path=documents_path,
            methodology=methodology,
            project_id=project_id,
        )

        session_id = session_result["session_id"]
        logger.info(f"Session created: {session_id}")

        # Discover documents
        discovery_result = await document_tools.discover_documents(session_id)

        # Format summary
        summary_lines = []
        for doc_type, count in sorted(discovery_result["classification_summary"].items()):
            summary_lines.append(f"  - {doc_type}: {count}")

        summary = "\n".join(summary_lines) if summary_lines else "  (none found)"

        return f"""✓ Review Started Successfully

Session ID: {session_id}
Project: {project_name}
Methodology: {methodology}
Documents Path: {documents_path}
Created: {session_result['created_at']}

Document Discovery Complete:
  Found {discovery_result['documents_found']} document(s)

Classification Summary:
{summary}

Next Steps:
  - Review the document classifications
  - Use the /document-discovery prompt for detailed results
  - Or proceed to evidence extraction (Phase 3)
"""

    except Exception as e:
        logger.error(f"Failed to start review: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def delete_session(session_id: str) -> str:
    """Delete a review session and all its data.

    Args:
        session_id: Unique session identifier

    Returns:
        Confirmation message
    """
    try:
        logger.info(f"Deleting session: {session_id}")

        result = await session_tools.delete_session(session_id)

        return f"✓ {result['message']}"

    except mcp_errors.SessionNotFoundError:
        return f"✗ Session not found: {session_id}"

    except Exception as e:
        logger.error(f"Failed to delete session: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"


# ============================================================================
# Document Processing Tools
# ============================================================================


@mcp.tool()
async def discover_documents(session_id: str) -> str:
    """Discover and classify all documents in the project directory.

    Args:
        session_id: Unique session identifier

    Returns:
        Summary of discovered documents with classifications
    """
    try:
        logger.info(f"Discovering documents for session: {session_id}")

        results = await document_tools.discover_documents(session_id)

        # Format summary
        summary_lines = []
        for doc_type, count in sorted(results["classification_summary"].items()):
            summary_lines.append(f"  - {doc_type}: {count}")

        summary = "\n".join(summary_lines) if summary_lines else "  (none found)"

        return f"""✓ Document Discovery Complete

Session: {session_id}
Documents Found: {results['documents_found']}

Classification Summary:
{summary}

Use the /document-discovery prompt for detailed results and next steps.
"""

    except mcp_errors.SessionNotFoundError:
        return f"✗ Session not found: {session_id}"

    except Exception as e:
        logger.error(f"Failed to discover documents: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"


@mcp.tool()
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
    try:
        logger.info(f"Extracting PDF text: {filepath}")

        page_range = (start_page, end_page) if start_page and end_page else None
        results = await document_tools.extract_pdf_text(
            filepath, page_range, extract_tables
        )

        # Format response
        pages_text = f"Pages {start_page}-{end_page}" if page_range else "All pages"
        tables_info = f", {len(results.get('tables', []))} tables found" if extract_tables else ""

        response = f"""✓ PDF Text Extraction Complete

File: {filepath}
Pages: {pages_text}
Total Pages: {results['page_count']}
Characters Extracted: {len(results['full_text'])}{tables_info}

"""

        # Include first 2000 characters of text
        preview = results['full_text'][:2000]
        if len(results['full_text']) > 2000:
            preview += f"\n\n... ({len(results['full_text']) - 2000} more characters)"

        response += f"Text Preview:\n{preview}"

        return response

    except Exception as e:
        logger.error(f"Failed to extract PDF text: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def extract_gis_metadata(filepath: str) -> str:
    """Extract metadata from a GIS shapefile or GeoJSON.

    Args:
        filepath: Absolute path to GIS file (.shp or .geojson)

    Returns:
        GIS metadata including CRS, bounds, feature count
    """
    try:
        logger.info(f"Extracting GIS metadata: {filepath}")

        results = await document_tools.extract_gis_metadata(filepath)

        return f"""✓ GIS Metadata Extraction Complete

File: {filepath}
Driver: {results.get('driver', 'Unknown')}
CRS: {results.get('crs', 'Unknown')}
Geometry Type: {results.get('geometry_type', 'Unknown')}
Feature Count: {results.get('feature_count', 0)}
Bounds: {results.get('bounds', 'Unknown')}

Schema: {results.get('schema', 'Not available')}
"""

    except Exception as e:
        logger.error(f"Failed to extract GIS metadata: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"


# ============================================================================
# Evidence Extraction Tools (Phase 3)
# ============================================================================


@mcp.tool()
async def extract_evidence(session_id: str) -> str:
    """Extract evidence for all requirements from discovered documents.

    This tool maps each requirement in the checklist to relevant documents,
    extracts evidence snippets with page citations, and calculates coverage statistics.

    Args:
        session_id: Unique session identifier

    Returns:
        Summary of evidence extraction results with coverage statistics
    """
    try:
        logger.info(f"Extracting evidence for session: {session_id}")

        results = await evidence_tools.extract_all_evidence(session_id)

        # Format summary
        return f"""✓ Evidence Extraction Complete

Session: {session_id}

Coverage Summary:
  Total Requirements: {results['requirements_total']}
  ✅ Covered: {results['requirements_covered']} ({results['requirements_covered']/results['requirements_total']*100:.1f}%)
  ⚠️  Partial: {results['requirements_partial']} ({results['requirements_partial']/results['requirements_total']*100:.1f}%)
  ❌ Missing: {results['requirements_missing']} ({results['requirements_missing']/results['requirements_total']*100:.1f}%)
  Overall Coverage: {results['overall_coverage']*100:.1f}%

Results saved to: evidence.json
Session updated with coverage statistics

Use the /evidence-extraction prompt for detailed results and next steps.
"""

    except mcp_errors.SessionNotFoundError:
        return f"✗ Session not found: {session_id}"

    except Exception as e:
        logger.error(f"Failed to extract evidence: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def map_requirement(session_id: str, requirement_id: str) -> str:
    """Map a single requirement to documents and extract evidence.

    Args:
        session_id: Unique session identifier
        requirement_id: Requirement ID (e.g., "REQ-002", "REQ-007")

    Returns:
        Evidence details for the specific requirement
    """
    try:
        logger.info(f"Mapping requirement {requirement_id} for session: {session_id}")

        result = await evidence_tools.map_requirement(session_id, requirement_id)

        # Format response
        status_emoji = {
            "covered": "✅",
            "partial": "⚠️",
            "missing": "❌",
            "flagged": "🚩"
        }

        emoji = status_emoji.get(result['status'], "❓")

        response = f"""✓ Requirement Mapping Complete

{emoji} {result['requirement_id']}: {result['requirement_text']}

Status: {result['status'].upper()}
Confidence: {result['confidence']:.2f}
Category: {result['category']}

Mapped Documents ({len(result['mapped_documents'])}):
"""

        for doc in result['mapped_documents'][:5]:
            response += f"  - {doc['document_name']} (relevance: {doc['relevance_score']:.2f})\n"

        if len(result['mapped_documents']) > 5:
            response += f"  ... and {len(result['mapped_documents']) - 5} more\n"

        response += f"\nEvidence Snippets ({len(result['evidence_snippets'])}):\n"

        for idx, snippet in enumerate(result['evidence_snippets'][:3], 1):
            page_info = f" (page {snippet['page']})" if snippet.get('page') else ""
            section_info = f" - {snippet['section']}" if snippet.get('section') else ""
            response += f"\n{idx}. {snippet['document_name']}{page_info}{section_info}\n"
            response += f"   {snippet['text'][:150]}...\n"
            response += f"   Confidence: {snippet['confidence']:.2f}\n"

        if len(result['evidence_snippets']) > 3:
            response += f"\n... and {len(result['evidence_snippets']) - 3} more snippets\n"

        return response

    except mcp_errors.SessionNotFoundError:
        return f"✗ Session not found: {session_id}"

    except ValueError as e:
        return f"✗ {str(e)}"

    except Exception as e:
        logger.error(f"Failed to map requirement: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"


# ============================================================================
# Prompts
# ============================================================================


@mcp.prompt()
def list_capabilities() -> list[TextContent]:
    """List all MCP server capabilities and workflows.

    Returns:
        Overview of tools, prompts, and workflows available
    """
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

**Coming Soon (Phase 4-5):**
- Cross-document validation
- Report generation

### Workflows (7 Sequential Stages)

1. **Initialize** - Create session and load checklist
2. **Document Discovery** - Scan and classify all documents
3. **Evidence Extraction** - Map requirements to evidence
4. **Cross-Validation** - Verify consistency across documents
5. **Report Generation** - Generate structured review report
6. **Human Review** - Present flagged items for decision
7. **Complete** - Finalize and export report

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
- **Phase 4 (Validation & Reporting):** ✅ Complete (Cross-validation, report generation in Markdown/JSON)
- **Phase 5 (Integration & Polish):** 📋 Planned

**Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}
"""

    return [TextContent(type="text", text=capabilities)]


@mcp.prompt()
async def initialize_workflow(
    project_name: str | None = None,
    documents_path: str | None = None
) -> list[TextContent]:
    """Initialize a new registry review session (Stage 1).

    Creates a new review session with project metadata and prepares for document discovery.

    Args:
        project_name: Name of the project being reviewed
        documents_path: Absolute path to directory containing project documents

    Returns:
        Session creation results with next step guidance

    Examples:
        /initialize Botany Farm 2022-2023, /path/to/documents/22-23
        /initialize My Project, /home/user/projects/my-project
    """
    return await initialize.initialize_prompt(project_name, documents_path)


@mcp.prompt()
async def document_discovery_workflow(
    project_name: str | None = None,
    documents_path: str | None = None,
    session_id: str | None = None
) -> list[TextContent]:
    """Run the document discovery workflow for a session (Stage 2).

    Can create a new session or use an existing one.

    Args:
        project_name: Project name (creates session if provided with documents_path)
        documents_path: Absolute path to documents (creates session if provided with project_name)
        session_id: Optional session ID (overrides project_name/documents_path)

    Returns:
        Detailed document discovery results with next steps

    Examples:
        /document-discovery Botany Farm 2022-2023, /path/to/documents
        /document-discovery (uses most recent session)
    """
    return await document_discovery.document_discovery_prompt(project_name, documents_path, session_id)


@mcp.prompt()
async def evidence_extraction_workflow(session_id: str | None = None) -> list[TextContent]:
    """Run the evidence extraction workflow for a session (Stage 3).

    This prompt maps checklist requirements to discovered documents, extracts evidence
    snippets with page citations, and calculates coverage statistics.

    Args:
        session_id: Optional session identifier. If not provided, uses most recent session.

    Returns:
        Detailed evidence extraction results with coverage analysis

    Examples:
        /evidence-extraction (uses most recent session)
        /evidence-extraction session-abc123
    """
    result = await evidence_extraction.evidence_extraction(session_id)
    return [TextContent(type="text", text=result)]


@mcp.prompt()
async def cross_validation_workflow(session_id: str | None = None) -> list[TextContent]:
    """Run cross-document validation checks for a session (Stage 4).

    Validates consistency across documents including date alignment, land tenure,
    and project ID consistency. Flags discrepancies for human review.

    Args:
        session_id: Optional session identifier. If not provided, uses most recent session.

    Returns:
        Validation results with summary statistics and flagged items

    Examples:
        /cross-validation (uses most recent session)
        /cross-validation session-abc123
    """
    return await cross_validation.cross_validation_prompt(session_id)


@mcp.prompt()
async def report_generation_workflow(session_id: str | None = None) -> list[TextContent]:
    """Generate complete review report in multiple formats (Stage 5).

    Creates Markdown and JSON reports with all findings, evidence citations,
    validation results, and items requiring human review.

    Args:
        session_id: Optional session identifier. If not provided, uses most recent session.

    Returns:
        Report generation summary with paths to generated files

    Examples:
        /report-generation (uses most recent session)
        /report-generation session-abc123
    """
    return await report_generation.report_generation_prompt(session_id)


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
