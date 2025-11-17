# Stage 5: Report Generation — UX First Principles Analysis

**Document Version:** 1.0
**Analysis Date:** 2025-11-14
**Stage:** Report Generation
**Primary User:** Becca (Registry Reviewer)
**Status:** Draft for Review

---

## Executive Summary

Report Generation represents the culmination of the Registry Review workflow—the moment when all discovered documents, extracted evidence, and validation findings coalesce into a coherent artifact that enables final approval decisions. This stage transforms raw data into actionable intelligence, balancing comprehensiveness with clarity, precision with readability, and automation with human oversight.

The report serves three critical functions: it provides Becca with a complete view of compliance status, creates an audit trail for approval decisions, and generates shareable artifacts for stakeholders. Success hinges on making vast amounts of structured data immediately comprehensible while preserving the granular detail needed for verification.

From a UX perspective, the core challenge is not generating data—it is presenting that data in a way that supports rapid comprehension, enables efficient verification, and facilitates confident decision-making. The report must answer the fundamental question: "Is this project ready for approval, and if not, what specifically needs attention?"

---

## 1. User Goals & Mental Model

### Primary Goal
Generate a comprehensive review report that enables confident approval decisions while creating a complete audit trail of the review process.

### Becca's Mental Model

When Becca thinks about report generation, she conceptualizes it as:

1. **The Final Synthesis** — All prior work (discovery, extraction, validation) coming together in one coherent view
2. **The Decision Document** — The artifact that supports her approval/rejection decision
3. **The Audit Record** — The permanent record of what was reviewed, what was found, and why decisions were made
4. **The Communication Tool** — The artifact shared with project developers, verifiers, and internal stakeholders

### Key User Needs

**Comprehension at Multiple Levels:**
- Executive summary: 30-second overview of compliance status
- Mid-level detail: Category-by-category breakdown of findings
- Deep detail: Full evidence trails for verification

**Confidence Calibration:**
- Clear distinction between agent-generated and human-verified findings
- Explicit confidence scores for automated assessments
- Highlighted areas requiring human attention

**Traceability:**
- Every assertion backed by specific document citations
- Page-level references for verification
- Evidence snippets with context

**Decision Support:**
- Clear identification of blockers vs. warnings vs. acceptable gaps
- Prioritized action items for incomplete submissions
- Explicit recommendation: approve, reject, or request revisions

**Shareability:**
- Professional formatting suitable for external stakeholders
- Multiple export formats for different audiences
- Preservation of formatting across platforms

---

## 2. Information Architecture

### Report Structure Hierarchy

```
Registry Review Report
│
├── Report Metadata
│   ├── Project identification (name, ID, methodology)
│   ├── Session information (ID, dates, reviewer)
│   ├── Generation timestamp and version
│   └── Workflow provenance (which stages completed)
│
├── Executive Summary
│   ├── Overall compliance status
│   ├── Coverage statistics (requirements met/partial/missing)
│   ├── Validation summary (pass/warn/fail)
│   ├── Items requiring human review
│   └── Recommended next action
│
├── Requirements Coverage Analysis
│   ├── ✅ Covered Requirements (detailed findings)
│   ├── ⚠️  Partially Covered Requirements (with gaps identified)
│   ├── ❌ Missing Requirements (with impact assessment)
│   └── 🚩 Flagged Requirements (needing special attention)
│
├── Cross-Document Validation Results
│   ├── Date Alignment Checks
│   ├── Land Tenure Consistency
│   ├── Project ID Verification
│   └── Other Methodology-Specific Validations
│
├── Evidence Index
│   ├── Documents Reviewed (inventory with metadata)
│   ├── Evidence Snippets (organized by requirement)
│   └── Citation Map (requirement → document → page)
│
├── Items for Human Review
│   ├── Prioritized by severity
│   ├── Categorized by type
│   └── With recommended actions
│
└── Audit Trail & Provenance
    ├── Session history (stages completed, timestamps)
    ├── Agent actions log (extractions, validations performed)
    ├── Document checksums (verification of sources)
    └── Version history (if report regenerated)
```

### Information Density Gradients

The report should support progressive disclosure:

1. **Glance Layer** (< 30 seconds): Status indicators, percentages, overall recommendation
2. **Scan Layer** (2-3 minutes): Category summaries, flagged items, key statistics
3. **Review Layer** (10-15 minutes): Requirement-by-requirement findings with evidence
4. **Verify Layer** (30+ minutes): Full evidence snippets, complete citations, validation details

---

## 3. Format Comparison Analysis

### Markdown Report

**Purpose:** Human-readable primary review document
**Audience:** Becca, internal reviewers, project developers (post-approval)

**Strengths:**
- Highly readable with clear visual hierarchy
- Renders well in browsers, GitHub, documentation systems
- Supports inline formatting (tables, lists, code blocks)
- Easy to version control and diff
- Can be converted to HTML/PDF for distribution

**Weaknesses:**
- Limited interactivity (no filtering, sorting, collapsing)
- Can become very long for complex projects
- No dynamic updates or computed views
- Limited styling options

**Optimal Use Cases:**
- Primary review document for Becca
- Archival record of review
- Basis for HTML/PDF generation
- Version-controlled audit trail

**Current Implementation Analysis:**

The existing Markdown formatter (`format_markdown_report`) provides:
- Clear hierarchical structure with emoji-based status indicators
- Requirements grouped by status (covered/partial/missing/flagged)
- Inline evidence summaries and citations
- Cross-validation results in structured sections

**Gaps Identified:**
- No table of contents for navigation
- Limited collapsibility for long sections
- No visual statistics (charts/graphs)
- Evidence snippets not included inline (only summaries)

**Recommendations:**
1. Add table of contents with anchor links
2. Include mini-statistics dashboard in executive summary
3. Add collapsible sections notation (even if not interactive, signals structure)
4. Consider adding evidence snippet excerpts (1-2 sentences max) inline

---

### JSON Report

**Purpose:** Machine-readable structured data
**Audience:** Programmatic systems, data integrations, advanced tooling

**Strengths:**
- Fully structured and queryable
- Enables programmatic analysis and automation
- Supports precise data extraction
- Can be transformed into any other format
- Ideal for API integrations and database storage

**Weaknesses:**
- Not human-readable without tooling
- Requires technical skills to consume
- No inherent presentation layer

**Optimal Use Cases:**
- Integration with tracking systems (Airtable, databases)
- Programmatic report analysis
- Data science and trend analysis
- Custom report generation pipelines
- KOI/Commons integration

**Current Implementation Analysis:**

The JSON export serializes the full `ReviewReport` Pydantic model, preserving:
- Complete metadata and provenance
- All requirement findings with full detail
- All validation results
- Summary statistics
- Items for review

