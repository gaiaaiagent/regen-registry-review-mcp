# Implementation Checklist

A phased checklist for building the Registry Review web application. Each phase is scoped for a single Claude Code session.

**Version:** 1.0
**Last Updated:** January 2026

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [README.md](./README.md) | Vision, MVP scope, key decisions |
| [FRONTEND_PLANNING.md](./FRONTEND_PLANNING.md) | UI components, user journeys, technical stack |
| [BACKEND_PLANNING.md](./BACKEND_PLANNING.md) | API endpoints, AI agent, data models |
| [BACKTEST_DATASET.md](./BACKTEST_DATASET.md) | Test data for validation |

**External References:**
| Resource | Purpose |
|----------|---------|
| GAIA/packages/client | Reference Vite + React 19 config |
| regen-koi-mcp | Reference Google OAuth implementation |
| Existing REST API (`chatgpt_rest_api.py`) | Backend endpoints to extend |

---

## Phase 1: Project Setup & PDF Proof-of-Concept

**Goal:** Prove react-pdf-highlighter works with real project PDFs before building anything else.

**Session Scope:** ~2 hours

### Checklist

- [ ] **1.1 Initialize project**
  - Create new repo or folder for frontend
  - Copy Vite config from GAIA/packages/client
  - Install React 19, React Router 7, TypeScript
  - Verify `npm run dev` works

- [ ] **1.2 Add styling**
  - Install Tailwind CSS 4
  - Install Radix UI primitives
  - Create basic layout component

- [ ] **1.3 Integrate PDF viewer**
  - Install react-pdf-highlighter
  - Create PDFViewer component
  - Load a local test PDF
  - Verify text selection works

- [ ] **1.4 Test highlight persistence**
  - Add highlight on text selection
  - Store highlights in local state
  - Reload page - verify highlights restore
  - Test with 5 different PDFs (see BACKTEST_DATASET.md)

### Exit Criteria

- [ ] PDFs render correctly (text selectable)
- [ ] Highlights persist across page reload
- [ ] No memory issues with 50+ page PDF
- [ ] Scanned PDFs show warning (no embedded text)

### References

- FRONTEND_PLANNING.md → Technical Stack section
- GAIA/packages/client → Vite config example

---

## Phase 2: API Client & Authentication

**Goal:** Connect to backend API with type-safe client; add Google sign-in.

**Session Scope:** ~2 hours

### Checklist

- [ ] **2.1 Generate API types**
  - Run openapi-typescript against backend OpenAPI spec
  - Create typed API client with openapi-fetch
  - Verify types match backend schemas

- [ ] **2.2 Add authentication**
  - Install authentication library (reference regen-koi-mcp)
  - Configure Google OAuth provider
  - Add sign-in button to layout
  - Store session token

- [ ] **2.3 Protect routes**
  - Create auth context/provider
  - Redirect unauthenticated users to sign-in
  - Pass auth token to API client

- [ ] **2.4 Test auth flow**
  - Sign in with @regen.network account
  - Verify API calls include auth header
  - Sign out and verify redirect

### Exit Criteria

- [ ] Can sign in with Google
- [ ] API client has full type coverage
- [ ] Unauthenticated users cannot access workspace
- [ ] Auth token refreshes correctly

### References

- BACKEND_PLANNING.md → Authentication section
- regen-koi-mcp → Google OAuth implementation

---

## Phase 3: Dashboard & Session Management

**Goal:** List sessions, create new sessions, navigate to workspace.

**Session Scope:** ~2 hours

### Checklist

- [ ] **3.1 Create dashboard page**
  - Route: `/`
  - Fetch sessions from API
  - Display session cards with status

- [ ] **3.2 Add session creation**
  - "New Review" button
  - Form: project name, methodology
  - Call POST /sessions API
  - Navigate to workspace on success

- [ ] **3.3 Add session card actions**
  - Click card → open workspace
  - Delete button (with confirmation)
  - Status badge (active/completed)

- [ ] **3.4 Add loading/error states**
  - Skeleton loaders while fetching
  - Error messages with retry
  - Empty state for no sessions

### Exit Criteria

- [ ] Sessions list loads from API
- [ ] Can create new session
- [ ] Can delete session
- [ ] Clicking session navigates to workspace

### References

- FRONTEND_PLANNING.md → User Journey 1, step 1
- BACKEND_PLANNING.md → Session data model

---

## Phase 4: Workspace Layout

**Goal:** Three-panel workspace with resizable panes.

**Session Scope:** ~2 hours

### Checklist

- [ ] **4.1 Create workspace route**
  - Route: `/workspace/:sessionId`
  - Fetch session data on mount
  - Pass session to child components

- [ ] **4.2 Build three-panel layout**
  - Left: Document panel (40%)
  - Center: Checklist panel (30%)
  - Right: AI Chat panel (30%)
  - Resizable dividers between panels

- [ ] **4.3 Add workspace header**
  - Project name and metadata
  - Stage progress indicator
  - Save button, Export button
  - Back to dashboard link

