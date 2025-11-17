# Stage 6: Human Review - UX First Principles Analysis

**Document Status:** Draft
**Created:** 2025-11-14
**Last Updated:** 2025-11-14
**Author:** UX Analysis Team

---

## Executive Summary

Stage 6 (Human Review) represents the critical inflection point where automated intelligence yields to human judgment. This stage is not merely a verification step but a decision-making environment where Becca reviews flagged validation items, assesses ambiguous evidence, and makes final determinations that carry accountability. The UX must support rapid pattern recognition while maintaining context depth, enable batch efficiency without sacrificing individual attention, and create an audit trail that demonstrates thorough expert review.

Current implementation presents flagged items linearly with full context but lacks decision recording workflows, prioritization mechanisms, batch review capabilities, and deferral patterns. This analysis explores what human review truly requires and proposes a thoughtful evolution toward a decision-centric interface.

---

## Core User Story

**As Becca**, I need to review items flagged during automated validation so that I can apply expert judgment to ambiguous situations, document my decisions with rationale, ensure compliance with protocol requirements, and maintain accountability for registration determinations.

### The Real Work

Human review is not passive verification. It is active decision-making under conditions of uncertainty, incomplete information, and methodological complexity. Becca must:

- **Assess context rapidly** - Is this flag legitimate or a false positive?
- **Triangulate evidence** - What do multiple documents say? What's missing?
- **Apply protocol knowledge** - What does this specific methodology require?
- **Make judgment calls** - Is this variance acceptable? Does it require clarification?
- **Document reasoning** - Why did I decide this way?
- **Track follow-ups** - What questions must go back to the proponent?
- **Maintain velocity** - Can I batch-approve similar items or must each be individual?
- **Build confidence** - Am I seeing patterns that suggest systemic issues?

This is cognitive work requiring both speed and depth. The interface must support both.

---

## First Principles: What Makes Human Review Effective?

### 1. Attention Management

Human attention is the scarce resource. Flagged items compete for cognitive focus. The system must:

- **Surface high-priority items first** - Not all flags carry equal weight
- **Minimize context switching** - Group similar items to maintain mental models
- **Preserve decision context** - Don't make Becca rebuild understanding for each item
- **Enable flow states** - Batch similar decisions while preventing autopilot errors

### 2. Decision Quality

Good decisions require good information at the right time. The system must:

- **Present complete context** - All evidence for a flag, not just the conflict
- **Show relationships** - How does this flag relate to other findings?
- **Provide comparison baselines** - What's typical? What's concerning?
- **Enable investigation** - Quick access to source documents when needed
- **Support deliberation** - Space to think, not just react

### 3. Accountability and Auditability

Registry review carries legal and reputational weight. The system must:

- **Record decisions explicitly** - What was decided and why
- **Timestamp all actions** - When was each determination made
- **Preserve reasoning** - Rationale for accept/defer/reject decisions
- **Enable review of reviews** - Can someone else understand why Becca decided this way?
- **Support compliance demonstration** - Proof of thorough expert review

### 4. Workflow Flexibility

Real review doesn't follow perfect linear paths. The system must:

- **Allow deferral** - "I need more information before deciding"
- **Enable partial progress** - Review what's clear now, defer what's not
- **Support iteration** - Return to deferred items with new information
- **Handle batch operations** - When appropriate, approve groups efficiently
- **Accommodate interruption** - Real work gets interrupted; state must persist

---

## Current Implementation Analysis

### What Exists Today

The current `/human-review` prompt:

1. **Loads validation results** from `validation.json`
2. **Filters flagged items** across four validation types:
   - Date alignments (dates that don't align within tolerance)
   - Land tenure (owner name variations, area inconsistencies)
   - Project IDs (format variations, multiple IDs found)
   - Contradictions (conflicting information across documents)
3. **Presents each flagged item** with:
   - Type and status indicator (✅ pass, ⚠️ warning, ❌ fail)
   - Issue description
   - Full context details (dates, sources, confidence scores)
   - Suggested actions (Accept / Request clarification / Reject)
4. **Provides navigation** to next step (report generation)

### Strengths

- **Complete context presentation** - All evidence for each flag is shown
- **Clear categorization** - Validation types are distinct and understandable
- **Source transparency** - Documents, pages, and confidence scores are visible
- **Action guidance** - Suggested response categories help structure thinking

### Critical Gaps

1. **No decision recording** - The prompt shows items but doesn't capture decisions
2. **No prioritization** - All flags presented equally, no severity sorting
3. **No deferral mechanism** - Can't mark "need more info" and continue
4. **No batch operations** - Must consider each item individually
5. **No decision audit trail** - Decisions exist only in human memory or external notes
6. **No progress tracking** - Can't see "3 of 12 reviewed"
7. **No decision summary** - Can't review all decisions before finalizing
8. **No follow-up tracking** - Items requiring clarification lack structured tracking
9. **No integration with reporting** - Decisions don't flow into final report
10. **No pattern detection** - System doesn't surface "all 5 date flags are same issue"

---

## Detailed UX Requirements

### Requirement 1: Decision Recording Workflows

**User Need:** Becca must explicitly record her decision for each flagged item with rationale.

**Proposed Solution:**

Each flagged item becomes a **decision point** with three primary actions:

#### Accept
- **Meaning:** The flag is a false positive or the variance is acceptable
- **Required input:** Brief rationale (1-3 sentences)
- **Optional input:** Reference to protocol section justifying acceptance
- **Effect:** Item marked as "accepted" in decision log
- **Report inclusion:** Noted in "Items Reviewed" section with rationale

#### Defer
- **Meaning:** Need more information before deciding
- **Required input:** Specific question or information needed
- **Optional input:** Target person/document to consult
- **Effect:** Item moved to "deferred" queue with reminder
- **Report inclusion:** Listed in "Items Requiring Clarification" section

#### Escalate
- **Meaning:** This is a genuine issue requiring proponent response or correction
- **Required input:** Specific concern and what needs to be addressed
- **Optional input:** Severity level (minor/major/blocking)
- **Effect:** Item added to "corrective action required" list
- **Report inclusion:** Appears in "Findings Requiring Response" section

**Data Model:**

```json
{
  "decision_id": "DEC-20241114-001",
  "validation_id": "VAL-date-alignment-001",
  "validation_type": "date_alignment",
  "decision": "accept",
  "rationale": "4-month alignment tolerance allows for operational flexibility in sampling scheduling per Protocol v2.1 Section 3.4.2. Both dates within crediting period.",
  "decided_by": "becca@regen.network",
  "decided_at": "2024-11-14T10:32:15Z",
  "protocol_reference": "Soil Carbon Protocol v2.1, Section 3.4.2",
  "tags": ["date_alignment", "sampling_schedule"]
}
```

**Implementation:**

- Add `review_decisions.json` file to session state
- Create tool `record_review_decision(validation_id, decision, rationale, ...)`
- Modify prompt to present decision interface for each flagged item
- Show decision status alongside each flag (undecided/accepted/deferred/escalated)

### Requirement 2: Prioritization and Severity Scoring

**User Need:** See critical issues first, low-priority items later.

**Proposed Solution:**

Implement automatic severity scoring for flagged items based on:

#### Severity Factors

1. **Status type weight**
   - `fail` = High priority
   - `warning` = Medium priority
   - `pass` (but flagged) = Low priority

2. **Confidence scores**
   - Low confidence in extracted data = Higher priority
   - High confidence with flag = Review source of flag

3. **Validation type criticality**
   - Contradictions = Highest (suggests data quality issues)
   - Land tenure inconsistency = High (legal implications)
   - Date alignment issues = Medium (operational flexibility exists)
   - Project ID format variations = Low (often clerical)

4. **Document coverage**
   - Flags affecting many documents = Higher priority
   - Isolated flags = Lower priority

5. **Protocol requirements**
   - Flags on mandatory requirements = Higher priority
   - Flags on optional/supplemental items = Lower priority

**Display:**

Present flagged items in priority order with visible severity indicators:

```
## Items Requiring Review (12 total)

### 🔴 High Priority (3 items)

1. **Land Tenure - Contradiction**
   Owner name appears as "John Smith" in Land Registry but "J. Smith Farm LLC" in Project Plan
   [Decision: Undecided] [Review Now] [Defer]

### 🟡 Medium Priority (7 items)

4. **Date Alignment - Warning**
   Imagery date (2023-06-15) and sampling date (2023-10-12) are 119 days apart (max: 120)
   [Decision: Undecided] [Review Now] [Defer]

### 🟢 Low Priority (2 items)

11. **Project ID - Format Variation**
    Found "C06-4997" and "C06:4997" (colon vs hyphen)
    [Decision: Undecided] [Review Now] [Defer]
```

**Implementation:**

- Add `priority_score` and `severity_level` to validation items
- Create scoring function considering factors above
- Sort flagged items by priority in display
- Allow manual priority override ("Mark as high priority")

### Requirement 3: Batch Review Capabilities

**User Need:** When multiple flags represent the same underlying issue, decide once and apply consistently.

**Proposed Solution:**

Implement **pattern detection** and **bulk decision application**:

#### Pattern Detection

Analyze flagged items to identify common patterns:

- **Same validation type with same root cause**
  - Example: All date alignments are sampling-to-imagery alignment
- **Same document involved in multiple flags**
  - Example: Land Registry document has consistent name variance
- **Same field/data point causing issues**
  - Example: All project ID variations stem from format inconsistency

#### Batch Decision Interface

When patterns detected, offer grouped review:

```
## Detected Pattern: Project ID Format Variation

5 flagged items all relate to Project ID appearing with both hyphen and colon separators:
  - "C06-4997" appears in: Project Plan, Monitoring Report, GIS metadata
  - "C06:4997" appears in: Land Registry, Field Boundaries shapefile

Primary ID appears to be: C06-4997 (appears 15 times vs 3 times for colon variant)

**Batch Decision:**
[ ] Accept all - Clerical variation, primary ID is clear
[ ] Defer all - Need clarification from proponent on official format
[ ] Review individually - Different issues despite similar appearance

Rationale: [text field]

[Apply to All 5 Items]
```

#### Batch Operations Safety

To prevent autopilot errors:

- **Show full list** of items being batch-decided
- **Require explicit confirmation** before applying
- **Allow exceptions** - "Apply to all except item #3"
- **One-click undo** for batch decisions
- **Audit trail** shows batch decision as single event affecting multiple items

**Implementation:**

- Add pattern detection analysis to flagged items
- Create `batch_review_decision(validation_ids, decision, rationale)`
- Display grouped items with batch action interface
- Store batch operation metadata in audit log

### Requirement 4: Deferral and Follow-up Tracking

**User Need:** Some decisions can't be made now. Track what's deferred and ensure it gets revisited.

**Proposed Solution:**

Implement **deferred item queue** with structured follow-up:

#### Deferral Capture

When deferring an item, capture:

```
Defer Item: Land Tenure Name Variation

Why are you deferring this decision?
[X] Need more information from proponent
[ ] Need to consult protocol documentation
[ ] Need to consult with another reviewer
[ ] Need to review additional documents

Specific information needed:
[Text: Please confirm legal entity name registered with land authority. Is "J. Smith Farm LLC" the official entity or a DBA for "John Smith"?]

Optional: Expected resolution timeline
( ) Within this review session
(X) Requires proponent response
( ) Requires external verification

Notes:
[This is critical for land tenure validation. Cannot proceed without clarification.]

[Defer Item] [Cancel]
```

#### Deferred Items Dashboard

Separate view showing all deferred items:

```
## Deferred Items (3 pending)

### Awaiting Proponent Response (2 items)

1. **Land Tenure - Name Variation**
   Deferred: 2024-11-14 10:45
   Question sent: "Please confirm legal entity name..."
   Status: Awaiting response
   [Mark as Resolved] [Update Status] [View Full Context]

### Awaiting Further Review (1 item)

3. **Date Alignment - Sampling Schedule**
   Deferred: 2024-11-14 11:12
   Reason: "Need to verify if extended sampling window was pre-approved"
   Next action: Check approval correspondence folder
   [Mark as Resolved] [Review Now]
```

#### Resolution Workflow

When returning to deferred items:

- **Show original flag context**
- **Show deferral reason and questions asked**
- **Show any new information received**
- **Prompt for decision** with original choices (Accept/Defer/Escalate)

**Implementation:**

- Add `deferred_items.json` to session state
- Create tool `defer_review_item(validation_id, reason, question, notes)`
- Create tool `resolve_deferred_item(deferral_id, decision, resolution_notes)`
- Add deferral tracking to workflow state
- Include deferred count in progress indicators

### Requirement 5: Context Presentation Strategies

**User Need:** See enough context to decide confidently without information overload.

**Proposed Solution:**

Implement **progressive disclosure** with **context layering**:

#### Level 1: Summary View (Default)

What Becca sees initially for each flag:

```
3. Land Tenure - Owner Name Variation ⚠️ [High Priority]

Issue: Owner name appears differently across documents
Impact: Land tenure validation requires consistent entity identification
Documents affected: 2 (Land Registry, Project Plan)

Quick Facts:
- Name 1: "John Smith" (Land Registry, confidence 95%)
- Name 2: "J. Smith Farm LLC" (Project Plan, confidence 92%)
- Similarity: 67%

[Show Full Context] [View Documents] [Make Decision]
```

#### Level 2: Full Context (Expandable)

Clicking "Show Full Context" reveals:

```
### Detailed Evidence

**Land Registry Document (DOC-003)**
- Source: Land_Registry_Parcel_45789.pdf, Page 3
- Owner Name: "John Smith"
- Area: 45.7 hectares
- Tenure Type: Ownership
- Extracted: 2024-11-14 09:23, Confidence: 95%
- Extraction Method: Table extraction with OCR

**Project Plan (DOC-001)**
- Source: Project_Plan_C06-4997.pdf, Page 8
- Owner Name: "J. Smith Farm LLC"
- Area: 45.7 hectares (consistent ✓)
- Tenure Type: Ownership (consistent ✓)
- Extracted: 2024-11-14 09:15, Confidence: 92%
- Extraction Method: Text extraction from PDF

**Analysis**
- Area values are identical (45.7 ha) - suggests same property
- Tenure types match - both ownership
- Name similarity: 67% (failed 80% threshold)
- Common pattern: Individual name vs LLC entity name

**Protocol Requirements**
Soil Carbon Protocol v2.1, Section 2.3.1:
"Land tenure documentation must demonstrate clear legal authority over project area. Entity names must be consistent or demonstrable relationship must be documented."

[View Original Documents] [Collapse Context]
```

#### Level 3: Document Viewer (Deep Dive)

Clicking "View Original Documents" opens inline document viewer:

- Shows highlighted excerpts from both documents
- Allows scrolling through full documents if needed
- Maintains decision interface visible alongside
- Enables side-by-side comparison when useful

#### Context Navigation

Enable quick jumping between related context:

- "View all flags from this document" - What else is flagged in Land Registry?
- "View related validations" - Are there other land tenure flags?
- "View requirement evidence" - What requirement does this relate to?

**Implementation:**

- Redesign prompt to show summary view by default
- Add collapsible sections for full context
- Implement document reference linking
- Consider rich text formatting for better scanability

### Requirement 6: Decision Audit Trail

**User Need:** Demonstrate thorough review process and enable decision review.

**Proposed Solution:**

Implement **comprehensive decision logging** with **audit trail visualization**:

#### What Gets Logged

Every decision interaction:

```json
{
  "audit_log": [
    {
      "event_id": "AUD-20241114-001",
      "event_type": "review_decision",
      "timestamp": "2024-11-14T10:32:15Z",
      "session_id": "session-abc123",
      "user": "becca@regen.network",
      "validation_id": "VAL-date-alignment-001",
      "decision": "accept",
      "rationale": "4-month tolerance acceptable per protocol",
      "protocol_reference": "Soil Carbon Protocol v2.1, Section 3.4.2",
      "time_spent_seconds": 45,
      "context_views": ["full_context", "document_viewer"],
      "priority_level": "medium"
    },
    {
      "event_id": "AUD-20241114-002",
      "event_type": "batch_decision",
      "timestamp": "2024-11-14T10:35:22Z",
      "session_id": "session-abc123",
      "user": "becca@regen.network",
      "validation_ids": ["VAL-project-id-001", "VAL-project-id-002", "VAL-project-id-003"],
      "pattern_type": "project_id_format_variation",
      "decision": "accept",
      "rationale": "Format variations clerical only, primary ID clear",
      "items_affected": 3
    },
    {
      "event_id": "AUD-20241114-003",
      "event_type": "deferral",
      "timestamp": "2024-11-14T10:37:45Z",
      "session_id": "session-abc123",
      "user": "becca@regen.network",
      "validation_id": "VAL-land-tenure-001",
      "deferral_reason": "need_proponent_response",
      "question": "Please confirm legal entity name registered with land authority",
      "expected_resolution": "requires_proponent_response"
    },
    {
      "event_id": "AUD-20241114-004",
      "event_type": "priority_override",
      "timestamp": "2024-11-14T10:40:12Z",
      "session_id": "session-abc123",
      "user": "becca@regen.network",
      "validation_id": "VAL-contradiction-002",
      "previous_priority": "medium",
      "new_priority": "high",
      "reason": "Affects multiple requirements"
    }
  ]
}
```

#### Audit Trail Visualization

Provide reviewable summary of all decisions:

```
## Review Session Audit Trail

**Session:** session-abc123
**Project:** Botany Farm 2022-2023
**Reviewer:** Becca
**Review Period:** 2024-11-14 10:30 - 11:15 (45 minutes)

### Decision Summary

Total items flagged: 12
- Accepted: 7 items (58%)
- Deferred: 3 items (25%)
- Escalated: 2 items (17%)

### Detailed Timeline

**10:32** - Accepted date alignment issue (VAL-date-001)
  Rationale: "4-month tolerance acceptable per protocol"
  Protocol ref: Soil Carbon Protocol v2.1, Section 3.4.2

**10:35** - Batch accepted 3 project ID format variations
  Pattern: Format variations clerical only
  Items: VAL-project-id-001, VAL-project-id-002, VAL-project-id-003

**10:37** - Deferred land tenure name variation (VAL-land-tenure-001)
  Question: "Please confirm legal entity name..."
  Status: Awaiting proponent response

**10:40** - Increased priority on contradiction (VAL-contradiction-002)
  Reason: Affects multiple requirements

**10:42** - Escalated area discrepancy (VAL-land-tenure-002)
  Concern: "3.2 ha difference between Land Registry and GIS files"
  Severity: Major

**11:12** - Accepted remaining date alignments (batch, 4 items)
  Pattern: All within tolerance, same rationale applies

### Export Options
[PDF Summary] [JSON Data] [CSV Log]
```

#### Audit Trail Uses

The audit trail enables:

- **Review of review** - QA checks on decision quality
- **Training** - Show new reviewers how experts decide
- **Compliance** - Demonstrate thorough expert review
- **Pattern analysis** - What issues come up repeatedly?
- **Time tracking** - How long does human review take?
- **Decision consistency** - Are similar items decided similarly?

**Implementation:**

- Create `audit_log.json` in session state
- Log every decision interaction with timestamp
- Track time spent on each item (time between views)
- Create audit trail summary view
- Enable export in multiple formats

### Requirement 7: Integration with Report Generation

**User Need:** Decisions made during human review flow seamlessly into final report.

**Proposed Solution:**

Integrate review decisions throughout the report:

#### Report Sections Affected

**1. Executive Summary**

```
## Human Review Summary

12 items were flagged for expert review during cross-validation.

**Decisions:**
- 7 items accepted as compliant (58%)
- 2 items require corrective action (17%)
- 3 items deferred pending additional information (25%)

All accepted items include documented rationale referencing protocol requirements.
Items requiring corrective action are detailed in Section 5: Findings Requiring Response.
Deferred items pending proponent clarification are listed in Section 6: Outstanding Questions.
```

**2. Validation Results Section**

For each validation finding, include review decision:

```
### Date Alignment: Imagery to Sampling

**Status:** ⚠️ Warning (Reviewed and Accepted)

**Finding:** Imagery date (2023-06-15) and sampling date (2023-10-12) are 119 days apart.

**Validation:** Exceeds typical 90-day window but within 120-day maximum tolerance.

**Expert Review Decision:** Accepted
**Reviewed by:** Becca
**Date:** 2024-11-14

**Rationale:** The 4-month alignment tolerance allows for operational flexibility in scheduling field sampling activities while ensuring temporal correlation between imagery and ground truth data. Both dates fall within the crediting period. This variance is explicitly permitted by Soil Carbon Protocol v2.1, Section 3.4.2.

**Protocol Reference:** Soil Carbon Protocol v2.1, Section 3.4.2 - Temporal Alignment Requirements
```

**3. Findings Requiring Response**

New section listing escalated items:

```
## Section 5: Findings Requiring Response

The following items require clarification or correction from the project proponent before final approval:

### Finding 1: Land Tenure Area Discrepancy (High Priority)

**Issue:** Significant difference in reported land area between documentation sources.

**Evidence:**
- Land Registry Document: 45.7 hectares
- GIS Field Boundaries: 48.9 hectares
- Discrepancy: 3.2 hectares (7% difference)

**Requirement:** Land tenure documentation must accurately reflect project area (Protocol Section 2.3.1)

**Required Action:** Please provide:
1. Explanation for area discrepancy
2. Verification of correct project area
3. If GIS boundaries are correct, provide updated land registry documentation
4. If Land Registry is correct, provide corrected GIS files

**Priority:** Major - affects credit quantification baseline
**Review Decision:** Escalated 2024-11-14 by Becca
```

**4. Outstanding Questions**

New section for deferred items:

```
## Section 6: Outstanding Questions

The following items require additional information before final determination:

### Question 1: Legal Entity Name Clarification

**Context:** Owner name appears differently across documents:
- Land Registry: "John Smith"
- Project Plan: "J. Smith Farm LLC"

**Question:** Please confirm the legal entity name registered with the land authority. Is "J. Smith Farm LLC" the official entity or a DBA (doing business as) name for "John Smith"?

**Documentation Needed:**
- Business registration documents showing relationship between names, OR
- Amended land registry documentation with LLC name, OR
- Legal opinion confirming entity identity

**Related Requirement:** Land tenure validation (Protocol Section 2.3.1)
**Deferred:** 2024-11-14 by Becca
```

**Implementation:**

- Modify report generation to read `review_decisions.json`
- Include decision details in validation finding sections
- Generate "Findings Requiring Response" from escalated items
- Generate "Outstanding Questions" from deferred items
- Add "Expert Review Summary" to executive summary

### Requirement 8: Progress Tracking and Session Management

**User Need:** Know review status at a glance, resume interrupted reviews efficiently.

**Proposed Solution:**

Implement **review progress dashboard** with **state persistence**:

#### Progress Indicators

Show review status throughout the workflow:

```
## Human Review Progress

**Session:** session-abc123
**Project:** Botany Farm 2022-2023

**Overall Progress:** 9 of 12 items decided (75%)

### Status Breakdown
✅ Accepted: 7 items
⏸️ Deferred: 2 items
🔴 Escalated: 0 items
⏳ Not yet reviewed: 3 items

**Estimated time remaining:** ~6 minutes (based on avg 2 min/item)

[Continue Review] [View Decisions] [Export Progress]
```

#### Session State Persistence

When review is interrupted:

- **Save review state** after each decision
- **Track position** in review queue
- **Preserve context** of what was being reviewed
- **Enable resumption** exactly where left off

Resumption experience:

```
## Resume Review Session

Welcome back! You were reviewing flagged items for Botany Farm 2022-2023.

**Last activity:** 2024-11-14 10:42 (23 minutes ago)
**Progress when paused:** 9 of 12 items decided

You left off reviewing:
- Item #10: Project ID format variation (Low Priority)

Would you like to:
( ) Continue from where you left off (recommended)
( ) Review your decisions so far
( ) Start from the beginning
( ) Jump to specific item

[Continue Review]
```

#### Review Velocity Tracking

Show time metrics to help with planning:

```
## Review Efficiency

**This session:**
- Average time per item: 2.3 minutes
- Fastest decision: 45 seconds (batch approval)
- Slowest decision: 5.2 minutes (deferred land tenure issue)

**Historical average:** 3.1 minutes per item

At current pace, you'll complete remaining items in ~7 minutes.
```

**Implementation:**

- Add progress tracking to workflow state
- Calculate completion percentage and estimates
- Save state after each decision
- Implement resume workflow
- Track timing metrics for efficiency analysis

---

## Interaction Patterns

### Pattern 1: Linear Review (Simple Cases)

For projects with few flags or straightforward issues:

```
Workflow:
1. Open human review
2. See 3 flagged items, all low priority
3. Review item 1 → Accept with rationale
4. Review item 2 → Accept with rationale
5. Review item 3 → Accept with rationale
6. Review complete → Generate report
```

**Time:** ~5-10 minutes
**Decisions:** All accept
**Outcome:** Clean approval path

### Pattern 2: Batch Review (Pattern Recognition)

For projects with repeated similar flags:

```
Workflow:
1. Open human review
2. See 8 flagged items
3. System detects pattern: 5 items are same issue (project ID format)
4. Review pattern → Batch accept all 5 with single rationale
5. Review remaining 3 items individually
6. Review complete → Generate report
```

**Time:** ~8-12 minutes
**Decisions:** 1 batch + 3 individual
**Outcome:** Efficient processing of common issue

### Pattern 3: Deferral and Iteration (Complex Cases)

For projects needing clarification:

```
Workflow Session 1:
1. Open human review
2. See 12 flagged items, mixed priorities
3. Review high priority items first (3 items)
   - Accept 1, Defer 1 (need info), Escalate 1 (major issue)
4. Review medium priority (6 items)
   - Accept 4, Defer 2 (same underlying question)
5. Pause review - deferred items need proponent response
6. Generate interim report with questions

Workflow Session 2 (After proponent response):
1. Resume review session
2. See 3 deferred items + proponent responses
3. Review deferred items with new information
   - Accept 2 (clarified), Escalate 1 (still insufficient)
4. Review remaining low priority items (3 items)
   - Batch accept all 3
5. Review complete → Generate final report
```

**Time:** ~30 minutes total (across 2 sessions)
**Decisions:** Mix of accept/defer/escalate
**Outcome:** Thorough review with proponent engagement

### Pattern 4: Investigation Mode (Deep Dive)

For projects with concerning patterns:

```
Workflow:
1. Open human review
2. See 7 flagged items
3. Notice pattern: Multiple contradictions affecting same fields
4. Switch to investigation mode:
   - View all flags from specific documents
   - Review requirement evidence for related requirements
   - Check cross-validation results in detail
5. Identify systemic issue (document version mismatch)
6. Escalate group of items with detailed explanation
7. Request proponent provide corrected document set
8. Defer remaining items until correction received
```

**Time:** ~45 minutes
**Decisions:** Multiple escalations, pattern analysis
**Outcome:** Identified systemic issue requiring correction

---

## Information Architecture

### Data Relationships

Human review connects multiple information layers:

```
Session
  └─ Validation Results
       ├─ Date Alignments (flagged subset)
       ├─ Land Tenure Validations (flagged subset)
       ├─ Project ID Validations (flagged subset)
       └─ Contradictions (flagged subset)
            └─ Review Decisions
                 ├─ Accept (with rationale)
                 ├─ Defer (with questions)
                 └─ Escalate (with findings)
                      └─ Audit Log
                           ├─ Timeline
                           ├─ User actions
                           └─ Decision reasoning
```

Each flagged item links to:

- **Validation data** - The technical finding
- **Evidence** - Documents and extractions that led to flag
- **Requirements** - Which protocol requirement this affects
- **Related flags** - Other flags affecting same documents/fields
- **Review decision** - Expert determination and reasoning
- **Audit trail** - Who decided when and why

### Navigation Structure

Enable multiple navigation paths:

**By Priority:**
- High → Medium → Low (default sort)

**By Type:**
- All Date Alignments → All Land Tenure → All Project IDs → All Contradictions

**By Status:**
- Not Reviewed → Deferred → Accepted → Escalated

**By Document:**
- Show all flags relating to specific document

**By Requirement:**
- Show all flags affecting specific protocol requirement

**Implementation:**

- Support multiple sort/filter options
- Enable quick switching between views
- Preserve decision context when navigating
- Show navigation breadcrumbs

---

## Error Handling and Edge Cases

### Edge Case 1: No Flags

When validation produces no flagged items:

```
## ✅ No Items Flagged for Review

All validation checks passed without requiring human review.

**Validation Summary:**
- Total validations: 23
- Passed: 21 (91%)
- Failed: 0
- Warnings: 2 (auto-accepted within tolerance)

All findings are within acceptable parameters per protocol requirements.

**Next Step:** Generate final report

[Generate Report]
```

**UX Decision:** Celebrate success, provide confidence in results, show clear path forward.

### Edge Case 2: All Items Escalated

When every flag requires corrective action:

```
## 🔴 All Flagged Items Require Corrective Action

All 8 flagged items have been escalated as requiring proponent response.

**This suggests:**
- Significant data quality issues, OR
- Document set incomplete or incorrect, OR
- Methodology requirements not fully understood

**Recommended approach:**
1. Review the "Findings Requiring Response" report section
2. Consolidate related issues into coherent feedback
3. Schedule call with proponent to discuss if needed
4. Request comprehensive corrected submission

[View Consolidated Findings] [Generate Corrective Action Report]
```

**UX Decision:** Flag unusual pattern, suggest proactive communication, offer consolidated view.

### Edge Case 3: Conflicting Decisions

When batch decision might not apply cleanly to all items:

```
## ⚠️ Batch Decision Conflict Detected

You're attempting to batch accept 5 date alignment flags, but:

Item #3 has a different underlying issue:
- Items 1,2,4,5: Sampling-to-imagery alignment (119 days, within tolerance)
- Item 3: Baseline-to-monitoring alignment (8 months, exceeds tolerance)

**Recommendation:**
- Accept items 1,2,4,5 as a batch
- Review item 3 individually

[Accept Recommendation] [Apply to All Anyway] [Cancel Batch]
```

**UX Decision:** Surface conflicts proactively, suggest intelligent splitting, allow override if intentional.

### Edge Case 4: Decision Reversal

When Becca wants to change a previous decision:

```
Change Decision for Item #5?

**Current Decision:** Accepted (2024-11-14 10:35)
**Rationale:** "Format variations clerical only"

**New Decision:**
( ) Accept
( ) Defer
(•) Escalate

New rationale:
[After reviewing further, this format variation appears in credit issuance records which could affect on-chain data integrity. Need proponent to confirm official format.]

⚠️ This will update the audit trail showing decision was revised.

[Confirm Change] [Cancel]
```

**UX Decision:** Allow changes but make them explicit in audit trail, require new rationale.

### Edge Case 5: Incomplete Review at Report Generation

When trying to generate report with unreviewed items:

```
## ⚠️ Review Incomplete

You have 3 flagged items that have not been reviewed yet.

**Options:**

1. **Review remaining items now** (recommended)
   Continue human review to complete all decisions

2. **Defer remaining items**
   Mark remaining items as "pending further information"
   They will appear in "Outstanding Questions" section

3. **Generate report anyway**
   Unreviewed items will appear as "Flagged - Review Pending"
   ⚠️ Not recommended for final approval

What would you like to do?
[Complete Review] [Defer Remaining] [Generate Anyway]
```

**UX Decision:** Block report generation by default but offer escape hatches with clear consequences.

---

## Performance Requirements

### Response Time Targets

- **Load flagged items:** < 1 second
- **Display item details:** < 500ms
- **Record decision:** < 300ms
- **Generate audit trail:** < 2 seconds
- **Switch between items:** < 200ms (feels instant)

### Scalability Considerations

**Small projects (< 5 flags):**
- Simple linear review adequate
- Minimal interface overhead

**Medium projects (5-20 flags):**
- Prioritization important
- Batch operations valuable
- Progress tracking helpful

**Large projects (20-50 flags):**
- Prioritization critical
- Batch operations essential
- Progress tracking required
- Pattern detection important

**Aggregated projects (50+ flags across multiple farms):**
- Group by sub-project
- Enable farm-level batch decisions
- Show aggregate patterns across portfolio
- Support partial review sessions

---

## Accessibility and Usability

### Keyboard Navigation

Enable full keyboard control:

- `j/k` - Navigate between items (vim-style)
- `1/2/3` - Accept / Defer / Escalate current item
- `Space` - Expand/collapse full context
- `d` - View document references
- `?` - Show keyboard shortcuts

### Visual Clarity

- **Color coding** - But not color-dependent (use icons + text)
- **Priority indicators** - Size, position, explicit labels
- **Status badges** - Clear accepted/deferred/escalated/pending states
- **White space** - Don't cram information, let it breathe

### Cognitive Load Reduction

- **Progressive disclosure** - Summary → Full context → Documents
- **Contextual help** - Protocol references inline when relevant
- **Decision templates** - Common rationales available to customize
- **Clear defaults** - Suggested actions based on validation type

---

## Future Enhancements

### Phase 1 (MVP)
- ✅ Present flagged items with context
- ⏳ Record basic decisions (accept/defer/escalate)
- ⏳ Include decisions in report
- ⏳ Basic audit trail

### Phase 2 (Efficiency)
- ⏳ Priority scoring and sorting
- ⏳ Pattern detection
- ⏳ Batch decision operations
- ⏳ Progress tracking
- ⏳ Resume capability

### Phase 3 (Intelligence)
- ⏳ Decision templates from historical patterns
- ⏳ Similar case recommendations ("Last time we saw this...")
- ⏳ Protocol requirement inline lookup
- ⏳ Cross-project pattern analysis

### Phase 4 (Collaboration)
- ⏳ Multi-reviewer workflows (second opinions)
- ⏳ Review comments and discussion threads
- ⏳ Reviewer assignment and routing
- ⏳ Review quality metrics and calibration

---

## Success Metrics

### Effectiveness Metrics

**Decision Quality:**
- Reversal rate < 5% (decisions later changed)
- Escalation precision > 90% (escalated items proven legitimate)
- Deferral resolution rate > 95% (deferred items eventually decided)

**Completeness:**
- 100% of flagged items explicitly decided
- 0 items slip through without review
- Audit trail complete for all decisions

**Consistency:**
- Similar items decided similarly (measured by pattern analysis)
- Decision rationales reference protocol requirements
- Batch decisions applied appropriately

### Efficiency Metrics

**Time:**
- Average time per item decision: 2-4 minutes (baseline)
- Batch decision time: < 5 minutes for group of 5-10 items
- Total review time: 50%+ reduction vs. manual review

**Cognitive Load:**
- Context switches < 10 per session (measured by navigation)
- Decision confidence self-rating > 8/10
- Interruption recovery time < 1 minute

### Usability Metrics

**User Satisfaction:**
- Becca finds interface intuitive (qualitative feedback)
- Decision recording feels natural not burdensome
- Audit trail inspires confidence not anxiety

**Adoption:**
- 100% of reviews use decision recording (not bypassed)
- Batch operations used when appropriate
- Deferral mechanism used for genuine uncertainties

---

## Implementation Roadmap

### Phase 1: Basic Decision Recording (Week 1-2)

**Goals:**
- Capture decisions explicitly
- Generate basic audit trail
- Include decisions in reports

**Deliverables:**
- `review_decisions.json` state file
- `record_review_decision()` tool
- Modified human review prompt with decision capture
- Report integration for decisions

**Testing:**
- Review 3 projects, record all decisions
- Verify audit trail completeness
- Confirm report includes decision rationales

### Phase 2: Prioritization and Progress (Week 3)

**Goals:**
- Show items by priority
- Track review progress
- Enable session resumption

**Deliverables:**
- Priority scoring algorithm
- Progress tracking in workflow state
- Sorted flag presentation
- Resume workflow capability

**Testing:**
- Review project with 15+ flags, verify prioritization
- Interrupt and resume session, verify state
- Measure time saved by priority focus

### Phase 3: Batch Operations (Week 4)

**Goals:**
- Detect patterns in flags
- Enable batch decisions
- Maintain decision quality

**Deliverables:**
- Pattern detection analysis
- Batch decision interface
- Safety confirmations
- Batch audit trail

**Testing:**
- Review project with repeating issues, use batch operations
- Verify batch decisions record correctly
- Confirm audit trail shows batch operations clearly

### Phase 4: Deferral Workflows (Week 5)

**Goals:**
- Support deferral with structured questions
- Track deferred items
- Enable resolution workflows

**Deliverables:**
- Deferral capture interface
- `deferred_items.json` state
- Deferred items dashboard
- Resolution workflow

**Testing:**
- Defer multiple items during review
- Return later to resolve deferred items
- Verify deferred items appear in report correctly

### Phase 5: Polish and Intelligence (Week 6+)

**Goals:**
- Improve context presentation
- Add contextual help
- Optimize performance

**Deliverables:**
- Progressive disclosure UI
- Protocol reference integration
- Keyboard shortcuts
- Performance optimization

**Testing:**
- User testing with Becca
- Measure time per decision
- Collect qualitative feedback
- Iterate based on real usage

---

## Open Questions

### For Product Team

1. **Should decisions be revisable?**
   - Pro: Allows correction of mistakes
   - Con: Complicates audit trail, could enable gaming
   - Proposal: Allow within review session, freeze after report generation

2. **What happens to decisions when validation is re-run?**
   - If documents change and validation re-runs, previous decisions may not apply
   - Proposal: Mark previous decisions as "stale," require re-review of changed items

3. **Should some flags auto-accept without human review?**
   - Very low severity, high confidence items might not need human eyes
   - Proposal: Flag for review anyway but pre-populate "Accept" with rationale

4. **How to handle multi-reviewer scenarios?**
   - What if two reviewers need to agree?
   - Proposal: Phase 4 feature, not MVP

5. **Should decision rationales be required or optional?**
   - Required = better audit trail but slower workflow
   - Optional = faster but less defensible
   - Proposal: Required for escalation/defer, optional for accept

### For Becca (User Validation)

1. **What's the typical breakdown of accept vs defer vs escalate?**
   - Helps calibrate expectations and design for common case

2. **Do you usually review all flags in one session or across multiple sessions?**
   - Determines importance of state persistence and progress tracking

3. **What information do you most often need that's not readily available?**
   - Identifies context presentation improvements

4. **How often do you batch-review similar items vs treat each uniquely?**
   - Validates value of batch operations feature

5. **What would make you trust the agent's validation results more?**
   - Guides future enhancements to increase confidence

---

## Conclusion

Stage 6 (Human Review) transforms the Registry Review MCP from a validation tool into a decision support system. The current implementation presents flagged items with excellent context but lacks the critical decision recording, workflow management, and audit capabilities required for accountable expert review.

The proposed enhancements follow a clear principle: **support expert judgment, don't replace it**. The system should make Becca's decision-making faster and more defensible without prescribing what those decisions should be. Prioritization focuses attention on what matters. Batch operations enable efficiency without sacrificing quality. Deferral workflows acknowledge that good decisions sometimes require more information. And audit trails demonstrate thoroughness to stakeholders.

This stage is where human and machine intelligence truly collaborate—the agent surfaces and structures the questions, the human applies judgment and accountability. Getting this stage right is essential for the system's credibility and Becca's confidence in using it.

---

**Next Steps:**

1. Review this analysis with Becca and product team
2. Validate user needs and interaction patterns
3. Prioritize enhancements based on impact and effort
4. Begin Phase 1 implementation of basic decision recording
5. Test with real projects and iterate based on usage patterns

**Document History:**

- 2025-11-14: Initial analysis created
- Status: Draft for review