**Gaps Identified:**
- No schema versioning (for future compatibility)
- Missing workflow context (which prompts were run, when)
- No diff information (if report regenerated)
- Limited provenance (no checksums for evidence sources)

**Recommendations:**
1. Add `schema_version` field for backward compatibility
2. Include `workflow_context` with stage completion details
3. Add `generation_context` with any re-generation history
4. Extend document references with checksums and source URLs
5. Include agent confidence metadata for each finding

---

### PDF Report (Future Consideration)

**Purpose:** Polished, professional external distribution
**Audience:** Project developers, verifiers, stakeholders, public record

**Strengths:**
- Professional presentation
- Consistent rendering across platforms
- Supports rich formatting (headers, footers, page numbers)
- Embedded images and charts possible
- Widely accepted as official documentation

**Weaknesses:**
- Not easily editable or versionable
- Requires PDF generation tooling
- Larger file sizes
- Accessibility challenges

**Optimal Use Cases:**
- Final approval documents
- Public registry records
- Stakeholder reports
- Compliance documentation

**Implementation Considerations:**
- Convert Markdown → HTML → PDF (using Pandoc, WeasyPrint, or similar)
- Add professional styling (Regen branding, logos, formatting)
- Include cover page with project metadata
- Add footer with report version and generation date
- Consider table of contents with page numbers
- Ensure accessibility (tagged PDFs, alt text)

---

### Interactive HTML Dashboard (Future Enhancement)

**Purpose:** Interactive exploration and filtering
**Audience:** Becca during active review, advanced users

**Strengths:**
- Dynamic filtering and sorting
- Collapsible sections for navigation
- Interactive charts and visualizations
- Search and keyword highlighting
- Real-time updates during review

**Weaknesses:**
- Requires web infrastructure
- More complex to implement
- Dependency on browser rendering
- Versioning/archival more complex

**Optimal Use Cases:**
- Active review process
- Exploratory analysis
- Multi-session comparison
- Collaborative review workflows

---

## 4. Citation & Evidence Linking Strategy

### Citation Architecture

Every assertion in the report should be traceable to source evidence through a multi-level citation system:

#### Level 1: Requirement → Document Mapping
```
REQ-015: Baseline soil carbon measurements
└─ Mapped Documents: Project_Plan.pdf, Baseline_Report.pdf
```

#### Level 2: Requirement → Document → Page Citations
```
REQ-015: Baseline soil carbon measurements
└─ Citations:
    ├─ Project_Plan.pdf, Page 12
    ├─ Project_Plan.pdf, Page 18
    └─ Baseline_Report.pdf, Page 3-5
```

#### Level 3: Requirement → Document → Page → Evidence Snippet
```
REQ-015: Baseline soil carbon measurements
└─ Evidence:
    ├─ Project_Plan.pdf, Page 12
    │   "Baseline soil organic carbon will be measured using..."
    │   [Confidence: 0.95]
    │
    └─ Baseline_Report.pdf, Page 3
        "Initial SOC measurements taken on 2024-03-15..."
        [Confidence: 0.98]
```

#### Level 4: Full Evidence Context (On-Demand)
- Complete paragraph or section containing evidence
- Surrounding context (before/after)
- Document metadata (version, date, author)
- Extraction metadata (method, confidence, timestamp)

### Citation Format Standards

**In Markdown Reports:**
```markdown
### ✅ REQ-015: Baseline soil carbon measurements

**Status:** Covered
**Confidence:** 0.96 (96%)
**Evidence:** 3 snippet(s) from 2 document(s)
**Summary:** Strong evidence found across Project Plan and Baseline Report

**Citations:**
- Project_Plan.pdf, Page 12
- Project_Plan.pdf, Page 18
- Baseline_Report.pdf, Page 3-5

**Key Evidence:**
> "Baseline soil organic carbon will be measured using laboratory analysis
> of composite samples from 0-30cm depth across all management zones."
> — Project_Plan.pdf, Page 12
```

**In JSON Reports:**
```json
{
  "requirement_id": "REQ-015",
  "requirement_text": "Baseline soil carbon measurements",
  "status": "covered",
  "confidence": 0.96,
  "evidence_snippets": [
    {
      "document_id": "doc-001",
      "document_name": "Project_Plan.pdf",
      "page": 12,
      "snippet_text": "Baseline soil organic carbon will be measured...",
      "confidence": 0.95,
      "extraction_method": "semantic_search",
      "context_before": "...",
      "context_after": "..."
    }
  ],
  "page_citations": [
    "Project_Plan.pdf, Page 12",
    "Project_Plan.pdf, Page 18",
    "Baseline_Report.pdf, Page 3-5"
  ]
}
```

### Linking Strategies

**1. Deep Links to Source Documents (Future)**

When documents are stored in Google Drive or SharePoint:
```
Project_Plan.pdf, Page 12
→ https://drive.google.com/file/d/abc123#page=12
```

This enables one-click navigation from report to source document at exact location.

**2. Embedded Evidence Snippets**

Include 1-3 sentence excerpts inline with citations, allowing verification without opening source documents for routine checks.

**3. Evidence Index Section**

Dedicated section listing all evidence snippets grouped by document, enabling systematic verification of extractions.

**4. Citation Confidence Indicators**

Each citation marked with confidence level:
- 🟢 High confidence (0.85+): Strong semantic match, clear relevance
- 🟡 Medium confidence (0.6-0.84): Probable match, may need verification
- 🔴 Low confidence (<0.6): Weak match, requires human review

---

## 5. Report Customization Options

### Pre-Generation Configuration

Becca should be able to configure report generation before it runs:

#### Content Filters
- **Include Evidence Snippets:** Yes/No/Summary-only
  - Full: All snippets with context
  - Summary: Brief summaries only
  - None: Citations only, no snippet text

- **Include Validation Details:** All/Failures-only/Summary-only
  - All: Every validation check with results
  - Failures: Only failed/warning validations
  - Summary: Statistics only

- **Detail Level:** Executive/Standard/Comprehensive
  - Executive: Summary + flagged items only
  - Standard: Summary + all requirements + validations
  - Comprehensive: Everything including full evidence

#### Section Selection
- [ ] Project Metadata
- [x] Executive Summary (always included)
- [x] Requirements Coverage
- [ ] Requirements Detail (expand each)
- [x] Validation Results
- [ ] Validation Detail (expand each)
- [ ] Evidence Index
- [x] Items for Review
- [x] Next Steps
- [ ] Audit Trail