- [ ] **4.4 Integrate PDF viewer**
  - Document list sidebar
  - Click document → load in viewer
  - Page navigation controls

### Exit Criteria

- [ ] Three-panel layout renders
- [ ] Panels are resizable
- [ ] PDF loads in document panel
- [ ] Header shows session info

### References

- FRONTEND_PLANNING.md → Workspace Layout section
- FRONTEND_PLANNING.md → Component Architecture

---

## Phase 5: Checklist Panel

**Goal:** Display requirements grouped by category with status badges.

**Session Scope:** ~2 hours

### Checklist

- [ ] **5.1 Fetch requirements**
  - Call GET /sessions/{id}/workspace
  - Extract checklist from response
  - Group by category

- [ ] **5.2 Build category accordion**
  - Collapsible category headers
  - Show progress per category (3/5)
  - Expand/collapse all button

- [ ] **5.3 Build requirement cards**
  - Requirement ID and text
  - Status badge (covered/partial/missing)
  - Confidence score if available
  - Click to focus

- [ ] **5.4 Add evidence preview**
  - Show linked evidence count
  - Expandable evidence list
  - Click evidence → jump to PDF page

### Exit Criteria

- [ ] Requirements load from API
- [ ] Categories expand/collapse
- [ ] Status badges show correctly
- [ ] Clicking requirement focuses it

### References

- FRONTEND_PLANNING.md → Checklist panel in workspace layout
- BACKEND_PLANNING.md → Workspace snapshot endpoint

---

## Phase 6: Drag-and-Drop Evidence Linking

**Goal:** Drag text from PDF to requirement card to create evidence link.

**Session Scope:** ~3 hours

### Checklist

- [ ] **6.1 Set up drag-and-drop**
  - Install @dnd-kit/core
  - Create DragDropProvider wrapper
  - Make PDF selections draggable

- [ ] **6.2 Make requirement cards drop targets**
  - Highlight valid drop targets on drag start
  - Visual feedback on hover
  - Handle drop event

- [ ] **6.3 Implement optimistic linking**
  - Update UI immediately on drop
  - Call API in background
  - Rollback on failure with toast

- [ ] **6.4 Store highlight coordinates**
  - Capture bounding box from PDF selection
  - Save to manual_evidence.json via API
  - Restore highlights on page load

- [ ] **6.5 Add evidence scratchpad**
  - Clip text without assigning (Cmd+C)
  - Show unassigned clips
  - Drag from scratchpad to requirement

### Exit Criteria

- [ ] Can drag text from PDF to requirement
- [ ] Evidence appears instantly (optimistic)
- [ ] Highlights persist after reload
- [ ] Scratchpad holds unassigned clips

### References

- FRONTEND_PLANNING.md → Drag-and-Drop Evidence Linking
- BACKEND_PLANNING.md → Evidence Anchoring section
- BACKEND_PLANNING.md → Manual Evidence data model

---

## Phase 7: AI Chat Panel

**Goal:** Conversational AI assistant that can explain, search, and suggest.

**Session Scope:** ~3 hours

### Checklist

- [ ] **7.1 Build chat UI**
  - Message list (user + assistant)
  - Input field with send button
  - Auto-scroll to bottom

- [ ] **7.2 Connect to agent API**
  - POST /sessions/{id}/agent/chat
  - Send message + context (focused requirement, visible page)
  - Stream or poll for response

- [ ] **7.3 Render action buttons**
  - Parse actions from response
  - Render as buttons below message
  - Click button → execute action with confirmation

- [ ] **7.4 Handle navigation commands**
  - Agent says "navigate to page 12"
  - Update PDF viewer to page 12
  - Highlight relevant text if provided

- [ ] **7.5 Add context awareness**
  - Send focused requirement ID
  - Send visible document and page
  - Show "Agent is typing..." indicator

### Exit Criteria

- [ ] Can send messages to agent
- [ ] Agent responds with context-aware answers
- [ ] Action buttons trigger UI updates
- [ ] User must confirm before any write action

### References

- BACKEND_PLANNING.md → AI Agent section
- BACKEND_PLANNING.md → Agent Tools
- FRONTEND_PLANNING.md → AI Chat Panel section

---

## Phase 8: Cross-Validation & Fact Sheets

**Goal:** Tabular validation results with stale badges and one-click refresh.

**Session Scope:** ~2 hours

### Checklist

- [ ] **8.1 Create validation page/tab**
  - Route or tab within workspace
  - Fetch validation results from API

- [ ] **8.2 Build fact sheet tables**
  - Date Alignment table
  - Land Tenure table
  - Project ID occurrence table

- [ ] **8.3 Add stale badges**
  - Check artifact freshness from session
  - Show "Out of date" badge if stale
  - "Re-run validation" button

- [ ] **8.4 Link issues to requirements**
  - Click validation warning
  - Navigate to related requirement
  - Highlight in checklist

### Exit Criteria

- [ ] Fact sheets display validation results
- [ ] Stale badges appear when upstream changes
- [ ] One-click refresh works
- [ ] Clicking issue jumps to requirement

