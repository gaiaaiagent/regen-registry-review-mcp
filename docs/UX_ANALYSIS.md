# Registry Review MCP UX Analysis

**Date:** 2025-11-20
**Version:** 2.0.0
**Analysis Focus:** User-facing API design, tool ergonomics, workflow clarity

---

## Executive Summary

The Registry Review MCP system currently exposes **15 tools** and **10 prompts** (25 total endpoints). After thorough analysis of the codebase, usage patterns, and test coverage, the API is **fundamentally sound** but could benefit from strategic consolidation and improved discoverability.

**Key Findings:**
- Tool count is appropriate for domain complexity (not excessive)
- Naming conventions are clear and consistent
- Error messages are comprehensive and actionable
- Workflow guidance is excellent (7-stage process with auto-selection)
- Primary UX weakness: Tool discovery and selection could be simplified

**Recommendation:** Focus on **documentation and workflow defaults** rather than API reduction. The current tool set represents the minimum viable surface area for the domain.

---

## 1. Tool Count Analysis

### Current Tool Inventory

**Session Management (6 tools):**
```
✓ create_session              - Create new review session
✓ load_session                - Load existing session
✓ update_session_state        - Update session progress
✓ list_sessions               - List all sessions
✓ list_example_projects       - List example test data
✓ delete_session              - Delete session
✓ start_review               ⭐ Quick-start (session + discovery)
```

**Upload Integration (3 tools):**
```
✓ create_session_from_uploads     - Create session from base64/path files
✓ upload_additional_files         - Add files to existing session
✓ start_review_from_uploads      ⭐ One-step upload workflow
```

**Document Processing (3 tools):**
```
✓ discover_documents          - Scan and classify documents
✓ extract_pdf_text            - Extract text from specific PDF
✓ extract_gis_metadata        - Extract GIS shapefile metadata
```

**Evidence & Analysis (2 tools):**
```
✓ extract_evidence            - Map all requirements to documents
✓ map_requirement             - Map single requirement (debugging)
```

**Total: 15 tools**

### Is 15 Too Many?

**No. Here's why:**

1. **Domain Complexity**: Registry review is inherently multi-stage with distinct concerns (session management, document processing, evidence extraction, validation, reporting). Each tool serves a specific function.

2. **Orthogonality**: Tools don't overlap. Each has a unique purpose:
   - `create_session` vs `start_review`: Different entry points (manual vs quick-start)
   - `extract_pdf_text` vs `discover_documents`: Single-file vs batch operations
   - `extract_evidence` vs `map_requirement`: Batch vs single requirement

3. **Integration Patterns**: The 3 upload tools serve a critical integration use case (ElizaOS, web apps, APIs) where files come from non-filesystem sources. Removing these would break external integrations.

4. **Comparison Benchmark**:
   - Simple MCP servers: 5-10 tools
   - Domain-specific MCP servers: 15-25 tools
   - Complex MCP servers: 30+ tools

   Registry Review (15 tools) is in the expected range for a domain-specific workflow system.

### Tools That Could Be Consolidated

**Candidate for removal: `list_example_projects`**

**Rationale:**
- Only used for testing/demos
- Not part of production workflow
- Could be replaced with better documentation in README
- Saves 1 tool, minimal impact

**Not recommended to consolidate:**
- Session management tools (all serve distinct purposes)
- Upload tools (critical for API integrations)
- Document extraction tools (different file types require different handlers)

**Verdict:** Tool count is appropriate. Consider removing `list_example_projects` only if tool discovery becomes overwhelming (not currently the case).

---

## 2. Tool Naming Analysis

### Current Naming Convention

**Pattern: `<verb>_<noun>`**

Examples:
- `create_session` ✓
- `discover_documents` ✓
- `extract_evidence` ✓
- `map_requirement` ✓

**Strengths:**
- Clear action verbs (create, load, discover, extract, map)
- Consistent snake_case (Python convention)
- Self-documenting (no abbreviations)
- Predictable patterns (all session tools start with verb then "session")

**Weaknesses:**
- Some inconsistency in noun specificity:
  - `start_review` (what are we reviewing?)
  - `extract_evidence` (evidence from what?)

**Recommendations:**

