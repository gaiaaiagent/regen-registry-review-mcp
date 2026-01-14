# Registry Review Web Application

## Overview

A purpose-built web application for carbon credit project verification, transforming the existing MCP-based workflow into a document-centric interface with an embedded AI assistant.

**Status:** MVP Development (Phases 1-9 Complete, Deployed to Production)
**Version:** 1.7
**Updated:** January 2026
**Live URL:** https://registry.regen.gaiaai.xyz/

---

## Vision

Registry reviewers currently spend 6-8 hours per project, manually cross-referencing 5-15 PDF documents against a methodology checklist. This application reduces that to 60-90 minutes by:

1. **Side-by-side view** - Documents visible alongside the checklist
2. **Drag-and-drop evidence linking** - No tedious popup menus
3. **AI assistant** - Chat panel that explains, extracts, and automates
4. **Batch processing** - Templates for 111+ farm clusters
5. **Collaboration** - Revision requests and proponent responses

---

## User Personas

### Primary: Registry Reviewer (Becca)

- Soil scientist with 3+ years in carbon credit verification
- Deep methodology expertise, not a software developer
- Needs: side-by-side documents, drag-drop linking, AI assistance, clear progress tracking

### Secondary: Project Proponent (Thomas)

- Farm owner or project developer
- Needs: view revision requests, upload responses, track status
- Must NOT see internal reviewer deliberations

### Tertiary: Registry Administrator

- Manages multiple reviewers
- Needs: dashboard of all reviews, bulk actions, metrics export, template management

---

## MVP Scope

### In Scope (MVP)

- Single-user review workflow
- PDF viewing with persistent highlighting
- Drag-and-drop evidence linking
- Evidence scratchpad
- AI chat panel (assistant + automation)
- Soft-gated stage navigation
- Cross-validation fact sheets
- Basic RBAC (reviewer/proponent/admin)
- Markdown/JSON report export
- Google Drive integration (import docs from shared folders)
- Notifications (Mailjet email + in-app)

### Out of Scope (Future)

- Multi-reviewer concurrent editing
- Real-time collaboration (WebSockets)
- Keyboard shortcuts (power-user feature)
- PDF annotation layers (separate from evidence)
- Offline support
- Mobile-optimized interface

---

## Key Decisions (Recommended)

1. **Vite + React 19 (not Next.js):** Aligns with GAIA repo stack; PDF libraries work better without SSR; simpler Nginx deployment.
2. **Templates are immutable:** updates create a new template version; child sessions opt-in to changes.
3. **Separate AI vs manual evidence storage:** AI extraction can regenerate without risking drag-drop highlights.
4. **Human-in-the-loop agent:** the agent proposes actions; UI requires explicit user confirmation for any state change.
5. **Explicit artifact "freshness":** mapping/evidence/validation/report show stale badges after upstream changes (new docs, mapping edits).
6. **Persistent backend storage required:** sessions/artifacts must live on durable storage (frontend can remain stateless).

---

## Success Metrics

| Metric | Current | Target | With Templates |
|--------|---------|--------|----------------|
| Review time (individual) | 6-8 hours | 60-90 min | 60-90 min |
| Review time (cluster farm) | 6-8 hours | 60-90 min | 20-30 min |
| 111 farms total time | 832 hours | 166 hours | ~57 hours |

---

## Documentation Structure

| Document | Description |
|----------|-------------|
| [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md) | **Start here** - Phased checklist for Claude Code sessions |
| [FRONTEND_PLANNING.md](./FRONTEND_PLANNING.md) | UI components, user journeys, technical stack details |
| [BACKEND_PLANNING.md](./BACKEND_PLANNING.md) | API architecture, AI agent, data models, MCP integration |
| [BACKTEST_DATASET.md](./BACKTEST_DATASET.md) | Official "Botany Farm" dataset for benchmarking extraction and workflow |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WEB APPLICATION                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      FRONTEND (Vite + React 19)                         ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  ││
│  │  │ PDF Viewer   │  │  Checklist   │  │  AI Chat     │                  ││
│  │  │ + Highlights │  │  + Evidence  │  │  Panel       │                  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         BACKEND (FastAPI)                               ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  ││
│  │  │ REST API     │  │  AI Agent    │  │  MCP Server  │                  ││
│  │  │ (existing)   │  │  (Claude)    │  │  (existing)  │                  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         STORAGE                                          ││
│  │  sessions/  templates/  uploads/  audit_logs/                            ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Existing Assets

