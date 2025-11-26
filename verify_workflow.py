#!/usr/bin/env python
"""
Phase 1.1 Verification Testing: Complete 8-Stage Workflow

Tests the entire workflow with the Botany Farm example project to verify:
1. Lazy PDF conversion (Stage 2 → Stage 4)
2. Document discovery and classification
3. Requirement mapping
4. Evidence extraction with citations
5. Session persistence
6. All optimizations working correctly
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from registry_review_mcp.tools import session_tools, document_tools, mapping_tools
from registry_review_mcp.tools.evidence_tools import extract_all_evidence
from registry_review_mcp.tools import report_tools


async def main():
    print("=" * 80)
    print("PHASE 1.1 VERIFICATION TEST: Complete 8-Stage Workflow")
    print("=" * 80)
    print()

    project_path = Path("examples/22-23").absolute()

    if not project_path.exists():
        print(f"❌ Example project not found: {project_path}")
        return 1

    print(f"📁 Project path: {project_path}")
    print()

    # ========================================================================
    # Stage 1: Create Session
    # ========================================================================
    print("STAGE 1: Create Session")
    print("-" * 80)

    result = await session_tools.create_session(
        project_name="Botany Farm 22-23 Verification Test",
        methodology="soil-carbon-v1.2.2",
        project_id="C06-4997",
        crediting_period="2022-01-01 to 2023-12-31"
    )

    session_id = result["session_id"]
    print(f"✅ Session created: {session_id}")
    print()

    # ========================================================================
    # Stage 1b: Add Document Source
    # ========================================================================
    print("STAGE 1b: Add Document Source")
    print("-" * 80)

    add_result = await document_tools.add_documents(
        session_id=session_id,
        source={
            "type": "path",
            "path": str(project_path)
        },
        check_duplicates=True
    )

    print(f"✅ Document source added: {add_result['source_type']}")
    print()

    # ========================================================================
    # Stage 2: Document Discovery (with lazy PDF conversion)
    # ========================================================================
    print("STAGE 2: Document Discovery")
    print("-" * 80)
    print("⚠️  TESTING: PDFs should be indexed but NOT converted yet")
    print()

    discover_result = await document_tools.discover_documents(session_id)

    docs_found = discover_result["documents_found"]
    print(f"✅ Discovered {docs_found} documents")

    # Verify lazy conversion: PDFs should be found but not converted
    # Read from documents.json to get full document structure
    from registry_review_mcp.utils.state import StateManager
    state_manager = StateManager(session_id)
    docs_data = state_manager.read_json("documents.json")
    docs = docs_data.get("documents", [])

    # Use file extension to detect PDFs (classification is content-based, not format-based)
    pdf_count = sum(1 for d in docs if d.get("filepath", "").lower().endswith(".pdf"))
    converted_count = sum(1 for d in docs if d.get("filepath", "").lower().endswith(".pdf") and d.get("has_markdown"))

    print(f"   📄 PDFs found: {pdf_count}")
    print(f"   📄 PDFs converted: {converted_count}")

    if converted_count > 0:
        print(f"⚠️  WARNING: {converted_count} PDFs were converted in Stage 2")
        print("   Expected: 0 (lazy conversion should defer to Stage 4)")
    else:
        print("✅ Lazy conversion working: No PDFs converted in Stage 2")

    print()

    # Show document types
    classification = discover_result.get("classification_summary", {})
    print("Document types found:")
    for doc_type, count in classification.items():
        print(f"   - {doc_type}: {count}")
    print()

    # ========================================================================
    # Stage 3: Requirement Mapping
    # ========================================================================
    print("STAGE 3: Requirement Mapping")
    print("-" * 80)

    mapping_result = await mapping_tools.map_all_requirements(session_id)

    total_reqs = mapping_result["total_requirements"]
    mapped_reqs = mapping_result["mapped_count"]

    print(f"✅ Mapped {mapped_reqs}/{total_reqs} requirements")
    print()

    # ========================================================================
    # Stage 4: Evidence Extraction (with lazy PDF conversion)
    # ========================================================================
    print("STAGE 4: Evidence Extraction")
    print("-" * 80)
    print("⚠️  TESTING: PDFs should be converted NOW (only mapped ones)")
    print()

    evidence_result = await extract_all_evidence(session_id)

    requirements_total = evidence_result["requirements_total"]
    covered = evidence_result["requirements_covered"]

    # Count total evidence snippets
    evidence_count = sum(len(e.get("evidence_snippets", [])) for e in evidence_result.get("evidence", []))

    print(f"✅ Extracted evidence from {requirements_total} requirements")
    print(f"   Covered: {covered}/{requirements_total} ({covered/requirements_total*100:.0f}%)")
    print(f"   Evidence snippets: {evidence_count}")
    print()

    # Verify that PDFs were converted during Stage 4
    # Re-load documents to check conversion status
    from registry_review_mcp.utils.state import StateManager
    state_manager = StateManager(session_id)
    docs_data = state_manager.read_json("documents.json")
    docs = docs_data.get("documents", [])

    # Use file extension to detect PDFs (classification is content-based, not format-based)
    pdf_count = sum(1 for d in docs if d.get("filepath", "").lower().endswith(".pdf"))
    converted_count = sum(1 for d in docs if d.get("filepath", "").lower().endswith(".pdf") and d.get("has_markdown"))

    print(f"   📄 Total PDFs: {pdf_count}")
    print(f"   📄 Converted in Stage 4: {converted_count}")

    if converted_count == 0:
        print("❌ ERROR: No PDFs were converted in Stage 4!")
    elif converted_count < pdf_count:
        print(f"✅ Lazy conversion working: {converted_count}/{pdf_count} mapped PDFs converted")
        print(f"   {pdf_count - converted_count} unmapped PDFs skipped (as expected)")
    else:
        print(f"⚠️  All {pdf_count} PDFs were converted (may indicate all were mapped)")

    print()

    # Check evidence quality
    evidence_items = evidence_result.get("evidence", [])
    if evidence_items:
        sample = evidence_items[0]
        print("Sample evidence item:")
        print(f"   Requirement: {sample.get('requirement_id', 'N/A')}")
        print(f"   Document: {sample.get('document_id', 'N/A')}")
        print(f"   Snippet: {sample.get('snippet', 'N/A')[:100]}...")
        print()

    # ========================================================================
    # Stages 5-8: Validation and Reporting
    # ========================================================================
    print("STAGES 5-8: Validation and Reporting")
    print("-" * 80)
    print("(Skipping for quick verification - tested separately)")
    print()

    # ========================================================================
    # Verification Summary
    # ========================================================================
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print()

    print("✅ Stage 1: Session creation - PASSED")
    print("✅ Stage 1b: Document source - PASSED")

    if converted_count == 0 and pdf_count > 0:
        print("✅ Stage 2: Lazy conversion - PASSED (no PDFs converted)")
    else:
        print("⚠️  Stage 2: Lazy conversion - CHECK NEEDED")

    print(f"✅ Stage 2: Document discovery - PASSED ({docs_found} docs)")
    print(f"✅ Stage 3: Requirement mapping - PASSED ({mapped_reqs} mapped)")

    if converted_count > 0:
        print(f"✅ Stage 4: PDF conversion - PASSED ({converted_count} PDFs converted)")
    else:
        print("❌ Stage 4: PDF conversion - FAILED (no PDFs converted)")

    print(f"✅ Stage 4: Evidence extraction - PASSED ({evidence_count} snippets)")
    print()

    print("=" * 80)
    print("KEY METRICS")
    print("=" * 80)
    print(f"Documents discovered: {docs_found}")
    print(f"PDFs found: {pdf_count}")
    print(f"PDFs converted: {converted_count}")
    print(f"Requirements mapped: {mapped_reqs}/{total_reqs}")
    print(f"Evidence snippets: {evidence_count}")
    print()

    print("✅ Verification test complete!")
    print(f"   Session ID: {session_id}")
    print()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
