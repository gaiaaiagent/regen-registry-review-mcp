# Core Agent Checklist

*Registry Review Agent — Regen Internal Use*

---

## 1. Scope & Assumptions

- Version 1 used for registration
- Version 2 used for issuance review (monitoring reports, sampling, etc)
- Carboneg is a **data provider**, not a tool user
- Requirements are fixed and known (no protocol interpretation)
- Review goal = **pass / fail validation + evidence citation**

---

## 2. Review Workflow

### 2.1 Input

- [ ]  Issues with mapping remain - cross validation before. check on it.
    
    ![Screenshot 2026-02-03 at 1.53.02 PM.png](attachment:9c9dfe79-cd0d-428e-a5bc-be579e79131f:Screenshot_2026-02-03_at_1.53.02_PM.png)
    
- [ ]  Injest pdfs and spreadsheets —
- [ ]  Agent supports **100+ farms-** 100+ projects at different stages of review or 1 meta project? → treat as indivudal projects
    - [ ]  Ingestion bot you can add to any folder in drive→ input docs
    - [ ]  yes to airtable, explore

### 2.2 PDD Review

- [ ]  Per-farm checklist rows- Becca needs to think through and update checklist → **make helpful knowldge to explain structure and differentiate farms vs meta project. have shortlist for farms and shortlist for metaproject.**
- [ ]  Bypassing the upload and mapping stages
- [x]  Per-farm land tenure records can be validated

### 2.3 Output

- [ ]  Duplicate `"value"` field removed- shawn checking with deployment
- [x]  Citations include document name + section reference
- [ ]  Supplementary evidence- how well can it pull that?
- [x]  Human review is explicitly flagged only where needed

---

## 3. Directional Items: Data Pipeline Alignment

- [ ]  Registry agent reads from Airtable (or structured export)
- [ ]  Agent reads from canonical data sources
- [ ]  Outputs align with ledger-anchored records
- [ ]  No parallel document silos introduced
- [ ]  Ability to **bypass document discovery, bypass requirement mapping and** start at **evidence extraction + validation**
- [ ]  Carboneg registry requirements are pre-loaded

**Sam →**

> The agent should not “figure out what to check” — it should confirm whether required evidence exists and passes.
> 

---

---

# Demo-Ready Web App Checklist

*Business Outreach & Partner Demos — Next Week*

---

## 1. First Impression

- [x]  Web app does **not** feel like ChatGPT
- [x]  Clear visual structure:
    - sessions
    - progress states
    - completion indicators
- [x]  Professional, registry-grade UI

---

## 2. Demo Flow

- [x]  Start a review without explaining setup complexity
- [x]  Show:
    - requirements coverage
    - evidence citations
    - completion status
- [x]  Viewer understands value in < 3 minutes

**Target reaction:**

> “Oh — this replaces a ton of manual checking.”
> 

---

## 3. Report Quality

- [ ]  Report output does not look like chatgpt, more containerized
- [ ]  Reports downloadable as **PDF- not working**
- [ ]  Tables render cleanly outside the app
- [x]  Markdown is optional, not prima

---

## 4. Credible Story (Business Framing)

- [ ]  Demo clearly framed as:
    - internal tooling
    - adaptable to partner workflows
- [ ]  Explicit distinction from generic AI chat tools
- [ ]  Privacy + data isolation can be stated simply

**One-liner that should land:**

> “This is a registry agent, not an AI assistant.”
> 

---

### Demo-Ready Definition

> The tool is stable, legible, and impressive enough that partners focus on *usefulness*, not rough edges
>
