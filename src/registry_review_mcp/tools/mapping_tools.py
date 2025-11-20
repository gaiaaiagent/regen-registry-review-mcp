"""Requirement mapping tools for mapping documents to checklist requirements.

Stage 3 of the registry review workflow.
"""

import json
from datetime import datetime, timezone
from typing import Any

from ..config.settings import settings
from ..models.schemas import (
    RequirementMapping,
    MappingCollection,
    ConfidenceScore,
)
from ..utils.state import StateManager, get_session_or_raise


async def map_all_requirements(session_id: str) -> dict[str, Any]:
    """Map all requirements to documents using semantic matching.

    This function:
    1. Loads the checklist for the session methodology
    2. Loads discovered documents from Stage 2
    3. For each requirement, suggests document matches
    4. Generates confidence scores for suggestions
    5. Stores mappings in mappings.json

    Args:
        session_id: Unique session identifier

    Returns:
        Summary of mapping results with statistics
    """
    state_manager = get_session_or_raise(session_id)

    # Load session to get methodology
    session_data = state_manager.read_json("session.json")
    methodology = session_data.get("project_metadata", {}).get("methodology", "soil-carbon-v1.2.2")

    # Load checklist
    checklist_path = settings.get_checklist_path(methodology)
    if not checklist_path.exists():
        raise FileNotFoundError(f"Checklist not found for methodology: {methodology}")

    with open(checklist_path, "r") as f:
        checklist_data = json.load(f)

    requirements = checklist_data.get("requirements", [])

    # Load discovered documents
    documents_data = state_manager.read_json("documents.json")
    documents = documents_data.get("documents", documents_data)

    if not documents:
        raise ValueError("No documents discovered. Run document discovery first (Stage 2).")

    # Create document lookup by ID and classification
    doc_by_id = {doc["document_id"]: doc for doc in documents}
    docs_by_type = {}
    for doc in documents:
        classification = doc.get("classification", "unknown")
        if classification not in docs_by_type:
            docs_by_type[classification] = []
        docs_by_type[classification].append(doc)

    # Map each requirement to documents
    mappings = []
    mapped_count = 0
    unmapped_count = 0

    for req in requirements:
        requirement_id = req["requirement_id"]
        category = req.get("category", "")
        accepted_evidence = req.get("accepted_evidence", "").lower()

        # Determine expected document types based on requirement
        expected_types = _infer_document_types(category, accepted_evidence)

        # Find matching documents
        matched_docs = []
        confidence = 0.0

        for doc_type in expected_types:
            if doc_type in docs_by_type:
                for doc in docs_by_type[doc_type]:
                    matched_docs.append(doc["document_id"])

        # Calculate confidence based on match quality
        if matched_docs:
            # High confidence if we found expected type
            confidence = 0.85 if len(matched_docs) == 1 else 0.75
            mapping_status = "suggested"
            mapped_count += 1
        else:
            # Try fallback: any document might contain relevant info
            if "project_plan" in docs_by_type or "project-plan" in docs_by_type:
                # Project plan often contains most information
                project_plans = docs_by_type.get("project_plan", docs_by_type.get("project-plan", []))
                if project_plans:
                    matched_docs = [project_plans[0]["document_id"]]
                    confidence = 0.50  # Lower confidence for fallback
                    mapping_status = "suggested"
                    mapped_count += 1
                else:
                    mapping_status = "unmapped"
                    confidence = 0.0
                    unmapped_count += 1
            else:
                mapping_status = "unmapped"
                confidence = 0.0
                unmapped_count += 1

        # Create mapping
        mapping = RequirementMapping(
            requirement_id=requirement_id,
            mapped_documents=matched_docs,
            mapping_status=mapping_status,
            confidence=confidence,
            suggested_by="agent",
            confirmed_by=None,
            confirmed_at=None,
        )

        mappings.append(mapping)

    # Create collection
    now = datetime.now(timezone.utc)
    collection = MappingCollection(
        session_id=session_id,
        mappings=mappings,
        total_requirements=len(requirements),
        mapped_count=mapped_count,
        unmapped_count=unmapped_count,
        confirmed_count=0,  # None confirmed yet
        created_at=now,
        updated_at=now,
    )

    # Save to state
    state_manager.write_json("mappings.json", collection.model_dump(mode="json"))

    # Update workflow progress
    state_manager.update_json("session.json", {
        "workflow_progress.requirement_mapping": "completed",
        "statistics.requirements_mapped": mapped_count,
    })

    return {
        "session_id": session_id,
        "total_requirements": len(requirements),
        "mapped_count": mapped_count,
        "unmapped_count": unmapped_count,
        "confirmed_count": 0,
        "coverage_rate": mapped_count / len(requirements) if len(requirements) > 0 else 0.0,
        "message": f"Mapped {mapped_count}/{len(requirements)} requirements to documents",
    }