#### Formatting Options
- **Status Indicator Style:** Emoji/Text/Icons
- **Grouping Strategy:**
  - By Status (Covered/Partial/Missing)
  - By Category (Registry Docs/Protocol Requirements/Project Details)
  - By Priority (Flagged first)
- **Sort Order:** Alphabetical/By confidence/By requirement ID

### Post-Generation Customization

After initial generation, Becca should be able to:

**Add Narrative Sections:**
- Custom executive summary
- Reviewer notes per requirement
- Overall assessment paragraph
- Recommendations for approval

**Suppress/Emphasize Content:**
- Hide non-critical covered requirements (noise reduction)
- Expand flagged items with additional detail
- Add custom sections (special considerations)

**Annotate Findings:**
- Mark agent findings as "Verified" or "Needs Correction"
- Add reviewer confidence assessments
- Link related requirements (cross-references)

**Visual Customization:**
- Apply Regen branding templates
- Adjust color schemes for printing
- Modify layout for different export formats

### Template System (Future)

For recurring project types (e.g., Ecometric batch submissions):

**Saved Report Templates:**
```yaml
template:
  name: "Ecometric Carbon Farm - Standard Review"
  methodology: "Soil Carbon Protocol v2.1"

  content:
    detail_level: "standard"
    include_evidence_snippets: "summary-only"
    include_validation_details: "failures-only"

  formatting:
    grouping: "by-status"
    sort_order: "by-priority"
    status_style: "emoji"

  custom_sections:
    - title: "Batch Review Summary"
      position: "after-metadata"
      content: "Auto-generated from aggregation metadata"

    - title: "Common Issues Across Batch"
      position: "before-requirements"
      content: "Flagged items appearing in >3 farms"
```

---

## 6. Export & Sharing Workflows

### Export Formats

#### Markdown Export (Current)
- **Primary Format:** report.md saved to session directory
- **Use Case:** Active review, version control, text editing
- **Access:** File path provided in prompt response
- **Limitations:** Must manually open/view file

**Enhancement Opportunities:**
1. Inline preview in MCP response (first 100 lines)
2. Automatic opening in default editor
3. Copy to clipboard option
4. Push to Google Drive/SharePoint

#### JSON Export (Current)
- **Primary Format:** report.json saved to session directory
- **Use Case:** Programmatic access, data integration
- **Access:** File path provided in prompt response
- **Limitations:** No built-in visualization

**Enhancement Opportunities:**
1. JSON schema documentation
2. Example queries/transformations
3. API endpoint for remote access
4. Automatic upload to data warehouse

#### Future Export Formats

**HTML Export:**
```
report.html
├─ Self-contained file
├─ Embedded CSS styling
├─ Collapsible sections with JavaScript
├─ Print-optimized CSS
└─ Shareable via web/email
```

**PDF Export:**
```
report.pdf
├─ Professional layout with branding
├─ Table of contents with page numbers
├─ Headers/footers (project name, date, page #)
├─ Embedded images (logos, charts)
└─ Tagged for accessibility
```

**Spreadsheet Export (Requirements Checklist):**
```
checklist.xlsx
├─ Requirements sheet (ID, text, status, confidence)
├─ Evidence sheet (citations per requirement)
├─ Validation sheet (check results)
├─ Summary sheet (statistics, charts)
└─ Audit sheet (session history)
```

**Google Docs Export:**
```
Integration with Google Drive API
├─ Create editable Google Doc
├─ Preserve formatting and structure
├─ Enable collaborative commenting
├─ Maintain version history
└─ Share with stakeholders directly
```

### Sharing Workflows

#### Internal Sharing (Regen Team)

**Scenario:** Share with another reviewer for second opinion

**Workflow:**
1. Generate report (Markdown + JSON)
2. Push to shared Google Drive folder
3. Notify reviewer via Slack/email
4. Reviewer accesses via link
5. Comments/edits in Google Docs
6. Original reviewer incorporates feedback

**System Support Needed:**
- Google Drive integration
- Notification templates
- Permission management (internal-only visibility)

#### External Sharing (Project Developers)

**Scenario:** Request corrections from project developer

**Workflow:**
1. Generate focused report (flagged items only)
2. Add reviewer notes explaining issues
3. Export to professional PDF
4. Email to developer with cover letter
5. Developer submits corrections
6. Re-run workflow and regenerate report

**System Support Needed:**
- Filtered report generation (issues-only)
- PDF export with branding
- Email templates with standard language
- Revision tracking (before/after comparison)

#### Stakeholder Sharing (Verifiers, Methodology Developers)

**Scenario:** Share approved review with third-party verifier

**Workflow:**
1. Generate comprehensive report
2. Mark as "Final - Approved"
3. Export to PDF with approval signature
4. Upload to project folder
5. Share folder link with verifier

**System Support Needed:**
- Approval marking/status
- Digital signature integration
- Final report locking (no further edits)
- Provenance anchoring (checksum to ledger)

---

## 7. Report Versioning Strategy

### Why Versioning Matters

Reports may be regenerated multiple times:
- After additional evidence extraction
- After cross-validation is run
- After document corrections are submitted
- After human review annotations
- Before final approval

Each version should be tracked, compared, and preserved.

### Versioning Model

#### Version Identifiers
```
report-session-abc123-v1.md (Initial generation)
report-session-abc123-v2.md (After validation added)
report-session-abc123-v3.md (After developer corrections)
report-session-abc123-final.md (Approved version)
```

#### Version Metadata
```json
{
  "report_version": "3",
  "session_id": "session-abc123",
  "generated_at": "2025-11-14T15:30:00Z",
  "generation_trigger": "developer_corrections_submitted",
  "workflow_state": {
    "document_discovery": "completed",
    "evidence_extraction": "completed",
    "cross_validation": "completed",
    "report_generation": "completed"
  },
  "previous_version": "2",
  "changes_since_previous": [
    "2 new documents added",
    "REQ-015 status changed: missing → partial",
    "3 validation warnings resolved"
  ]
}
```

#### Version Comparison

**Diff Report:**
When regenerating, show what changed:

```markdown
# Report Version Comparison: v2 → v3

## Changes Summary
- 2 new documents discovered
- 1 requirement status improved
- 3 validation warnings resolved
- 0 requirements degraded

## Changed Requirements

### REQ-015: Baseline soil carbon measurements
- **Status:** missing → partial
- **Confidence:** 0.0 → 0.75
- **Reason:** New document "Baseline_Report.pdf" added
- **New Evidence:** 2 snippets extracted

### REQ-018: Additionality demonstration
- **Status:** partial → covered
- **Confidence:** 0.65 → 0.92
- **Reason:** Developer added clarifying paragraph to Project_Plan.pdf
- **New Evidence:** 1 snippet extracted
```

