## Epic: Registry Agent – MVP Review Workflow

**Epic Goal**

Deliver a usable **Registry Agent** that takes a project from “folder/links + chosen checklist” → to a **draft Registry Review Report** that a human reviewer can trust and edit, using the Regen Agent Interface as the surface.

Success metrics (for your planning docs):

- At least 1–2 real projects run fully through the workflow.
- Registry reviewers report **time saved** and **clearer structure** vs. manual process.

---

## Story 1 – Project Initialization (Create Review Session)

**Title:** Create a Registry review session from uploaded files or linked folder

**User Story:**

As a **Registry reviewer**, I want to create a review session by uploading files or linking to a document folder and selecting the appropriate checklist template, so that the Registry Agent can organize and assess the project against the correct requirements.

**Acceptance Criteria:**

- A reviewer can:
    - Select or create a **Registry project** in the Regen Agent Interface.
    - Choose between:
        - **Mirror mode (MVP default):** upload files or link a Google Drive folder.
        - **Reference mode (optional spike):** link a SharePoint folder/URL (if enabled in config).
    - Select a **checklist template** (e.g., specific Credit Class + Methodology) from a list of available templates.
- On session creation:
    - The system stores:
        - Project ID / Review session ID.
        - List of provided files/links.
        - Selected checklist template ID.
        - Chosen mode (Mirror vs Reference).
    - A `Resource Descriptor` entry is created for each file with:
        - `iri`, `title`, `source`, `visibility`, `checksum`, `indexedAt`.
- If required information is missing (no files/links OR no checklist template selected), the UI prevents session creation and shows a clear validation message.
- The newly created session appears in a **“Recent Reviews”** list in the UI with status `Initialized`.

---

## Story 2 – Document Discovery & Normalization

**Title:** Automatically discover and normalize project documents

**User Story:**

As a **Registry reviewer**, I want the agent to scan the configured folder/links, normalize file names, and group files by type so that I can quickly understand which documents are in scope and which ones are critical.

**Acceptance Criteria:**

- When a review session is opened:
    - The agent scans all files in the configured folder/links (Mirror or Reference mode, depending on the session).
- The system:
    - Normalizes file names (e.g., trims noise, keeps clear titles).
    - Classifies/group files by type (e.g., technical report, management plan, shapefile, spreadsheet, “other”).
- The UI shows:
    - A list or table of discovered documents with:
        - Normalized name
        - Original source name
        - File type
        - Source (Drive / SharePoint / upload)
        - Status (In scope / Ignored / Pinned)
- Reviewer can:
    - Mark any doc as **Ignored** (excluded from context).
    - Mark any doc as **Pinned** (critical context for the agent).
- Only **non-ignored** documents are exposed to the agent for mapping and evidence extraction.
- Changes (Pinned/Ignored) are saved and persisted between sessions.

---

## Story 3 – Checklist Loading & Requirement Mapping

**Title:** Map project documents to checklist requirements

**User Story:**

As a **Registry reviewer**, I want the agent to load the selected checklist template and suggest matches between documents and specific requirements, so I can quickly see where each requirement is addressed and adjust those mappings.

**Acceptance Criteria:**

- For a given session:
    - The system loads the **checklist template** associated with the session (machine-readable list of requirements derived from Program Guide & Methodology).
- The agent:
    - Analyzes **Pinned + non-ignored documents**.
    - Suggests one or more **document→requirement** mappings for each checklist item.
- The UI presents:
    - A table or matrix view:
        - Rows: checklist requirements.
        - Columns: mapped documents (with file names).
        - Status indicator (e.g., `Suggested`, `Confirmed`, `Unmapped`).
- Reviewer can:
    - Confirm suggested mappings.
    - Remove incorrect mappings.
    - Manually add new mappings (select requirement + file).
- After reviewer edits:
    - Each checklist item has a stored list of associated document IDs (can be empty).
    - Mapping changes persist and are visible in subsequent sessions.
- Edge cases:
    - If no plausible doc is found for a requirement, requirement is marked `Unmapped` with a visible warning icon.

---

## Story 4 – Completeness Check & Gaps Identification

**Title:** Automatically check completeness of checklist coverage

**User Story:**

As a **Registry reviewer**, I want the agent to highlight which requirements appear sufficiently documented and which are missing or ambiguous, so I can focus my attention on gaps and risks.

**Acceptance Criteria:**

- For each checklist requirement:
    - The system computes a **coverage status** based on:
        - Whether it has one or more mapped documents.
        - Whether mapped docs contain minimal expected content (light content check, not full semantic validation).
- Requirements are categorized into at least three statuses:
    - `Covered` – mapped documents and minimal evidence found.
    - `Partially Covered / Ambiguous` – mapped documents but content may be incomplete or unclear.
    - `Missing` – no mapped documents or clearly insufficient evidence.
- The UI shows:
    - Overall summary (e.g., “34/50 requirements covered; 10 partial; 6 missing”).
    - Filters to view requirements by status.