The following are already built and will be reused:

| Asset | Location | Description |
|-------|----------|-------------|
| MCP Server | `src/registry_review_mcp/` | 8-stage workflow, evidence extraction |
| REST API | `chatgpt_rest_api.py` | 45+ endpoints, FastAPI |
| Data Models | `src/registry_review_mcp/models/` | Pydantic schemas |
| LLM Extractors | `src/registry_review_mcp/extractors/` | Evidence extraction |

---

## Authentication

**Decision:** Sign in with Google (reuse the same Regen Google Workspace identity model as `regen-koi-mcp`).

- **Reviewer/Admin:** allowlist (e.g., `@regen.network`) + role assignment
- **Proponent:** invited per project/session, strict least-privilege view

---

## Resolved Questions

1. **Proponent notifications:** Both email (Mailjet - already configured) and in-app notifications.
2. **Scanned PDFs:** Warn user when PDF has no searchable text (no OCR for MVP).
3. **Deployment storage:** Same production server as other Regen services (202.61.196.119).
4. **Document source:** Connect to existing Google Drive used by reviewers to minimize manual uploads.

---

## Current Implementation

The web application frontend is located in `/web_app/` with the following completed features:

### Completed Phases (1-9)

| Phase | Features |
|-------|----------|
| **1. Project Setup** | Vite + React 19 + TypeScript, Tailwind CSS 4, react-pdf-highlighter |
| **2. API Client & Auth** | openapi-fetch typed client, React Query, Auth context (stubbed Google OAuth) |
| **3. Dashboard** | Session list, create/delete sessions, methodology dropdown |
| **4. Workspace Layout** | Three-panel resizable layout (Documents / Checklist / Chat) |
| **5. Checklist Panel** | Category accordions, requirement cards, evidence preview, cross-panel navigation |
| **6. Evidence Linking** | @dnd-kit drag-and-drop, scratchpad, manual evidence with toast notifications |
| **7. AI Chat** | Agent endpoint, context-aware chat, action buttons with confirmation |
| **8. PDF Highlighting** | Click evidence → navigate to PDF page, bounding box highlighting |
| **9. Verification Workflow** | Per-snippet verify/reject buttons, verification progress tracking |

### Running the Application

```bash
# Frontend (port 5173)
cd web_app
npm install
npm run dev

# Backend (port 8003)
python chatgpt_rest_api.py
```

### Remaining Phases (10-12)

- **10. Proponent Flow** - Revision requests, responses, notifications
- **11. Report Generation** - Markdown/JSON export with full evidence citations
- **12. Polish & Production** - Error handling, performance optimization

---

## Production Deployment

The application is deployed at **https://registry.regen.gaiaai.xyz/**

### Architecture
- **Server:** `202.61.196.119`
- **Backend:** FastAPI service (`registry-review-api.service`) on port 8003
- **Frontend:** Static files in `/opt/projects/registry-review/web_app/dist/`
- **Proxy:** nginx (Docker) with SSL from Let's Encrypt wildcard cert

### Server Commands
```bash
# Check status
sudo systemctl status registry-review-api

# View logs
journalctl -u registry-review-api -f

# Restart
sudo systemctl restart registry-review-api
```

---

## Next Steps

1. **Phase 10: Proponent Flow** - Revision requests and responses
2. **Phase 11: Report Generation** - Export review reports with full citations
3. Implement real Google OAuth (requires backend endpoint)
4. Multi-reviewer support (future)

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | January 2026 | Initial monolithic planning document |
| v1.1 | January 2026 | UX feedback: drag-drop, scratchpad, soft gating, templates |
| v1.2 | January 2026 | Architectural feedback: MVP scope, RBAC, data handling |
| v1.3 | January 2026 | Restructured into separate frontend/backend docs; added AI agent |
| v1.4 | January 2026 | Switch to Vite + React 19 (align with GAIA); add Google Drive + Mailjet |
| v1.5 | January 2026 | Phases 1-7 implemented; added Current Implementation section |
| v1.6 | January 2026 | Added Phase 9B: Verification Workflow ("DocuSign with AI" pattern) |
| v1.7 | January 2026 | Phases 8-9 complete (PDF highlighting, verification); deployed to production |