1. **Keep current names** - They're clear and consistent
2. **Document semantic groups** in `list_capabilities`:
   ```
   Session Lifecycle: create_session, load_session, delete_session
   Quick-Start: start_review, start_review_from_uploads
   Document Analysis: discover_documents, extract_pdf_text, extract_gis_metadata
   Evidence Mapping: extract_evidence, map_requirement
   ```

3. **Add tool categorization** to help users discover related tools

**Verdict:** Naming is excellent. No changes needed.

---

## 3. Parameter Complexity Analysis

### Simple Tools (0-2 required params) ✅

```python
# Excellent - no parameters
list_sessions() -> list[dict]
list_example_projects() -> dict

# Excellent - single required parameter
load_session(session_id: str) -> dict
delete_session(session_id: str) -> dict
discover_documents(session_id: str) -> dict
extract_evidence(session_id: str) -> dict
map_requirement(session_id: str, requirement_id: str) -> dict
```

**Assessment:** 7/15 tools (47%) have simple signatures. This is excellent.

### Moderate Tools (2-4 required params) ✅

```python
# Good - essential project metadata
create_session(
    project_name: str,
    documents_path: str,
    methodology: str = "soil-carbon-v1.2.2",  # good default
    project_id: str | None = None,            # optional
    proponent: str | None = None,             # optional
    crediting_period: str | None = None       # optional
) -> dict

# Good - file extraction with sensible defaults
extract_pdf_text(
    filepath: str,
    start_page: int | None = None,
    end_page: int | None = None,
    extract_tables: bool = False
) -> dict
```

**Assessment:** Clear required vs optional distinction. Sensible defaults.

### Complex Tools (5+ params) ⚠️

```python
# Most complex tool
start_review_from_uploads(
    project_name: str,                    # required
    files: list[dict],                    # required
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
    proponent: str | None = None,
    crediting_period: str | None = None,
    auto_extract: bool = True,            # good default
    deduplicate: bool = True,             # good default
    force_new_session: bool = False       # safety default
) -> dict
```

**Assessment:** Complexity is justified - this is an all-in-one integration tool designed to minimize API calls for external systems. The 7 optional parameters all have sensible defaults.

**Verdict:** Parameter complexity is well-managed. No simplification needed.

---

## 4. Error Message Quality Analysis

### Error Handling Architecture

**Tool-level error handling:**
```python
@with_error_handling("tool_name")
async def tool(...):
    # Automatic try/catch with structured logging
    # Returns: formatted error string with context
```

**Error response format:**
```
✗ Error in <tool_name>: [ErrorType] Human-readable message
```

**Examples from codebase:**

```python
# Good: Specific error with context
SessionNotFoundError(
    f"Session {session_id} not found. Use list_sessions() to see available sessions."
)

# Good: Validation error with suggestion
ValueError(
    f"File '{filename}' path does not exist: {file_path}\n"
    f"Original path: {file_path_str}"
)

# Good: Security validation with explanation
ValueError(
    f"File '{filename}' path resolution failed (possible directory traversal): {file_path_str}"
)
```

### Error Message Categories

**1. Not Found Errors** ✅
```
Session Not Found: session-abc123

Available sessions:
  • session-xyz789 - Botany Farm 2022
  • session-def456 - Sample Project

Create a new session using /initialize.
```

**Strengths:**
- Lists alternatives
- Provides next action
- Clear formatting

**2. Validation Errors** ✅
```
File 'ProjectPlan.pdf' at index 0 must have either 'content_base64' or 'path' field
```

**Strengths:**
- Identifies exact location (index 0)
- States requirement clearly
- No jargon

**3. Workflow Guidance** ⭐ EXCELLENT
```
No review sessions found. You can either:

## Option 1: Provide Project Details (Recommended)
/document-discovery Your Project Name, /absolute/path/to/documents

## Option 2: Use Initialize First
Create a session with /initialize first
```

**Strengths:**
- Multiple resolution paths
- Concrete examples
- Recommendation provided

**Verdict:** Error messages are exemplary. They're informative, actionable, and guide users to success.

---

## 5. Workflow Clarity Analysis

### The 7-Stage Workflow

```
1. Initialize          → Create session + load checklist
2. Document Discovery  → Scan and classify documents
3. Evidence Extraction → Map requirements to evidence
4. Cross-Validation    → Verify consistency
5. Report Generation   → Generate structured report
6. Human Review        → Present flagged items
7. Complete            → Finalize and export
```

### Workflow Entry Points