- For each requirement, the UI displays:
    - Status.
    - Mapped documents list.
    - A short agent-generated note if coverage is partial/ambiguous (e.g., “Method mentions monitoring but no baseline data provided.”).
- If the agent cannot assess completeness (e.g., unsupported file format), the requirement is flagged appropriately (e.g. `Needs Manual Review`) with a tooltip.

---

## Story 5 – Evidence Extraction (Lightweight Snippets)

**Title:** Extract key evidence snippets for each requirement

**User Story:**

As a **Registry reviewer**, I want the agent to extract short text snippets or references from mapped documents for each requirement, so that I can quickly verify evidence without reading entire documents.

**Acceptance Criteria:**

- For requirements with mapped documents:
    - The agent attempts to extract 0–3 **evidence snippets** per requirement:
        - Each snippet includes: a short quote or summary + reference to document + page/section if available.
- Snippets are:
    - Stored in a structured format (e.g. JSON: `{ requirementId, docId, location, snippetText }`).
    - Limited to a maximum length (e.g. ~2–3 sentences) to avoid dumping whole documents.
- The UI shows for each requirement:
    - A collapsible “Evidence” panel with the list of snippets.
- Reviewer can:
    - Delete irrelevant snippets.
    - Add manual notes alongside snippets.
- If no good snippets are found:
    - The requirement shows `No automatic evidence found` with an option to request **re-run evidence search** for selected docs.

---

## Story 6 – Registry Review Report Generation

**Title:** Generate a structured Registry Review Report

**User Story:**

As a **Registry reviewer**, I want the agent to generate a structured Registry Review Report summarizing coverage, flagged issues, and evidence links, so that I have a strong starting point for my final review document.

**Acceptance Criteria:**

- From the review session, the reviewer can click **“Generate Report”**.
- The system generates a **structured report** in at least two representations:
    - **JSON** representation suitable for internal systems.
    - **Human-readable document** (e.g., HTML/PDF/Markdown) for sharing.
- The report includes:
    - Project metadata (name, date, reviewer, mode).
    - Summary stats of checklist coverage.
    - Per-requirement entries:
        - Requirement text.
        - Status (`Covered`, `Partial`, `Missing`, `Needs Manual Review`).
        - Mapped documents (names + IRIs/URLs).
        - Evidence snippets (if any).
        - Reviewer notes (if any).
    - Provenance details:
        - For each document, show `source` (Drive/SharePoint/upload), `resolver` (URL), and `checksum`.
- Reports are:
    - Saved and versioned; each generation gets a timestamp and version ID.
    - Accessible from a “Reports” section within the session.
- Reviewer can download the human-readable version as a file (e.g., PDF or Markdown export).

---

## Story 7 – Human Review, Revisions & Re-run

**Title:** Edit draft report and handle project revisions

**User Story:**

As a **Registry reviewer**, I want to edit the draft report, request changes from proponents, and re-run parts of the workflow when new documents arrive, so that the review stays in sync with evolving project materials.

**Acceptance Criteria:**

- Reviewer can:
    - Edit narrative sections and notes directly in the report UI or associated text fields.
    - Mark requirements as:
        - `Pending Proponent Revision`
        - `Resolved after Revision`
- When new documents are uploaded/linked:
    - The system allows a **re-scan** of added documents (without losing prior mappings, unless explicitly reset).
    - Agent can re-run:
        - Document discovery for new items.
        - Requirement mapping for unmapped / partial requirements.
        - Evidence extraction for affected requirements.
- A **change log** is maintained per session:
    - Document additions/removals.
    - Re-runs of agent steps (discovery/mapping/completeness/evidence).
    - Report regeneration events.
- Reports show a **version history** indicating:
    - Who changed what (for notes/flags).
    - When the latest agent re-run occurred.

---

## Story 8 – Minimal Commons & Permissioning Integration (Pre-KOI)

**Title:** Store Registry review artifacts in Commons with basic permissioning

**User Story:**

As a **platform operator**, I want all documents, mappings, and generated reports to be represented as resources in the Commons with basic visibility controls, so we can safely operate today and have a clear migration path to full KOI permissioning and ledger anchoring later.

**Acceptance Criteria:**

- For every ingested file (Mirror/Reference modes), a **Resource Descriptor** exists in KOI Postgres with:
    - `iri`, `title`, `source`, `visibility`, `tags`, `contributors`, `resolvers`, `checksum`, `indexedAt`.
- For internal registry materials:
    - `visibility = "internal"` by default.
    - Access to these resources via any API used by the agent is restricted to authenticated RND accounts.
- For partner or public materials (as defined by config or manual override):
    - `visibility` can be set to `"partner"` or `"public"` and respected by the access layer.
- All **agent queries and report generations** against Commons-backed resources:
    - Are logged in an audit log table (resource IRI, user, timestamp, action type).
- No on-ledger anchoring is required in this story; **checksum + metadata + logs** are sufficient for MVP.
