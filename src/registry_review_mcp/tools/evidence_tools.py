"""Evidence extraction and requirement mapping tools."""

import re
from pathlib import Path
from typing import Any

from ..config.settings import settings
from ..models.evidence import (
    EvidenceSnippet,
    MappedDocument,
    RequirementEvidence,
    EvidenceExtractionResult,
    StructuredField,
)
from ..models.errors import SessionNotFoundError, DocumentExtractionError
from ..utils.state import StateManager, get_session_or_raise


# Stop words to filter out from keyword extraction
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "will", "with",
    "shall", "must", "should", "may", "can", "or", "provide", "evidence",
}


def extract_keywords(requirement: dict[str, Any]) -> list[str]:
    """Extract search keywords from a requirement.
    """
    # Combine requirement text and accepted evidence
    text = requirement.get("requirement_text", "")
    evidence = requirement.get("accepted_evidence", "")
    combined = f"{text} {evidence}".lower()

    # Extract words (alphanumeric sequences)
    words = re.findall(r'\b[a-z]{3,}\b', combined)

    # Filter stop words and deduplicate
    keywords = []
    seen = set()
    for word in words:
        if word not in STOP_WORDS and word not in seen:
            keywords.append(word)
            seen.add(word)

    # Extract important phrases (2-3 words)
    phrases = re.findall(r'\b([a-z]+\s+[a-z]+(?:\s+[a-z]+)?)\b', combined)
    for phrase in phrases:
        phrase = phrase.strip()
        # Only add if not mostly stop words
        phrase_words = phrase.split()
        if len(phrase_words) >= 2:
            non_stop = [w for w in phrase_words if w not in STOP_WORDS]
            if len(non_stop) >= 2:
                if phrase not in seen:
                    keywords.append(phrase)
                    seen.add(phrase)

    return keywords[:20]  # Limit to top 20 keywords/phrases


async def get_markdown_content(document: dict[str, Any], session_id: str) -> str | None:
    """Get markdown content for a document, converting lazily if needed.

    This implements lazy PDF→markdown conversion during evidence extraction (Stage 5)
    rather than eagerly during discovery (Stage 2). Only converts PDFs when actually
    needed for evidence extraction.
    """
    # First: Check if document has markdown_path from discovery
    if document.get("has_markdown") and document.get("markdown_path"):
        md_path = Path(document["markdown_path"])
        if md_path.exists():
            return md_path.read_text(encoding="utf-8")

    # Fallback 1: Try to find markdown version manually
    pdf_path = Path(document["filepath"])
    parent_dir = pdf_path.parent
    stem = pdf_path.stem

    # Check for markdown in subdirectory (marker output format)
    md_path = parent_dir / stem / f"{stem}.md"

    if md_path.exists():
        return md_path.read_text(encoding="utf-8")

    # Fallback 2: check for .md next to .pdf
    md_path_alt = pdf_path.with_suffix(".md")
    if md_path_alt.exists():
        return md_path_alt.read_text(encoding="utf-8")

    # Lazy conversion: If no markdown exists and this is a PDF, convert it now
    # This only happens during evidence extraction when content is actually needed
    if document["filepath"].lower().endswith(".pdf"):
        try:
            from ..extractors.marker_extractor import convert_pdf_to_markdown

            # Convert PDF to markdown on-demand
            markdown_result = await convert_pdf_to_markdown(document["filepath"])

            # Cache the markdown next to the PDF for future use
            md_cache_path = pdf_path.with_suffix('.md')
            md_cache_path.write_text(markdown_result["markdown"], encoding="utf-8")

            return markdown_result["markdown"]
        except Exception as e:
            # If conversion fails, return None and let caller handle it
            print(f"⚠️  Lazy markdown conversion failed for {pdf_path.name}: {e}")
            return None

    return None


