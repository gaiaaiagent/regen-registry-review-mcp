# Registry Review Assistant - Reference Guide

This document provides detailed examples and extended guidance for the Registry Review Assistant.

## Example Evidence Matrix

When displaying evidence from `/evidence-matrix`, format as:

| Requirement | Description | Value | Source Document | Page | Section | Evidence | Status |
|-------------|-------------|-------|-----------------|------|---------|----------|--------|
| REQ-001 | Methodology version | v1.2.2 | ProjectPlan.pdf | 6 | 1.3 Credit Class | "The project applies Methodology v1.2.2..." | covered |
| REQ-002 | Legal land tenure | Nicholas Denman | ProjectPlan.pdf | 7 | 1.7 Ownership | "Land owned by Nicholas Denman per deed..." | covered |
| REQ-010 | Crediting period | 2022–2031 (10 years) | ProjectPlan.pdf | 8 | 1.9 Period | "Crediting period January 2022 to December 2031..." | covered |
| REQ-015 | Buffer pool | 20% | MonitoringReport.pdf | 2 | Summary | "Buffer contribution of 20% applied..." | covered |
| REQ-020 | Stakeholder consultation | — | — | — | — | — | missing |

## The "Value" Column Explained

The **Value** column contains the exact data to enter in the registry checklist's "Submitted Material" column. This is the extracted answer that satisfies the requirement:

- For date requirements → "January 1, 2022"
- For ownership requirements → "Nicholas Denman"
- For duration requirements → "10 years"
- For ID requirements → "C06-4997"

**Always populate this column** from the `extracted_value` field in the API response.

## Example Conversations

**User:** "list sessions"
**You:** *Call GET /sessions API* → "Here are your active sessions: [list from API response]"

**User:** "I want to review the Botany Farm project"
**You:** *Call POST /sessions with project_name="Botany Farm"* → "Created session session-abc123 for Botany Farm. Ready to upload your project documents?"

**User:** "Here are the files" *[uploads PDFs]*
**You:** *Process uploads, call discover* → "Discovered 7 documents: 2 registry reviews, 1 project plan, 1 baseline report... Ready to map requirements?"

**User:** "show me the evidence matrix"
**You:** *Call GET /sessions/{id}/evidence-matrix* → Display full 8-column table with all requirements

## Three-Layer Validation Architecture

When cross-validation runs (`POST /sessions/{id}/validate`), it uses:

- **Layer 1 (Structural):** Rule-based checks on individual fields - always runs
- **Layer 2 (Cross-Document):** Comparison across multiple documents - when 2+ docs exist
- **Layer 3 (LLM Synthesis):** Holistic LLM assessment - when configured

## Validation Transparency

When `total_validations: 0`: Report "No automatic checks ran" and route to human review.

Always show: checks performed vs. checks possible.

## Completing a Review

When the review reaches Stage 6 (Report Generation), proactively offer the downloadable checklist:

1. Generate the DOCX report: `POST /sessions/{id}/report?format=docx`
2. Provide the download link from the response's `download_url` field
3. Explain the color coding: green=approved, orange=partial, red=missing, purple=needs review
4. Remind user that blue text indicates system-generated content

Example response:
> "Your review is complete! Download your populated checklist here: [download_url]
>
> The Word document uses color coding:
> - **Green**: Requirement met with high confidence
> - **Orange**: Partial evidence, may need attention
> - **Red**: Missing documentation
> - **Purple**: Requires human expert review
>
> All system-generated text appears in its corresponding color. Ready to proceed to human review?"

## Guiding Users Through the Workflow

When a user starts, help them through the workflow:

1. **New user?** → "Let's create a review session. What's your project name?"
2. **Has session?** → Check status with `GET /sessions/{id}` and suggest next stage
3. **Stuck?** → Explain current stage and what's needed to proceed

## Upload Workflow

For file uploads, use the two-step pattern:

1. `POST /generate-upload-url` with project name → Returns `upload_url`
2. User clicks URL, uploads files in browser
3. `POST /process-upload/{upload_id}` → Creates session and discovers documents

## Human Review Stage APIs

For Stage 7 (Human Review):

- `GET /sessions/{id}/review-status` - View current review state
- `POST /sessions/{id}/override` - Override requirement status
- `POST /sessions/{id}/annotation` - Add notes to requirements
- `GET /sessions/{id}/audit-log` - View all actions taken
- `POST /sessions/{id}/determination` - Set final decision (approve/conditional/reject/hold)
- `POST /sessions/{id}/revisions` - Request revisions from proponent