### Version History UI

**In Report Metadata Section:**
```markdown
## Report Version History

**Current Version:** 3 (2025-11-14 15:30 UTC)
**Previous Versions:**
- Version 2: 2025-11-13 10:15 UTC (After validation)
- Version 1: 2025-11-12 14:00 UTC (Initial generation)

**Changes in This Version:**
- 2 new documents added
- 1 requirement improved (missing → partial)
- 3 validation warnings resolved

[View detailed comparison with v2] ← Link to diff
```

### Retention Policy

**Current Session:**
- Keep all versions during active review
- Mark one version as "active" for current work

**After Approval:**
- Preserve final approved version permanently
- Archive intermediate versions (compressed)
- Keep version metadata for audit trail

**After Session Completion:**
- Final report → permanent archive
- Intermediate versions → compressed archive (30 days)
- Version metadata → permanent audit log

---

## 8. Report Regeneration Scenarios

### When to Regenerate

Becca might need to regenerate reports in several scenarios:

#### Scenario 1: After Additional Evidence Extraction

**Context:** Initial extraction missed some evidence; re-ran with better search terms

**User Need:**
- See updated coverage statistics
- Identify which requirements improved
- Preserve previous findings not affected

**System Behavior:**
1. Detect that evidence.json has changed
2. Prompt: "Evidence data has been updated. Regenerate report?"
3. If yes: Generate new version with comparison to previous
4. Preserve previous version as v[N-1]
5. Highlight changes in new report

**UX Considerations:**
- Don't force regeneration automatically (might be mid-review)
- Show what changed before regenerating
- Offer preview of changes

#### Scenario 2: After Cross-Validation

**Context:** Initial report generated before validation was run

**User Need:**
- Add validation results to existing report
- Maintain consistency in structure
- Understand new items flagged for review

**System Behavior:**
1. Detect that validation.json now exists
2. Auto-suggest: "Cross-validation complete. Update report?"
3. If yes: Regenerate with validation section added
4. Mark as incremental update (not full regeneration)

**UX Considerations:**
- This is additive (no data lost)
- Consider in-place update vs. new version
- Highlight new validation section clearly

#### Scenario 3: After Developer Corrections

**Context:** Developer submitted new/corrected documents

**User Need:**
- See what improved
- Identify remaining gaps
- Compare before/after status

**System Behavior:**
1. Re-run document discovery (new documents found)
2. Re-run evidence extraction (new evidence found)
3. Prompt: "New documents processed. Regenerate report to see improvements?"
4. If yes: Generate new version with before/after comparison
5. Highlight improvements in green, degradations in red

**UX Considerations:**
- Show diff prominently
- Make improvement tracking automatic
- Preserve correction history for audit

#### Scenario 4: After Human Annotations

**Context:** Becca added notes, verified findings, corrected errors

**User Need:**
- Include human annotations in report
- Mark agent findings as verified/corrected
- Generate final version for approval

**System Behavior:**
1. Detect that annotations/notes have been added
2. Prompt: "Ready to generate final report with your notes?"
3. If yes: Generate final version clearly marked with human input
4. Distinguish agent findings (blue) from human annotations (black)

**UX Considerations:**
- Make human vs. agent distinction visually clear
- Support both inline and separate annotation styles
- Preserve annotation provenance (who, when)

#### Scenario 5: Format Conversion

**Context:** Need PDF for stakeholder sharing after generating Markdown

**User Need:**
- Same content, different format
- Professional presentation
- No data changes

**System Behavior:**
1. Offer export without regeneration: "Export current report as PDF?"
2. Apply formatting/styling for PDF
3. Preserve version number (same version, different format)

**UX Considerations:**
- This is not a regeneration, just format conversion
- Maintain version consistency across formats
- Cache formatted versions for performance

---

## 9. Workflow Integration Analysis

### Position in Overall Workflow

Report Generation is Stage 5 of 7:

```
1. Initialize → 2. Document Discovery → 3. Evidence Extraction →
4. Cross-Validation → 5. REPORT GENERATION → 6. Human Review → 7. Complete
```

**Upstream Dependencies:**
- Requires: Evidence extraction completed
- Optional: Cross-validation completed (enhances report)
- Uses: All prior stage outputs

**Downstream Impacts:**
- Enables: Human review of flagged items
- Supports: Final approval decision
- Feeds: Completion/archival stage

### State Transitions

**Entering Report Generation:**

From `VALIDATED` or `EVIDENCE_EXTRACTED` state:
```
Prerequisites Check:
✅ evidence.json exists
✅ evidence_extraction == "completed"
⚠️  validation.json optional (warn if missing)

→ REPORT_GENERATED state
```

**During Report Generation:**

```
Status: in_progress
Actions:
1. Load session data (session.json)
2. Load evidence data (evidence.json)
3. Load validation data (validation.json) if exists
4. Load documents metadata (documents.json)
5. Generate Markdown report
6. Generate JSON report
7. Update workflow progress
8. Transition to REPORT_GENERATED

Output:
- report.md saved to session directory
- report.json saved to session directory
- Session state updated
```

**After Report Generation:**

```
State: REPORT_GENERATED
Next Steps:
→ Run /human-review if items flagged
→ Run /complete if no review needed
→ Re-run /report-generation if data changes
```

### Integration with Human Review Stage

Report Generation directly feeds into Human Review (Stage 6):

**Handoff Points:**

1. **Items for Human Review List**
   - Generated in report
   - Consumed by human review prompt
   - Used to focus reviewer attention

2. **Evidence Snippets**
   - Extracted in evidence stage
   - Formatted in report
   - Verified in human review

3. **Validation Flags**
   - Created in validation stage
   - Surfaced in report
   - Resolved in human review

**Bi-directional Flow:**

```
Report Generation → Human Review
- Provides: Flagged items, evidence summaries, validation results
- Receives: Annotations, corrections, verification status

Human Review → Report Regeneration
- Triggers: New annotations added, corrections made
- Provides: Updated notes, verification marks
- Receives: Updated report with human input highlighted
```

---

## 10. Error Handling & Edge Cases

### Missing Data Scenarios

#### No Evidence Extracted

**Scenario:** Evidence extraction failed or found no evidence

**User Experience:**
```
⚠️  Warning: No evidence data found

Report generation requires evidence extraction to be completed first.

Please run:
  /evidence-extraction

Then return here for report generation.
```

**System Behavior:**
- Check for evidence.json existence
- Show helpful error with next steps
- Don't generate incomplete report

#### No Validation Data

**Scenario:** Report generated before cross-validation run

**User Experience:**
```
ℹ️  Note: Cross-validation has not been run

Generating report without validation results.

For a more comprehensive review, consider running:
  /cross-validation

Then regenerate the report.
```