**Traditional (explicit):**
```bash
/initialize Botany Farm, /path/to/docs
/document-discovery
/evidence-extraction
```

**Quick-start (implicit):**
```bash
start_review(project_name, documents_path)  # Does stages 1-2
```

**Ultra-streamlined (auto-selection):**
```bash
/document-discovery   # Auto-selects most recent session
```

### Workflow Intelligence Features

**1. Auto-Session Selection** ✅
- Prompts automatically use most recent session if no session_id provided
- Clear visual indicator: "ℹ️ Auto-selected most recent session"

**2. Inline Session Creation** ✅
```bash
# Can provide project details to any prompt
/document-discovery Botany Farm, /path/to/docs
# Creates session + runs discovery in one step
```

**3. Progress Tracking** ✅
```json
"workflow_progress": {
    "initialize": "completed",
    "document_discovery": "completed",
    "evidence_extraction": "in_progress"
}
```

**4. Next-Step Guidance** ✅
Every prompt ends with:
```
## Next Step: Evidence Extraction
1. Review the document classifications above
2. Run evidence extraction: /evidence-extraction
3. Or view session status: load_session(session-abc123)
```

### Workflow Confusion Points

**1. Tool vs Prompt choice**
```python
# Both do the same thing:
discover_documents(session_id)  # Tool
/document-discovery             # Prompt
```

**Solution:** Documentation should clarify:
- Tools: For programmatic/API use
- Prompts: For interactive/guided use

**2. Multiple entry points**
```python
# 3 ways to start:
create_session(...)               # Manual
start_review(...)                 # Quick-start
/initialize ...                   # Guided prompt
```

**Solution:** Documentation should recommend primary path:
- **New users:** Use prompts (`/initialize`)
- **API integration:** Use `start_review_from_uploads`
- **Advanced users:** Use individual tools

**Verdict:** Workflow is intuitive with excellent guidance. Minor documentation improvements needed to clarify tool vs prompt usage.

---

## 6. Documentation Quality Analysis

### list_capabilities Prompt

**Current structure:**
```markdown
# Regen Registry Review MCP Server

## Capabilities
- Tools Available (categorized)
- Workflows (7 stages)
- Supported Methodology
- File Types Supported

## Getting Started
- Quick Start (recommended)
- Or use prompts directly
- Manual workflow

## Status
- Phase completion checklist
- Test coverage
- Last updated timestamp
```

**Strengths:**
- Comprehensive coverage
- Clear categorization
- Quick-start emphasis
- Status transparency

**Weaknesses:**

1. **Tool discovery is text-heavy**
   - 25 endpoints listed in prose
   - Hard to scan quickly

2. **No tool signature examples**
   - Shows tool names but not parameters
   - Users must guess or try tools

3. **Missing decision guidance**
   - Doesn't say "Use X for Y scenario"
   - No flowchart or decision tree

4. **Workflow sequence buried**
   - 7-stage process explained but not prominent
   - No visual progression indicator

### Recommendations

**1. Add Quick Reference Table**
```markdown
## Quick Reference

| I want to...                          | Use this                  |
|---------------------------------------|---------------------------|
| Start a new review                    | /initialize               |
| Use uploaded files (API/web)          | start_review_from_uploads |
| Analyze a single requirement          | map_requirement           |
| See all active reviews                | list_sessions             |
| Extract dates from documents          | (automatic in extract_evidence) |
```

**2. Add Tool Signatures**
```markdown
### Session Management

**start_review** (Quick-start)
```
start_review(
  project_name: str,
  documents_path: str,
  methodology: str = "soil-carbon-v1.2.2"
) -> dict
```
Creates session and discovers documents in one step.
```

**3. Add Workflow Visualization**
```markdown
## Workflow Stages

┌─────────────┐
│ 1. Initialize │
└──────┬───────┘
       │ /initialize
┌──────▼────────────┐
│ 2. Discovery      │
└──────┬────────────┘
       │ /document-discovery
┌──────▼────────────┐
│ 3. Evidence       │
└──────┬────────────┘
       │ /evidence-extraction
       ▼
     (etc...)
```

**4. Add Integration Patterns**
```markdown
## Integration Patterns

### Claude Desktop (Interactive)
Use prompts: /initialize, /document-discovery, /evidence-extraction

### REST API / Web App
Use tools: start_review_from_uploads(...), extract_evidence(...)

### Debugging / Development
Use individual tools: create_session(...), discover_documents(...)
```

