# Registry Review MCP UX Visual Guide

**Purpose:** Visual decision trees and flowcharts for tool selection

---

## Quick Decision Tree: Which Tool Should I Use?

```
START
  │
  ├─ Are you using Claude Desktop interactively?
  │   │
  │   YES → Use PROMPTS
  │         │
  │         ├─ New project? → /initialize
  │         ├─ Process docs? → /document-discovery
  │         └─ Extract evidence? → /evidence-extraction
  │
  └─ NO → Are you building an API/web integration?
      │
      YES → Use TOOLS
            │
            ├─ Uploading files from API/web?
            │   │
            │   YES → start_review_from_uploads()
            │         (handles base64 or file paths)
            │
            └─ Files already on filesystem?
                │
                YES → start_review()
                      (quick-start: session + discovery)
```

---

## Tool Selection Matrix

### By Use Case

| Use Case                               | Tool                          | Why                                    |
|----------------------------------------|-------------------------------|----------------------------------------|
| 🚀 **First-time user**                 | `/initialize` prompt          | Guided workflow with explanations      |
| 📤 **API file upload**                 | `start_review_from_uploads()` | One-step upload + processing           |
| 🗂️ **Batch processing**                | Multiple `start_review()` calls | Parallel project processing          |
| 🔍 **Debug single requirement**        | `map_requirement()`           | Detailed single-requirement view       |
| 📊 **Check project status**            | `list_sessions()`             | See all active reviews                 |
| 📄 **Extract from one PDF**            | `extract_pdf_text()`          | Single-file text extraction            |
| 🗺️ **GIS metadata**                    | `extract_gis_metadata()`      | Shapefile/GeoJSON analysis             |
| 🔄 **Re-scan after adding files**      | `discover_documents()`        | Update document index                  |

### By Integration Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    INTEGRATION PATTERNS                     │
└─────────────────────────────────────────────────────────────┘

┌────────────────────┐
│  Claude Desktop    │
│   (Interactive)    │
└─────────┬──────────┘
          │
          ├─ Use: PROMPTS (/initialize, /document-discovery)
          ├─ Feature: Auto-session selection
          └─ Feature: Inline session creation

┌────────────────────┐
│  ElizaOS Agent     │
│  (Conversational)  │
└─────────┬──────────┘
          │
          ├─ Use: start_review_from_uploads()
          ├─ File format: {name: "...", path: "/media/uploads/..."}
          └─ Feature: Automatic path resolution

┌────────────────────┐
│  REST API Wrapper  │
│  (Web Backend)     │
└─────────┬──────────┘
          │
          ├─ Use: start_review_from_uploads()
          ├─ File format: {filename: "...", content_base64: "..."}
          └─ Feature: Base64 file handling

┌────────────────────┐
│  Python SDK        │
│  (Direct Import)   │
└─────────┬──────────┘
          │
          ├─ Use: session_tools, document_tools, evidence_tools
          ├─ Pattern: await session_tools.create_session(...)
          └─ Feature: Full async/await support
```

---

## Workflow Visualization

### The 7-Stage Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│                    Registry Review Pipeline                  │
└──────────────────────────────────────────────────────────────┘

[1. Initialize]
    │ Create session + load checklist
    │ Input: project_name, documents_path
    │ Output: session_id
    │
    ├─ Interactive: /initialize Botany Farm, /path/to/docs
    └─ Tool: start_review(project_name, documents_path)
    ▼

[2. Discovery]
    │ Scan directory + classify documents
    │ Input: session_id
    │ Output: document index with classifications
    │
    ├─ Interactive: /document-discovery
    └─ Tool: discover_documents(session_id)
    ▼

[3. Evidence]
    │ Map 23 requirements to documents
    │ Input: session_id
    │ Output: evidence snippets + coverage stats
    │
    ├─ Interactive: /evidence-extraction
    └─ Tool: extract_evidence(session_id)
    ▼

[4. Validation]
    │ Cross-document consistency checks
    │ Input: session_id
    │ Output: validation results + flagged items
    │
    ├─ Interactive: /cross-validation
    └─ Tool: (coming in Phase 5)
    ▼

[5. Report]
    │ Generate structured report
    │ Input: session_id
    │ Output: Markdown + JSON reports
    │
    ├─ Interactive: /report-generation
    └─ Tool: (coming in Phase 5)
    ▼

[6. Human Review]
    │ Present flagged items for decision
    │ Input: session_id
    │ Output: human judgments recorded
    │
    ├─ Interactive: /human-review
    └─ Tool: (coming in Phase 5)
    ▼

[7. Complete]
    │ Finalize and export
    │ Input: session_id
    │ Output: final report + session archived
    │
    ├─ Interactive: /complete
    └─ Tool: (coming in Phase 5)
```