def _infer_document_types(category: str, accepted_evidence: str) -> list[str]:
    """Infer expected document types from requirement category and evidence description.

    Args:
        category: Requirement category (e.g., "Land Tenure", "Baseline")
        accepted_evidence: Description of accepted evidence

    Returns:
        List of document classification types that might contain this evidence
    """
    category_lower = category.lower()
    evidence_lower = accepted_evidence.lower()

    # Map categories to document types
    type_mapping = {
        "land tenure": ["land-tenure", "legal-document", "project-plan", "project_plan"],
        "land eligibility": ["land-tenure", "land-eligibility", "project-plan", "project_plan"],
        "baseline": ["baseline-report", "baseline_report", "project-plan", "project_plan"],
        "monitoring": ["monitoring-report", "monitoring_report"],
        "sampling": ["sampling-plan", "sampling_plan", "monitoring-report", "monitoring_report"],
        "gis": ["gis-data", "geospatial", "shapefile", "project-plan", "project_plan"],
        "emissions": ["emissions-report", "monitoring-report", "monitoring_report"],
        "project details": ["project-plan", "project_plan"],
        "safeguards": ["project-plan", "project_plan", "safeguards-report"],
    }

    # Check category matches
    for key, types in type_mapping.items():
        if key in category_lower:
            return types

    # Check evidence description keywords
    if "deed" in evidence_lower or "title" in evidence_lower or "ownership" in evidence_lower:
        return ["land-tenure", "legal-document", "project-plan", "project_plan"]
    elif "map" in evidence_lower or "shapefile" in evidence_lower or "gis" in evidence_lower:
        return ["gis-data", "geospatial", "shapefile"]
    elif "baseline" in evidence_lower:
        return ["baseline-report", "baseline_report", "project-plan", "project_plan"]
    elif "monitoring" in evidence_lower or "sampling" in evidence_lower:
        return ["monitoring-report", "monitoring_report", "sampling-plan", "sampling_plan"]
    elif "emission" in evidence_lower or "ghg" in evidence_lower:
        return ["emissions-report", "monitoring-report", "monitoring_report"]

    # Default: project plan is most comprehensive
    return ["project-plan", "project_plan"]


async def confirm_mapping(
    session_id: str,
    requirement_id: str,
    document_ids: list[str],
    confirmed_by: str = "user",
) -> dict[str, Any]:
    """Confirm or manually set document mappings for a requirement.

    Args:
        session_id: Unique session identifier
        requirement_id: Requirement ID to update
        document_ids: List of document IDs to map to this requirement
        confirmed_by: Username or identifier of person confirming

    Returns:
        Updated mapping information
    """
    state_manager = get_session_or_raise(session_id)

    # Load current mappings
    mappings_data = state_manager.read_json("mappings.json")

    # Find and update the mapping
    updated = False
    for mapping in mappings_data["mappings"]:
        if mapping["requirement_id"] == requirement_id:
            mapping["mapped_documents"] = document_ids
            mapping["mapping_status"] = "confirmed"
            mapping["confirmed_by"] = confirmed_by
            mapping["confirmed_at"] = datetime.now(timezone.utc).isoformat()
            mapping["suggested_by"] = "manual"
            updated = True
            break

    if not updated:
        raise ValueError(f"Requirement not found: {requirement_id}")

    # Recalculate statistics
    total = len(mappings_data["mappings"])
    confirmed = sum(1 for m in mappings_data["mappings"] if m["mapping_status"] == "confirmed")
    mapped = sum(1 for m in mappings_data["mappings"] if m["mapped_documents"])
    unmapped = total - mapped

    mappings_data["confirmed_count"] = confirmed
    mappings_data["mapped_count"] = mapped
    mappings_data["unmapped_count"] = unmapped
    mappings_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Save updated mappings
    state_manager.write_json("mappings.json", mappings_data)

    return {
        "requirement_id": requirement_id,
        "mapped_documents": document_ids,
        "mapping_status": "confirmed",
        "confirmed_by": confirmed_by,
        "message": f"Confirmed mapping for {requirement_id}",
    }


