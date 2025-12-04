"""Human review tools for Stage 7 of registry review.

Provides tools for human reviewers to:
- Override agent assessments with expert judgment
- Add annotations/notes to requirements
- Set final determination for the review
- Track all changes with timestamps for audit trail
"""

from datetime import datetime, timezone
from typing import Any, Literal

from ..utils.state import get_session_or_raise


OverrideStatus = Literal["approved", "rejected", "needs_revision", "conditional", "pending"]
DeterminationStatus = Literal["approve", "conditional", "reject", "hold"]
RevisionPriority = Literal["critical", "high", "medium", "low"]
AuditActionType = Literal[
    "override_set", "override_cleared", "annotation_added",
    "determination_set", "determination_cleared",
    "revision_requested", "revision_resolved",
    "session_completed",
]


def _log_audit_event(
    state_manager,
    action: AuditActionType,
    entity_type: str,
    entity_id: str,
    actor: str,
    details: dict[str, Any],
) -> None:
    """Log an event to the audit trail.

    This creates a centralized audit log for compliance and transparency.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Load or create audit log
    if state_manager.exists("audit_log.json"):
        audit_data = state_manager.read_json("audit_log.json")
    else:
        audit_data = {
            "session_id": state_manager.session_id,
            "events": [],
            "created_at": now,
        }

    # Create audit event
    event = {
        "id": len(audit_data["events"]) + 1,
        "timestamp": now,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "actor": actor,
        "details": details,
    }

    audit_data["events"].append(event)
    audit_data["updated_at"] = now

    state_manager.write_json("audit_log.json", audit_data)


async def set_requirement_override(
    session_id: str,
    requirement_id: str,
    override_status: OverrideStatus,
    notes: str | None = None,
    reviewer: str = "user",
) -> dict[str, Any]:
    """Set human override status for a requirement.

    This allows the human reviewer to override agent assessments with their
    expert judgment. The override is recorded with timestamp and attribution.

    Args:
        session_id: Unique session identifier
        requirement_id: Requirement ID (e.g., "REQ-001")
        override_status: Decision status (approved/rejected/needs_revision/conditional/pending)
        notes: Optional notes explaining the decision
        reviewer: Identifier of the person making the override

    Returns:
        Updated requirement override information
    """
    state_manager = get_session_or_raise(session_id)

    # Load or create annotations file
    if state_manager.exists("annotations.json"):
        annotations_data = state_manager.read_json("annotations.json")
    else:
        annotations_data = {
            "session_id": session_id,
            "overrides": {},
            "annotations": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    now = datetime.now(timezone.utc).isoformat()

    # Record the override
    override_entry = {
        "requirement_id": requirement_id,
        "status": override_status,
        "notes": notes,
        "set_by": reviewer,
        "set_at": now,
    }

    # Track history if there was a previous override
    if requirement_id in annotations_data["overrides"]:
        previous = annotations_data["overrides"][requirement_id]
        if "history" not in annotations_data:
            annotations_data["history"] = []
        annotations_data["history"].append({
            "type": "override_changed",
            "requirement_id": requirement_id,
            "previous_status": previous.get("status"),
            "new_status": override_status,
            "changed_by": reviewer,
            "changed_at": now,
        })

    annotations_data["overrides"][requirement_id] = override_entry
    annotations_data["updated_at"] = now

    # Save
    state_manager.write_json("annotations.json", annotations_data)

    # Log audit event
    _log_audit_event(
        state_manager,
        action="override_set",
        entity_type="requirement",
        entity_id=requirement_id,
        actor=reviewer,
        details={"status": override_status, "notes": notes},
    )

    # Update session statistics
    total_overrides = len(annotations_data["overrides"])
    approved = sum(1 for o in annotations_data["overrides"].values() if o["status"] == "approved")
    rejected = sum(1 for o in annotations_data["overrides"].values() if o["status"] == "rejected")
    needs_revision = sum(1 for o in annotations_data["overrides"].values() if o["status"] == "needs_revision")

    state_manager.update_json("session.json", {
        "statistics.human_overrides": total_overrides,
        "statistics.requirements_approved": approved,
        "statistics.requirements_rejected": rejected,
        "statistics.requirements_needs_revision": needs_revision,
    })

    return {
        "session_id": session_id,
        "requirement_id": requirement_id,
        "override_status": override_status,
        "notes": notes,
        "set_by": reviewer,
        "set_at": now,
        "message": f"Override set for {requirement_id}: {override_status}",
    }


async def add_annotation(
    session_id: str,
    requirement_id: str,
    note: str,
    annotation_type: Literal["note", "question", "concern", "clarification"] = "note",
    reviewer: str = "user",
) -> dict[str, Any]:
    """Add an annotation/note to a requirement.

    Annotations are separate from overrides and allow the reviewer to
    capture observations, questions, or concerns without making a decision.

    Args:
        session_id: Unique session identifier
        requirement_id: Requirement ID (e.g., "REQ-001")
        note: The annotation text
        annotation_type: Type of annotation (note/question/concern/clarification)
        reviewer: Identifier of the person adding the annotation

    Returns:
        The created annotation
    """
    state_manager = get_session_or_raise(session_id)

    # Load or create annotations file
    if state_manager.exists("annotations.json"):
        annotations_data = state_manager.read_json("annotations.json")
    else:
        annotations_data = {
            "session_id": session_id,
            "overrides": {},
            "annotations": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    now = datetime.now(timezone.utc).isoformat()

    # Initialize annotations list for this requirement if needed
    if requirement_id not in annotations_data["annotations"]:
        annotations_data["annotations"][requirement_id] = []

    # Create annotation entry
    annotation_entry = {
        "type": annotation_type,
        "note": note,
        "added_by": reviewer,
        "added_at": now,
    }

    annotations_data["annotations"][requirement_id].append(annotation_entry)
    annotations_data["updated_at"] = now

    # Save
    state_manager.write_json("annotations.json", annotations_data)

    # Log audit event
    _log_audit_event(
        state_manager,
        action="annotation_added",
        entity_type="requirement",
        entity_id=requirement_id,
        actor=reviewer,
        details={"annotation_type": annotation_type, "note": note},
    )

    # Count total annotations
    total_annotations = sum(len(notes) for notes in annotations_data["annotations"].values())

    return {
        "session_id": session_id,
        "requirement_id": requirement_id,
        "annotation": annotation_entry,
        "total_annotations_for_requirement": len(annotations_data["annotations"][requirement_id]),
        "total_annotations": total_annotations,
        "message": f"Added {annotation_type} to {requirement_id}",
    }


async def get_requirement_review_status(
    session_id: str,
    requirement_id: str | None = None,
) -> dict[str, Any]:
    """Get the human review status for requirements.

    Args:
        session_id: Unique session identifier
        requirement_id: Optional specific requirement ID. If None, returns all.

    Returns:
        Review status including overrides and annotations
    """
    state_manager = get_session_or_raise(session_id)

    if not state_manager.exists("annotations.json"):
        return {
            "session_id": session_id,
            "overrides": {},
            "annotations": {},
            "summary": {
                "total_overrides": 0,
                "total_annotations": 0,
                "approved": 0,
                "rejected": 0,
                "needs_revision": 0,
                "conditional": 0,
                "pending": 0,
            },
        }

    annotations_data = state_manager.read_json("annotations.json")

    if requirement_id:
        # Return specific requirement
        override = annotations_data["overrides"].get(requirement_id)
        notes = annotations_data["annotations"].get(requirement_id, [])
        return {
            "session_id": session_id,
            "requirement_id": requirement_id,
            "override": override,
            "annotations": notes,
        }

    # Return all with summary
    overrides = annotations_data.get("overrides", {})
    annotations = annotations_data.get("annotations", {})

    summary = {
        "total_overrides": len(overrides),
        "total_annotations": sum(len(notes) for notes in annotations.values()),
        "approved": sum(1 for o in overrides.values() if o["status"] == "approved"),
        "rejected": sum(1 for o in overrides.values() if o["status"] == "rejected"),
        "needs_revision": sum(1 for o in overrides.values() if o["status"] == "needs_revision"),
        "conditional": sum(1 for o in overrides.values() if o["status"] == "conditional"),
        "pending": sum(1 for o in overrides.values() if o["status"] == "pending"),
    }

    return {
        "session_id": session_id,
        "overrides": overrides,
        "annotations": annotations,
        "summary": summary,
    }


async def clear_requirement_override(
    session_id: str,
    requirement_id: str,
    reviewer: str = "user",
) -> dict[str, Any]:
    """Clear an override for a requirement.

    This removes the override status, reverting to agent assessment.

    Args:
        session_id: Unique session identifier
        requirement_id: Requirement ID to clear
        reviewer: Identifier of the person clearing the override

    Returns:
        Confirmation of cleared override
    """
    state_manager = get_session_or_raise(session_id)

    if not state_manager.exists("annotations.json"):
        return {
            "session_id": session_id,
            "requirement_id": requirement_id,
            "message": "No overrides exist for this session",
        }

    annotations_data = state_manager.read_json("annotations.json")
    now = datetime.now(timezone.utc).isoformat()

    if requirement_id not in annotations_data["overrides"]:
        return {
            "session_id": session_id,
            "requirement_id": requirement_id,
            "message": f"No override exists for {requirement_id}",
        }

    # Record in history
    previous = annotations_data["overrides"][requirement_id]
    if "history" not in annotations_data:
        annotations_data["history"] = []
    annotations_data["history"].append({
        "type": "override_cleared",
        "requirement_id": requirement_id,
        "previous_status": previous.get("status"),
        "cleared_by": reviewer,
        "cleared_at": now,
    })

    # Remove override
    del annotations_data["overrides"][requirement_id]
    annotations_data["updated_at"] = now

    # Save
    state_manager.write_json("annotations.json", annotations_data)

    # Log audit event
    _log_audit_event(
        state_manager,
        action="override_cleared",
        entity_type="requirement",
        entity_id=requirement_id,
        actor=reviewer,
        details={"previous_status": previous.get("status")},
    )

    return {
        "session_id": session_id,
        "requirement_id": requirement_id,
        "previous_status": previous.get("status"),
        "message": f"Cleared override for {requirement_id}",
    }


async def set_final_determination(
    session_id: str,
    determination: DeterminationStatus,
    notes: str,
    conditions: str | None = None,
    reviewer: str = "user",
) -> dict[str, Any]:
    """Set the final determination for the review.

    This is the official decision on whether the project should be approved,
    conditionally approved, rejected, or placed on hold. This must be set
    before the session can be completed (Stage 8).

    Args:
        session_id: Unique session identifier
        determination: The final decision - one of: approve, conditional, reject, hold
        notes: Required explanation of the determination
        conditions: For conditional approvals, the conditions that must be met
        reviewer: Identifier of the person making the determination

    Returns:
        Confirmation of the determination with session status
    """
    if not notes or not notes.strip():
        raise ValueError("Notes are required for final determination")

    if determination == "conditional" and not conditions:
        raise ValueError("Conditions are required for conditional determinations")

    state_manager = get_session_or_raise(session_id)
    now = datetime.now(timezone.utc).isoformat()

    # Load or create determination file
    if state_manager.exists("determination.json"):
        determination_data = state_manager.read_json("determination.json")
        # Record history
        if "history" not in determination_data:
            determination_data["history"] = []
        determination_data["history"].append({
            "previous_determination": determination_data.get("determination"),
            "changed_by": reviewer,
            "changed_at": now,
        })
    else:
        determination_data = {
            "session_id": session_id,
            "created_at": now,
        }

    # Set the determination
    determination_data["determination"] = determination
    determination_data["notes"] = notes
    determination_data["conditions"] = conditions
    determination_data["set_by"] = reviewer
    determination_data["set_at"] = now
    determination_data["updated_at"] = now

    # Save determination
    state_manager.write_json("determination.json", determination_data)

    # Log audit event
    _log_audit_event(
        state_manager,
        action="determination_set",
        entity_type="session",
        entity_id=session_id,
        actor=reviewer,
        details={"determination": determination, "conditions": conditions},
    )

    # Update session with determination info
    state_manager.update_json("session.json", {
        "final_determination": determination,
        "determination_set_at": now,
        "determination_set_by": reviewer,
    })

    status_messages = {
        "approve": "Project APPROVED for registration",
        "conditional": "Project CONDITIONALLY APPROVED pending specified conditions",
        "reject": "Project REJECTED - does not meet requirements",
        "hold": "Project placed ON HOLD pending further review",
    }

    return {
        "session_id": session_id,
        "determination": determination,
        "notes": notes,
        "conditions": conditions,
        "set_by": reviewer,
        "set_at": now,
        "message": status_messages.get(determination, f"Determination set: {determination}"),
        "next_step": "Run `/H-completion` to finalize the review",
    }


async def get_final_determination(
    session_id: str,
) -> dict[str, Any]:
    """Get the final determination for a session.

    Args:
        session_id: Unique session identifier

    Returns:
        The current determination status and details
    """
    state_manager = get_session_or_raise(session_id)

    if not state_manager.exists("determination.json"):
        return {
            "session_id": session_id,
            "determination": None,
            "message": "No final determination has been set",
            "next_step": "Use set_final_determination to record the decision",
        }

    determination_data = state_manager.read_json("determination.json")

    return {
        "session_id": session_id,
        "determination": determination_data.get("determination"),
        "notes": determination_data.get("notes"),
        "conditions": determination_data.get("conditions"),
        "set_by": determination_data.get("set_by"),
        "set_at": determination_data.get("set_at"),
        "history": determination_data.get("history", []),
    }


async def clear_final_determination(
    session_id: str,
    reviewer: str = "user",
) -> dict[str, Any]:
    """Clear the final determination.

    This allows the determination to be reconsidered. Use with caution.

    Args:
        session_id: Unique session identifier
        reviewer: Identifier of the person clearing the determination

    Returns:
        Confirmation that the determination was cleared
    """
    state_manager = get_session_or_raise(session_id)
    now = datetime.now(timezone.utc).isoformat()

    if not state_manager.exists("determination.json"):
        return {
            "session_id": session_id,
            "message": "No determination exists to clear",
        }

    determination_data = state_manager.read_json("determination.json")
    previous_determination = determination_data.get("determination")

    # Record in history
    if "history" not in determination_data:
        determination_data["history"] = []
    determination_data["history"].append({
        "action": "cleared",
        "previous_determination": previous_determination,
        "cleared_by": reviewer,
        "cleared_at": now,
    })

    # Clear the determination
    determination_data["determination"] = None
    determination_data["notes"] = None
    determination_data["conditions"] = None
    determination_data["set_by"] = None
    determination_data["set_at"] = None
    determination_data["updated_at"] = now

    state_manager.write_json("determination.json", determination_data)

    # Log audit event
    _log_audit_event(
        state_manager,
        action="determination_cleared",
        entity_type="session",
        entity_id=session_id,
        actor=reviewer,
        details={"previous_determination": previous_determination},
    )

    # Update session
    state_manager.update_json("session.json", {
        "final_determination": None,
        "determination_set_at": None,
        "determination_set_by": None,
    })

    return {
        "session_id": session_id,
        "previous_determination": previous_determination,
        "cleared_by": reviewer,
        "message": "Final determination has been cleared",
    }


# ============================================================================
# Revision Request Workflow
# ============================================================================


async def request_revision(
    session_id: str,
    requirement_id: str,
    description: str,
    priority: RevisionPriority = "medium",
    requested_by: str = "user",
) -> dict[str, Any]:
    """Request revision from project proponent for a requirement.

    Marks a requirement as pending proponent revision with details about
    what needs to be addressed.

    Args:
        session_id: Unique session identifier
        requirement_id: Requirement ID (e.g., "REQ-001")
        description: What revision is needed from the proponent
        priority: Priority level (critical, high, medium, low)
        requested_by: Identifier of the person requesting revision

    Returns:
        Confirmation of revision request
    """
    if not description or not description.strip():
        raise ValueError("Description is required for revision requests")

    state_manager = get_session_or_raise(session_id)
    now = datetime.now(timezone.utc).isoformat()

    # Load or create revisions file
    if state_manager.exists("revisions.json"):
        revisions_data = state_manager.read_json("revisions.json")
    else:
        revisions_data = {
            "session_id": session_id,
            "requests": {},
            "created_at": now,
            "updated_at": now,
        }

    # Create revision request
    request_entry = {
        "requirement_id": requirement_id,
        "description": description,
        "priority": priority,
        "status": "pending",
        "requested_by": requested_by,
        "requested_at": now,
        "resolved_at": None,
        "resolution_notes": None,
    }

    revisions_data["requests"][requirement_id] = request_entry
    revisions_data["updated_at"] = now

    # Save
    state_manager.write_json("revisions.json", revisions_data)

    # Log audit event
    _log_audit_event(
        state_manager,
        action="revision_requested",
        entity_type="requirement",
        entity_id=requirement_id,
        actor=requested_by,
        details={"priority": priority, "description": description},
    )

    # Also mark the requirement as needs_revision in annotations
    await set_requirement_override(
        session_id=session_id,
        requirement_id=requirement_id,
        override_status="needs_revision",
        notes=f"Revision requested: {description}",
        reviewer=requested_by,
    )

    # Count pending revisions
    pending_count = sum(1 for r in revisions_data["requests"].values() if r["status"] == "pending")

    return {
        "session_id": session_id,
        "requirement_id": requirement_id,
        "description": description,
        "priority": priority,
        "status": "pending",
        "requested_by": requested_by,
        "requested_at": now,
        "pending_revisions": pending_count,
        "message": f"Revision requested for {requirement_id}",
    }


async def get_revision_requests(
    session_id: str,
    status_filter: str | None = None,
) -> dict[str, Any]:
    """Get all revision requests for a session.

    Args:
        session_id: Unique session identifier
        status_filter: Optional filter by status (pending, resolved, all)

    Returns:
        List of revision requests with summary statistics
    """
    state_manager = get_session_or_raise(session_id)

    if not state_manager.exists("revisions.json"):
        return {
            "session_id": session_id,
            "requests": {},
            "summary": {
                "total": 0,
                "pending": 0,
                "resolved": 0,
                "by_priority": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            },
        }

    revisions_data = state_manager.read_json("revisions.json")
    requests = revisions_data.get("requests", {})

    # Filter if requested
    if status_filter and status_filter != "all":
        requests = {k: v for k, v in requests.items() if v.get("status") == status_filter}

    # Calculate summary
    all_requests = revisions_data.get("requests", {})
    pending = [r for r in all_requests.values() if r["status"] == "pending"]
    resolved = [r for r in all_requests.values() if r["status"] == "resolved"]

    by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for r in pending:
        priority = r.get("priority", "medium")
        by_priority[priority] = by_priority.get(priority, 0) + 1

    return {
        "session_id": session_id,
        "requests": requests,
        "summary": {
            "total": len(all_requests),
            "pending": len(pending),
            "resolved": len(resolved),
            "by_priority": by_priority,
        },
    }


async def generate_revision_summary(
    session_id: str,
) -> dict[str, Any]:
    """Generate a summary of revision requests for the project proponent.

    Creates a formatted summary that can be shared with the proponent
    detailing what revisions are needed.

    Args:
        session_id: Unique session identifier

    Returns:
        Formatted revision summary with markdown content
    """
    state_manager = get_session_or_raise(session_id)

    # Load session for project info
    session_data = state_manager.read_json("session.json")
    project_name = session_data.get("project_metadata", {}).get("project_name", "Unknown Project")
    project_id = session_data.get("project_metadata", {}).get("project_id", "")

    # Get revision requests
    revisions_result = await get_revision_requests(session_id, status_filter="pending")
    requests = revisions_result.get("requests", {})
    summary = revisions_result.get("summary", {})

    if not requests:
        return {
            "session_id": session_id,
            "project_name": project_name,
            "has_pending_revisions": False,
            "message": "No pending revisions to report",
            "markdown": f"# Revision Request Summary\n\n**Project:** {project_name}\n\n✅ No revisions currently required.",
        }

    # Build markdown summary
    lines = [
        f"# Revision Request Summary",
        f"",
        f"**Project:** {project_name}",
        f"**Project ID:** {project_id}" if project_id else "",
        f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"",
        f"## Overview",
        f"",
        f"The following items require revision before the review can proceed:",
        f"",
        f"- **Total Pending:** {summary.get('pending', 0)}",
        f"- **Critical:** {summary.get('by_priority', {}).get('critical', 0)}",
        f"- **High Priority:** {summary.get('by_priority', {}).get('high', 0)}",
        f"- **Medium Priority:** {summary.get('by_priority', {}).get('medium', 0)}",
        f"- **Low Priority:** {summary.get('by_priority', {}).get('low', 0)}",
        f"",
        f"## Required Revisions",
        f"",
    ]

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_requests = sorted(
        requests.items(),
        key=lambda x: priority_order.get(x[1].get("priority", "medium"), 2)
    )

    for req_id, req in sorted_requests:
        priority_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
            req.get("priority", "medium"), "⚪"
        )
        lines.extend([
            f"### {priority_icon} {req_id} ({req.get('priority', 'medium').upper()})",
            f"",
            f"{req.get('description', 'No description provided')}",
            f"",
            f"*Requested: {req.get('requested_at', 'Unknown')[:10]}*",
            f"",
        ])

    lines.extend([
        f"---",
        f"",
        f"Please submit revised documents addressing the items above.",
        f"Once received, the review will be updated with the new information.",
    ])

    markdown_content = "\n".join(lines)

    return {
        "session_id": session_id,
        "project_name": project_name,
        "has_pending_revisions": True,
        "pending_count": summary.get("pending", 0),
        "markdown": markdown_content,
        "message": f"Generated revision summary with {summary.get('pending', 0)} pending items",
    }


async def resolve_revision(
    session_id: str,
    requirement_id: str,
    resolution_notes: str,
    resolved_by: str = "user",
) -> dict[str, Any]:
    """Mark a revision request as resolved.

    Call this after receiving and processing revised documents.

    Args:
        session_id: Unique session identifier
        requirement_id: Requirement ID that was revised
        resolution_notes: Notes about how the revision was resolved
        resolved_by: Identifier of the person resolving

    Returns:
        Confirmation of resolution
    """
    state_manager = get_session_or_raise(session_id)
    now = datetime.now(timezone.utc).isoformat()

    if not state_manager.exists("revisions.json"):
        return {
            "session_id": session_id,
            "requirement_id": requirement_id,
            "message": "No revision requests exist for this session",
        }

    revisions_data = state_manager.read_json("revisions.json")

    if requirement_id not in revisions_data["requests"]:
        return {
            "session_id": session_id,
            "requirement_id": requirement_id,
            "message": f"No revision request exists for {requirement_id}",
        }

    # Update the request
    request = revisions_data["requests"][requirement_id]
    request["status"] = "resolved"
    request["resolved_at"] = now
    request["resolution_notes"] = resolution_notes
    request["resolved_by"] = resolved_by
    revisions_data["updated_at"] = now

    state_manager.write_json("revisions.json", revisions_data)

    # Log audit event
    _log_audit_event(
        state_manager,
        action="revision_resolved",
        entity_type="requirement",
        entity_id=requirement_id,
        actor=resolved_by,
        details={"resolution_notes": resolution_notes},
    )

    # Update the override to pending (ready for re-review)
    await set_requirement_override(
        session_id=session_id,
        requirement_id=requirement_id,
        override_status="pending",
        notes=f"Revision resolved: {resolution_notes}. Ready for re-review.",
        reviewer=resolved_by,
    )

    # Count remaining pending
    pending_count = sum(1 for r in revisions_data["requests"].values() if r["status"] == "pending")

    return {
        "session_id": session_id,
        "requirement_id": requirement_id,
        "resolution_notes": resolution_notes,
        "resolved_by": resolved_by,
        "resolved_at": now,
        "remaining_pending": pending_count,
        "message": f"Revision for {requirement_id} marked as resolved",
    }


# ============================================================================
# Audit Trail
# ============================================================================


async def get_audit_log(
    session_id: str,
    action_filter: AuditActionType | None = None,
    actor_filter: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Get the audit log for a session.

    Returns a chronological list of all actions taken during the review,
    with optional filtering by action type or actor.

    Args:
        session_id: Unique session identifier
        action_filter: Optional filter by action type
        actor_filter: Optional filter by actor
        limit: Maximum number of events to return (default 100)

    Returns:
        Audit log with events and summary statistics
    """
    state_manager = get_session_or_raise(session_id)

    if not state_manager.exists("audit_log.json"):
        return {
            "session_id": session_id,
            "events": [],
            "summary": {
                "total_events": 0,
                "by_action": {},
                "by_actor": {},
            },
            "message": "No audit events recorded",
        }

    audit_data = state_manager.read_json("audit_log.json")
    events = audit_data.get("events", [])

    # Apply filters
    filtered_events = events
    if action_filter:
        filtered_events = [e for e in filtered_events if e.get("action") == action_filter]
    if actor_filter:
        filtered_events = [e for e in filtered_events if e.get("actor") == actor_filter]

    # Apply limit (most recent first)
    filtered_events = filtered_events[-limit:]

    # Calculate summary from all events (not filtered)
    by_action: dict[str, int] = {}
    by_actor: dict[str, int] = {}
    for event in events:
        action = event.get("action", "unknown")
        actor = event.get("actor", "unknown")
        by_action[action] = by_action.get(action, 0) + 1
        by_actor[actor] = by_actor.get(actor, 0) + 1

    return {
        "session_id": session_id,
        "events": filtered_events,
        "summary": {
            "total_events": len(events),
            "filtered_events": len(filtered_events),
            "by_action": by_action,
            "by_actor": by_actor,
        },
        "created_at": audit_data.get("created_at"),
        "updated_at": audit_data.get("updated_at"),
    }