---

## Session Lifecycle State Machine

```
┌─────────────┐
│  No Session │
└──────┬──────┘
       │
       ├─ create_session() or start_review()
       │
       ▼
┌─────────────┐
│ initialized │ ─────────────────────────────────┐
└──────┬──────┘                                   │
       │                                          │
       ├─ discover_documents()                    │
       │                                          │
       ▼                                          │
┌─────────────┐                                   │
│  discovery  │ ─────────────────────────────────┤
│  complete   │                                   │
└──────┬──────┘                                   │
       │                                          │
       ├─ extract_evidence()                      │
       │                                          │
       ▼                                          │
┌─────────────┐                                   │
│  evidence   │ ─────────────────────────────────┤
│  complete   │                                   │ Any state can:
└──────┬──────┘                                   │ • load_session()
       │                                          │ • update_session_state()
       ├─ cross_validation()                      │ • delete_session()
       │                                          │
       ▼                                          │
┌─────────────┐                                   │
│ validation  │ ─────────────────────────────────┤
│  complete   │                                   │
└──────┬──────┘                                   │
       │                                          │
       ├─ generate_report()                       │
       │                                          │
       ▼                                          │
┌─────────────┐                                   │
│   report    │ ─────────────────────────────────┤
│  complete   │                                   │
└──────┬──────┘                                   │
       │                                          │
       ├─ human_review()                          │
       │                                          │
       ▼                                          │
┌─────────────┐                                   │
│   review    │ ─────────────────────────────────┤
│  complete   │                                   │
└──────┬──────┘                                   │
       │                                          │
       ├─ complete()                              │
       │                                          │
       ▼                                          │
┌─────────────┐                                   │
│  finalized  │ ─────────────────────────────────┘
└─────────────┘
       │
       ├─ delete_session()
       │
       ▼
┌─────────────┐
│   deleted   │
└─────────────┘
```

---

## Tool Complexity Distribution

```
Simple (0-2 params)          Moderate (2-4 params)        Complex (5+ params)
════════════════             ════════════════════         ═══════════════════

list_sessions()              create_session()             start_review_from_uploads()
list_example_projects()      start_review()               create_session_from_uploads()
load_session()               extract_pdf_text()
delete_session()             extract_gis_metadata()
discover_documents()         map_requirement()
extract_evidence()           upload_additional_files()

     7 tools                       5 tools                      2 tools
    (47%)                         (33%)                        (13%)

✅ Good distribution - most tools are simple
```

---

## Error Recovery Flowchart

```
┌──────────────────┐
│  Tool Call Fails │
└────────┬─────────┘
         │
         ├─ Session Not Found?
         │   │
         │   YES → List available sessions
         │         Suggest: list_sessions() or /initialize
         │
         ├─ File Not Found?
         │   │
         │   YES → Show expected path
         │         Check: permissions, existence
         │
         ├─ Invalid Parameters?
         │   │
         │   YES → Show parameter requirements
         │         Example: "session_id required (string)"
         │
         └─ Other Error?
             │
             YES → Show error type and message
                   Suggest: Check logs, contact support
                   Context: Tool name, input values
```

---

## Tool Categories Visual Map

```
┌─────────────────────────────────────────────────────────────────┐
│                      REGISTRY REVIEW TOOLS                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│  SESSION LIFECYCLE  │
│  (6 tools)          │
├─────────────────────┤
│ create_session      │ ← Manual setup
│ start_review        │ ← Quick-start ⭐
│ load_session        │ ← Status check
│ update_session_state│ ← Progress tracking
│ list_sessions       │ ← Discovery
│ delete_session      │ ← Cleanup
└─────────────────────┘

┌─────────────────────┐
│  UPLOAD (API/WEB)   │
│  (3 tools)          │
├─────────────────────┤
│ create_session_from_uploads    │ ← Upload + create
│ upload_additional_files        │ ← Add to existing
│ start_review_from_uploads ⭐   │ ← All-in-one
└────────────────────────────────┘

┌─────────────────────┐
│  DOCUMENT ANALYSIS  │
│  (3 tools)          │
├─────────────────────┤
│ discover_documents  │ ← Batch scan
│ extract_pdf_text    │ ← Single PDF
│ extract_gis_metadata│ ← GIS files
└─────────────────────┘

┌─────────────────────┐
│  EVIDENCE MAPPING   │
│  (2 tools)          │
├─────────────────────┤
│ extract_evidence    │ ← All requirements
│ map_requirement     │ ← Single requirement (debug)
└─────────────────────┘

┌─────────────────────┐
│  TESTING/DEMO       │
│  (1 tool)           │
├─────────────────────┤
│ list_example_projects│ ← [Candidate for removal]
└─────────────────────┘
```

