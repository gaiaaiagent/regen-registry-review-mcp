"""Evidence extraction workflow prompt."""

from ..config.settings import settings
from ..tools import session_tools, evidence_tools
from ..models.errors import SessionNotFoundError


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

1. **Create a session** with `/document-discovery` or by running:
   - The document discovery prompt will guide you through session creation

2. **Run this prompt again** and it will automatically extract evidence

**Quick Start:**
Use the document discovery prompt first: `/document-discovery`

It will help you create a session and discover documents, then you can return here for evidence extraction.
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
    workflow = session.get("workflow_progress", {})
    if workflow.get("document_discovery") != "completed":
        return f"""Documents have not been discovered for session {session_id}.

Please run document discovery first:
```python
await discover_documents("{session_id}")
```
"""

    # Extract project info from nested structure
    project_metadata = session.get('project_metadata', {})
    project_name = project_metadata.get('project_name', 'Unknown')
    methodology = project_metadata.get('methodology', 'Unknown')

    print(f"\n{'='*80}")
    print(f"Evidence Extraction for: {project_name}")
    print(f"Session: {session_id}")
    print(f"Methodology: {methodology}")
    print(f"{'='*80}\n")

    # Run evidence extraction (use LLM-native if enabled)
    if settings.use_llm_native_extraction:
        print("🤖 Using LLM-native unified analysis...")
        print("This may take a few moments...\n")
        from ..tools import analyze_llm
        results = await analyze_llm.extract_all_evidence_llm(session_id)
    else:
        print("Extracting evidence for all requirements...")
        print("This may take a few moments...\n")
        results = await evidence_tools.extract_all_evidence(session_id)

    # Format results
    report = []
    report.append(f"\n{'='*80}")
    report.append("EVIDENCE EXTRACTION RESULTS")
    report.append(f"{'='*80}\n")

    # Summary statistics
    report.append("📊 Coverage Summary:")
    report.append(f"  Total Requirements: {results['requirements_total']}")
    report.append(f"  ✅ Covered: {results['requirements_covered']} ({results['requirements_covered']/results['requirements_total']*100:.1f}%)")
    report.append(f"  ⚠️  Partial: {results['requirements_partial']} ({results['requirements_partial']/results['requirements_total']*100:.1f}%)")
    report.append(f"  ❌ Missing: {results['requirements_missing']} ({results['requirements_missing']/results['requirements_total']*100:.1f}%)")
    if results['requirements_flagged'] > 0:
        report.append(f"  🚩 Flagged: {results['requirements_flagged']} ({results['requirements_flagged']/results['requirements_total']*100:.1f}%)")
    report.append(f"  Overall Coverage: {results['overall_coverage']*100:.1f}%\n")

    # Requirements by status
    evidence_list = results['evidence']

    # Show covered requirements
    covered = [e for e in evidence_list if e['status'] == 'covered']
    if covered:
        report.append(f"✅ COVERED REQUIREMENTS ({len(covered)}):")
        for ev in covered[:5]:  # Show first 5
            report.append(f"  {ev['requirement_id']}: {ev['requirement_text'][:60]}...")
            report.append(f"    Confidence: {ev['confidence']:.2f}")
            report.append(f"    Documents: {len(ev['mapped_documents'])}")
            report.append(f"    Snippets: {len(ev['evidence_snippets'])}")
        if len(covered) > 5:
            report.append(f"  ... and {len(covered) - 5} more")
        report.append("")

    # Show partial requirements
    partial = [e for e in evidence_list if e['status'] == 'partial']
    if partial:
        report.append(f"⚠️  PARTIAL REQUIREMENTS ({len(partial)}):")
        for ev in partial[:5]:  # Show first 5
            report.append(f"  {ev['requirement_id']}: {ev['requirement_text'][:60]}...")
            report.append(f"    Confidence: {ev['confidence']:.2f}")
            report.append(f"    Documents: {len(ev['mapped_documents'])}")
            report.append(f"    Snippets: {len(ev['evidence_snippets'])}")
        if len(partial) > 5:
            report.append(f"  ... and {len(partial) - 5} more")
        report.append("")

    # Show missing requirements (needs attention)
    missing = [e for e in evidence_list if e['status'] == 'missing']
    if missing:
        report.append(f"❌ MISSING REQUIREMENTS ({len(missing)}) - NEEDS ATTENTION:")
        for ev in missing:
            report.append(f"  {ev['requirement_id']}: {ev['requirement_text'][:80]}...")
            report.append(f"    Category: {ev['category']}")
        report.append("")

    # Show flagged requirements (errors)
    flagged = [e for e in evidence_list if e['status'] == 'flagged']
    if flagged:
        report.append(f"🚩 FLAGGED REQUIREMENTS ({len(flagged)}) - ERRORS:")
        for ev in flagged:
            report.append(f"  {ev['requirement_id']}: {ev['requirement_text'][:80]}...")
            report.append(f"    Notes: {ev.get('notes', 'Unknown error')}")
        report.append("")

    # Next steps
    report.append(f"{'='*80}")
    report.append("NEXT STEPS:")
    report.append(f"{'='*80}\n")

    if results['requirements_missing'] > 0 or results['requirements_flagged'] > 0:
        report.append("⚠️  Action Required:")
        report.append("  Some requirements need attention. Consider:")
        report.append("  1. Review missing requirements and add supporting documents")
        report.append("  2. Investigate flagged requirements for errors")
        report.append("  3. Re-run evidence extraction after adding documents\n")

    report.append("📄 Results saved to: evidence.json")
    report.append("📊 Session updated with coverage statistics")
    report.append(f"\nView detailed evidence for a specific requirement:")
    report.append("```python")
    report.append(f'evidence = await map_requirement("{session_id}", "REQ-XXX")')
    report.append("```\n")

    return "\n".join(report)