**System Behavior:**
- Generate report with available data
- Clearly mark validation section as "Not Run"
- Include note about optional validation

#### No Documents Discovered

**Scenario:** Document discovery found nothing

**User Experience:**
```
❌ Error: No documents discovered

Cannot generate report without discovered documents.

Please check:
1. Document discovery has been run (/document-discovery)
2. Documents were found in the specified path
3. Documents are accessible and readable
```

**System Behavior:**
- Check documents.json for entries
- Provide diagnostic information
- Block report generation

### Data Quality Issues

#### Low Confidence Evidence

**Scenario:** All evidence has confidence < 0.5

**User Experience:**
```
⚠️  Data Quality Warning

Evidence extraction confidence is very low across all requirements.

This may indicate:
- Documents are in unsupported formats
- Documents don't contain expected information
- Extraction parameters need adjustment

Recommended actions:
1. Review document quality and format
2. Check if correct methodology was selected
3. Consider manual evidence annotation

Continue with report generation? (Results may need extensive human review)
```

**System Behavior:**
- Calculate average confidence across all evidence
- Warn if below threshold (e.g., 0.5)
- Generate report but highlight quality concerns

#### Conflicting Validation Results

**Scenario:** Multiple validations of same type with contradictory results

**User Experience:**
```
⚠️  Validation Conflict Detected

Multiple date alignment validations produced conflicting results:
- Check 1: PASS (Project_Plan dates align)
- Check 2: FAIL (Baseline_Report dates misaligned)

This requires human investigation.

Including all validation results in report with conflict flag.
```

**System Behavior:**
- Detect contradictory validation results
- Flag for human review
- Include all results with explanation

### Format/Export Errors

#### Markdown Generation Failure

**Scenario:** Error during Markdown formatting

**User Experience:**
```
❌ Error: Markdown report generation failed

Error: Invalid character encoding in evidence snippet

Attempting fallback to JSON-only report...
✅ JSON report generated successfully: report.json

Please review the error and contact support if needed.
```

**System Behavior:**
- Try JSON generation as fallback
- Log detailed error for debugging
- Provide partial results where possible

#### File Write Permission Error

**Scenario:** Cannot write report to session directory

**User Experience:**
```
❌ Error: Cannot save report to disk

Permission denied writing to: /path/to/session/report.md

Please check:
1. Session directory exists and is writable
2. Disk space is available
3. File is not locked by another process

Report has been generated but not saved.
Would you like to:
1. Retry save
2. Save to alternative location
3. View report inline (without saving)
```

**System Behavior:**
- Catch file write errors
- Offer alternative save locations
- Allow viewing generated content even if save fails

### Regeneration Conflicts

#### Report Modified Externally

**Scenario:** User edited report.md file manually

**User Experience:**
```
⚠️  Warning: Report has been modified since generation

report.md was last modified: 2025-11-14 16:45 (external edit)
Last generated by system: 2025-11-14 15:30

Regenerating will overwrite your manual changes.

Options:
1. Cancel (keep manual edits)
2. Rename existing report (create backup)
3. Overwrite (lose manual changes)
```

**System Behavior:**
- Check file modification timestamp
- Compare to generation timestamp in metadata
- Offer backup/rename before overwriting

---

## 11. Accessibility & Usability Considerations

### Visual Design Principles

#### Status Indicators

**Current Approach:** Emoji-based status
```
✅ Covered
⚠️  Partial
❌ Missing
🚩 Flagged
```

**Accessibility Concerns:**
- Screen readers may not convey emoji meaning
- Emoji rendering varies across platforms
- Color-blind users may not distinguish meanings

**Enhanced Approach:**
```
✅ COVERED: [Requirement text]
⚠️  PARTIAL: [Requirement text]
❌ MISSING: [Requirement text]
🚩 FLAGGED: [Requirement text]
```

Add explicit text labels alongside emoji for clarity.

**Alternative for Export:**
```
[COVERED] Requirement text
[PARTIAL] Requirement text
[MISSING] Requirement text
[FLAGGED] Requirement text
```

Use text-only indicators when emoji may not render properly.

#### Color Usage

**Principle:** Never rely solely on color to convey information

**Current Implementation:**
- Status conveyed through emoji + text
- No color-only distinctions

**Future Enhancements:**
- If adding color coding, always include text labels
- Use patterns/shapes in addition to color
- Provide high-contrast mode option

#### Readability

**Font Choices:**
- Monospace for code, IDs, file paths
- Sans-serif for body text
- Adequate font size (minimum 11pt for PDF)

**Layout:**
- Clear visual hierarchy (headings, subheadings)
- Adequate whitespace
- Maximum line length ~80-100 characters
- Logical reading order for screen readers

**Language:**
- Clear, concise writing
- Avoid jargon where possible
- Define technical terms on first use
- Use active voice

### Screen Reader Compatibility

#### Markdown Considerations