---

## Performance Characteristics

```
┌────────────────────────────────────────────────────────────┐
│              OPERATION PERFORMANCE PROFILE                 │
└────────────────────────────────────────────────────────────┘

Session Operations (Fast)
═════════════════════════
create_session()        ▓ <100ms   (File I/O only)
load_session()          ▓ <50ms    (JSON read)
update_session_state()  ▓ <50ms    (JSON patch)
list_sessions()         ▓▓ <200ms  (Directory scan)
delete_session()        ▓ <100ms   (Directory removal)

Document Operations (Moderate)
═══════════════════════════════
discover_documents()    ▓▓▓▓ 1-2s     (Scan + classify)
extract_pdf_text()      ▓▓▓▓▓ 2-5s    (Per document)
extract_gis_metadata()  ▓▓ 0.5-1s     (Metadata only)

Evidence Operations (Slow - LLM)
════════════════════════════════
extract_evidence()      ▓▓▓▓▓▓▓ 2-4s  (23 requirements, cached)
map_requirement()       ▓▓ 0.5-1s     (Single requirement)

Upload Operations (Variable)
═════════════════════════════
create_session_from_uploads() ▓▓▓▓▓▓ 2-10s (Depends on file size)
upload_additional_files()     ▓▓▓ 1-5s     (Depends on file count)
start_review_from_uploads()   ▓▓▓▓▓▓▓▓ 5-15s (Full workflow)

Legend:
▓ = 100ms    Fast - immediate response
▓▓ = 500ms   Quick - minimal wait
▓▓▓ = 1s     Moderate - noticeable
▓▓▓▓ = 2s    Slow - coffee break
▓▓▓▓▓ = 5s   Very slow - deep breath
```

---

## Common Workflow Patterns

### Pattern 1: Interactive Review (Claude Desktop)

```
User: I have project documents to review

Assistant uses:
  ├─ /initialize Botany Farm, /path/to/docs
  │     ↓
  │  ✅ Session created: session-abc123
  │
  ├─ /document-discovery
  │     ↓
  │  ✅ Found 7 documents, classified
  │
  └─ /evidence-extraction
        ↓
     ✅ 73.9% coverage, 11 covered, 12 partial

Total: 3 prompts, ~10 seconds
```

### Pattern 2: API Upload (ElizaOS, Web App)

```
Web form submits files → Backend receives:
  │
  ├─ Convert files to base64 or save to temp
  │
  └─ Call: start_review_from_uploads(
        project_name="Uploaded Project",
        files=[{filename, content_base64}, ...],
        auto_extract=True
    )
    ↓
 ✅ Returns: {
      session_creation: {...},
      evidence_extraction: {...}
    }

Total: 1 tool call, ~10-15 seconds
```

### Pattern 3: Batch Processing (Python Script)

```python
projects = [
    ("Farm A", "/data/farm-a"),
    ("Farm B", "/data/farm-b"),
    ("Farm C", "/data/farm-c")
]

results = await asyncio.gather(*[
    process_project(name, path)
    for name, path in projects
])

# Each project:
#   1. create_session()
#   2. discover_documents()
#   3. extract_evidence()

Total: 3 projects × 3 tools = 9 calls, parallel (~15s)
```

### Pattern 4: Debugging Single Requirement

```
Requirement REQ-007 has low confidence (0.45)

Developer runs:
  ├─ map_requirement(session_id, "REQ-007")
  │     ↓
  │  Returns: {
  │    documents: [doc1, doc2],
  │    evidence_snippets: [
  │      {text, page, document_id},
  │      ...
  │    ]
  │  }
  │
  └─ Examine snippets to understand why confidence is low

Total: 1 tool call, ~1 second
```

---

## Documentation Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│                  DOCUMENTATION STRUCTURE                   │
└────────────────────────────────────────────────────────────┘

Entry Point
├─ list_capabilities prompt ⭐
│  └─ Quick Reference Table
│  └─ Integration Patterns
│  └─ Tool Signatures
│  └─ Workflow Stages
│
├─ README.md
│  └─ Quick Start (3 prompts)
│  └─ Tool Selection Guide
│  └─ Integration Examples
│  └─ Configuration
│
├─ ROADMAP.md
│  └─ Phase completion status
│  └─ Upcoming features
│
└─ docs/
   ├─ UX_ANALYSIS.md (this document)
   ├─ UX_IMPROVEMENTS_IMPLEMENTATION.md
   ├─ PHASE_*_COMPLETION.md
   └─ PROMPT_DESIGN_PRINCIPLES.md
