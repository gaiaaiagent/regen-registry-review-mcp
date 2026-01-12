# Frontend Planning

## Overview

A Next.js web application providing a document-centric review workspace with an embedded AI chat panel.

---

## Table of Contents

1. [User Journeys](#user-journeys)
2. [Workspace Layout](#workspace-layout)
3. [Interaction Design](#interaction-design)
4. [AI Chat Panel](#ai-chat-panel)
5. [Component Architecture](#component-architecture)
6. [Technical Stack](#technical-stack)
7. [Implementation Phases](#implementation-phases)

---

## User Journeys

### Journey 1: New Project Review (60-90 min)

**Actor:** Reviewer (Becca)

```
1. LOGIN & SELECT PROJECT                                    [5 min]
   • Sign in with Google
   • View dashboard with assigned projects
   • Click project to open workspace

   ACCEPTANCE CRITERIA:
   ✓ Login completes in <2 sec
   ✓ Dashboard shows project list with status indicators
   ✓ Clicking project loads workspace with documents

2. DOCUMENT SCAN                                             [10 min]
   • System shows 7 uploaded PDFs
   • Scan each document
   • Ask AI: "What documents are most relevant to land tenure?"

   ACCEPTANCE CRITERIA:
   ✓ PDFs render correctly with searchable text
   ✓ Page navigation is responsive (<100ms)
   ✓ AI responds with document recommendations

3. REQUIREMENT-BY-REQUIREMENT REVIEW                         [40 min]
   • Click REQ-001 in checklist
   • Smart filter shows relevant documents
   • Drag text from PDF to requirement card
   • Evidence links instantly (optimistic UI)
   • Ask AI: "Find more evidence for this requirement"
   • Repeat for all 23 requirements

   ACCEPTANCE CRITERIA:
   ✓ Drag-drop from PDF to requirement takes <500ms
   ✓ Evidence persists on page refresh
   ✓ AI can search and suggest evidence

4. CROSS-VALIDATION CHECK                                    [10 min]
   • Navigate to Cross-Validation stage
   • View Fact Sheet: Date Alignment table
   • Ask AI: "Explain the 97-day gap"
   • View Land Tenure table

   ACCEPTANCE CRITERIA:
   ✓ Fact Sheet tables are scannable in <30 sec
   ✓ AI explains validation results

5. REPORT & FINALIZATION                                     [25 min]
   • Click "Generate Report"
   • Review gaps
   • Add internal notes where needed
   • Request revision from proponent for missing items
   • Save progress

   ACCEPTANCE CRITERIA:
   ✓ Report generates in <10 sec
   ✓ Internal notes are visually distinct
```

### Journey 2: Proponent Revision Response (15 min)

**Actor:** Proponent (Thomas)

```
1. VIEW REVISION REQUEST                                     [2 min]
   • Sign in with Google and see "1 pending revision"
   • Open revision detail
   • Ask AI: "What do I need to provide?"

   ACCEPTANCE CRITERIA:
   ✓ Only public comments visible (not internal notes)
   ✓ AI explains what's needed in plain language

2. UPLOAD RESPONSE                                           [5 min]
   • Drag PDF into upload zone
   • Add note explaining the upload
   • Submit response

   ACCEPTANCE CRITERIA:
   ✓ Upload validates PDF format and size
   ✓ Response notifies reviewer

3. TRACK PROGRESS                                            [1 min]
   • View updated status

   ACCEPTANCE CRITERIA:
   ✓ Status reflects actual backend state
```

### Journey 3: Batch Farm Review (Template Flow)

**Actor:** Reviewer

```
1. CREATE TEMPLATE                                           [30 min]
   • Create "Czech Farm Cluster 2024" template
   • Upload shared docs
   • Mark 8 requirements as inherited

2. BATCH CREATE PROJECTS                                     [5 min]
   • Upload CSV with 10 farm names
   • 10 projects created with inherited evidence

3. REVIEW FARM-SPECIFIC                                      [35 min/farm]
   • Open Farm CZ-001
   • 8 requirements already Covered (inherited)
   • Only 15 farm-specific requirements to review

4. BULK EXPORT                                               [10 min]
   • Select all farms
   • Export reports as ZIP

   ACCEPTANCE CRITERIA:
   ✓ Inherited requirements show "From Template" badge
   ✓ Inherited evidence is read-only
   ✓ Per-farm time is 30-45 min
```

---

## Workspace Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  REGISTRY REVIEW WORKSPACE                              Project: Botany Farm 22      │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  Progress: ████████████░░░░░ Stage 5/8: Cross-Validation    [Save] [Export]          │
├──────────────────────────┬─────────────────────────────┬─────────────────────────────┤
│                          │                             │                             │
│  📄 DOCUMENT VIEWER      │  ✓ CHECKLIST                │  🤖 AI ASSISTANT            │
│  ────────────────────    │  ───────────────────        │  ─────────────────          │
│  [baseline_report.pdf ▼] │                             │                             │
│                          │  Progress: 18/23 (78%)      │  How can I help?            │
│  ┌────────────────────┐  │                             │                             │
│  │                    │  │  ▼ Land Tenure (3/3) ✓      │  ┌───────────────────────┐  │
│  │                    │  │    ✓ REQ-001               │  │ "Why is REQ-005       │  │
│  │   PDF CONTENT      │  │    ✓ REQ-002               │  │  marked as partial?"  │  │
│  │                    │  │    ✓ REQ-003               │  └───────────────────────┘  │
│  │   [Drag text to    │  │                             │                             │
│  │    link evidence]  │  │  ▼ GHG Accounting (2/5) ⏳  │  REQ-005 requires a         │
│  │                    │  │    ✓ REQ-004               │  monitoring protocol with   │
│  │                    │  │    ⏳ REQ-005  ←focused    │  specific sampling dates... │
│  └────────────────────┘  │    ○ REQ-006               │                             │
│                          │    ○ REQ-007               │  [Search monitoring report] │
│  [◀ Prev] Page 12/45 [▶] │    ○ REQ-008               │                             │
│                          │                             │  ────────────────────────   │
│  Documents (7):          │  ▶ Safeguards (0/4)         │  [____________________]     │
│  ├─ 📄 baseline.pdf  ✓   │  ▶ Monitoring (0/6)         │  [Send]                     │
│  └─ 📄 monitoring.pdf ⏳ │                             │                             │
│                          │                             │                             │
├──────────────────────────┴─────────────────────────────┴─────────────────────────────┤
│  Stages: [✓ Init] [✓ Discover] [✓ Map] [✓ Extract] [⏳ Validate] [○ Report] [○ Done] │
│          ⚠️ 3 requirements need evidence                        [▶ Run Validation]   │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Panel Sizing

- **Document Viewer:** 40% width (resizable)
- **Checklist:** 30% width (resizable)
- **AI Chat:** 30% width (collapsible)

### Responsive Behavior

- **Desktop (>1200px):** Three-column layout
- **Tablet (768-1200px):** Two columns, AI as overlay
- **Mobile (<768px):** Single column, tab navigation

---

## Interaction Design

### Drag-and-Drop Evidence Linking

```
1. User selects text in PDF (no popup appears)

2. User drags selection toward checklist panel
   ┌─────────────────────┐
   │ "127.4 hectares of  │ ─────drag─────▶  Requirement cards light up
   │  managed grassland" │                   showing valid drop targets
   └─────────────────────┘

3. User drops on requirement card
   ┌────────────────────────────────┐
   │ REQ-002 Land tenure    [DROP]  │ ← Card highlights as drop target
   │ ════════════════════════════   │
   │ ✓ Evidence linked!             │
   │   📄 baseline.pdf, pg 8        │
   └────────────────────────────────┘

4. Optimistic UI: Link appears instantly, syncs in background
```

### Evidence Scratchpad

For "find first, sort later" workflow:

```
┌─────────────────────────────────────────────────────────────────────┐
│  📋 SCRATCHPAD                                           [Collapse] │
├─────────────────────────────────────────────────────────────────────┤
│  Unassigned clips (3):                                              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ "Sampling conducted by AgriLab certified technician..."       │ │
│  │ 📄 monitoring_report.pdf, Page 7                              │ │
│  │ [Assign to REQ ▼] [Delete]                        Clipped 2m │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Drag clips to requirements or use dropdown to assign               │
└─────────────────────────────────────────────────────────────────────┘
```

### Soft-Gated Navigation

Allow jumping between stages, but show warnings:

```
┌─────────────────────────────────────────────────────────────────────┐
│  ⚠️ Report Stage - Dependencies Not Met                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  You can view the Report stage, but gaps will appear:               │
│                                                                     │
│  • 3 requirements have no evidence mapped                           │
│    └─ REQ-006, REQ-007, REQ-008                                    │
│  • Cross-validation has 1 unresolved warning                        │
│                                                                     │
│  [Continue Anyway] [Go Back to Fix]                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Artifact Freshness (Stale Badges)

Whenever upstream inputs change (new uploads, mapping edits), mark downstream artifacts as **Out of date** and provide one-click recovery.

- Evidence out of date → “Re-run extraction”
- Validation out of date → “Re-run validation”
- Report out of date → “Re-generate report”

### Focus Mode

Expand single requirement for detailed review:

```
┌─────────────────────────────────────────────────────────────────────┐
│  FOCUS MODE: REQ-005 Monitoring Protocol                   [Close]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Requirement Text:                                                  │
│  "Projects shall implement a monitoring protocol that includes      │
│   soil sampling at least once per crediting period..."              │
│                                                                     │
│  Status: ⏳ Partial              Confidence: 0.67                   │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  EVIDENCE (2 snippets)                                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1. "Soil samples were collected on 2024-03-15..."           │   │
│  │    📄 baseline_report.pdf, Page 12                          │   │
│  │    Confidence: 0.92                                         │   │
│  │    [View in Document] [Remove]                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [+ Add Evidence] [+ Add Note] [Request Revision]                   │
│                                                                     │
│  ← Previous: REQ-004                      Next: REQ-006 →           │
└─────────────────────────────────────────────────────────────────────┘
```

### Cross-Validation Fact Sheets

Tabular view for quick scanning:

```
┌─────────────────────────────────────────────────────────────────────┐
│  CROSS-VALIDATION: FACT SHEET                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DATE ALIGNMENT (120-day rule)                                      │
│  ┌─────────────────┬──────────────┬──────────────┬────────┐        │
│  │ Field           │ Project Plan │ Baseline Rpt │ Status │        │
│  ├─────────────────┼──────────────┼──────────────┼────────┤        │
│  │ Project Start   │ 2024-01-01   │ 2024-01-01   │ ✓      │        │
│  │ Baseline Date   │ 2024-02-15   │ 2024-02-15   │ ✓      │        │
│  │ Sampling Date   │ —            │ 2024-03-15   │ ⚠️ 97d │        │
│  └─────────────────┴──────────────┴──────────────┴────────┘        │
│                                                                     │
│  Summary: 1 warning (Sampling Date: 97 days, max: 120)              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## AI Chat Panel

### Layout

```
┌─────────────────────────────────────────┐
│  🤖 AI Assistant              [Collapse] │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ You                              │   │
│  │ Why is REQ-005 marked partial?   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 🤖 Assistant                     │   │
│  │                                  │   │
│  │ REQ-005 requires documentation   │   │
│  │ of a monitoring protocol with    │   │
│  │ specific sampling dates.         │   │
│  │                                  │   │
│  │ I found 1 snippet that says      │   │
│  │ "annual monitoring" but it       │   │
│  │ lacks specific dates.            │   │
│  │                                  │   │
│  │ [Search for dates]               │   │
│  │ [View evidence]                  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ────────────────────────────────────   │
│  [________________________________]     │
│  [Send]                                 │
│                                         │
└─────────────────────────────────────────┘
```

### Context Awareness

The AI receives context about:
- Current session state
- Focused requirement
- Visible document + page
- User role

This enables contextual responses without the user restating everything.

### Action Buttons

AI responses can include action buttons:
- **[Search for dates]** → Triggers document search
- **[Link to REQ-005]** → Links evidence to requirement
- **[View in document]** → Navigates PDF viewer
- **[Run extraction]** → Starts evidence extraction job

### Proponent Mode

When a proponent is logged in, the AI:
- Uses simpler language
- Explains what's needed for revisions
- Cannot reveal internal notes
- Suggests what documents to upload

---

## Component Architecture

```
App
├── AppLayout
│   ├── TopNav
│   │   ├── Logo
│   │   ├── ProjectSelector
│   │   └── UserMenu
│   └── MainContent
│
├── DashboardPage
│   ├── StatsCards
│   ├── ProjectList
│   │   └── ProjectCard
│   └── BulkActionsBar
│
├── WorkspacePage
│   ├── WorkspaceHeader
│   │   ├── ProjectInfo
│   │   ├── StageProgress
│   │   └── ActionButtons
│   ├── SplitPane
│   │   ├── DocumentPanel
│   │   │   ├── DocumentTabs
│   │   │   ├── PDFViewer (react-pdf-highlighter)
│   │   │   │   ├── HighlightLayer
│   │   │   │   └── DragSource
│   │   │   └── DocumentList
│   │   ├── ChecklistPanel
│   │   │   ├── Scratchpad
│   │   │   ├── CategoryAccordion
│   │   │   │   └── RequirementCard (DropTarget)
│   │   │   │       ├── StatusBadge
│   │   │   │       └── EvidenceList
│   │   │   └── ValidationSummary
│   │   └── AIChatPanel
│   │       ├── MessageList
│   │       │   ├── UserMessage
│   │       │   └── AssistantMessage
│   │       │       └── ActionButton
│   │       └── ChatInput
│   ├── FocusModeOverlay
│   └── StageNavigator
│
├── CrossValidationPage
│   ├── FactSheetTabs
│   │   ├── DateAlignmentTable
│   │   ├── LandTenureTable
│   │   └── ProjectIDTable
│   └── IssuesList
│
├── RevisionsPage (Proponent)
│   ├── RevisionList
│   ├── UploadZone
│   └── ResponseForm
│
└── TemplatesPage (Admin)
    ├── TemplateList
    ├── CreateTemplateWizard
    └── BatchCreateForm
```

---

## Technical Stack

```
Frontend
├── Framework: Next.js 14+ (App Router)
├── Language: TypeScript
├── Styling: Tailwind CSS + shadcn/ui
├── PDF Viewer: react-pdf-highlighter
├── Drag-and-Drop: @dnd-kit/core
├── State Management: Zustand + React Query
├── API Client: openapi-fetch (generated types)
└── Deployment: Vercel or self-hosted
```

### Key Libraries

| Library | Purpose |
|---------|---------|
| `react-pdf-highlighter` | PDF rendering with persistent highlights |
| `@dnd-kit/core` | Drag-and-drop with accessibility |
| `zustand` | Client state with optimistic updates |
| `@tanstack/react-query` | Server state and caching |
| `openapi-fetch` | Type-safe API client |
| `shadcn/ui` | UI components |

### Optimistic UI Pattern

```typescript
// Update UI immediately, sync in background
const linkEvidence = async (snippetId: string, requirementId: string) => {
  // 1. Optimistic update
  addEvidenceLocally(snippetId, requirementId);

  try {
    // 2. Sync to server
    await api.linkEvidence(sessionId, snippetId, requirementId);
  } catch (error) {
    // 3. Rollback on failure
    removeEvidenceLocally(snippetId, requirementId);
    showToast('Failed to save - retrying...');
  }
};
```

---

## Implementation Phases

### Phase 1: PDF Viewer Proof-of-Concept (Week 1-2)

**Goal:** Prove PDF rendering and highlighting works

**Tasks:**
- [ ] Initialize Next.js project
- [ ] Integrate react-pdf-highlighter
- [ ] Test with 5+ real project PDFs
- [ ] Verify highlight persistence across reload
- [ ] Set up API client with type generation

**EXIT CRITERIA:**
- [ ] 5 different PDFs render correctly
- [ ] Highlights persist after page reload
- [ ] No memory issues with 50+ page PDF
- [ ] Text selection works on native PDFs

**Risk Mitigation:** If react-pdf-highlighter fails, evaluate alternatives before proceeding.

---

### Phase 2: Workspace Shell (Week 3-4)

**Goal:** Basic three-panel layout with session management

**Tasks:**
- [ ] Implement Sign in with Google (Auth.js/NextAuth) for reviewer/admin
- [ ] Implement Dashboard with session list
- [ ] Create split-pane workspace layout
- [ ] Add document list sidebar
- [ ] Add page/zoom navigation
- [ ] Set up Zustand stores

**EXIT CRITERIA:**
- [ ] Can create/open/delete sessions
- [ ] Three-panel layout renders correctly
- [ ] Documents load in PDF viewer
- [ ] Authenticated users only (no anonymous workspace access)

---

### Phase 3: Evidence Linking (Week 5-6)

**Goal:** Drag-and-drop evidence workflow

**Tasks:**
- [ ] Implement checklist panel
- [ ] Create requirement cards as drop targets
- [ ] Implement drag-drop from PDF
- [ ] Add evidence scratchpad
- [ ] Implement optimistic UI
- [ ] Add Focus Mode

**EXIT CRITERIA:**
- [ ] Can drag text to requirement
- [ ] Evidence appears instantly
- [ ] Scratchpad holds clips
- [ ] Focus Mode expands requirement

---

### Phase 4: AI Chat Panel (Week 7-8)

**Goal:** Embedded AI assistant

**Tasks:**
- [ ] Create chat panel component
- [ ] Integrate with agent API
- [ ] Pass session context to agent
- [ ] Render action buttons in responses
- [ ] Handle navigation commands from AI
- [ ] Require explicit user confirmation for any write action suggested by the agent

**EXIT CRITERIA:**
- [ ] Can ask questions about requirements
- [ ] AI explains confidence scores
- [ ] AI can search documents
- [ ] Action buttons trigger UI updates

---

### Phase 5: Validation & Cross-Issues (Week 9-10)

**Goal:** Cross-validation with tabular views

**Tasks:**
- [ ] Implement Fact Sheet tables
- [ ] Add issues panel in workspace
- [ ] Link issues to requirements
- [ ] Implement soft-gating
- [ ] Add heatmap scrollbar

**EXIT CRITERIA:**
- [ ] Fact sheets render from API
- [ ] Clicking issue navigates correctly
- [ ] Soft gate shows warnings

---

### Phase 6: RBAC & Proponent Flow (Week 11-12)

**Goal:** Multi-user with proponent collaboration

**Tasks:**
- [ ] Add role-based UI restrictions
- [ ] Create proponent dashboard
- [ ] Build revision response UI
- [ ] Implement internal/external comments
- [ ] Add proponent invitation + least-privilege session access

**EXIT CRITERIA:**
- [ ] Proponent cannot see internal notes
- [ ] Revision flow works end-to-end
- [ ] Comments have distinct styling

---

### Phase 7: Polish & Production (Week 13-14)

**Goal:** Production-ready MVP

**Tasks:**
- [ ] Performance optimization
- [ ] Error handling and recovery
- [ ] Job progress UI
- [ ] User onboarding hints
- [ ] Documentation

**EXIT CRITERIA:**
- [ ] 50+ page PDF loads in <3s
- [ ] No console errors in production
- [ ] Help available for key features
