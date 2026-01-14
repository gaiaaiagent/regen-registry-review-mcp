# Registry Review Web Application

## Overview

A purpose-built web application for carbon credit project verification, transforming the existing MCP-based workflow into a document-centric interface with an embedded AI assistant.

**Status:** MVP Development (Phases 1-12 Complete, Deployed to Production)
**Version:** 1.9
**Updated:** January 2026
**Live URL:** https://regen.gaiaai.xyz/registry-review/

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

### Google OAuth Configuration

The application uses Google OAuth 2.0 for authentication. Configuration requires:

**Environment Variables:**
```bash
# Backend (.env)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
REGISTRY_REVIEW_FRONTEND_URL=https://regen.gaiaai.xyz/registry-review

# Frontend (.env.production)
VITE_API_URL=https://regen.gaiaai.xyz/api/registry
```

**Google Cloud Console Setup:**
1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID → **Web application** type
3. Add Authorized redirect URI: `https://regen.gaiaai.xyz/registry-review/auth/callback`
4. Copy Client ID and Client Secret to `.env`

**Auth Flow:**
```
1. User clicks "Sign in with Google"
2. Frontend calls GET /auth/google/login
3. Backend returns Google OAuth URL with redirect_uri
4. User authenticates with Google
5. Google redirects to /registry-review/auth/callback?code=xxx
6. Frontend calls GET /auth/google/callback?code=xxx
7. Backend exchanges code for tokens, creates session
8. Frontend stores JWT token, user is authenticated
```

**Domain Restriction:**
The backend enforces `@regen.network` email domain for reviewers. This is checked in `AuthContext.tsx`:
```typescript
if (!userData.email.endsWith('@regen.network')) {
  throw new Error('Only @regen.network emails are allowed')
}
```

### Development Test Login

For local development and testing without Google OAuth, use the test login endpoint:

| Username | Password | Role |
|----------|----------|------|
| `reviewer` | `test123` | Reviewer (full access) |
| `proponent` | `test123` | Proponent (limited view) |

The login page includes a "Test Login" button for reviewers. Proponents can enter credentials directly in the Proponent tab.

---

## Known Workflow Gaps

### Session Creation: Proponent vs Reviewer

**Current State:** Reviewers manually create sessions (entering project name, methodology) and upload documents.

**Actual Registry Workflow:** Per the [Regen Registry Handbook](https://handbook.regen.network/project-development/project-registration), the **proponent initiates** project submission:

| Role | Responsibility |
|------|----------------|
| **Proponent** | Submits project plan, selects methodology, uploads documents |
| **Reviewer** | Receives submission, validates against checklist, requests clarifications |

**Why the gap exists:** Phase 10 (Proponent Flow) was deferred. The reviewer is currently "wearing both hats."

**Future solutions:**
1. **Phase 10 implementation** - Proponent portal for submissions
2. **Regen Teams integration** (Q1 2026) - Native organization workspaces with submission workflow
3. **Google Drive auto-import** - Each project has a folder; documents auto-populate when session is created

### Document Auto-Import

**Current State:** Test PDFs appear for all sessions (demo data). Production would require manual upload.

**Ideal Flow:**
```
1. Proponent uploads docs to Google Drive folder (e.g., /Projects/Botany-Farm/)
2. Proponent submits project → folder URL included
3. System auto-imports all PDFs from folder
4. Reviewer sees documents pre-populated, ready for review
```

This would eliminate manual document handling entirely.

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
| **9.5 Google OAuth** | Real Google OAuth with @regen.network domain restriction |
| **11. Report Generation** | Report tab with generation, Markdown preview, and download (MD/Checklist/DOCX) |

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

The application is deployed at **https://regen.gaiaai.xyz/registry-review/**

### Architecture
- **Server:** `202.61.196.119`
- **Backend:** FastAPI service (`registry-review-api.service`) on port 8020
- **Frontend:** Static files in `/opt/projects/registry-review/web_app/dist/`
- **Proxy:** nginx (Docker) with SSL from Let's Encrypt wildcard cert
- **Base Path:** `/registry-review/` (configured in `vite.config.ts` and React Router)

### URL Structure
| URL | Purpose |
|-----|---------|
| `https://regen.gaiaai.xyz/registry-review/` | Frontend SPA |
| `https://regen.gaiaai.xyz/api/registry/` | Backend API |
| `https://registry.regen.gaiaai.xyz/` | Redirects to main URL |

### Server Commands
```bash
# Check status
sudo systemctl status registry-review-api

# View logs
journalctl -u registry-review-api -f

# Restart
sudo systemctl restart registry-review-api

# Restart nginx (for config changes)
docker restart nginx
```

### Deployment Steps
```bash
# 1. Build frontend with production env
cd web_app
npm run build

# 2. Deploy to server
rsync -avz dist/ darren@202.61.196.119:/opt/projects/registry-review/web_app/dist/

# 3. Deploy backend changes
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='.git' \
  /path/to/regen-registry-review-mcp/ \
  darren@202.61.196.119:/opt/projects/registry-review/

# 4. Restart backend
ssh darren@202.61.196.119 "sudo systemctl restart registry-review-api"
```

### Important Configuration Files
| File | Location | Purpose |
|------|----------|---------|
| `.env` | `/opt/projects/registry-review/.env` | Backend env vars (API keys, OAuth) |
| `nginx-ssl.conf` | `/opt/projects/GAIA/config/nginx-ssl.conf` | Nginx routing config |
| `registry-review-api.service` | `/etc/systemd/system/` | Systemd service definition |
| `.env.production` | `web_app/.env.production` | Frontend build-time env vars |

---

## Next Steps

1. **Phase 11: Report Generation** - Export review reports with full evidence citations
2. **Phase 10: Proponent Flow** - *Deferred* - May integrate with **Regen Teams** (launching Q1 2026) which provides organization workspaces, role-based permissions, and team collaboration natively within Regen Registry
3. Multi-reviewer support (future, potentially via Regen Teams)

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
| v1.8 | January 2026 | Google OAuth implemented with KOI MCP Web Client |
| v1.9 | January 2026 | Phase 11-12 complete; moved to `/registry-review/` base path; comprehensive auth docs |