async def calculate_relevance_score(
    document: dict[str, Any],
    keywords: list[str],
    session_id: str
) -> float:
    """Calculate relevance score for a document based on keyword matches.
    """
    content = await get_markdown_content(document, session_id)
    if not content:
        return 0.0

    content_lower = content.lower()
    total_keywords = len(keywords)
    matches = 0
    match_density = 0

    for keyword in keywords:
        keyword_lower = keyword.lower()
        count = content_lower.count(keyword_lower)
        if count > 0:
            matches += 1
            # Bonus for multiple occurrences
            match_density += min(count, 5) / 5.0

    # Score based on percentage of keywords found + density bonus
    coverage_score = matches / total_keywords if total_keywords > 0 else 0.0
    density_bonus = (match_density / total_keywords) * 0.3 if total_keywords > 0 else 0.0

    return min(coverage_score + density_bonus, 1.0)


def extract_page_number(text_before: str) -> int | None:
    """Extract page number from page markers in markdown.
    """
    # Look for page markers like ![](_page_3_Picture_0.jpeg)
    page_markers = re.findall(r'!\[\]\(_page_(\d+)_', text_before)
    if page_markers:
        # Get the last page marker before this position
        return int(page_markers[-1]) + 1  # Convert to 1-indexed

    return None


def extract_section_header(text_before: str, max_distance: int = 500) -> str | None:
    """Extract the most recent section header before a match.
    """
    # Limit lookback
    lookback = text_before[-max_distance:] if len(text_before) > max_distance else text_before

    # Look for markdown headers (# Header, ## Header, etc.)
    headers = re.findall(r'^#{1,6}\s+(.+)$', lookback, re.MULTILINE)
    if headers:
        return headers[-1].strip()

    return None


async def extract_evidence_snippets(
    document: dict[str, Any],
    keywords: list[str],
    session_id: str,
    max_snippets: int = 5,
    context_words: int = 100
) -> list[EvidenceSnippet]:
    """Extract evidence snippets from a document.
    """
    content = await get_markdown_content(document, session_id)
    if not content:
        return []

    snippets = []
    content_lower = content.lower()

    # Search for each keyword
    for keyword in keywords[:10]:  # Limit keywords processed
        keyword_lower = keyword.lower()
        pattern = re.compile(r'\b' + re.escape(keyword_lower) + r'\b', re.IGNORECASE)

        for match in pattern.finditer(content):
            start_pos = match.start()
            end_pos = match.end()

            # Extract context
            words_before = content[:start_pos].split()[-context_words:]
            words_after = content[end_pos:].split()[:context_words]
            words_match = content[start_pos:end_pos].split()

            snippet_text = ' '.join(words_before + words_match + words_after)

            # Truncate to fit within EvidenceSnippet max_length (5000 chars)
            # This can happen with tables or very long markdown content
            if len(snippet_text) > 5000:
                snippet_text = snippet_text[:4997] + "..."

            # Extract page and section
            text_before = content[:start_pos]
            page = extract_page_number(text_before)
            section = extract_section_header(text_before)

            # Calculate confidence based on keyword density
            snippet_lower = snippet_text.lower()
            keywords_in_snippet = sum(1 for kw in keywords if kw.lower() in snippet_lower)
            confidence = min(keywords_in_snippet / len(keywords), 1.0) if keywords else 0.5

            snippet = EvidenceSnippet(
                text=snippet_text,
                document_id=document["document_id"],
                document_name=document["filename"],
                page=page,
                section=section,
                confidence=confidence,
                keywords_matched=[keyword]
            )

            snippets.append(snippet)

            if len(snippets) >= max_snippets:
                break

        if len(snippets) >= max_snippets:
            break

    # Sort by confidence and return top N
    snippets.sort(key=lambda s: s.confidence, reverse=True)
    return snippets[:max_snippets]