```

---

## Tool Discovery Journey

```
┌──────────────────────────────────────────────────────────┐
│           HOW USERS FIND THE RIGHT TOOL                 │
└──────────────────────────────────────────────────────────┘

New User Path
═════════════
1. Opens Claude Desktop
2. Sees MCP server: "registry-review"
3. Types: "What can you do?"
4. Claude shows: list_capabilities
   ├─ Quick Reference Table ← Finds task-based entry
   └─ Integration Patterns  ← Understands context
5. Tries: /initialize (guided)
6. Success! ✅

API Developer Path
══════════════════
1. Reading integration docs
2. Finds: "REST API Integration" section
3. Sees: start_review_from_uploads() example
4. Copies code template
5. Adapts to their use case
6. Success! ✅

Advanced User Path
══════════════════
1. Needs specific functionality
2. Searches: list_capabilities for keyword
3. Finds: extract_pdf_text() signature
4. Uses tool directly
5. Success! ✅
```

---

## The UX Verdict Visual

```
┌──────────────────────────────────────────────────────────────┐
│                    IS 15 TOOLS TOO MANY?                     │
└──────────────────────────────────────────────────────────────┘

Comparison with Other MCP Servers
═════════════════════════════════

  Simple MCP            Domain-Specific        Complex MCP
  (5-10 tools)          (15-25 tools)          (30+ tools)
  ════════              ════════════            ════════════

  • Calculator          • Registry Review ⭐    • Database
  • Time/Date           • Code Review           • Cloud Provider
  • Search              • Data Analysis         • ERP System

  Too simple            Just Right ✅           Too complex
  for domain            Balance complexity       Needs redesign
                        and usability

Registry Review Position
════════════════════════

  │ Complexity
  │
  │         │ ┌─────┐
  │         │ │ DB  │ ← Too complex
  │         │ └─────┘
  │     ┌───┴────┐
  │     │Registry│ ← Just right ✅
  │     │ Review │
  │     └────────┘
  │ ┌──────┐
  │ │Calc  │ ← Too simple
  │ └──────┘
  └──────────────────── Tool Count
    0   5   10  15  20  25  30  35

Verdict: 15 tools is appropriate for domain complexity
```

---

## Summary: The Real UX Issue

```
❌ NOT THE PROBLEM
══════════════════
• Too many tools (15 is appropriate)
• Tool naming (clear and consistent)
• Parameter complexity (well-designed)
• Error messages (exemplary)

✅ THE ACTUAL PROBLEM
══════════════════════
• Tool discovery (hard to scan 15 tools)
• Integration guidance (when to use what?)
• Task-based mapping (I want X → use Y)
• Code examples (how to integrate?)

🔧 THE SOLUTION
═══════════════
• Enhanced list_capabilities (Quick Reference Table)
• Integration patterns (5 examples)
• Tool signatures (with code samples)
• README improvements (task-based guide)

Effort: ~5.5 hours
Impact: 50% faster tool discovery
Risk: Low (documentation only)
```

---

## Next Steps Visualization

```
┌────────────────────────────────────────────────────────────┐
│              IMPLEMENTATION ROADMAP                        │
└────────────────────────────────────────────────────────────┘

Week 1: Documentation Phase
═══════════════════════════
[████████████░░░░░░░░░░] 60% complete (this analysis)

Day 1-2: Enhance list_capabilities
  ├─ Add Quick Reference Table
  ├─ Add Tool Signatures
  └─ Add Integration Patterns

Day 3-4: README improvements
  ├─ Tool Selection Guide
  ├─ Integration Examples
  └─ Common Patterns

Day 5: Code changes
  └─ Remove list_example_projects

Week 2: Validation Phase
════════════════════════
[ ] Test in Claude Desktop
[ ] User feedback collection
[ ] Iterate based on findings
[ ] Publish final version

Success Criteria
════════════════
✅ Tool discovery time: <30 seconds (from 60s)
✅ Zero-to-first-success: <5 minutes (from 10m)
✅ Integration examples: 5+ patterns documented
✅ User satisfaction: "Clear and easy to use"
```

---

**Document Purpose:** Quick visual reference for tool selection and workflow design

**Related Docs:**
- [UX_ANALYSIS_SUMMARY.md](./UX_ANALYSIS_SUMMARY.md) - Executive summary
- [UX_ANALYSIS.md](./UX_ANALYSIS.md) - Full 10,000-word analysis
- [UX_IMPROVEMENTS_IMPLEMENTATION.md](./UX_IMPROVEMENTS_IMPLEMENTATION.md) - Implementation details