**Good Practices:**
- Use semantic headings (# ## ###) not decorative formatting
- Provide alt text for any future images/charts
- Use lists for enumerated content
- Include descriptive link text

**Table Accessibility:**
```markdown
<!-- Good: Headers clearly defined -->
| Requirement | Status | Confidence |
|-------------|--------|------------|
| REQ-001     | ✅ Covered | 95% |

<!-- Better: Include aria-label equivalents in HTML export -->
<table role="table" aria-label="Requirements Coverage">
  <thead>
    <tr>
      <th scope="col">Requirement</th>
      <th scope="col">Status</th>
      <th scope="col">Confidence</th>
    </tr>
  </thead>
  ...
</table>
```

#### PDF Considerations

**Accessibility Features:**
- Tagged PDF structure
- Document outline (headings hierarchy)
- Alt text for images
- Logical reading order
- Embedded fonts
- Searchable text (not scanned images)

### Cognitive Load Management

#### Progressive Disclosure

**Principle:** Show summary first, details on demand

**Implementation:**
```markdown
## Executive Summary
[High-level overview - 1 page max]

## Quick Stats
Requirements: 23 covered, 5 partial, 2 missing
Overall Coverage: 77%

## Detailed Findings
[Full requirement-by-requirement breakdown]
[Only shown if user scrolls/expands]
```

#### Scannable Structure

**Techniques:**
- Bold key phrases
- Use of bullet points
- Clear section headers
- Consistent formatting
- Visual breaks between sections

#### Information Hierarchy

**Priority Ordering:**
1. What matters most (flagged items, missing requirements)
2. What needs attention (partial coverage, warnings)
3. What's working (covered requirements, passed validations)
4. Supporting detail (full evidence, audit trail)

---

## 12. Performance & Scalability

### Generation Performance

#### Current Performance Profile

**Small Project (20 requirements, 5 documents):**
- Evidence loading: <1s
- Report formatting: <1s
- File writing: <1s
- **Total: ~2-3 seconds**

**Medium Project (50 requirements, 15 documents):**
- Evidence loading: ~2s
- Report formatting: ~3s
- File writing: ~1s
- **Total: ~5-6 seconds**

**Large Project (100 requirements, 40 documents):**
- Evidence loading: ~5s
- Report formatting: ~8s
- File writing: ~2s
- **Total: ~15 seconds**

**Aggregated Batch (70 farms, 50 requirements each):**
- Current approach: 70 × 15s = **17.5 minutes**
- Parallel processing: ~5 minutes (theoretical)
- **Target: <10 minutes**

#### Performance Bottlenecks

1. **Evidence Data Loading**
   - JSON parsing for large evidence files
   - Iteration over thousands of snippets
   - **Solution:** Lazy loading, pagination

2. **Markdown Formatting**
   - String concatenation in loops
   - Complex formatting logic
   - **Solution:** Template engine, buffered writing

3. **File I/O**
   - Multiple write operations
   - Large file sizes
   - **Solution:** Streaming writes, compression

#### Optimization Strategies

**Lazy Loading:**
```python
# Instead of loading all evidence at once
evidence_data = state_manager.read_json("evidence.json")

# Load summary first, details on demand
evidence_summary = load_evidence_summary()
evidence_details = load_evidence_details_lazy()
```

**Streaming Generation:**
```python
# Instead of building entire report in memory
report_lines = []
for req in requirements:
    report_lines.extend(format_requirement(req))
report_content = "\n".join(report_lines)

# Stream to file incrementally
with open(report_path, "w") as f:
    write_report_header(f)
    for req in requirements:
        write_requirement(f, req)
    write_report_footer(f)
```

**Parallel Generation:**
```python
# For multi-format generation
async def generate_reports(session_id):
    markdown_task = asyncio.create_task(generate_markdown(session_id))
    json_task = asyncio.create_task(generate_json(session_id))

    markdown_result, json_result = await asyncio.gather(
        markdown_task, json_task
    )
```

### Scalability Considerations

#### Large Evidence Sets

**Challenge:** 100+ requirements × 10+ snippets each = 1000+ evidence snippets

**Strategy:**
- Paginate evidence in report (first 3 snippets per requirement)
- Provide "View All Evidence" link to separate detailed report
- Generate summary report + detailed appendix

#### Long-Running Sessions

**Challenge:** Session data grows over time with multiple regenerations

**Strategy:**
- Archive old report versions (compress)
- Separate current data from historical data
- Implement data retention policies

#### Concurrent Report Generation

**Challenge:** Multiple reviewers generating reports simultaneously

**Strategy:**
- Session-level locking during generation
- Queue system for batch generation
- Caching of formatted sections

---

## 13. Integration with KOI & Knowledge Commons

### Future Integration Points

While current implementation operates at the file system level, future integration with KOI and Knowledge Commons will enhance provenance, accessibility, and collaboration.

#### Resource Registration

**Every Generated Report as a KOI Resource:**

```json
{
  "iri": "regen:koi:resource:report-session-abc123-v3",
  "title": "Registry Review Report - Botany Farm 2022-2023",
  "type": "registry-review-report",
  "format": "text/markdown",
  "source": "registry-review-mcp",
  "visibility": "internal",
  "tags": ["registry", "review", "soil-carbon", "ecometric"],
  "contributors": ["becca@regen.network", "agent:registry-review"],
  "related_resources": [
    "regen:koi:resource:project-plan-botany-farm",
    "regen:koi:resource:baseline-report-botany-farm"
  ],
  "metadata": {
    "session_id": "session-abc123",
    "project_id": "EC-2024-001",
    "methodology": "Soil Carbon Protocol v2.1",
    "report_version": "3",
    "generation_date": "2025-11-14T15:30:00Z",
    "coverage_percentage": 77,
    "items_for_review": 5
  },
  "resolvers": ["https://drive.google.com/file/d/..."],
  "checksum": "sha256:def5678",
  "indexed_at": "2025-11-14T15:31:00Z"
}
```

#### Provenance Anchoring

**Ledger Integration:**

1. Generate report checksum (SHA-256)
2. Anchor checksum to Regen Ledger via `x/data` module
3. Record provenance chain:
   ```
   Report → Evidence → Documents → Source Files
   ```
4. Enable cryptographic verification of report integrity

**RDF Metadata:**

```turtle
@prefix regen: <http://regen.network/ontology/> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .

<regen:report:session-abc123-v3>
    a regen:RegistryReviewReport ;
    dc:title "Registry Review Report - Botany Farm" ;
    dc:creator "agent:registry-review" ;
    dc:contributor "becca@regen.network" ;
    dc:created "2025-11-14T15:30:00Z" ;
    regen:projectID "EC-2024-001" ;
    regen:methodology "Soil Carbon Protocol v2.1" ;
    regen:coveragePercentage 77 ;
    regen:basedOn <regen:evidence:session-abc123> ;
    regen:basedOn <regen:validation:session-abc123> ;
    regen:checksum "sha256:def5678" ;
    regen:ledgerAnchor "regen:ledger:anchor:12345" .
```

#### Permissions & Access Control

**Visibility Rules:**

- **Internal:** Registry reviewers only (default)
- **Partner:** Project developer can view their own project reports
- **Public:** Approved reports for public registry (post-approval)

**Access Scenarios:**

1. **Active Review:** Internal only
2. **Corrections Requested:** Shared with developer (filtered view)
3. **Approved:** Public visibility (final version)

#### Subgraph Integration

**Registry Review Subgraph:**

Collection of all registry review artifacts for querying and analysis:

```sparql
# Find all reports for a specific methodology
SELECT ?report ?project ?coverage
WHERE {
  ?report a regen:RegistryReviewReport ;
          regen:methodology "Soil Carbon Protocol v2.1" ;
          regen:projectID ?project ;
          regen:coveragePercentage ?coverage .
  FILTER (?coverage < 80)
}
ORDER BY ?coverage
```

**Use Cases:**
- Trend analysis: Common gaps across projects
- Methodology evaluation: Which protocols have highest compliance?
- Process improvement: Which requirements most often missing?

---

## 14. User Testing Insights & Iteration

### Key Questions for User Testing

When testing report generation with Becca, focus on:

#### Comprehension

1. Can you determine project approval status in <30 seconds?
2. Which requirements need attention? Can you find them quickly?
3. What does the confidence score mean to you? Is it helpful?
4. Are the evidence citations clear and verifiable?

#### Usability

5. How would you verify an agent finding? Is the process clear?
6. What information is missing that you need for decisions?
7. What information is included that you don't need?
8. How would you share this report with a developer?

#### Workflow

9. When would you regenerate a report vs. annotate existing?
10. How do you track changes between report versions?
11. What format do you prefer for final approval documentation?
12. How does this report compare to your current manual checklist?

#### Trust

13. How confident are you in the agent's findings?
14. What makes you trust or distrust a finding?
15. Where do you feel you need to verify vs. accept?
16. What would increase your confidence in automation?

### Iteration Opportunities

Based on anticipated user feedback:

#### Iteration 1: Clarity Enhancements

**Focus:** Make report easier to scan and comprehend

**Changes:**
- Add visual summary dashboard at top
- Use color coding (with text labels) for status
- Add "Quick Actions" section for next steps
- Improve evidence snippet formatting

#### Iteration 2: Verification Support

**Focus:** Make agent findings easier to verify

**Changes:**
- Add "Verify" checkboxes per finding
- Include evidence snippet context (surrounding text)
- Link citations directly to source documents
- Add verification confidence tracking

#### Iteration 3: Customization

**Focus:** Support different review styles and preferences

**Changes:**
- Implement report templates
- Add filtering/hiding of sections
- Support custom annotation styles
- Enable report comparison view

#### Iteration 4: Collaboration

**Focus:** Enable multi-reviewer workflows

**Changes:**
- Add commenting system
- Support review assignments (REQ-001 → Reviewer A)
- Enable partial approval (approve some requirements, flag others)
- Add review status tracking per requirement

---

## 15. Success Metrics

### Quantitative Metrics

#### Report Quality

- **Coverage Accuracy:** % of requirements correctly classified (covered/partial/missing)
  - Target: >95% accuracy vs. human review

- **Evidence Precision:** % of cited evidence actually relevant
  - Target: >90% precision

- **Evidence Recall:** % of relevant evidence captured
  - Target: >85% recall

#### Performance

- **Generation Speed:** Time to generate report
  - Target: <5 seconds for standard project
  - Target: <10 minutes for 70-farm batch

- **Regeneration Frequency:** # of regenerations per project
  - Baseline: TBD (track current usage)
  - Target: <3 regenerations per project (indicates quality)

#### Efficiency

- **Time Savings:** Time to review report vs. manual checklist
  - Target: 50-70% reduction in review time

- **Verification Rate:** % of findings requiring human verification
  - Target: <20% (80% of findings accepted as-is)

### Qualitative Metrics

#### User Satisfaction

- "The report clearly shows what needs my attention" (1-5 scale)
- "I trust the agent's findings" (1-5 scale)
- "The report is easy to understand" (1-5 scale)
- "The report supports my decision-making" (1-5 scale)

#### Usefulness

- "I use the report as-is without modifications" (frequency)
- "I share the report with stakeholders" (frequency)
- "The report replaces my manual checklist" (yes/no/partially)

#### Trust Calibration

- Agent says "covered" → Human agrees (% agreement)
- Agent says "missing" → Human agrees (% agreement)
- Agent says "partial" → Human agrees (% agreement)

**Well-Calibrated System:**
- High confidence (>0.85) → >95% human agreement
- Medium confidence (0.6-0.85) → 70-85% human agreement
- Low confidence (<0.6) → Flagged for review

---

## 16. Open Questions & Research Needs

### Unresolved UX Questions

1. **Optimal Detail Level**
   - How much evidence snippet text is helpful vs. overwhelming?
   - Should snippets be inline or in separate appendix?
   - Current: 1-2 sentences; is this enough?

2. **Status Granularity**
   - Current: covered/partial/missing/flagged
   - Is "partial" clear enough? Should it be split (e.g., "mostly covered" vs. "barely covered")?
   - Should confidence scores be shown or abstracted?

3. **Report Organization**
   - Group by status vs. category vs. priority?
   - Default to showing everything or hiding details?
   - Should there be multiple report variants (executive vs. detailed)?

4. **Version Management**
   - How many versions to keep in active view?
   - When to auto-archive old versions?
   - How prominent should version history be?

5. **Human Annotation Integration**
   - Inline annotations vs. separate notes section?
   - How to distinguish agent vs. human content in single document?
   - Should human edits trigger auto-regeneration?

### Technical Unknowns

1. **PDF Generation Tooling**
   - Best approach: Pandoc vs. WeasyPrint vs. other?
   - Styling framework for professional output?
   - Accessibility (tagged PDF) support?

2. **Google Docs Integration**
   - Export to Google Docs: feasible?
   - Preserve formatting?
   - Enable collaborative editing with provenance tracking?

3. **Performance at Scale**
   - Actual performance for 100-requirement projects?
   - Parallel generation for batch projects?
   - Caching strategies for repeated generation?

4. **Comparison Algorithms**
   - How to diff two reports intelligently?
   - Present changes in most useful format?
   - Track requirement status changes over time?

### User Research Needs

1. **Report Format Preferences**
   - Conduct A/B testing with different formats
   - Test readability with different organization schemes
   - Validate optimal evidence snippet length

2. **Verification Workflows**
   - Shadow Becca during report review
   - Identify pain points in verification process
   - Test different verification UI approaches

3. **Trust Calibration**
   - When does Becca trust agent findings?
   - What factors increase/decrease trust?
   - How to communicate confidence appropriately?

4. **Sharing & Collaboration**
   - Who needs access to reports? In what format?
   - What annotations/edits are typical?
   - How are corrections communicated to developers?

---

## 17. Recommendations & Next Steps

### Immediate Priorities (P0)

1. **Add Report Preview in MCP Response**
   - Show first 50-100 lines of Markdown report inline
   - Provide summary statistics immediately
   - Reduce friction of opening files

2. **Implement Version Metadata**
   - Track generation context (what triggered regeneration)
   - Store changes-since-previous-version
   - Enable version comparison

3. **Enhance Evidence Citations**
   - Include page numbers consistently
   - Add confidence indicators per citation
   - Test deep linking to source documents

4. **Improve Status Explanations**
   - Add help text for "partial" status
   - Explain what confidence scores mean
   - Provide examples of each status category

### Short-Term Enhancements (P1)

5. **HTML Export**
   - Generate interactive HTML report
   - Enable filtering/sorting of requirements
   - Add collapsible sections
   - Include basic charts (coverage visualization)

6. **Report Templates**
   - Create template for Ecometric batch reviews
   - Support custom section ordering
   - Enable saved configurations

7. **Evidence Snippet Refinement**
   - Test optimal snippet length with users
   - Add context (before/after text)
   - Improve snippet extraction quality

8. **Comparison View**
   - Generate diff reports automatically
   - Highlight improvements/degradations
   - Track requirement status changes

### Medium-Term Goals (P2)

9. **PDF Export**
   - Professional formatting with branding
   - Accessibility (tagged PDFs)
   - Cover page with metadata
   - Charts and visualizations

10. **Google Docs Integration**
    - Export to editable Google Doc
    - Preserve formatting
    - Enable collaborative review
    - Track provenance of edits

11. **Advanced Customization**
    - Filter by category, status, confidence
    - Hide/show sections dynamically
    - Custom annotation styles
    - Multi-reviewer support

12. **Analytics Dashboard**
    - Trend analysis across projects
    - Common gaps identification
    - Methodology comparison
    - Process improvement insights

### Long-Term Vision (P3)

13. **KOI Integration**
    - Register reports as KOI resources
    - Anchor checksums to ledger
    - Enable semantic querying
    - Support subgraph integration

14. **Collaborative Review**
    - Multi-reviewer assignment
    - Comment threads per requirement
    - Review status tracking
    - Approval workflow orchestration

15. **AI-Assisted Improvement**
    - Suggest corrective actions for gaps
    - Generate developer communication
    - Learn from corrections (feedback loop)
    - Predict approval likelihood

---

## Conclusion

Report Generation is where the Registry Review workflow transforms data into decisions. The success of this stage depends on presenting complex, multi-dimensional information in a way that supports rapid comprehension, enables efficient verification, and facilitates confident decision-making.

The current implementation provides a solid foundation with dual-format reports (Markdown + JSON), clear status indicators, evidence citations, and validation results. However, significant opportunities exist to enhance usability through improved visualization, better customization, version management, and export options.

Key insights from this analysis:

1. **Progressive Disclosure:** Support multiple detail levels—glance, scan, review, verify—to accommodate different use cases and time constraints.

2. **Trust Through Transparency:** Make agent reasoning visible through evidence citations, confidence scores, and clear distinction between automated and human findings.

3. **Workflow Integration:** Report generation is not an endpoint but a pivot point—enabling human review, supporting corrections, facilitating approval.

4. **Format Flexibility:** Different audiences need different formats—Markdown for active review, JSON for programmatic access, PDF for official records, HTML for exploration.

5. **Version Intelligence:** Track not just current state but change over time—improvements after corrections, additions after new evidence, evolution toward approval.

The path forward involves iterative enhancement based on user feedback, performance optimization for large projects, and integration with broader infrastructure (KOI, Knowledge Commons, Ledger). By keeping user needs central and building incrementally, the report generation stage can evolve into a powerful decision support tool that enables the registry review process to scale while maintaining quality and rigor.

---

## Appendix A: Report Structure Examples

### Example: Executive Summary Section

```markdown
# Registry Review Report

## Project Metadata
- **Project Name:** Botany Farm Carbon Sequestration 2022-2023
- **Project ID:** EC-2024-001
- **Methodology:** Soil Carbon Protocol v2.1
- **Review Date:** 2025-11-14 15:30:00 UTC

## Executive Summary

### Overall Status: ⚠️  PARTIAL COMPLIANCE

This project demonstrates strong documentation across most requirements but has **5 items requiring attention** before approval.

### Requirements Coverage
- **Total Requirements:** 30
- ✅ **Covered:** 23/30 (77%)
- ⚠️  **Partial:** 5/30 (17%)
- ❌ **Missing:** 2/30 (7%)
- **Overall Coverage:** 77%

### Cross-Document Validation
- **Total Checks:** 8
- ✅ **Passed:** 6
- ⚠️  **Warnings:** 2
- ❌ **Failed:** 0

### Review Statistics
- **Documents Reviewed:** 12
- **Evidence Snippets Extracted:** 67
- **Items Requiring Human Review:** 5

### Recommended Action: REQUEST CORRECTIONS

The following items must be addressed before approval:
1. REQ-015: Baseline soil carbon measurements (MISSING)
2. REQ-018: Additionality demonstration (MISSING)
3. REQ-022: Monitoring plan details (PARTIAL - needs clarification)
4. VAL-DATE-02: Imagery date alignment (WARNING - 5-month gap)
5. VAL-TENURE-01: Land ownership discrepancy (WARNING - name variation)
```

### Example: Detailed Requirement Finding

```markdown
### ⚠️  REQ-022: Monitoring Plan Details

**Category:** Protocol Requirements
**Status:** Partial
**Confidence:** 0.68 (68%)
**Evidence:** 2 snippet(s) from 2 document(s)

**Summary:** Monitoring plan is mentioned but lacks required detail on sampling frequency and methodology-specific protocols for SOC measurement.

**Citations:**
- Project_Plan.pdf, Page 15
- Monitoring_Framework.pdf, Page 3

**Key Evidence:**

> "Monitoring will occur annually following the five-year baseline period,
> with soil samples collected from representative areas of each management zone."
> — Project_Plan.pdf, Page 15 [Confidence: 0.72]

> "Soil organic carbon monitoring follows Soil Carbon Protocol requirements..."
> — Monitoring_Framework.pdf, Page 3 [Confidence: 0.64]

**Issues Identified:**
- Sampling methodology not specified (composite vs. individual samples)
- SOC measurement procedure not detailed (lab analysis methods)
- Quality control/quality assurance procedures not mentioned

**Recommended Action:**
Request developer to add section in Monitoring Plan specifying:
1. Exact sampling methodology (depth increments, composite strategy)
2. Laboratory analysis procedures
3. QA/QC protocols

**Human Review Required:** Yes
**Priority:** Medium
```

---

## Appendix B: Glossary

**Agent Confidence:** Algorithmic score (0.0-1.0) indicating how certain the extraction/classification is based on semantic similarity and pattern matching.

**Citation:** Reference to specific location in source document (file + page) where evidence was found.

**Coverage:** Percentage of requirements that have adequate evidence (covered or partial status).

**Evidence Snippet:** Short text excerpt (1-3 sentences) extracted from document that supports a requirement.

**Flagged Status:** Requirement or validation marked for mandatory human review due to uncertainty or complexity.

**Regeneration:** Process of re-creating report after underlying data changes (new documents, corrections, validations).

**Report Version:** Distinct snapshot of report at specific point in time, numbered sequentially.

**Status Indicator:** Classification of requirement compliance (covered/partial/missing/flagged).

**Validation Finding:** Result of cross-document consistency check (date alignment, land tenure, project ID).

---

**Document Status:** Draft for Review
**Next Review:** After user testing with Becca
**Feedback:** Send to development team and UX stakeholders