async def map_requirement(
    session_id: str,
    requirement_id: str
) -> dict[str, Any]:
    """Map a single requirement to documents and extract evidence.
    """
    state_manager = StateManager(session_id)

    # Load documents
    if not state_manager.exists("documents.json"):
        raise SessionNotFoundError(
            f"Documents not discovered for session {session_id}",
            details={"session_id": session_id}
        )

    docs_data = state_manager.read_json("documents.json")
    documents = docs_data.get("documents", [])

    # Load checklist
    checklist_path = settings.get_checklist_path("soil-carbon-v1.2.2")
    import json
    with open(checklist_path, "r") as f:
        checklist_data = json.load(f)
    requirements = checklist_data.get("requirements", [])

    # Find the requirement
    requirement = next((r for r in requirements if r["requirement_id"] == requirement_id), None)
    if not requirement:
        raise ValueError(f"Requirement {requirement_id} not found in checklist")

    # Extract keywords
    keywords = extract_keywords(requirement)

    # Score all documents
    scored_docs = []
    for doc in documents:
        score = await calculate_relevance_score(doc, keywords, session_id)
        if score > 0.1:  # Only include docs with some relevance
            scored_docs.append({
                "document": doc,
                "score": score
            })

    # Sort by relevance
    scored_docs.sort(key=lambda x: x["score"], reverse=True)

    # Map documents
    mapped_documents = []
    all_snippets = []

    for scored in scored_docs[:5]:  # Top 5 documents
        doc = scored["document"]
        mapped_doc = MappedDocument(
            document_id=doc["document_id"],
            document_name=doc["filename"],
            filepath=doc["filepath"],
            relevance_score=scored["score"],
            keywords_found=keywords
        )
        mapped_documents.append(mapped_doc)

        # Extract snippets from this document
        snippets = await extract_evidence_snippets(doc, keywords, session_id, max_snippets=3)
        all_snippets.extend(snippets)

    # Determine status and confidence
    if not all_snippets:
        status = "missing"
        confidence = 0.0
    elif all_snippets and all_snippets[0].confidence > 0.8:
        status = "covered"
        confidence = all_snippets[0].confidence
    elif all_snippets:
        status = "partial"
        confidence = max(s.confidence for s in all_snippets)
    else:
        status = "flagged"
        confidence = 0.5

    evidence = RequirementEvidence(
        requirement_id=requirement_id,
        requirement_text=requirement.get("requirement_text", ""),
        category=requirement.get("category", ""),
        status=status,
        confidence=confidence,
        mapped_documents=mapped_documents,
        evidence_snippets=all_snippets
    )

    return evidence.model_dump()


