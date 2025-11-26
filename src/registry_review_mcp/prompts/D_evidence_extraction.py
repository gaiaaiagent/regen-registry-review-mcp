"""Evidence extraction workflow - Stage 4 of registry review."""

from ..tools import session_tools
from ..tools.evidence_tools import extract_all_evidence
from ..models.errors import SessionNotFoundError
from .helpers import (
    format_error,
    format_workflow_header,
    format_next_steps_section,
)


async def evidence_extraction(session_id: str | None = None) -> str:
    """Execute evidence extraction workflow.

    This prompt orchestrates the evidence extraction process:
    1. Loads documents from session
    2. Maps each requirement to relevant documents
    3. Extracts evidence snippets with citations
    4. Calculates coverage statistics
    5. Saves results to evidence.json

    Args:
        session_id: Optional session identifier. If not provided, uses most recent session.

    Returns:
        Formatted report of extraction results
    """
    # Handle session selection
    if not session_id:
        sessions = await session_tools.list_sessions()
        if not sessions:
            return """# Evidence Extraction Workflow

No review sessions found. To extract evidence, you need to:

1. **Create a session** with `/document-discovery` or by running the document discovery prompt
2. **Run this prompt again** and it will automatically extract evidence

**Quick Start:** Use `/document-discovery` first to create a session and discover documents.
"""
        # Use most recent session
        session_id = sessions[0]["session_id"]
        print(f"Auto-selected most recent session: {session_id}")

    # Verify session exists
    try:
        session = await session_tools.load_session(session_id)
    except SessionNotFoundError:
        sessions = await session_tools.list_sessions()
        session_list = "\n".join([f"- {s['session_id']} ({s['project_name']})" for s in sessions])
        return f"""Session '{session_id}' not found.

Available sessions:
{session_list}

Use one of the above session IDs or create a new session.
"""

    # Check if documents have been discovered
    if session.get("statistics", {}).get("documents_found", 0) == 0:
        return f"""Session '{session_id}' has no documents yet.

Run document discovery first: `/document-discovery {session_id}`
"""

    project_name = session.get("project_metadata", {}).get("project_name", "Unknown")

    try:
        # Run evidence extraction (optimized with LLM)
        results = await extract_all_evidence(session_id)

        # Build header
        header = format_workflow_header("Evidence Extraction", session_id, project_name)

        # Build coverage summary
        total = results['requirements_total']
        covered = results['requirements_covered']
        partial = results['requirements_partial']
        missing = results['requirements_missing']
        coverage_pct = results['overall_coverage'] * 100

        content = f"""## ✅ Evidence Extraction Complete

**Coverage Summary:**
- ✅ Covered: {covered}/{total} ({covered/total*100:.1f}%)
- ⚠️  Partial: {partial}/{total} ({partial/total*100:.1f}%)
- ❌ Missing: {missing}/{total} ({missing/total*100:.1f}%)
- **Overall Coverage: {coverage_pct:.1f}%**

All requirements have been mapped to documents and evidence extracted.
Results saved to evidence.json.
"""

        next_steps = format_next_steps_section([
            "Review coverage statistics above",
            "Run cross-validation: `/cross-validation`",
            f"Or examine specific requirements: `map_requirement {session_id} REQ-###`"
        ])

        return header + content + next_steps

    except Exception as e:
        return str(format_error(
            "Evidence Extraction Failed",
            f"An error occurred: {str(e)}",
            "Please check the session and try again."
        )[0].text)