**Verdict:** Documentation is comprehensive but could be more scannable and task-oriented.

---

## 7. Tool Consolidation Opportunities

### Analyzed Consolidation Candidates

**1. Upload Tools (3 tools)**

Current:
```python
create_session_from_uploads(...)
upload_additional_files(...)
start_review_from_uploads(...)
```

Could consolidate to:
```python
upload_files(
    files: list[dict],
    session_id: str | None = None,  # If None, creates new session
    project_name: str | None = None,
    auto_extract: bool = True
)
```

**Verdict: DO NOT CONSOLIDATE**
- Semantic clarity lost (is this creating or updating?)
- Parameter complexity increases (session_id + project_name both optional)
- Error messages become ambiguous ("session_id required when...")
- Current separation matches user mental models

**2. Quick-Start Tools (2 tools)**

Current:
```python
start_review(project_name, documents_path)
start_review_from_uploads(project_name, files)
```

Could consolidate to:
```python
start_review(
    project_name: str,
    documents_path: str | None = None,
    files: list[dict] | None = None
)
```

**Verdict: DO NOT CONSOLIDATE**
- Parameter validation becomes complex (require one of documents_path OR files)
- Error messages less clear ("you must provide either...")
- Two distinct integration patterns (filesystem vs API)
- Current names clearly signal which to use

**3. Evidence Tools (2 tools)**

Current:
```python
extract_evidence(session_id)         # All requirements
map_requirement(session_id, req_id)  # Single requirement
```

Could consolidate to:
```python
extract_evidence(
    session_id: str,
    requirement_id: str | None = None  # If None, extracts all
)
```

**Verdict: CONSIDER CONSOLIDATION**
- Semantically consistent (both do evidence extraction)
- Parameter is simple (optional requirement_id)
- Reduces tool count by 1
- Risk: Less discoverable (users might not realize single-requirement option exists)

**Recommendation:** Keep separate. Debugging single requirements is common enough to warrant dedicated tool.

**4. Session Listing Tools (2 tools)**

Current:
```python
list_sessions() -> list[dict]           # Production use
list_example_projects() -> dict         # Testing/demos only
```

Could consolidate:
```python
list_sessions(
    include_examples: bool = False
) -> dict
```

**Verdict: REMOVE list_example_projects**
- Only used in testing/demos
- Not part of production workflow
- Examples should be documented in README, not exposed as tool
- Saves 1 tool

---

## 8. Simplification Strategies

### Strategy 1: Reduce Tool Count (Low Priority)

**Changes:**
- Remove: `list_example_projects` (testing tool)
- Result: 15 → 14 tools (7% reduction)

**Impact:**
- Minimal - tool count not a UX problem
- Better achieved through documentation

### Strategy 2: Improve Tool Discovery (High Priority) ⭐

**Changes:**
1. Add "Most Used" section to `list_capabilities`
2. Add tool signatures with examples
3. Add decision flowchart
4. Add integration pattern guidance

**Impact:**
- Significantly improves discoverability
- Reduces trial-and-error
- Guides users to optimal paths

### Strategy 3: Strengthen Defaults (Medium Priority)

**Current defaults analysis:**

```python
# Good defaults
methodology: str = "soil-carbon-v1.2.2"  ✅ Only supported methodology
auto_extract: bool = True                ✅ Most users want this
deduplicate: bool = True                 ✅ Safe and helpful
extract_tables: bool = False             ✅ Performance optimization

# Could improve
start_page: int | None = None            ⚠️ Could default to 1
end_page: int | None = None              ⚠️ Could default to -1 (last page)
```