async def extract_all_evidence(session_id: str) -> dict[str, Any]:
    """Extract evidence for all requirements from mapped documents.

    This is Stage 4 of the workflow. It requires that Stage 3 (Requirement Mapping)
    has been completed first. Evidence is only extracted from documents that have been
    mapped to requirements.
    """
    state_manager = StateManager(session_id)

    # Check that requirement mapping was completed (Stage 3)
    session_data = state_manager.read_json("session.json")
    workflow_progress = session_data.get("workflow_progress", {})

    if workflow_progress.get("requirement_mapping") != "completed":
        raise ValueError(
            "Requirement mapping not complete. Run Stage 3 first: /C-requirement-mapping\n\n"
            "Evidence extraction requires mapped documents. You must complete requirement "
            "mapping before extracting evidence."
        )

    # Load mappings from Stage 3
    if not state_manager.exists("mappings.json"):
        raise FileNotFoundError(
            "mappings.json not found. Run Stage 3 first: /C-requirement-mapping"
        )

    mappings_data = state_manager.read_json("mappings.json")
    mappings = {m["requirement_id"]: m for m in mappings_data.get("mappings", [])}

    # Load checklist
    checklist_path = settings.get_checklist_path("soil-carbon-v1.2.2")
    import json
    with open(checklist_path, "r") as f:
        checklist_data = json.load(f)
    requirements = checklist_data.get("requirements", [])

    total_requirements = len(requirements)
    mapped_count = sum(1 for m in mappings.values() if m.get("mapped_documents"))
    print(f"📋 Extracting evidence for {total_requirements} requirements ({mapped_count} mapped)", flush=True)

    # Extract evidence for each requirement with progress
    all_evidence = []
    for i, requirement in enumerate(requirements, 1):
        requirement_id = requirement["requirement_id"]
        mapping = mappings.get(requirement_id)

        # Show progress every 5 requirements or on first/last
        if i % 5 == 0 or i == 1 or i == total_requirements:
            percentage = (i / total_requirements * 100)
            print(f"  ⏳ Processing {i}/{total_requirements} ({percentage:.0f}%): {requirement_id}", flush=True)

        # Skip unmapped requirements - mark as missing
        if not mapping or not mapping.get("mapped_documents"):
            print(f"  ⏭️  Skipping unmapped: {requirement_id}", flush=True)
            all_evidence.append(RequirementEvidence(
                requirement_id=requirement_id,
                requirement_text=requirement.get("requirement_text", ""),
                category=requirement.get("category", ""),
                status="missing",
                confidence=0.0,
                mapped_documents=[],
                evidence_snippets=[],
                notes="No documents mapped to this requirement in Stage 3"
            ))
            continue

        # Extract evidence only from mapped documents
        try:
            evidence = await map_requirement(session_id, requirement_id)
            all_evidence.append(RequirementEvidence(**evidence))
        except Exception as e:
            # Create a flagged entry for failed requirements
            # Note: mapped_documents should be empty list for error cases
            # since we can't construct MappedDocument objects without full document data
            print(f"⚠️  Warning: Failed to extract {requirement_id}: {e}", flush=True)
            all_evidence.append(RequirementEvidence(
                requirement_id=requirement_id,
                requirement_text=requirement.get("requirement_text", ""),
                category=requirement.get("category", ""),
                status="flagged",
                confidence=0.0,
                mapped_documents=[],  # Can't include partial data - let map_requirement handle it
                evidence_snippets=[],
                notes=f"Error during extraction: {str(e)}"
            ))

    # Calculate statistics
    covered = sum(1 for e in all_evidence if e.status == "covered")
    partial = sum(1 for e in all_evidence if e.status == "partial")
    missing = sum(1 for e in all_evidence if e.status == "missing")
    flagged = sum(1 for e in all_evidence if e.status == "flagged")

    overall_coverage = (covered + (partial * 0.5)) / len(all_evidence) if all_evidence else 0.0

    # Show completion summary
    print(f"✅ Evidence extraction complete:", flush=True)
    print(f"   • Covered: {covered} ({covered/total_requirements*100:.0f}%)", flush=True)
    print(f"   • Partial: {partial} ({partial/total_requirements*100:.0f}%)", flush=True)
    print(f"   • Missing: {missing} ({missing/total_requirements*100:.0f}%)", flush=True)
    if flagged > 0:
        print(f"   • Flagged: {flagged} (needs attention)", flush=True)

    result = EvidenceExtractionResult(
        session_id=session_id,
        requirements_total=len(requirements),
        requirements_covered=covered,
        requirements_partial=partial,
        requirements_missing=missing,
        requirements_flagged=flagged,
        overall_coverage=overall_coverage,
        evidence=[e for e in all_evidence]
    )

    # Save to state
    state_manager.write_json("evidence.json", result.model_dump())

    # Update session workflow progress
    session_data = state_manager.read_json("session.json")
    session_data["workflow_progress"]["evidence_extraction"] = "completed"
    session_data["statistics"]["requirements_covered"] = covered
    session_data["statistics"]["requirements_partial"] = partial
    session_data["statistics"]["requirements_missing"] = missing
    state_manager.write_json("session.json", session_data)

    return result.model_dump()


async def extract_structured_field(
    session_id: str,
    field_name: str,
    field_patterns: list[str]
) -> dict[str, Any] | None:
    """Extract a specific structured field from documents.
    """
    state_manager = StateManager(session_id)
    docs_data = state_manager.read_json("documents.json")
    documents = docs_data.get("documents", [])

    for doc in documents:
        content = await get_markdown_content(doc, session_id)
        if not content:
            continue

        for pattern in field_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                value = match.group(1) if match.groups() else match.group(0)

                # Extract page number
                text_before = content[:match.start()]
                page = extract_page_number(text_before)

                field = StructuredField(
                    field_name=field_name,
                    field_value=value.strip(),
                    source_document=doc["document_id"],
                    page=page,
                    confidence=0.9,  # High confidence for regex matches
                    extraction_method="regex"
                )

                return field.model_dump()

    return None