### References

- FRONTEND_PLANNING.md → Cross-Validation Fact Sheets
- BACKEND_PLANNING.md → Artifact freshness fields

---

## Phase 9: Google Drive Integration

**Goal:** Import documents from Google Drive instead of manual upload.

**Session Scope:** ~2 hours

### Checklist

- [ ] **9.1 Add Drive scope to OAuth**
  - Request drive.readonly scope
  - Re-authenticate if needed

- [ ] **9.2 Build folder picker**
  - Fetch folders from GET /gdrive/folders
  - Display folder tree
  - Click folder → list files

- [ ] **9.3 Implement file import**
  - Select files with checkboxes
  - Call POST /sessions/{id}/import/gdrive
  - Show import progress

- [ ] **9.4 Trigger document discovery**
  - After import, run discovery
  - Show conversion status
  - Refresh document list

### Exit Criteria

- [ ] Can browse Google Drive folders
- [ ] Can select and import PDFs
- [ ] Imported files appear in session
- [ ] Document discovery runs automatically

### References

- BACKEND_PLANNING.md → Google Drive Integration section

---

## Phase 10: Proponent Flow & Notifications

**Goal:** Proponent can view revisions and upload responses; notifications work.

**Session Scope:** ~3 hours

### Checklist

- [ ] **10.1 Create proponent dashboard**
  - Restricted view (no internal notes)
  - Show only their projects
  - Display pending revisions

- [ ] **10.2 Build revision response UI**
  - View revision request details
  - Upload response document
  - Add response note
  - Submit response

- [ ] **10.3 Add email notifications**
  - Trigger Mailjet on revision request
  - Trigger Mailjet on response
  - Include deep link to revision

- [ ] **10.4 Add in-app notifications**
  - Notification bell in header
  - Dropdown with recent notifications
  - Mark as read on click
  - Badge for unread count

### Exit Criteria

- [ ] Proponent can view their revisions
- [ ] Proponent can upload and submit response
- [ ] Email sent on revision request
- [ ] In-app notifications appear

### References

- BACKEND_PLANNING.md → Notifications section
- BACKEND_PLANNING.md → RBAC & Permissions
- FRONTEND_PLANNING.md → User Journey 2

---

## Phase 11: Report Generation & Export

**Goal:** Generate and export review reports.

**Session Scope:** ~2 hours

### Checklist

- [ ] **11.1 Add report generation**
  - "Generate Report" button
  - Call API (may be long-running job)
  - Show progress if job-based

- [ ] **11.2 Display report preview**
  - Render markdown in UI
  - Highlight gaps and warnings
  - Show items needing review

- [ ] **11.3 Add export options**
  - Export as Markdown
  - Export as JSON
  - Download button

- [ ] **11.4 Add stale badge**
  - Show if validation changed since report
  - "Re-generate" button

### Exit Criteria

- [ ] Report generates from current state
- [ ] Report displays in UI
- [ ] Can export Markdown and JSON
- [ ] Stale badge shows when needed

### References

- BACKEND_PLANNING.md → Long-Running Operations
- FRONTEND_PLANNING.md → User Journey 1, step 5

---

## Phase 12: Polish & Production

**Goal:** Error handling, performance, deployment.

**Session Scope:** ~3 hours

### Checklist

- [ ] **12.1 Error handling**
  - API error boundaries
  - Retry logic with exponential backoff
  - User-friendly error messages

- [ ] **12.2 Performance**
  - Lazy load heavy components
  - Virtualize long lists
  - Optimize PDF loading

- [ ] **12.3 Deployment**
  - Build static files (`npm run build`)
  - Configure Nginx to serve
  - Set up on 202.61.196.119
  - Test with production API

- [ ] **12.4 Final testing**
  - Run through all user journeys
  - Test with BACKTEST_DATASET.md
  - Fix any issues found

### Exit Criteria

- [ ] No console errors in production
- [ ] 50+ page PDF loads in <3 seconds
- [ ] Deployed and accessible
- [ ] All user journeys pass

### References

- README.md → Success Metrics
- BACKTEST_DATASET.md → Test cases

---

## Progress Tracker

| Phase | Status | Notes |
|-------|--------|-------|
| 1. Project Setup & PDF | Not Started | |
| 2. API Client & Auth | Not Started | |
| 3. Dashboard & Sessions | Not Started | |
| 4. Workspace Layout | Not Started | |
| 5. Checklist Panel | Not Started | |
| 6. Drag-and-Drop Evidence | Not Started | |
| 7. AI Chat Panel | Not Started | |
| 8. Cross-Validation | Not Started | |
| 9. Google Drive | Not Started | |
| 10. Proponent & Notifications | Not Started | |
| 11. Report Generation | Not Started | |
| 12. Polish & Production | Not Started | |

---

## Notes

- Each phase assumes previous phases are complete
- Update Progress Tracker after each session
- If a phase takes longer than expected, split into sub-sessions
- Reference detailed docs for implementation specifics - this checklist is intentionally high-level
