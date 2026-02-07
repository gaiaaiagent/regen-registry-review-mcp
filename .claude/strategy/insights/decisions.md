# Decision Log

This log captures significant architectural, product, and process decisions with their context and rationale. Entries are prepended (newest first).

---

## 2026-02-07: Strategy Directory Created

**Context:** The project had accumulated substantial planning context across transcripts, Notion docs, Slack history, and developer memory, but lacked a single coherent reference point for project state, priorities, and procedures.

**Decision:** Create `.claude/strategy/` as a git-tracked living command center with status tracking, roadmaps, indexes, runbooks, and decision logs. Maintain through regular commits as development progresses.

**Rationale:** Git is the team's primary coordination tool. Having strategy documents live alongside the code they govern means they travel with the code, are versioned, and can be reviewed in PRs. This replaces ad-hoc Slack threads and ephemeral Notion pages as the engineering source of truth.

---

## 2026-02-03: Web App for Client-Facing Work, Not Directory-Based Agents

**Context:** Two paradigms were proposed for BizDev demos. Shawn described a lightweight approach: a GitHub repo with CLAUDE.md + documents = instant specialized agent. Darren advocated for wrapping everything in a proper web app frontend.

**Decision:** Web app approach for all client-facing work. Lightweight directory approach retained for internal rapid prototyping.

**Rationale:** "We don't need to show under the hood." Partners should see a polished product, not an engineering workflow. The web app provides the "oh wow" moment that a terminal session cannot. The lightweight approach remains valuable for developer productivity and internal experimentation.

Source: 2026-02-03-agent-readiness-strategy.md

---

## 2026-02-03: Each Carbon Egg Farm = Independent Project

**Context:** Carbon Egg has 100+ individual farms, each with metadata and on-chain anchoring, plus a meta-project. The question: one massive review or many small ones?

**Decision:** Treat each farm as an independent project with its own review session. Create an additional project for the meta-project itself. Provide auxiliary knowledge explaining the multi-project structure.

**Rationale:** Independent projects allow clean per-farm validation ("yes, this one is clear") rather than one unwieldy review. Aligns with on-chain representation where each farm is an individual entity. The meta-project handles cross-cutting concerns. This also becomes a template for future multi-farm engagements.

Source: 2026-02-03-agent-readiness-strategy.md (Darren's recommendation, Becca's question)

---

## 2026-02-03: Registration Agent First, Issuance Agent Second

**Context:** Becca scoped both registration and issuance review agents in the updated MVP spec.

**Decision:** Complete registration review agent for Carbon Egg before starting issuance. The two are architecturally similar but issuance has significantly expanded evidence validation requirements (monitoring, sampling, lab analysis, temporal alignment).

**Rationale:** Carbon Egg is registering now. Ship what's needed, learn from it, then extend. Both agents share the same backend architecture, so registration work directly benefits the issuance implementation.

Source: updated-registry-spec.md, 2026-02-03-agent-readiness-strategy.md

---

## 2026-01-26: Becca's Six Feedback Items (Task-12)

**Context:** Becca provided detailed feedback on the checklist output via Slack on Jan 14, with screenshots and specific improvement requests.

**Decision:** Implement all six items: section numbers in citations, value vs evidence distinction, supplementary evidence support, evidence in comments column, sentence-boundary truncation, project ID in document references.

**Rationale:** These aren't cosmetic. They represent domain expertise about what a registry review output needs to look like for professional use. Each item makes the output more useful for the human reviewer. Seven new tests added to verify the implementations.

Source: Commit 72128b3, Becca's Slack message (Jan 14)

---

## 2025-12-04: Fast PyMuPDF Extraction by Default, Marker as Opt-In

**Context:** The system supported two PDF extraction paths: PyMuPDF (fast, ~75-90% quality) and Marker (high-quality but slow, requires 8GB+ RAM and ~3min per PDF).

**Decision:** Use PyMuPDF as the default extraction method. Marker available as opt-in for documents where fast extraction produces insufficient quality.

**Rationale:** Most registry documents are text-heavy PDFs where PyMuPDF performs well. The speed difference is dramatic — fast extraction enables interactive use while Marker requires background processing. Users who need higher quality can enable it, but the common case should be fast.

Source: Commits 26a49e5, bbdd2c4

---

## 2025-12-04: File-Based Storage, No External Database

**Context:** The system needed session persistence but the question was whether to introduce a database.

**Decision:** Use file-system storage with XDG Base Directory Specification conventions. Atomic JSON read/write with file-level locking.

**Rationale:** The system manages discrete review sessions, not relational data. File-based storage is transparent (you can inspect sessions with a text editor), deployable anywhere without database setup, and naturally isolates sessions. The StateManager provides atomic operations and locking sufficient for the current concurrency model.

Source: `src/registry_review_mcp/utils/state.py`
