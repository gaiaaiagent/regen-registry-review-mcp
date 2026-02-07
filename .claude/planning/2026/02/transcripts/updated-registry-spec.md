# Registry Agent Review — Updated MVP Spec

**Web App Version (February 2026)**

## Overview

The Registry Agent is delivered as a **purpose-built registry review tool**, not a general AI assistant.

In the MVP, it is split into **two distinct agents** with clear scope boundaries:

1. **Registration Review Agent** — supports project registration review
2. **Issuance Review Agent** — supports monitoring + credit issuance review

Both are accessed through a **professional, registry-grade web app** that produces structured, auditable outputs suitable for human review and partner demos.

---

## 1. Registration Review Agent (MVP)

### Purpose

Automate the **first-pass registry review** of project registration submissions by validating completeness and evidence presence against ***pre-defined, fixed requirements*.**

The agent **does not interpret protocols** — it confirms whether required evidence exists, where it is located, and whether it passes basic validation checks 

---

### Inputs (MVP)

**Required**

- Project Design Documents (PDDs)
- Land tenure & ownership documents (titles, deeds, contracts)
- Registry-defined **registration checklist** (pre-loaded, fixed)

**Ingestion**

- PDFs and spreadsheets ingested via an **ingestion bot** added to a Drive folder OR Upload link
- Each project treated as an **individual project** (even when part of a larger program / meta-project)

---

### Core Capabilities — What It Can Do Today

### 1. Completeness Checking

- Confirms all **required documents are present**
- Flags missing or incomplete submission elements
- Distinguishes **per-farm vs. meta-project requirements** (based on checklist structure)

### 2. Evidence Validation

- Cross-checks:
    - stated land ownership vs. tenure documents
    - project claims vs. cited evidence
- Validates that evidence corresponds to the **correct project unit / farm**
- Supports per-farm land tenure validation

### 3. Structured Review Output

For each requirement:

- **Status**: Pass / Fail
- **Evidence citation**: document name + section reference
- **Notes**: clarification required, inconsistency flagged
- **Explicit human-review flag** only where needed

### 4. Web App Review Experience

- Clear progress states and completion indicators
- Requirements coverage visible at a glance
- Output presented as **registry-style tables**, not chat responses
- Downloadable report structure (PDF export = post-MVP)

---

### Explicit MVP Constraints (Important for Demos)

The Registration Review Agent:

- ❌ does not interpret ambiguous protocol language
- ❌ does not resolve disputes or make judgment calls
- ❌ does not generate new evidence
- ❌ does not replace human approval

This constraint is a **feature**, not a limitation:

> *“This is a registry agent, not an AI assistant.”*
> 

---

## 2. Issuance Review Agent (Post-Registration MVP WIP)

### Purpose

Support **credit issuance review** by validating monitoring reports, sampling evidence, and issuance-specific technical checks.

This agent builds on the same architecture as Registration, with **expanded evidence validation**.

---

### Inputs

- Monitoring reports
- Sampling plans & raw sampling data
- Lab analysis reports (SOC %, accreditation)
- Issuance-specific registry checklist (pre-loaded)

---

### Core Capabilities (Planned MVP / v1.5)

### 1. Monitoring Completeness

- Confirms required monitoring period documents are present
- Verifies monitoring and crediting periods are defined correctly

### 2. Technical Validation

- Sampling method checks:
    - stratification method
    - sample depth
    - number of samples
    - GNSS accuracy
- Lab verification:
    - SOC % included
    - accreditation referenced
    - data fields present
- Temporal alignment:
    - sampling dates vs imagery dates (±4 months)
- Flags  thresholds (ex: MAPE >20%)

### 3. Issuance-Specific Outputs

- Buffer pool contribution checks
- Leakage and additionality evidence presence
- Structured issuance review report aligned with ledger expectations

---

### What Is *Not* in MVP (Explicitly Deferred)

- ❌Automated protocol interpretation
- ❌Credit quantity calculations
- ❌Final issuance approval
- ❌Verifier substitution

---

# Web App MVP — What We Are Offering *Now*

### What a Partner Sees in <3 Minutes

- A clean, professional registry-grade UI
- Upload or point to documents
- Click “Start Review”
- Dashboard of multi project progress
- Watch requirements auto-populate
- See:
    - coverage
    - pass/fail flags
    - evidence citations
- Immediate “oh wow” moment:
    
    > *“This replaces a ton of manual checking.”*
    > 

---

### What Makes This Credible (vs ChatGPT)

- Fixed requirements (no hallucination risk)
- Deterministic outputs
- Explicit human-in-the-loop boundaries
- Data isolation per project
- Registry-specific framing and language

---

## What Comes Next (Clearly Sequenced)

### Short-Term (Post-Demo)

- PDF report export
- Cleaner table rendering outside the app
- Airtable / structured export alignment
- Better meta-project vs farm abstractions

### Medium-Term

- Ledger-aligned outputs
- Issuance agent productionization
- Program-specific checklists
- Partner-specific workflow adaptations

### Long-Term

- Multi-registry support
- Verifier-specific views
- Registry-as-a-service offerings

---

## Final Framing (Recommended)

For CarbonEG and demos:

> **“This is not an AI assistant.This is a registry agent that replaces first-pass compliance checking, with auditable outputs and human approval where it matters.”**
>