async def remove_mapping(
    session_id: str,
    requirement_id: str,
    document_id: str,
) -> dict[str, Any]:
    """Remove a document from a requirement mapping.

    Args:
        session_id: Unique session identifier
        requirement_id: Requirement ID to update
        document_id: Document ID to remove from mapping

    Returns:
        Updated mapping information
    """
    state_manager = get_session_or_raise(session_id)

    # Load current mappings
    mappings_data = state_manager.read_json("mappings.json")

    # Find and update the mapping
    updated = False
    for mapping in mappings_data["mappings"]:
        if mapping["requirement_id"] == requirement_id:
            if document_id in mapping["mapped_documents"]:
                mapping["mapped_documents"].remove(document_id)

                # Update status based on remaining documents
                if not mapping["mapped_documents"]:
                    mapping["mapping_status"] = "unmapped"
                    mapping["confidence"] = 0.0

                mapping["updated_at"] = datetime.now(timezone.utc).isoformat()
                updated = True
                break

    if not updated:
        raise ValueError(f"Requirement or document not found: {requirement_id}, {document_id}")

    # Recalculate statistics
    total = len(mappings_data["mappings"])
    mapped = sum(1 for m in mappings_data["mappings"] if m["mapped_documents"])
    unmapped = total - mapped

    mappings_data["mapped_count"] = mapped
    mappings_data["unmapped_count"] = unmapped
    mappings_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Save updated mappings
    state_manager.write_json("mappings.json", mappings_data)

    return {
        "requirement_id": requirement_id,
        "document_id": document_id,
        "remaining_documents": mappings_data["mappings"],
        "message": f"Removed {document_id} from {requirement_id} mapping",
    }


async def get_mapping_status(session_id: str) -> dict[str, Any]:
    """Get current mapping status and statistics.

    Args:
        session_id: Unique session identifier

    Returns:
        Complete mapping status with statistics and details
    """
    state_manager = get_session_or_raise(session_id)

    # Load mappings
    mappings_data = state_manager.read_json("mappings.json")

    # Calculate detailed statistics
    total = mappings_data.get("total_requirements", 0)
    mapped = mappings_data.get("mapped_count", 0)
    unmapped = mappings_data.get("unmapped_count", 0)
    confirmed = mappings_data.get("confirmed_count", 0)

    # Breakdown by confidence level
    high_confidence = sum(1 for m in mappings_data["mappings"] if m.get("confidence", 0) > 0.75)
    medium_confidence = sum(1 for m in mappings_data["mappings"] if 0.5 <= m.get("confidence", 0) <= 0.75)
    low_confidence = sum(1 for m in mappings_data["mappings"] if 0 < m.get("confidence", 0) < 0.5)

    return {
        "session_id": session_id,
        "total_requirements": total,
        "mapped_count": mapped,
        "unmapped_count": unmapped,
        "confirmed_count": confirmed,
        "coverage_rate": mapped / total if total > 0 else 0.0,
        "confidence_breakdown": {
            "high": high_confidence,
            "medium": medium_confidence,
            "low": low_confidence,
        },
        "created_at": mappings_data.get("created_at"),
        "updated_at": mappings_data.get("updated_at"),
    }
