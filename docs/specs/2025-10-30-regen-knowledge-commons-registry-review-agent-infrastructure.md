# **Regen Knowledge Commons & Registry Agent Infrastructure: Proposed Product Roadmap**

**Authors:** Sam Bennetts
**Date:** October 2025
**References:** 

- [[WIP] Permissions and Access Specification for Regen Knowledge Commons](https://www.notion.so/WIP-Permissions-and-Access-Specification-for-Regen-Knowledge-Commons-25425b77eda180fc89aef93d02be0eb3?pvs=21)
- [High-Level Specs for Registry AI Agents](https://www.notion.so/High-Level-Specs-for-Registry-AI-Agents-26925b77eda180b8b205f29c178d0431?pvs=21)
- [GAIA Canva](https://www.canva.com/design/DAG2DsKBx2U/9CNKnU0T7aFjVVea-MZzzA/edit)
- [Claims Engine Technical Architecture](https://www.notion.so/2a225b77eda180cf9948c48a0e2f69e2?pvs=21)

---

## 1. Introduction

### Purpose

This document defines a proposed next step to develop our the product and feature specifications for the *Regen Knowledge Commons,* [outlined in the [WIP] Permissions and Access Specification for Regen Knowledge Commons](https://www.notion.so/WIP-Permissions-and-Access-Specification-for-Regen-Knowledge-Commons-25425b77eda180fc89aef93d02be0eb3?pvs=21). 

In the long run, the commons will act as a permissioned, semantically indexed knowledge base built on Regen’s core technical stack (Ledger + KOI + MCP) to provide a substrate through which internal team members and the broader ecosystem can: 

- **Upload and tag information** (documents, datasets, code, discussions) into KOI with explicit permission controls.
- **Query and interact** with the Commons via natural-language or structured chat interfaces.
- **Construct subgraphs** — curated, domain-specific slices of the Commons — that isolate relevant knowledge for research, program operations, or software development.
- **Deploy agents** trained or instructed on these subgraphs to perform specific workflows such as registry review, software engineering assistance, data validation, or community governance support.

Ultimately, the Knowledge Commons is designed to evolve from an internal RND/GAIA asset into a **shared digital public good** stewarded by the Regen Commons DUNA, enabling permissioned access, interoperability, and open participation across the broader ecosystem.

### Scope of this RFC

This RFC specifies the architecture and feature roadmap for the initial build-out phase (Q4 2025 – Q2 2026). It covers:

- System architecture and inter-layer relationships
- Four foundational feature areas:
    1. Architecture Proposal for KOI Data Permissioning System (Phase 1)
    2. Full-Stack MCP for Regen Software Development
    3. Regen Agent Improvements (ElizaOS + MCP Integration)
    4. Registry Agent Automation Workflow
- Deliverables and acceptance criteria for GAIA’s remaining contract term.

## **2. System Overview**

The Regen Knowledge Commons extends the Regen software ecosystem to include a structured, AI-readable layer of indexed, permissioned data that bridges unstructured knowledge (documents, chats, repositories) with on-chain provenance and intelligent agents.

The architecture mirrors the [layering pattern proposed for the the *Claims Engine*](https://www.notion.so/2a225b77eda180cf9948c48a0e2f69e2?pvs=21) while introducing the **MCP Agent Layer**, which enables interactive and autonomous reasoning over Commons data.

| **Layer** | **Primary Function** | **Example Components / Technologies** |
| --- | --- | --- |
| **Ledger Layer** | Provenance and anchoring of hashes, attestations, and access logs. | Regen Ledger (`x/data`, CosmWasm contracts) |
| **Indexer Layer** | Extracts, normalizes, and enriches data from connected sources. | KOI + MCP Indexers, IRI Indexer, DAODAO Indexer |
| **Data Layer (non-graph)** | Persistent storage for raw and structured non-graph data. | PostgreSQL, IPFS, AWS S3 |
| **Datastore (graph)** | Semantic and embedding-based knowledge graph that models relationships and subgraphs. | Apache Jena / Fuseki |
| **Agent Layer (NEW)** | Runtime environment for AI agents deployed on the Commons or its subgraphs. | MCP Agents (GAIA framework) |
| **Application Layer** | Human-facing interfaces and developer APIs for interaction and control. | Web App, CLI, GraphQL/REST APIs |

The Agent Layer sits between the *Datastore* and *Application Layer*, consuming data from both the non-graph and graph stores and exposing reasoning or task-automation capabilities through user-facing applications.

This layered architecture provides:

- **Data provenance** (Ledger Layer)
- **Comprehensive indexing + embedding** (Indexer Layer)
- **Secure storage + semantic structure** (Data and Graph Layers)
- **Agentic execution + automation** (Agent Layer)
- **Accessible interfaces + tooling** (Application Layer)

It ensures that every dataset, document, or codebase within the Regen ecosystem can be discoverable, verifiable, and actionable—forming the substrate for intelligent agents that augment registry operations, research, and development.

The overall design mirrors the *Claims Engine* architecture (minus its EAS layer), and will converge toward it in later phases for unified provenance and data interoperability.

![image.png](attachment:44c773f7-a3cd-4d96-8d55-fb96e79f79a8:image.png)

## 3. KOI Data Permissioning System — Technical Architecture Proposal

### **Purpose**

This line of work defines a proposed architecture for the **KOI Data Permissioning System**, which will serve as the foundation of access control and provenance management for the Regen Knowledge Commons.

The purpose of this proposal is not to deliver a production implementation, but to:

1. Describe the **technical logic** and architectural components of a permissioned knowledge system built on KOI.
2. Propose an **incremental development pathway** from a simple API-based permission layer to a fully on-ledger, RDF-anchored system.
3. Provide a design framework for GAIA and Regen teams to evaluate implementation feasibility and future integration points with Regen Ledger and the Claims Engine.

### **Design Principles**

1. **Open Contribution, Permissioned Access:** Anyone should be able to contribute or upload information into the Commons, but resource visibility and accessibility are determined by data source permissions (e.g., Notion vs Google Drive) and explicit sharing tags.
2. **Source-Aware Access Control:** Access policies should reflect the source system’s rules—internal files remain limited to Regen team members; public documents, GitHub repos, and open datasets remain accessible to all.
3. **Progressive Provenance:** Ledger-based anchoring, RDF tagging, and on-chain indexing will be introduced gradually, starting from simple off-chain metadata logs.
4. **Interoperability & Extensibility:** The permissioning model must work across file types, data sources, and future Commons subgraphs, without relying on centralized access management.

### **System Overview**

At its core, the permissioning system extends KOI’s current indexing and metadata management functionality to include *access constraints* and *visibility metadata*.

Every resource (document, dataset, code repo, etc.) indexed in the Commons is described by a `Resource Descriptor` object stored in KOI.

### **Resource Descriptor Example**

```json
{
  "iri": "regen:koi:resource:abcd1234",
  "title": "Regen Registry Program Guide v1.1",
  "source": "google-drive",
  "visibility": "internal",
  "tags": ["registry", "program-guide"],
  "contributors": ["sam.bennetts@regen.network"],
  "resolvers": ["https://drive.google.com/file/d/..."],
  "checksum": "sha256:abcd1234",
  "indexedAt": "2025-11-03T12:00:00Z"
}

```

This metadata record (stored in KOI’s Postgres layer and optionally surfaced in Jena) governs access to the underlying file and provides the foundational structure for future RDF expansion.

### **Phase 1 — Foundational KOI-Level Permissions (Current Scope)**

**Objective:** Design and prototype an access-control schema and API within KOI, without on-chain anchoring.

**Core Features:**

- Define metadata schema for `visibility` and `source` fields.
- Enforce access rules at query time via the KOI API.
- Implement source-based access logic:
    - Public sources → visible to all.
    - Internal sources (Drive, Notion) → accessible only by authorized Regen accounts.
- Maintain audit logs (in KOI database) for query and modification events.
- Deliver API endpoints:
    - `GET /resource/:iri` (permission-checked retrieval)
    - `POST /resource` (upload + tagging)

**Outcome:** Operational internal Commons with safe access separation across data sources.

---

### **Phase 2 — RDF Metadata and Partial Ledger Anchoring**

**Objective:** Extend the permissioning system with semantic descriptions and partial provenance anchoring via Regen Ledger’s `x/data` module.

**Core Features:**

- Extend `Resource Descriptor` with RDF-compatible metadata (e.g., creator, subject, license, provenance).
- Generate RDF graph fragments for each resource stored in Jena.
- Create content hash for each resource → anchor to Ledger using `MsgAnchor` in `x/data`.
- Introduce IRIs for dataset references.
- Implement “anchoring proofs” for Commons entries accessible via the API.

**Outcome:** Each Commons resource becomes verifiable via hash and queryable in RDF. Ledger provides cryptographic provenance, but full access logic remains off-chain.

---

### **Phase 3 — Fully Integrated On-Ledger Provenance and Policy Anchoring**

**Objective:** Transition to a fully decentralized model of access governance and provenance tracking.

**Core Features:**

- Every `PermissionChange` or `AccessEvent` generates a hash anchored to Ledger.
- Dataset-level permissions represented as RDF policies linked to resource IRIs.
- Integration with DAODAO for multi-party data stewardship (e.g., “shared subgraph” governance).
- Potential updates to the `x/data` module to support semantic metadata anchoring.
- Automated generation of on-chain provenance graphs mapping resource relationships.

**Outcome:** The Commons achieves verifiable, interoperable, and auditable access control, enabling both trustless data sharing and decentralized collaboration.

## **4. Full-Stack MCP for Regen Software Development**

### **Purpose**

This feature focuses on implementing a **full-stack MCP environment** that connects Regen’s engineering knowledge sources — GitHub repositories, documentation, internal databases, and the Knowledge Commons — to a unified AI development assistant and automation layer. Think claude code for regen. 

The objective is to make Regen’s codebase documentation *AI-addressable*: searchable, explainable, and operable through agents that can draft code, generate tests, automate documentation, or analyze dependencies.

This MCP integration will also establish the foundation for other “developer-facing” Commons applications, such as automated deployment, continuous documentation generation, or code review agents.

---

### **Goals**

- **Create an internal Claude MCP integration** that connects Regen’s core codebases, figma, databases, and documentation to Claude for context-aware assistance.
- **Accelerate development velocity** by enabling natural-language code exploration, dependency understanding, and inline assistance directly in developer tools.
- **Ensure security and data privacy** by enforcing KOI permission checks and restricting access to internal repositories.
- **Provide the foundation** for future AI-assisted development tooling (e.g., test generation, documentation automation, PR analysis).

### **Scope**

**In Scope (MVP):**

- Deploy an internal **MCP server** hosted in Regen infrastructure.
- Integrate with Regen’s GitHub org (read-only access).
- Index and sync repository metadata and code embeddings into KOI/Commons.
- Enable secure interaction with Claude via MCP configuration (Desktop or VS Code).
- Provide internal setup documentation and developer onboarding instructions.

**Out of Scope (Future Phases):**

- Write actions (e.g., PR creation, test commits).
- Multi-source connectors (Databases, Figma, Notion).
- Ecosystem or external user access.
- Ledger anchoring or provenance logging.

### **System Overview**

The **Regen Code Assistant** acts as a bridge between Regen’s development environment and Claude’s MCP client interface.

At a high level:

```
Claude (Desktop / VS Code)
        │
   MCP Protocol (local)
        │
 ┌──────────────────────┐
 │  Regen MCP Server    │  ← Hosted in Regen infra
 │  (GAIA-built runtime)│
 └──────────────────────┘
        │
        ├── KOI Permissioning API (access control)
        ├── GitHub API (read-only metadata + code)
        └── Commons (embeddings + repo metadata)
```

## **5. Regen Agent Interface and Curation Improvements**

### **Purpose**

Evolve the existing Regen Agent — already functional under GAIA’s ElizaOS + MCP stack — into a to allow people to **view & curate information** directly through chat, to build sub-agents trained on specific information for specific tasks. 

**Note:** this is just a proposal and in draft form as I’m not sure how much of it depends on (1). 

### **Goals**

- Enabling **manual context selection** — what data to pull from the Commons or subgraphs for a given prompt.
- Supporting **prompt engineering and saved templates** for repeatable agent behaviors.
- Creating a shared foundation that can later integrate KOI permissions and provenance once those systems are operational.

**This proposal does *not* assume** completion of the KOI permissioning backend; rather, it introduces *UI patterns and agent behaviors* that can anticipate and gracefully degrade when fine-grained access controls are unavailable.

## **6. Registry Agent Automation Workflow Proposal**

### Purpose

Stand up a usable **Registry Agent** that automates the highest-value, lowest-risk parts of registry review (document organization, checklist population, evidence location verification) **before** KOI permissioning (2.1) is implemented—while capturing the access patterns and metadata that will directly feed into 2.1’s design.

### What we’re optimizing for right now

- Deliver value to the Registry team quickly.
- Keep data handling safe and simple (least privilege, explicit consent).
- Structure storage & metadata so we can “flip” to KOI permissioning and ledger provenance later with minimal refactor.

### Scope & Dependencies (deliberately minimal)

**In scope (now):**

- Turn GAIA’s workflow (the Canva diagram) into a working agent + UI flow.
- Use **Regen Agent Interface** (3) as the default UI surface for:
    
    upload/link, context curation, progress view, report review/export.
    
- Implement a pragmatic **data access & storage plan** (below) that works today with Google Drive and (optionally) reads from SharePoint.

**Out of scope (now):**

- Full KOI permissioning & on-ledger anchoring (we’ll emit the metadata for it).
- Automated issuance/validation decisions.
- Cross-registry integrations.

**Depends on (soft):**

- 2.3 interface components (upload/link, context panel, curated context, report viewer).
- Commons “Registry Subgraph” (Program Guide + Credit Classes + Methodologies).

### Data Access & Storage Plan (pre-KOI)

We can explore two pragmatic modes so we can start immediately and evolve cleanly:

### Mode A — **Mirror** (MVP default)

- Partners still send files (or links).
- We store a **canonical working copy** in Regen’s Google Drive (or S3), generate embeddings, and index metadata to the Commons.

### Mode B — **Reference** (spike/optional)

- Read directly from **SharePoint** (Microsoft Graph) without mirroring, when consent + credentials are provided by the partner.
- We retain only transient processing copies for parsing/embeddings (auto-purged).
- Store **resolvers** (source URL + checksum) and minimal metadata in the Commons.
- This mode lets us test “read-through” permissions and informs KOI’s future **source-aware** policy design.

### Interface & Workflow (mapped to the Canva stages)

We’ll use the **Regen Agent Interface** as the default surface. If we hit UX limits, we add a thin “Review Dashboard” that reuses the same back-end.

1. **Project Initialization**
    - Choose project → link SharePoint folder *or* upload files → select checklist template (Credit Class + Methodology).
    - (Interface 2.3 provides upload/link + basic tagging.)
2. **Document Discovery**
    - Agent scans folder/links; normalizes file names; groups by type.
    - Reviewer can approve/ignore items and **pin** critical docs to context.
3. **Requirement Mapping**
    - Load the selected **checklist template** (machine-readable mapping of Program Guide & Methodology requirements).
    - Agent suggests doc→requirement matches; reviewer can confirm/edit.
4. **Completeness Check**
    - Auto-populate checklist status; flag missing/ambiguous items.
    - Evidence location verification (does a cited doc/section actually exist?).
5. **Evidence Extraction (lightweight)**
    - Optional: extract cited sections/snippets for the report (no heavy NLP).
6. **Report Generation**
    - Structured “Registry Review Report” (JSON + human PDF) with: checklist table, flags, citations (file/section), and provenance (source URL + checksum).
7. **Human Review & Revision Handling**
    - Reviewer edits notes, requests fixes; uploads revisions (new version recorded).
    - Finalize and export.

[Epic: Registry Agent – MVP Review Workflow](https://www.notion.so/Epic-Registry-Agent-MVP-Review-Workflow-2a725b77eda180dbbd58d390fc924158?pvs=21)
