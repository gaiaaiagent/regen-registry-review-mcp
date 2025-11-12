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
from .tools import session_tools, document_tools
from .prompts import document_discovery

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
- `create_session` - Create new review session
- `load_session` - Load existing session
- `update_session_state` - Update session progress
- `list_sessions` - List all sessions
- `delete_session` - Delete a session

**Document Processing (Phase 2):**
- `discover_documents` - Scan and classify project documents
- `extract_pdf_text` - Extract text from PDF files
- `extract_gis_metadata` - Extract GIS shapefile metadata

**Coming Soon (Phase 3-5):**
- Evidence extraction and requirement mapping
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

1. Create a session:
   ```
   create_session(
       project_name="Botany Farm",
       documents_path="/absolute/path/to/documents",
       methodology="soil-carbon-v1.2.2"
   )
   ```

2. Next steps will be provided after session creation

## Status

- **Phase 1 (Foundation):** ✅ Complete (Session management, infrastructure)
- **Phase 2 (Document Processing):** 🚧 In Progress
- **Phase 3 (Evidence Extraction):** 📋 Planned
- **Phase 4 (Validation & Reporting):** 📋 Planned
- **Phase 5 (Integration & Polish):** 📋 Planned

**Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}
"""

    return [TextContent(type="text", text=capabilities)]


@mcp.prompt()
async def document_discovery_workflow(session_id: str) -> list[TextContent]:
    """Run the document discovery workflow for a session.

    Args:
        session_id: Unique session identifier

    Returns:
        Detailed document discovery results with next steps
    """
    return await document_discovery.document_discovery_prompt(session_id)


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