**Recommendation:**
- Keep current defaults (they're sensible)
- Document page range semantics better

### Strategy 4: Consolidate Error Response Format (Low Priority)

**Current:**
- Tools return: `"✗ Error: [Type] message"` (string)
- Prompts return: TextContent with formatted markdown

**Could standardize:**
```python
{
    "success": false,
    "error": {
        "type": "SessionNotFoundError",
        "message": "Session xyz not found",
        "suggestions": ["Use list_sessions()", "Use /initialize"]
    }
}
```

**Verdict:** Current approach is fine. Markdown errors are human-readable and work well with Claude.

---

## 9. Comparison with MCP Best Practices

### MCP Primitive Hierarchy ✅

**Recommendation:** Prompts > Tools > Resources

**Implementation:**
- ✅ 10 workflow prompts (primary interface)
- ✅ 15 tools (exposed but not emphasized)
- ⚠️ 0 resources (could add checklist templates, but not critical)

**Verdict:** Correctly implements prompt-first design.

### Discovery Prompt ✅

**Requirement:** `/list-capabilities` prompt for feature discovery

**Implementation:**
```python
@mcp.prompt()
def list_capabilities() -> list[TextContent]:
    """List all MCP server capabilities, tools, and workflow prompts"""
```

**Verdict:** Implemented and comprehensive.

### Error Handling ✅

**Requirement:** Graceful degradation, helpful error messages

**Implementation:**
- ✅ Structured error hierarchy (10 error types)
- ✅ Consistent error formatting
- ✅ Actionable suggestions
- ✅ Alternative path guidance

**Verdict:** Exemplary error handling.

### Logging ✅

**Requirement:** Structured logging to stderr

**Implementation:**
```python
logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format,
    stream=sys.stderr,  # CRITICAL: stderr only for MCP protocol
)
```

**Verdict:** Correct implementation.

---

## 10. Real-World Usage Analysis

### From test_user_experience.py

**Test: No sessions exist**
```python
result = await document_discovery_prompt(session_id=None)
# Returns: Helpful guidance with 2 options + examples
```
**Verdict:** ✅ Excellent UX

**Test: Auto-select most recent**
```python
result = await document_discovery_prompt(session_id=None)
# Returns: Discovery results + "Auto-selected most recent session" notice
```
**Verdict:** ✅ Intelligent default

**Test: Invalid session ID**
```python
result = await document_discovery_prompt(session_id="invalid")
# Returns: Error + list of available sessions
```
**Verdict:** ✅ Helpful recovery

### From README.md Examples

**Quick-start workflow:**
```bash
/initialize Botany Farm 2022-2023, /path/to/docs
/document-discovery
/evidence-extraction
```
**Verdict:** ✅ Clear 3-step process

**Tool-based workflow:**
```python
start_review(project_name, documents_path)  # 1 call vs 2 prompts
```
**Verdict:** ✅ Good alternative for API users

---

## Summary of Recommendations

### High Priority (Do This)

1. **Enhance list_capabilities prompt** with:
   - Quick reference table (task → tool mapping)
   - Tool signatures with examples
   - Integration pattern guidance
   - Workflow visualization

2. **Add usage examples** to README:
   - When to use tools vs prompts
   - Integration patterns (Claude Desktop vs API)
   - Common troubleshooting scenarios

3. **Document semantic groupings** explicitly:
   - Session lifecycle tools
   - Document processing tools
   - Evidence analysis tools
   - Upload integration tools

### Medium Priority (Consider)

4. **Remove list_example_projects tool**
   - Move example documentation to README
   - Reduces tool count by 1
   - Simplifies tool discovery

5. **Add "Most Used" section** to list_capabilities:
   - `/initialize` + `/document-discovery` + `/evidence-extraction` (interactive)
   - `start_review_from_uploads` (API integration)
   - `list_sessions` (status check)

### Low Priority (Nice to Have)

6. **Add decision flowchart** to docs/
   - Visual guide for tool selection
   - Integration pattern comparison
   - Troubleshooting decision tree

7. **Create integration templates**:
   - Claude Desktop config example
   - REST API wrapper example
   - ElizaOS integration example

---

## Conclusion

The Registry Review MCP system has **excellent API design fundamentals**:

✅ **Tool count is appropriate** - 15 tools is not excessive for this domain
✅ **Naming is clear and consistent** - Self-documenting, predictable patterns
✅ **Parameters are well-designed** - Simple signatures with sensible defaults
✅ **Error messages are exemplary** - Informative, actionable, guiding
✅ **Workflow is intuitive** - 7-stage process with auto-selection and guidance

⚠️ **Primary improvement opportunity:**
- Tool discovery and selection guidance
- Better documentation of when to use tools vs prompts
- Integration pattern examples

**No major API redesign needed.** Focus on documentation and discoverability rather than consolidation.

**Recommended immediate actions:**
1. Enhance `list_capabilities` prompt (2 hours)
2. Add quick reference table to README (1 hour)
3. Document integration patterns (2 hours)
4. Remove `list_example_projects` tool (30 minutes)

**Total effort:** ~5.5 hours of documentation work, no API breaking changes.
