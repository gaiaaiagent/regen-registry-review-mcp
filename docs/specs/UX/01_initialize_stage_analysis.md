# Stage 1: Initialize - Comprehensive UX Analysis

**Analysis Date:** November 14, 2025
**Analyst:** UX Research Team
**Stage:** Initialize (Stage 1 of 7)
**Status:** Draft for Review

---

## Executive Summary

The Initialize stage is the critical entry point to the Registry Review workflow. It creates the session foundation upon which all subsequent stages depend. This analysis reveals that while the current implementation handles the happy path adequately, it has significant gaps in duplicate detection, state recovery, and user guidance that could lead to confusion, data loss, and workflow abandonment.

### Critical Findings

1. **No duplicate session detection** - Users can create infinite duplicate sessions for the same project
2. **Missing context recovery** - No way to resume interrupted sessions or understand current state
3. **Minimal error guidance** - Path validation errors lack actionable next steps
4. **No breadcrumb trail** - Users have no visibility into what happens after initialization
5. **Implicit assumptions** - System assumes users understand the entire workflow upfront

### Priority Recommendations

**P0 (Immediate)**
- Implement duplicate session detection with resume/replace options
- Add session listing to show existing sessions before creation
- Enhance error messages with specific recovery steps
- Add "what happens next" preview to set expectations

**P1 (Next Sprint)**
- Implement session health checks at initialization
- Add validation for documents_path contents (not just existence)
- Create interactive session recovery for interrupted workflows
- Add session naming/tagging for better organization

**P2 (Future)**
- Session templates for common project types
- Batch initialization for aggregated projects
- Integration with upstream submission systems (Airtable, SharePoint)

---

## 1. User Story Analysis

### Who is Becca?

**Role**: Registry Agent at Regen Network
**Primary Responsibility**: Conducting compliance reviews for carbon credit project registrations
**Current Pain**: Manual review process takes 6-8 hours per project, cannot scale to handle 100+ annual projects from Ecometric alone

**Technical Context**:
- Works with multiple document sources (Google Drive, SharePoint, Airtable)
- Manages reviews across different methodologies (Soil Carbon v1.2.2, etc.)
- Maintains detailed checklists with 20+ requirements per project
- Cross-validates data across multiple document types
- Deals with both individual projects and aggregated batches (up to 70 farms)

**Workflow Context**:
1. Receives project submission notification
2. Downloads/accesses project documents from various sources
3. Organizes documents in standardized folder structure
4. Creates review checklist in Google Sheets
5. Manually transcribes document names and locations
6. Cross-checks requirements against evidence
7. Validates data consistency across documents
8. Generates final review report
9. Provides feedback to project proponents

### Entry Points to Initialize Stage

Becca arrives at `/initialize` through several pathways:

#### **Pathway A: Fresh Project Submission** (Primary)
- **Trigger**: Notification of new project from Ecometric or individual developer
- **Context**: Has project name, knows documents location, ready to start
- **Mental State**: Task-focused, wants quick setup
- **Expectations**: Fast session creation, clear next steps

#### **Pathway B: Returning to Interrupted Work** (Common)
- **Trigger**: Reopening work after days/weeks
- **Context**: May have started session before, unsure of current state
- **Mental State**: Uncertain, needs orientation
- **Expectations**: Ability to find existing session, resume where left off
- **Current Gap**: No way to discover existing sessions from `/initialize`

#### **Pathway C: Managing Multiple Projects** (Frequent)
- **Trigger**: Juggling reviews for multiple projects simultaneously
- **Context**: May have 3-5 active sessions
- **Mental State**: Cognitive load is high, needs organization
- **Expectations**: Clear session identification, easy switching
- **Current Gap**: No session listing, easy to create duplicates

#### **Pathway D: Aggregated Batch Projects** (Special Case)
- **Trigger**: Ecometric batch with 45-70 farm projects
- **Context**: Need to create many sessions with similar structure
- **Mental State**: Efficiency-focused, pattern-seeking
- **Expectations**: Batch operations, templates, bulk actions
- **Current Gap**: Must initialize each session individually

#### **Pathway E: Error Recovery** (Edge Case)
- **Trigger**: Previous initialization failed or was interrupted
- **Context**: Partial state may exist, unclear what's broken
- **Mental State**: Frustrated, needs troubleshooting help
- **Expectations**: Clear error diagnosis, recovery options
- **Current Gap**: No health checking, unclear recovery paths

### Becca's Goals at Initialization

**Immediate Goals**:
- Create a working review session quickly
- Confirm documents are accessible
- Start the review workflow without friction

**Secondary Goals**:
- Avoid creating duplicate sessions
- Understand what will happen next
- Have confidence the setup is correct
- Be able to find this session again later

**Hidden Goals** (not explicitly stated):
- Maintain mental model of all active sessions
- Minimize cognitive switching cost between projects
- Create audit trail for compliance
- Ensure data integrity for on-chain metadata

### Becca's Fears and Pain Points

**Fears**:
- Creating duplicate sessions and losing track of which is current
- Spending time on setup only to discover documents aren't accessible
- Making an error that invalidates hours of work downstream
- Missing a critical step in a complex workflow
- Not being able to find a session later

**Current Pain Points**:
- No visibility into existing sessions
- Path errors are cryptic ("does not exist" - but why?)
- No guidance on what "documents_path" should contain
- No preview of what initialization will do
- No way to validate setup before committing

---

## 2. Happy Path Analysis

### Perfect Scenario Walkthrough

**Preconditions**:
- Becca has organized project documents in `/home/becca/projects/botany-farm-2023/`
- Directory contains all required documents (7 files including PDFs, shapefiles)
- Project name is "Botany Farm 2022-2023"
- Using Soil Carbon v1.2.2 methodology

**Step-by-Step Experience**:

1. **Invocation**
   ```
   /initialize Botany Farm 2022-2023, /home/becca/projects/botany-farm-2023
   ```

   **User Thought**: "This should create my session"

2. **System Response** (Current)
   ```
   ✅ Registry Review Session Initialized

   Session ID: session-a1b2c3d4e5f6
   Project: Botany Farm 2022-2023
   Documents: /home/becca/projects/botany-farm-2023
   Methodology: Soil Carbon v1.2.2
   Created: 2025-11-14T10:30:00Z

   Session Created Successfully
   - Created session state directory
   - Loaded checklist template (23 requirements)
   - Validated document path
   - Initialized workflow tracking

   Next Step: Document Discovery
   /document-discovery
   ```

   **User Thought**: "Great! Now what exactly is in that directory? Should I run discovery now or verify something first?"

3. **What Makes This Delightful**:
   - ✅ Fast execution (< 1 second)
   - ✅ Clear confirmation with session ID
   - ✅ Shows what was initialized
   - ✅ Explicit next step guidance
   - ✅ No errors or warnings

4. **What Could Be Better**:
   - ⚠️ No preview of documents found (user must trust path is right)
   - ⚠️ No indication if session already exists for this project
   - ⚠️ Session ID is opaque (hard to remember or reference)
   - ⚠️ No breadcrumb trail showing full workflow ahead
   - ⚠️ No validation that documents_path contains expected file types

### Confirmation of Success

**Visual Indicators** (Current):
- ✅ Success emoji
- Session ID prominently displayed
- Creation timestamp
- Checklist loaded confirmation (23 requirements)

**Missing Indicators**:
- 📁 Document count preview (e.g., "7 files detected")
- 📋 Quick checklist summary (what categories exist)
- 🔄 Workflow status bar (Initialize ✅ → Discovery ⏸️ → ...)
- 💾 Storage location for session data
- 🔍 Link to view/manage all sessions

### What Happens Next - User Expectations vs. Reality

**Becca Expects**:
1. Run `/document-discovery` immediately
2. System will scan the 7 files
3. Each file will be classified by type
4. Then she'll move to evidence extraction

**Reality Matches** - but only implicitly communicated. She has to trust the process.

**Improvement**: Show the workflow roadmap upfront:
```
Your Next Steps:
1. ✅ Initialize (just completed)
2. ⏭️ Document Discovery - scan and classify 7 documents
3. ⏸️ Evidence Extraction - map 23 requirements to evidence
4. ⏸️ Cross-Validation - check consistency across documents
5. ⏸️ Report Generation - create review report
6. ⏸️ Human Review - review flagged items
7. ⏸️ Complete - finalize review
```

---

## 3. Error Scenarios

### Error 3.1: Document Path Does Not Exist

**User Action**:
```
/initialize Botany Farm 2022-2023, /home/becca/projects/wrong-path
```

**Current Error Message**:
```
❌ Error: Document Path Not Found

The path you provided does not exist:
/home/becca/projects/wrong-path

Please check:
- The path is correct
- The path is absolute (not relative)
- You have permission to access the directory

Try again with a valid path.
```

**Analysis**:

✅ **Strengths**:
- Clear error indicator (❌)
- Shows the problematic path
- Provides checklist of things to verify
- Actionable guidance (try again)

⚠️ **Weaknesses**:
- Doesn't suggest similar paths (typo detection)
- Doesn't offer to list available directories
- No examples of valid paths
- Doesn't check if path is a *file* vs directory
- No guidance on how to find correct path

**Improved Error Message**:
```
❌ Document Path Not Found

The path you provided does not exist:
`/home/becca/projects/wrong-path`

Troubleshooting:

1. **Check for typos** - Did you mean one of these?
   - /home/becca/projects/botany-farm-2023 (similar)
   - /home/becca/projects/willow-creek-2024 (similar)

2. **Verify the path exists**
   Run: `ls -la /home/becca/projects/` to see available directories

3. **Use absolute paths**
   ✅ Correct: /home/becca/projects/botany-farm-2023
   ❌ Wrong: ~/projects/botany-farm-2023 (use full path)
   ❌ Wrong: projects/botany-farm-2023 (relative path)

4. **Check permissions**
   Run: `ls -la /home/becca/projects/wrong-path` to verify access

Examples of valid paths:
- /home/becca/projects/botany-farm-2023
- /mnt/sharepoint/ecometric/2024/C06-4997

Try again with a corrected path.
```

**Recovery Path**:
- User fixes typo and re-runs
- Success on second attempt
- **Time Lost**: 1-2 minutes

### Error 3.2: Path is a File, Not Directory

**User Action**:
```
/initialize Botany Farm 2022-2023, /home/becca/projects/project-plan.pdf
```

**Current Error Message**:
```
❌ Error: Document Path Not Found

The path you provided does not exist:
/home/becca/projects/project-plan.pdf

Please check:
- The path is correct
- The path is absolute (not relative)
- You have permission to access the directory

Try again with a valid path.
```

**Problem**: Message says "does not exist" but file DOES exist - it's just not a directory. Confusing!

**Actual Error** (from Pydantic validation):
```python
ValueError: Path is not a directory: /home/becca/projects/project-plan.pdf
```

**Issue**: This error is caught in schemas.py but returned as generic FileNotFoundError.

**Improved Error Message**:
```
❌ Invalid Document Path: File Instead of Directory

You provided a file path, but we need a directory:
`/home/becca/projects/project-plan.pdf`

The documents path should point to a *folder* containing all project documents, not a single file.

Example:
❌ Wrong: /home/becca/projects/project-plan.pdf (single file)
✅ Correct: /home/becca/projects/botany-farm-2023/ (directory with multiple files)

Your directory should contain files like:
- Project plans (PDF)
- Baseline reports (PDF)
- Land tenure docs (PDF)
- GIS files (SHP, GeoJSON)
- Monitoring reports (PDF)

Try again with the directory containing all project files.
```

**Recovery Path**:
- User navigates up to parent directory
- Provides correct directory path
- **Time Lost**: 2-3 minutes

### Error 3.3: Empty Directory

**User Action**:
```
/initialize Botany Farm 2022-2023, /home/becca/projects/empty-folder
```

**Current Behavior**: ✅ Session created successfully!

**Problem**: No documents exist, but initialization succeeds. User discovers this only at document discovery stage.

**Better Approach**: Validate directory has files.

**Improved Validation**:
```python
@field_validator("documents_path")
@classmethod
def validate_path_exists(cls, value: str) -> str:
    path = Path(value)
    if not path.exists():
        raise ValueError(f"Path does not exist: {value}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {value}")

    # Check if directory has any files
    files = list(path.glob("**/*"))
    if not any(f.is_file() for f in files):
        raise ValueError(
            f"Directory is empty: {value}\n\n"
            "Your documents directory should contain project files like:\n"
            "- PDF documents (project plans, reports)\n"
            "- GIS files (shapefiles, GeoJSON)\n"
            "- Spreadsheets (monitoring data)\n\n"
            "Please add documents before initializing."
        )

    return str(path.absolute())
```

**Warning Message** (if few files):
```
⚠️ Warning: Few Documents Detected

Your documents directory only contains 2 files:
- project-plan.pdf
- notes.txt

Typical projects have 5-10 documents including:
- Project plan or design document
- Land tenure documentation
- Baseline report
- GIS files (shapefiles, boundaries)
- Monitoring data

Do you want to:
1. Continue anyway (you can add documents later)
2. Cancel and add more documents first

Choose: [1/2]
```

**Recovery Path**:
- User adds documents
- Re-runs initialization
- **Time Lost**: 5-10 minutes

### Error 3.4: Permission Denied

**User Action**:
```
/initialize Botany Farm 2022-2023, /root/restricted/projects
```

**Current Error Message**:
```
❌ Error Creating Session

An error occurred: [Errno 13] Permission denied: '/root/restricted/projects'

Please check your inputs and try again.
```

**Analysis**:

⚠️ **Weaknesses**:
- Generic error message
- Shows raw Python exception (not user-friendly)
- No troubleshooting guidance
- Doesn't explain *why* permissions matter

**Improved Error Message**:
```
❌ Permission Denied: Cannot Access Directory

You don't have permission to access:
`/root/restricted/projects`

This usually means:
1. **Directory is owned by another user**
   The directory may be owned by 'root' or another user.

2. **Insufficient read permissions**
   You need read and list permissions for the Registry Review Agent to scan documents.

Solutions:

1. **Use a directory you own**
   Recommended: /home/becca/projects/

2. **Request access from directory owner**
   If this is a shared directory, ask the owner to grant you read access.

3. **Copy files to your workspace**
   Copy project files to a location you control:
   ```
   cp -r /root/restricted/projects /home/becca/projects/botany-farm-2023
   ```

Try again with a directory you have permission to access.
```

**Recovery Path**:
- User copies files to accessible location
- Re-runs with correct path
- **Time Lost**: 5-15 minutes (depending on file copy size)

### Error 3.5: Duplicate Session (Critical Gap)

**User Action**:
```
# First time
/initialize Botany Farm 2022-2023, /home/becca/projects/botany-farm-2023

# Later, user forgets and runs again
/initialize Botany Farm 2022-2023, /home/becca/projects/botany-farm-2023
```

**Current Behavior**: ✅ Creates second session with different session_id!

**Problem**: Now Becca has TWO sessions for the same project:
- `session-a1b2c3d4e5f6` (original, may have progress)
- `session-x9y8z7w6v5u4` (duplicate, empty)

**Impact**:
- Data fragmentation
- Confusion about which session to use
- Lost work if she proceeds with wrong session
- No way to merge or reconcile

**Ideal Behavior**: Detect duplicate and offer options.

**Improved Flow**:

```
⚠️ Duplicate Session Detected

A session already exists for this project:

**Existing Session**
Session ID: session-a1b2c3d4e5f6
Created: 2025-11-13 10:30:00 (1 day ago)
Status: in_progress
Progress:
  ✅ Initialize
  ✅ Document Discovery (7 documents)
  🔄 Evidence Extraction (in progress, 15/23 requirements)
  ⏸️ Cross-Validation
  ⏸️ Report Generation

What would you like to do?

1. **Resume existing session** (recommended)
   Continue where you left off with session-a1b2c3d4e5f6

2. **Create new session anyway**
   Start fresh (existing session will remain)
   Use this if you're reviewing different documents for the same project.

3. **Replace existing session**
   Delete session-a1b2c3d4e5f6 and create new one
   ⚠️ Warning: This will delete all progress from existing session!

4. **View existing session details**
   Show full status and findings before deciding

Choose: [1/2/3/4]
```

**Detection Logic**:
```python
async def check_for_duplicates(
    project_name: str,
    documents_path: str
) -> list[dict[str, Any]]:
    """Check if session exists for this project+path combination."""
    all_sessions = await list_sessions()

    duplicates = [
        s for s in all_sessions
        if s["project_name"] == project_name
        and s["documents_path"] == documents_path
    ]

    return duplicates
```

**Recovery Path**:
- User chooses option 1 (resume)
- Continues with existing session
- **Time Saved**: Could have lost hours of work!

### Error 3.6: Invalid Methodology

**User Action**:
```
/initialize Botany Farm 2022-2023, /home/becca/projects/botany-farm-2023
# Using default methodology: soil-carbon-v1.2.2
```

**Scenario**: Project actually uses different methodology (e.g., biodiversity-v2.0).

**Current Behavior**: Session created with wrong methodology.

**Problem**: Wrong checklist loaded (23 requirements for soil carbon, but project needs biodiversity requirements). User discovers this only after evidence extraction fails.

**Better Approach**: Validate methodology or detect from documents.

**Improved Flow**:

```
⚠️ Methodology Confirmation Required

You're initializing with methodology: Soil Carbon v1.2.2 (default)

This will load a checklist with 23 requirements for carbon farming projects.

Is this correct for your project?

1. ✅ Yes, use Soil Carbon v1.2.2
2. ❌ No, I need a different methodology

If "No", available methodologies:
- biodiversity-v2.0 (Biodiversity Monitoring)
- grazing-v1.0 (Grassland Carbon)
- agroforestry-v1.5 (Agroforestry Carbon)

Choose: [1/2]
```

**Even Better**: Auto-detect from documents.

```python
async def detect_methodology(documents_path: str) -> str | None:
    """Attempt to detect methodology from project documents."""
    # Look for project plan
    for pdf in Path(documents_path).glob("**/*.pdf"):
        text = extract_pdf_text(pdf, pages=[0, 1])  # First 2 pages

        if "methodology: soil carbon" in text.lower():
            return "soil-carbon-v1.2.2"
        elif "methodology: biodiversity" in text.lower():
            return "biodiversity-v2.0"
        # ... etc

    return None  # Could not detect
```

**Recovery Path**:
- User selects correct methodology
- Session created with right checklist
- **Time Saved**: Hours of rework

### Error 3.7: Corrupted Session State

**Scenario**: User created session, then session.json file got corrupted (disk error, interrupted write).

**User Action**:
```
# Try to resume session later
/document-discovery  # Auto-selects most recent session
```

**Current Behavior**: JSON parse error, cryptic exception.

**Improved Error Handling**:

```
❌ Session Data Corrupted

Session session-a1b2c3d4e5f6 has corrupted data and cannot be loaded.

Error: Invalid JSON in session.json
Location: /home/becca/.registry-review/sessions/session-a1b2c3d4e5f6/session.json

Recovery Options:

1. **Restore from backup** (if available)
   Check: /home/becca/.registry-review/sessions/session-a1b2c3d4e5f6/backups/

2. **Delete corrupted session**
   Run: /delete-session session-a1b2c3d4e5f6
   Then create new session with /initialize

3. **Manual repair** (advanced)
   Edit session.json to fix JSON syntax errors

4. **View raw data**
   Show corrupted data for debugging

Choose: [1/2/3/4]
```

**Prevention**: Implement atomic writes with backups.

```python
def write_json(self, filename: str, data: dict) -> None:
    """Write JSON with atomic operation and backup."""
    filepath = self.session_dir / filename

    # Create backup of existing file
    if filepath.exists():
        backup_dir = self.session_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{filename}.{timestamp}.bak"
        shutil.copy(filepath, backup_path)

    # Write to temporary file first
    temp_path = filepath.with_suffix(".tmp")
    with open(temp_path, "w") as f:
        json.dump(data, f, indent=2)

    # Atomic rename
    temp_path.replace(filepath)
```

**Recovery Path**:
- User selects option 1 (restore)
- System restores from latest backup
- **Time Lost**: 2-5 minutes

---

## 4. Edge Cases

### Edge 4.1: Re-running Initialize After Completion

**Scenario**: User completed entire workflow, then runs `/initialize` again for same project.

**Current Behavior**: Creates new duplicate session.

**Better Behavior**: Recognize completed session and offer options.

**Improved Flow**:

```
⚠️ Completed Session Found

You already completed a review for this project:

**Completed Session**
Session ID: session-a1b2c3d4e5f6
Created: 2025-11-10 09:00:00 (4 days ago)
Completed: 2025-11-10 15:30:00 (4 days ago)
Status: completed

Final Results:
- 7 documents reviewed
- 21/23 requirements covered (91%)
- 2 requirements flagged for follow-up
- Report generated: botany-farm-2022-2023-review.md

What would you like to do?

1. **View completed session**
   Review findings and reports from completed session

2. **Create new session** (re-review)
   Start a fresh review of the same project
   Use this if documents have changed or you need to re-review.

3. **Reopen completed session**
   Continue working on completed session (add notes, regenerate reports)

Choose: [1/2/3]
```

**Use Case**: Documents updated after initial review (proponent made corrections).

**Recovery Path**:
- User chooses option 2 (new session)
- Creates fresh session with updated documents
- **Outcome**: Clean separation between review iterations

### Edge 4.2: Very Long Project Name

**User Action**:
```
/initialize The Regenerative Agricultural Carbon Sequestration Initiative for Sustainable Soil Health Management in the Greater Willamette Valley Region 2023-2024 Phase 1, /home/becca/projects/long-name
```

**Current Validation**: Max 200 characters (schema constraint).

**Problem**: Long names create issues:
- Hard to display in UI
- Truncated in reports
- Difficult to reference verbally
- Creates long file paths

**Improved Handling**:

```
⚠️ Project Name Too Long

Your project name is 185 characters:
"The Regenerative Agricultural Carbon Sequestration Initiative for Sustainable Soil Health Management in the Greater Willamette Valley Region 2023-2024 Phase 1"

Maximum length: 100 characters (recommended for readability)

Suggestions:
1. "Willamette Valley Regen Ag Initiative 2023-2024 Phase 1" (58 chars)
2. "Greater Willamette Soil Carbon Project Phase 1" (46 chars)
3. "Willamette Carbon Sequestration 2023-24" (41 chars)

You can include the full name in project documents.
The project name here is for session organization and reports.

Would you like to:
1. Use suggested name #1
2. Use suggested name #2
3. Use suggested name #3
4. Enter a custom shorter name
5. Continue with full name anyway

Choose: [1/2/3/4/5]
```

**Recovery Path**:
- User selects shorter name
- Session created with readable identifier
- **Outcome**: Better UX throughout workflow

### Edge 4.3: Special Characters in Project Name

**User Action**:
```
/initialize O'Brien Farm / Cattle Ranch 2023, /home/becca/projects/obrien-farm
```

**Problem**: Special characters in names:
- Apostrophes: `O'Brien`
- Slashes: `/`
- Ampersands: `&`
- Unicode: `Müller Farm`

**Current Behavior**: Likely works (Python strings handle Unicode), but may cause issues in:
- File paths (slashes are directory separators)
- Shell commands
- URL encoding
- Report generation

**Improved Validation**:

```python
@field_validator("project_name")
@classmethod
def validate_project_name(cls, value: str) -> str:
    """Validate project name for filesystem safety."""
    # Check for problematic characters
    problematic = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']

    found = [char for char in problematic if char in value]

    if found:
        raise ValueError(
            f"Project name contains characters that may cause issues: {', '.join(found)}\n\n"
            f"Please avoid: / \\ : * ? \" < > |\n\n"
            f"Suggested alternatives:\n"
            f"- Use '-' instead of '/'\n"
            f"- Use 'and' instead of '&'\n"
            f"- Spell out special characters\n\n"
            f"Example: Instead of \"O'Brien Farm / Cattle Ranch\"\n"
            f"         Use: \"O'Brien Farm - Cattle Ranch\""
        )

    return value
```

**Recovery Path**:
- User modifies name to remove special chars
- Session created successfully
- **Time Lost**: 1 minute

### Edge 4.4: Documents Path with Symbolic Links

**User Action**:
```
/initialize Botany Farm 2022-2023, /home/becca/projects/current-project
# where current-project -> /mnt/sharepoint/ecometric/2024/C06-4997
```

**Current Behavior**: `Path.absolute()` resolves symlink to real path.

**Issue**: User sees different path than they provided.

**Response**:
```
Session ID: session-a1b2c3d4e5f6
Project: Botany Farm 2022-2023
Documents: /mnt/sharepoint/ecometric/2024/C06-4997  ← Wait, I said current-project!
```

**Improved Handling**:

```
ℹ️ Symbolic Link Detected

You provided: /home/becca/projects/current-project
This is a symbolic link to: /mnt/sharepoint/ecometric/2024/C06-4997

We'll use the real path for reliability.

⚠️ Note: If the symbolic link changes later, this session will still point to:
/mnt/sharepoint/ecometric/2024/C06-4997

Continue with resolved path? [Y/n]
```

**Recovery Path**:
- User confirms or cancels
- Session created with clear understanding
- **Outcome**: No surprise later when path differs

### Edge 4.5: Network-Mounted Documents Path

**User Action**:
```
/initialize Botany Farm 2022-2023, /mnt/sharepoint/ecometric/2024/C06-4997
```

**Issue**: Network mounts can be:
- Temporarily unavailable
- Slow to access
- Disconnected mid-workflow

**Improved Validation**:

```
⚠️ Network Path Detected

Your documents path appears to be on a network mount:
/mnt/sharepoint/ecometric/2024/C06-4997

This may cause issues:
- Slower document processing
- Connection errors if network is interrupted
- Files may change if others edit them

Recommendations:

1. **Copy files locally** (recommended for reliability)
   ```
   cp -r /mnt/sharepoint/ecometric/2024/C06-4997 /home/becca/projects/local-copy
   ```
   Then use: /home/becca/projects/local-copy

2. **Continue with network path** (ensure stable connection)

Choose: [1/2]
```

**Recovery Path**:
- User copies files locally
- Uses local path for session
- **Outcome**: Faster, more reliable processing

### Edge 4.6: Multiple Projects with Same Name

**Scenario**: Ecometric manages "Willow Creek Farm" in both Oregon and California.

**User Action**:
```
# First project
/initialize Willow Creek Farm 2023, /home/becca/projects/willow-creek-OR

# Second project
/initialize Willow Creek Farm 2023, /home/becca/projects/willow-creek-CA
```

**Current Behavior**: Creates two sessions with same project name but different paths.

**Issue**: Hard to distinguish in session lists.

**Improved Handling**:

```
ℹ️ Similar Project Name Detected

Another session exists with the same project name:

**Existing Session**
Project: Willow Creek Farm 2023
Documents: /home/becca/projects/willow-creek-OR
Session: session-a1b2c3d4e5f6

**New Session**
Project: Willow Creek Farm 2023
Documents: /home/becca/projects/willow-creek-CA

These appear to be different projects with the same name.

Suggestions to distinguish them:
1. "Willow Creek Farm 2023 - Oregon"
2. "Willow Creek Farm 2023 - California"
3. "Willow Creek Farm OR 2023"
4. "Willow Creek Farm CA 2023"

Would you like to:
1. Rename new project to suggestion #1
2. Rename new project to suggestion #2
3. Enter custom name
4. Continue with same name

Choose: [1/2/3/4]
```

**Recovery Path**:
- User adds distinguishing detail to name
- Both sessions clearly identifiable
- **Outcome**: No confusion later

### Edge 4.7: Concurrent Session Creation

**Scenario**: Two instances of MCP running simultaneously, both try to create session at exact same time.

**Issue**: Race condition on session ID generation.

**Current Risk**: Low (UUID collision is astronomically rare).

**Improved Safety**:

```python
def generate_session_id() -> str:
    """Generate unique session ID with collision detection."""
    max_attempts = 10

    for attempt in range(max_attempts):
        session_id = f"session-{uuid.uuid4().hex[:12]}"

        # Check if already exists
        session_dir = settings.sessions_dir / session_id
        if not session_dir.exists():
            return session_id

    # If we get here, something is very wrong
    raise RuntimeError(
        f"Failed to generate unique session ID after {max_attempts} attempts. "
        "This should never happen. Please report this bug."
    )
```

**Recovery Path**:
- System retries with new ID
- Session created successfully
- **Outcome**: No collision

---

## 5. State Management Deep Dive

### Idempotency Analysis

**Question**: Can `/initialize` run multiple times safely?

**Current Answer**: No - creates duplicate sessions.

**Should It Be Idempotent?**

**Arguments For**:
- Safer UX (re-running doesn't create duplicates)
- Follows principle of least surprise
- Easier error recovery

**Arguments Against**:
- User might intentionally want multiple sessions for same project
- Re-review scenarios (documents updated)
- A/B testing different approaches

**Recommendation**: Implement **smart idempotency**:
- Detect duplicates
- Offer to resume vs. create new
- Let user choose intentionally

**Implementation**:

```python
async def initialize_prompt(
    project_name: str | None = None,
    documents_path: str | None = None
) -> list[TextContent]:
    """Initialize with duplicate detection."""

    # ... validation ...

    # Check for duplicates
    duplicates = await check_for_duplicates(project_name, documents_path)

    if duplicates:
        # Most recent session
        latest = duplicates[0]

        return [TextContent(
            type="text",
            text=format_duplicate_warning(latest, project_name, documents_path)
        )]

    # No duplicates, proceed with creation
    result = await session_tools.create_session(...)
    # ...
```

### Out-of-Order Execution

**Scenario**: User runs prompts out of sequence.

**Example**:
```
/initialize ...  # Create session
/evidence-extraction  # Skip document discovery!
```

**Current Behavior**: Evidence extraction checks for completed document discovery and fails with error.

**Question**: Should `/initialize` prevent this?

**Answer**: No. Initialize creates foundation. Each downstream stage validates its own prerequisites.

**Division of Responsibility**:
- **Initialize**: Create session, validate path, load checklist
- **Each Stage**: Validate prerequisites for that stage

**Initialize Should NOT**:
- Prevent running other prompts
- Lock session state
- Enforce workflow order

**Initialize SHOULD**:
- Create valid, complete session structure
- Set stage to "completed" in workflow_progress
- Provide guidance on next step

### Incomplete Sessions

**Scenario**: User runs `/initialize` then stops (interruption, crash, etc.).

**Current State**:
```json
{
  "session_id": "session-a1b2c3d4e5f6",
  "status": "initialized",
  "workflow_progress": {
    "initialize": "completed",
    "document_discovery": "pending",
    ...
  }
}
```

**Question**: Is this recoverable?

**Answer**: Yes, fully recoverable.

**What Can Be Done**:
1. Resume with `/document-discovery`
2. View session with `/status` (future)
3. Delete and start over

**Initialize Should Support**:
- Partial completion (already does)
- Session listing to find orphaned sessions
- Health check to validate session structure

**Health Check Implementation**:

```python
async def validate_session_health(session_id: str) -> dict[str, Any]:
    """Validate session structure and state."""
    state_manager = StateManager(session_id)

    issues = []

    # Check required files exist
    if not (state_manager.session_dir / "session.json").exists():
        issues.append("Missing session.json")
    if not (state_manager.session_dir / "documents.json").exists():
        issues.append("Missing documents.json")
    if not (state_manager.session_dir / "findings.json").exists():
        issues.append("Missing findings.json")

    # Check session.json is valid JSON
    try:
        session_data = state_manager.read_json("session.json")
    except json.JSONDecodeError:
        issues.append("Corrupted session.json (invalid JSON)")
        session_data = None

    # Check required fields
    if session_data:
        required_fields = ["session_id", "created_at", "status", "project_metadata"]
        for field in required_fields:
            if field not in session_data:
                issues.append(f"Missing required field: {field}")

    # Check documents_path still exists
    if session_data:
        docs_path = session_data.get("project_metadata", {}).get("documents_path")
        if docs_path and not Path(docs_path).exists():
            issues.append(f"Documents path no longer exists: {docs_path}")

    return {
        "session_id": session_id,
        "healthy": len(issues) == 0,
        "issues": issues,
    }
```

### Concurrency Handling

**Scenario**: User runs `/document-discovery` in one terminal while `/initialize` runs in another.

**Current Risk**: Race condition on file writes.

**Mitigation**: File locking in StateManager.

**Verify Lock Works for Initialize**:

```python
# In session_tools.py create_session()
state_manager = StateManager(session_id)

# These use locks
state_manager.write_json("session.json", session.model_dump(mode="json"))  # ✅ Locked
state_manager.write_json("documents.json", {"documents": []})  # ✅ Locked
state_manager.write_json("findings.json", {"findings": []})  # ✅ Locked
```

**Conclusion**: Initialize is already concurrency-safe via StateManager locks.

---

## 6. UX Quality Assessment

### Voice and Tone

**Current Tone**: Professional, technical, informative.

**Examples**:
- ✅ "Registry Review Session Initialized"
- ✅ "Your review session is ready"
- ✅ "The system has: ..."

**Strengths**:
- Clear and direct
- Appropriate formality for professional tool
- Confidence-building (✅ checkmarks)

**Opportunities**:
- Add warmth: "Welcome! Let's start your review."
- Show empathy: "We'll help you through each step."
- Celebrate progress: "Great! Your session is ready."

**Tone Recommendations**:

**Current**:
```
# ✅ Registry Review Session Initialized

**Session ID:** `session-a1b2c3d4e5f6`
**Project:** Botany Farm 2022-2023
...
```

**Enhanced**:
```
# Welcome! Your Review Session is Ready ✅

Great news, Becca! We've created your session and loaded everything you need to review Botany Farm 2022-2023.

**Session Details**
Session ID: session-a1b2c3d4e5f6
Project: Botany Farm 2022-2023
Documents: /home/becca/projects/botany-farm-2023
Methodology: Soil Carbon v1.2.2
Created: Just now (2025-11-14 10:30)

**What We Set Up**
✅ Session workspace created
✅ Checklist loaded (23 requirements for Soil Carbon projects)
✅ Document path validated
✅ Workflow tracking initialized

**What's Next**
Let's discover and classify your project documents:
`/document-discovery`

Need help? Run `/help` or view the workflow guide.
```

**Balance**: Professional but personable. Becca is an expert, not a novice, so avoid being overly tutorial.

### Error Message Quality

**Current Error Messages**: Good foundation, but can be enhanced.

**Quality Rubric**:
1. **Clear Problem Statement** - What went wrong?
2. **Root Cause** - Why did it happen?
3. **Impact** - What does this mean for the user?
4. **Recovery Steps** - How to fix it?
5. **Prevention** - How to avoid it next time?

**Example: Path Not Found**

Current (scores 3/5):
```
❌ Error: Document Path Not Found

The path you provided does not exist:
/home/becca/projects/wrong-path

Please check:
- The path is correct
- The path is absolute (not relative)
- You have permission to access the directory

Try again with a valid path.
```

Scoring:
- ✅ Clear problem: "Path not found"
- ✅ Shows problematic path
- ⚠️ Root cause: Implied but not stated (typo? wrong directory?)
- ⚠️ Impact: Not stated (can't create session)
- ✅ Recovery: "Try again"
- ❌ Prevention: Not covered

Enhanced (scores 5/5):
```
❌ Cannot Create Session: Document Path Not Found

**Problem**: The directory you specified doesn't exist or isn't accessible.

**Path Provided**: `/home/becca/projects/wrong-path`

**Why This Happened**:
- The path may have a typo
- The directory may have been moved or renamed
- You may not have permission to access it

**Impact**: We can't create your review session without a valid documents folder.

**How to Fix**:

1. Check for typos - Did you mean:
   - /home/becca/projects/botany-farm-2023
   - /home/becca/projects/willow-creek-2024

2. Verify the directory exists:
   ```
   ls -la /home/becca/projects/
   ```

3. Use an absolute path (starting with /)
   ✅ Good: /home/becca/projects/my-project
   ❌ Bad: ~/projects/my-project
   ❌ Bad: projects/my-project

4. Check permissions:
   ```
   ls -la /home/becca/projects/wrong-path
   ```

**Prevention**:
- Copy the path from your file manager
- Use tab-completion when typing paths
- Verify the directory contains documents before initializing

**Ready to try again?**
Run: `/initialize Project Name, /correct/path/to/documents`
```

### Progress Indicators

**Current**: None during initialization (it's fast enough).

**After Initialization**: Shows workflow_progress in session state, but not visible to user.

**Recommendation**: Add workflow roadmap to success message.

**Implementation**:

```python
def format_workflow_roadmap(workflow_progress: WorkflowProgress) -> str:
    """Format visual workflow progress indicator."""

    stages = [
        ("Initialize", workflow_progress.initialize),
        ("Document Discovery", workflow_progress.document_discovery),
        ("Evidence Extraction", workflow_progress.evidence_extraction),
        ("Cross-Validation", workflow_progress.cross_validation),
        ("Report Generation", workflow_progress.report_generation),
        ("Human Review", workflow_progress.human_review),
        ("Complete", workflow_progress.complete),
    ]

    lines = ["## Your Review Workflow\n"]

    for i, (name, status) in enumerate(stages, 1):
        if status == "completed":
            icon = "✅"
        elif status == "in_progress":
            icon = "🔄"
        else:
            icon = "⏸️"

        lines.append(f"{i}. {icon} {name}")

    return "\n".join(lines)
```

**Result**:
```
## Your Review Workflow

1. ✅ Initialize
2. ⏸️ Document Discovery
3. ⏸️ Evidence Extraction
4. ⏸️ Cross-Validation
5. ⏸️ Report Generation
6. ⏸️ Human Review
7. ⏸️ Complete
```

### Next Step Guidance

**Current**: Good - shows next prompt.

**Could Be Better**: Explain what the next step does.

**Enhanced**:

```
## Next Step: Document Discovery

Run: `/document-discovery`

**What This Will Do**:
- Scan all files in /home/becca/projects/botany-farm-2023
- Identify document types (project plan, baseline report, GIS files, etc.)
- Extract metadata from each document
- Generate document inventory

**Expected Time**: 10-30 seconds (depending on number of files)

**Ready?** Run `/document-discovery` whenever you're ready.
```

### Help and Documentation

**Current**: References exist in ROADMAP.md and specs, but not linked from prompts.

**Gap**: No `/help` command, no inline documentation links.

**Recommendation**: Add help links and `/help` prompt.

**Implementation**:

```
## Need Help?

- **Workflow Guide**: /help workflow
- **Troubleshooting**: /help troubleshooting
- **All Sessions**: /list-sessions
- **Documentation**: https://docs.regen.network/registry-review

**Questions?** Reach out to the Regen Network team.
```

### Recovery Paths

**Current Recovery Options**:
- Delete session: `/delete-session session-id`
- Create new session: Re-run `/initialize`

**Missing Recovery Options**:
- Resume session: No discovery mechanism
- Repair session: No health check or repair tools
- Backup/restore: No backup mechanism (though StateManager supports it)

**Recommendation**: Add session management prompts:
- `/list-sessions` - Show all sessions
- `/session-status <session-id>` - Health check for specific session
- `/resume-session <session-id>` - Set as active session

---

## 7. Integration Points

### How Initialize Hands Off to Stage 2 (Document Discovery)

**What Initialize Provides**:

Session structure:
```json
{
  "session_id": "session-a1b2c3d4e5f6",
  "status": "initialized",
  "project_metadata": {
    "project_name": "Botany Farm 2022-2023",
    "documents_path": "/home/becca/projects/botany-farm-2023",
    "methodology": "soil-carbon-v1.2.2"
  },
  "workflow_progress": {
    "initialize": "completed",
    "document_discovery": "pending"
  }
}
```

Files created:
- `session.json` (full session state)
- `documents.json` (empty: `{"documents": []}`)
- `findings.json` (empty: `{"findings": []}`)

**What Document Discovery Expects**:
- Valid session_id
- Existing documents_path
- initialize status = "completed"
- documents.json exists (will be overwritten)

**Contract Verification**:

```python
# In document_discovery.py
async def document_discovery_prompt(session_id: str | None = None):
    """Run document discovery."""

    # Verify session exists
    session = await load_session(session_id)

    # Verify initialize completed
    if session["workflow_progress"]["initialize"] != "completed":
        return error_message(
            "Initialize stage must be completed first",
            "Run /initialize to create a session"
        )

    # Verify documents_path exists
    docs_path = session["project_metadata"]["documents_path"]
    if not Path(docs_path).exists():
        return error_message(
            f"Documents path no longer exists: {docs_path}",
            "The directory may have been moved or deleted. "
            "Update the session or create a new one."
        )

    # Proceed with discovery
    # ...
```

**Handoff Quality**: ✅ Good - clear contract, validated.

### State Guarantees

**What Initialize Guarantees to Downstream Stages**:

1. **Session Structure**:
   - session.json exists and is valid
   - Contains all required fields
   - Follows Session schema

2. **Documents Path**:
   - Exists at time of initialization
   - Is a directory (not a file)
   - Is absolute path

3. **Methodology**:
   - Valid methodology identifier
   - Checklist exists for this methodology

4. **Workflow State**:
   - initialize = "completed"
   - All other stages = "pending"

5. **Empty Structures**:
   - documents.json created
   - findings.json created

**What Initialize Does NOT Guarantee**:

1. **Documents Path Contents**:
   - May be empty (not validated)
   - May have wrong file types
   - Files may be corrupted

2. **Documents Path Stability**:
   - Path may be deleted after initialization
   - Files may change
   - Network paths may disconnect

3. **Methodology Match**:
   - May not match actual project methodology
   - User may have selected wrong methodology

**Recommendation**: Add optional validation flags.

```python
async def create_session(
    project_name: str,
    documents_path: str,
    methodology: str = "soil-carbon-v1.2.2",
    validate_contents: bool = False,  # NEW: Optional deeper validation
    # ...
) -> dict[str, Any]:
    """Create session with optional validation."""

    # ... existing validation ...

    if validate_contents:
        # Check directory has files
        files = list(Path(documents_path).glob("**/*"))
        if not any(f.is_file() for f in files):
            raise ValueError("Documents directory is empty")

        # Check for expected file types
        pdf_count = len(list(Path(documents_path).glob("**/*.pdf")))
        if pdf_count == 0:
            raise ValueError(
                "No PDF documents found. Typical projects have multiple PDFs "
                "(project plan, baseline report, etc.)"
            )

    # ... create session ...
```

### Assumptions About Downstream Stages

**Initialize Assumes**:

1. **Document Discovery Will**:
   - Read documents_path
   - Classify documents
   - Populate documents.json

2. **Evidence Extraction Will**:
   - Load checklist for methodology
   - Read documents
   - Populate findings.json

3. **Cross-Validation Will**:
   - Read findings
   - Check consistency
   - Flag issues

**These Are Safe Assumptions** - documented in workflow.

**Initialize Does NOT Assume**:
- Stages run in order (they validate their own prerequisites)
- Session will be completed
- Documents won't change

### Data Dependencies

**Initialize Creates**:
- session.json (read by all stages)
- documents.json (overwritten by discovery, read by extraction)
- findings.json (overwritten by extraction, read by validation)

**Initialize Reads**:
- Checklist file (e.g., soil-carbon-v1.2.2.json)

**Dependency Graph**:
```
Initialize
  ├─ Creates: session.json
  ├─ Creates: documents.json (empty)
  ├─ Creates: findings.json (empty)
  └─ Reads: data/checklists/{methodology}.json

Document Discovery
  ├─ Reads: session.json
  └─ Writes: documents.json

Evidence Extraction
  ├─ Reads: session.json
  ├─ Reads: documents.json
  ├─ Reads: data/checklists/{methodology}.json
  └─ Writes: findings.json

...
```

**No Circular Dependencies**: ✅ Good

---

## 8. User Journey Maps

### Journey 1: First-Time User (Happy Path)

**Context**: Becca's first time using the Registry Review MCP for a new Ecometric project.

**Mental State Timeline**:

**Before**:
- Uncertain about new tool
- Accustomed to manual process
- Eager to save time but skeptical

**During Initialization**:
- Focused on getting setup right
- Watching for errors
- Building mental model of workflow

**After Initialization**:
- Confidence building
- Relieved it was easy
- Ready to proceed

**Touchpoints**:

1. **Discovery**: Hears about new MCP from team
   - Emotion: Curious, cautious
   - Question: "Will this really help?"

2. **Setup**: Installs MCP, configures in Claude Code
   - Emotion: Technical, focused
   - Question: "Is it working?"

3. **First Use**: Runs `/initialize`
   - Emotion: Tentative, careful
   - Question: "Am I doing this right?"

4. **Success Response**: Sees session created message
   - Emotion: Pleased, validated
   - Question: "What's next?"

5. **Next Step**: Reads guidance, runs `/document-discovery`
   - Emotion: Confident, engaged
   - Question: "How fast will this be?"

**Pain Points**:
- No example to follow (needs quick-start guide)
- Unsure of path format (absolute? relative?)
- Doesn't know what methodology to use (needs list)

**Delighters**:
- Fast execution (< 1 second)
- Clear success message
- Explicit next step

**Journey Optimization**:
- Add `/quickstart` command with example
- Show methodology list when none provided
- Validate path format and suggest corrections

### Journey 2: Returning User (Session Recovery)

**Context**: Becca started a review yesterday, interrupted, now returning to finish.

**Mental State**:
- Task-focused
- Slightly anxious (where did I leave off?)
- Wants to resume quickly

**Touchpoints**:

1. **Return**: Opens Claude Code, doesn't remember session ID
   - Emotion: Frustrated
   - Question: "Which session was I working on?"

2. **Search**: Looks for session listing
   - Current: No built-in way
   - Emotion: Confused
   - Action: Checks file system? Tries to remember?

3. **Guess**: Tries to run next stage
   - Run `/document-discovery`
   - Auto-selection picks most recent
   - Emotion: Relieved (if right session) or Alarmed (if wrong)

4. **Verify**: Checks if it's the right project
   - Emotion: Uncertain
   - Question: "Is this the right one?"

**Current Problems**:
- No session listing from prompts
- No easy way to verify active session
- Auto-selection is opaque (picks most recent)

**Improved Journey**:

1. **Return**: Runs `/list-sessions`
   ```
   Active Sessions

   1. session-a1b2c3d4 - Botany Farm 2022-2023
      Created: 1 day ago
      Status: Evidence extraction in progress (15/23 requirements)
      Last activity: 1 day ago

   2. session-x9y8z7w6 - Willow Creek 2024
      Created: 3 days ago
      Status: Completed
      Last activity: 3 days ago

   Run any prompt to auto-select session #1, or specify:
   /document-discovery session-a1b2c3d4
   ```

2. **Resume**: Runs appropriate next stage
   - Emotion: Confident
   - Outcome: Continues seamlessly

**Journey Optimization**:
- Add `/list-sessions` prompt
- Show active session at top of every prompt response
- Add session summary to next-step guidance

### Journey 3: Power User (Batch Processing)

**Context**: Becca needs to initialize 20 projects from an Ecometric batch.

**Mental State**:
- Efficiency-focused
- Wants automation
- Willing to learn advanced features

**Current Approach**:
```
/initialize Farm 1, /path/to/farm-1
/initialize Farm 2, /path/to/farm-2
...
/initialize Farm 20, /path/to/farm-20
```

**Pain Points**:
- Repetitive
- Slow (20 separate invocations)
- Error-prone (easy to make typo)
- No batch status tracking

**Desired Journey**:

1. **Prepare**: Creates CSV or JSON with project list
   ```json
   [
     {"name": "Farm 1", "path": "/path/to/farm-1"},
     {"name": "Farm 2", "path": "/path/to/farm-2"},
     ...
   ]
   ```

2. **Batch Initialize**: Runs batch command
   ```
   /initialize-batch /path/to/projects.json
   ```

3. **Progress**: Sees batch progress
   ```
   Initializing 20 sessions...

   ✅ 1/20 - Farm 1 (session-abc123)
   ✅ 2/20 - Farm 2 (session-def456)
   ❌ 3/20 - Farm 3 (path not found: /path/to/farm-3)
   ✅ 4/20 - Farm 4 (session-ghi789)
   ...

   Completed: 18/20 successful, 2 errors
   ```

4. **Review Errors**: Checks error details
   ```
   Errors:

   - Farm 3: Path not found (/path/to/farm-3)
     Fix: Verify path and re-run for this project

   - Farm 7: Duplicate session exists
     Fix: Choose to resume or replace
   ```

**Journey Optimization**:
- Implement `/initialize-batch` command
- Support CSV and JSON input formats
- Provide batch progress and error reporting
- Allow retry of failed initializations

### Journey 4: Error Recovery

**Context**: Becca's initialization failed due to path error.

**Mental State**:
- Frustrated
- Wants quick fix
- Needs clear guidance

**Current Journey**:

1. **Error**: Path not found
   - Emotion: Annoyed
   - Reaction: Checks path

2. **Fix**: Corrects path
   - Action: Edits command, re-runs
   - Emotion: Cautious

3. **Retry**: Runs initialize again
   - Outcome: Success
   - Emotion: Relieved

**Problems**:
- Error message could be more helpful
- No path validation before attempt
- No suggestions for corrections

**Improved Journey**:

1. **Error with Suggestions**:
   ```
   ❌ Document Path Not Found

   Path: /home/becca/projects/wrong-path

   Did you mean:
   1. /home/becca/projects/botany-farm-2023
   2. /home/becca/projects/willow-creek-2024
   3. Enter different path

   Choose: [1/2/3]
   ```

2. **Select Correction**:
   - User chooses option 1
   - System uses corrected path

3. **Success**:
   - Session created
   - Emotion: Satisfied

**Journey Optimization**:
- Add fuzzy path matching
- Suggest similar paths
- Interactive error correction

---

## 9. Concrete Improvement Recommendations

### Priority 0: Critical (Implement Immediately)

#### P0-1: Duplicate Session Detection

**Problem**: Users can create infinite duplicate sessions.

**Solution**: Check for existing sessions before creating new one.

**Implementation**:
```python
async def initialize_prompt(
    project_name: str | None = None,
    documents_path: str | None = None
) -> list[TextContent]:
    """Initialize with duplicate detection."""

    # ... existing validation ...

    # Check for duplicates
    all_sessions = await list_sessions()
    duplicates = [
        s for s in all_sessions
        if s["project_name"] == project_name
        and s["documents_path"] == documents_path
    ]

    if duplicates:
        latest = duplicates[0]

        message = f"""# ⚠️ Session Already Exists

Found existing session for this project:

**Session ID:** {latest['session_id']}
**Created:** {latest['created_at']}
**Status:** {latest['status']}

**Progress:**
{format_workflow_progress(latest)}

## What would you like to do?

1. **Resume existing session** (recommended)
   Continue with: {latest['session_id']}

2. **Create new session anyway**
   Start fresh (existing session remains)
   Use this for re-review with updated documents.

3. **Replace existing session**
   Delete {latest['session_id']} and create new one
   ⚠️ Warning: This deletes all progress!

4. **View session details**
   Run: /session-status {latest['session_id']}

**To resume existing session**, just run the next workflow stage:
`/document-discovery`

**To create new session anyway**, add force flag:
`/initialize {project_name}, {documents_path} --force`

**To replace**, first delete the old session:
`/delete-session {latest['session_id']}`
Then re-run /initialize
"""

        return [TextContent(type="text", text=message)]

    # No duplicates, proceed
    # ... existing creation code ...
```

**Testing**:
- Create session
- Run initialize again with same params
- Verify duplicate warning appears
- Test resume flow
- Test force creation

**Success Metric**: Zero duplicate sessions created accidentally.

#### P0-2: Enhanced Error Messages with Recovery Steps

**Problem**: Errors are clear but lack actionable recovery guidance.

**Solution**: Every error should include:
1. What went wrong
2. Why it happened
3. How to fix it
4. How to prevent it

**Implementation**: Create error message templates.

```python
# In models/errors.py

class ErrorMessage:
    """Structured error message with recovery guidance."""

    def __init__(
        self,
        title: str,
        problem: str,
        cause: str | None = None,
        impact: str | None = None,
        solutions: list[str] | None = None,
        prevention: str | None = None,
    ):
        self.title = title
        self.problem = problem
        self.cause = cause
        self.impact = impact
        self.solutions = solutions or []
        self.prevention = prevention

    def format(self) -> str:
        """Format as user-friendly message."""
        parts = [f"# ❌ {self.title}\n"]

        parts.append(f"**Problem**: {self.problem}\n")

        if self.cause:
            parts.append(f"**Why This Happened**: {self.cause}\n")

        if self.impact:
            parts.append(f"**Impact**: {self.impact}\n")

        if self.solutions:
            parts.append("**How to Fix**:\n")
            for i, solution in enumerate(self.solutions, 1):
                parts.append(f"{i}. {solution}\n")

        if self.prevention:
            parts.append(f"**Prevention**: {self.prevention}\n")

        return "\n".join(parts)


# Usage in initialize.py
except FileNotFoundError:
    error = ErrorMessage(
        title="Document Path Not Found",
        problem=f"The directory you specified doesn't exist or isn't accessible:\n`{documents_path}`",
        cause="The path may have a typo, been moved, or you may lack permissions.",
        impact="Cannot create review session without valid documents folder.",
        solutions=[
            "Check for typos in the path",
            "Verify directory exists: `ls -la /parent/directory/`",
            "Use absolute path (starting with /)",
            "Check permissions: `ls -la {documents_path}`",
        ],
        prevention="Copy paths from file manager or use tab-completion when typing."
    )

    return [TextContent(type="text", text=error.format())]
```

**Testing**:
- Trigger each error type
- Verify message follows template
- Test that solutions actually work

**Success Metric**: Users can self-recover from 90%+ of errors without external help.

#### P0-3: Workflow Roadmap in Success Message

**Problem**: Users don't see what's ahead after initialization.

**Solution**: Show full workflow with progress indicator.

**Implementation**:

```python
def format_workflow_roadmap(session: dict) -> str:
    """Format workflow progress roadmap."""

    progress = session["workflow_progress"]

    stages = [
        ("Initialize", progress["initialize"], "Create session and load checklist"),
        ("Document Discovery", progress["document_discovery"], "Scan and classify project documents"),
        ("Evidence Extraction", progress["evidence_extraction"], "Map requirements to evidence"),
        ("Cross-Validation", progress["cross_validation"], "Verify consistency across documents"),
        ("Report Generation", progress["report_generation"], "Generate review report"),
        ("Human Review", progress["human_review"], "Review flagged items (optional)"),
        ("Complete", progress["complete"], "Finalize and export review"),
    ]

    lines = ["## Your Review Workflow\n"]

    for i, (name, status, description) in enumerate(stages, 1):
        if status == "completed":
            icon = "✅"
            status_text = ""
        elif status == "in_progress":
            icon = "🔄"
            status_text = " ← **YOU ARE HERE**"
        else:
            icon = "⏸️"
            status_text = ""

        lines.append(f"{i}. {icon} **{name}**{status_text}")
        lines.append(f"   {description}\n")

    return "\n".join(lines)
```

**Success Message Enhancement**:

```python
message = f"""# ✅ Registry Review Session Initialized

**Session ID:** `{session_id}`
**Project:** {project_name}
**Documents:** {documents_path}
**Methodology:** Soil Carbon v1.2.2
**Created:** {result['created_at']}

---

## Session Created Successfully

Your review session is ready. The system has:
- ✅ Created session workspace
- ✅ Loaded checklist (23 requirements for Soil Carbon projects)
- ✅ Validated document path
- ✅ Initialized workflow tracking

---

{format_workflow_roadmap(session)}

---

## Next Step: Document Discovery

Run: `/document-discovery`

**What This Will Do**:
- Scan all files in your project directory
- Classify documents by type (Project Plan, Baseline Report, etc.)
- Extract metadata (page counts, creation dates)
- Generate document index

**Expected Time**: 10-30 seconds

The prompt will auto-select your session - no need to provide the session ID!
"""
```

**Testing**:
- Initialize session
- Verify roadmap appears
- Check formatting and icons
- Verify descriptions are helpful

**Success Metric**: Users understand workflow progression before starting.

#### P0-4: Session Listing Before Creation

**Problem**: No way to see existing sessions before creating new one.

**Solution**: Add session list to initialization prompt.

**Implementation**:

```python
async def initialize_prompt(
    project_name: str | None = None,
    documents_path: str | None = None
) -> list[TextContent]:
    """Initialize with existing sessions context."""

    # If no params provided, show usage AND existing sessions
    if not project_name or not documents_path:

        # Get existing sessions
        sessions = await list_sessions()

        usage = """# Registry Review Workflow - Stage 1: Initialize

Welcome! Let's start a new registry review.

## Usage

Provide your project details:

`/initialize Your Project Name, /absolute/path/to/documents`

## Example

For the Botany Farm example project:

`/initialize Botany Farm 2022-2023, /home/ygg/Workspace/RegenAI/regen-registry-review-mcp/examples/22-23`
"""

        if sessions:
            usage += "\n\n---\n\n## Your Existing Sessions\n\n"

            for i, session in enumerate(sessions[:5], 1):  # Show max 5
                status = session.get("status", "unknown")
                created = session.get("created_at", "unknown")

                usage += f"{i}. **{session['project_name']}**\n"
                usage += f"   Session: {session['session_id']}\n"
                usage += f"   Created: {created}\n"
                usage += f"   Status: {status}\n\n"

            if len(sessions) > 5:
                usage += f"\n... and {len(sessions) - 5} more.\n"

            usage += "\nTo resume an existing session, just run the next workflow stage (e.g., `/document-discovery`).\n"
            usage += "The most recent session will be auto-selected.\n"

        usage += """
---

## What This Does

This prompt will:
1. ✅ Create a new review session
2. ✅ Load the checklist template
3. ✅ Validate the document path
4. ✅ Set up session state

Then you can proceed to Stage 2: `/document-discovery`
"""

        return [TextContent(type="text", text=usage)]

    # Params provided, proceed with creation
    # ... existing code ...
```

**Testing**:
- Run `/initialize` with no params
- Verify existing sessions shown
- Create multiple sessions
- Verify list updates

**Success Metric**: Users aware of existing sessions before creating duplicates.

### Priority 1: Important (Next Sprint)

#### P1-1: Session Health Check

**Problem**: No way to verify session integrity.

**Solution**: Add health check at initialization and expose via prompt.

**Implementation**: (Already designed in Edge Cases section)

```python
# Add to initialize prompt
async def initialize_prompt(...):
    # ... after creating session ...

    # Run health check
    health = await validate_session_health(session_id)

    if not health["healthy"]:
        # Log issues but don't fail
        logger.warning(
            f"Session {session_id} created but has health issues",
            issues=health["issues"]
        )
```

**New Prompt**: `/session-status <session-id>`

```python
async def session_status_prompt(session_id: str) -> list[TextContent]:
    """Show session health and status."""

    health = await validate_session_health(session_id)
    session = await load_session(session_id)

    message = f"""# Session Health Check

**Session ID:** {session_id}
**Project:** {session['project_metadata']['project_name']}
**Status:** {session['status']}
**Created:** {session['created_at']}

## Health Status

"""

    if health["healthy"]:
        message += "✅ **Healthy** - No issues detected\n"
    else:
        message += f"❌ **Unhealthy** - {len(health['issues'])} issues found\n\n"
        message += "**Issues:**\n"
        for issue in health["issues"]:
            message += f"- {issue}\n"

    message += f"\n{format_workflow_roadmap(session)}\n"

    # ... add more details ...

    return [TextContent(type="text", text=message)]
```

**Testing**:
- Create healthy session, run status check
- Corrupt session.json, run status check
- Delete documents_path, run status check
- Verify all issues detected

**Success Metric**: Can diagnose session problems without manual inspection.

#### P1-2: Documents Path Content Validation

**Problem**: Initialize doesn't check if path contains appropriate files.

**Solution**: Add optional validation of directory contents.

**Implementation**:

```python
def validate_documents_directory(path: Path) -> dict[str, Any]:
    """Validate directory contains expected document types."""

    issues = []
    warnings = []

    # Count files
    files = [f for f in path.glob("**/*") if f.is_file()]

    if len(files) == 0:
        issues.append("Directory is empty")
        return {"valid": False, "issues": issues, "warnings": warnings}

    if len(files) < 3:
        warnings.append(
            f"Only {len(files)} files found. "
            "Typical projects have 5-10 documents."
        )

    # Check for PDFs
    pdfs = [f for f in files if f.suffix.lower() == ".pdf"]
    if len(pdfs) == 0:
        warnings.append(
            "No PDF documents found. "
            "Most projects include PDF reports and plans."
        )

    # Check for GIS files
    gis_extensions = {".shp", ".geojson", ".kml", ".gpx"}
    gis_files = [f for f in files if f.suffix.lower() in gis_extensions]

    # Not an error, but noteworthy

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "file_count": len(files),
        "pdf_count": len(pdfs),
        "gis_count": len(gis_files),
    }
```

**Integration**:

```python
async def initialize_prompt(...):
    # ... validation ...

    # Validate contents
    validation = validate_documents_directory(Path(documents_path))

    if not validation["valid"]:
        # Show errors
        # ...

    if validation["warnings"]:
        # Show warnings but allow continuation
        message = f"""⚠️ Document Path Warnings

Your documents directory has some potential issues:

"""
        for warning in validation["warnings"]:
            message += f"- {warning}\n"

        message += """
You can continue anyway, or cancel and add more documents.

Continue? [Y/n]
"""
        # ... interactive prompt ...
```

**Testing**:
- Empty directory -> error
- Single file -> warning
- No PDFs -> warning
- Typical structure -> success

**Success Metric**: Users warned before creating sessions for empty/unusual directories.

#### P1-3: Interactive Session Recovery

**Problem**: When duplicate found, user must manually decide what to do.

**Solution**: Make recovery interactive and guided.

**Implementation**: Use AskUserQuestion tool.

```python
if duplicates:
    latest = duplicates[0]

    # Show duplicate info
    # ... existing code ...

    # Ask what to do
    question = {
        "question": "What would you like to do with the existing session?",
        "header": "Duplicate",
        "multiSelect": False,
        "options": [
            {
                "label": "Resume existing session",
                "description": f"Continue with {latest['session_id']} - recommended if documents haven't changed"
            },
            {
                "label": "Create new session",
                "description": "Start fresh - use this for re-review with updated documents"
            },
            {
                "label": "Replace existing session",
                "description": f"Delete {latest['session_id']} and create new - ⚠️ destroys all progress"
            },
            {
                "label": "View session details",
                "description": "See full status before deciding"
            }
        ]
    }

    # Get user choice
    response = await ask_user_question([question])
    choice = response["answers"]["0"]

    if choice == "Resume existing session":
        return format_resume_message(latest)
    elif choice == "Create new session":
        force = True
        # Proceed with creation
    elif choice == "Replace existing session":
        await delete_session(latest['session_id'])
        # Proceed with creation
    elif choice == "View session details":
        return await session_status_prompt(latest['session_id'])
```

**Testing**:
- Create duplicate
- Test each choice path
- Verify actions match choices

**Success Metric**: Zero user confusion about handling duplicates.

#### P1-4: Methodology Selection

**Problem**: Default methodology may be wrong; no list shown.

**Solution**: Interactive methodology selection.

**Implementation**:

```python
# If no methodology provided or want to confirm
available_methodologies = [
    {
        "id": "soil-carbon-v1.2.2",
        "name": "Soil Carbon Protocol v1.2.2",
        "description": "Carbon farming projects with soil carbon sequestration",
        "requirements_count": 23
    },
    {
        "id": "biodiversity-v2.0",
        "name": "Biodiversity Monitoring v2.0",
        "description": "Biodiversity and ecosystem health projects",
        "requirements_count": 31
    },
    # ... more ...
]

question = {
    "question": "Which methodology does this project use?",
    "header": "Methodology",
    "multiSelect": False,
    "options": [
        {
            "label": m["name"],
            "description": f"{m['description']} ({m['requirements_count']} requirements)"
        }
        for m in available_methodologies
    ]
}
```

**Testing**:
- Initialize without methodology
- Verify selection prompt appears
- Select methodology
- Verify correct checklist loaded

**Success Metric**: Zero wrong-methodology sessions created.

### Priority 2: Nice to Have (Future)

#### P2-1: Session Templates

**Problem**: Repetitive setup for similar projects.

**Solution**: Save session configuration as template.

**Implementation**:

```python
# Save template
async def save_session_template(
    session_id: str,
    template_name: str
) -> dict:
    """Save session configuration as reusable template."""

    session = await load_session(session_id)

    template = {
        "template_name": template_name,
        "methodology": session["project_metadata"]["methodology"],
        "settings": {
            # ... configurable settings ...
        }
    }

    # Save template
    templates_dir = settings.data_dir / "templates"
    templates_dir.mkdir(exist_ok=True)

    template_file = templates_dir / f"{template_name}.json"
    with open(template_file, "w") as f:
        json.dump(template, f, indent=2)

    return {"template_name": template_name, "path": str(template_file)}


# Use template
async def initialize_from_template(
    project_name: str,
    documents_path: str,
    template_name: str
) -> dict:
    """Initialize session from template."""

    # Load template
    template_file = settings.data_dir / "templates" / f"{template_name}.json"
    with open(template_file) as f:
        template = json.load(f)

    # Create session with template settings
    return await create_session(
        project_name=project_name,
        documents_path=documents_path,
        methodology=template["methodology"],
        **template["settings"]
    )
```

**Use Case**: Ecometric always uses same methodology and settings.

**Testing**:
- Create template from session
- Initialize new session from template
- Verify settings applied

**Success Metric**: Batch initialization time reduced by 50%.

#### P2-2: Batch Initialization

**Problem**: Must initialize projects one by one.

**Solution**: Batch initialization from CSV/JSON.

**Implementation**: (Already designed in Journey Maps section)

```python
async def initialize_batch_prompt(
    batch_file: str
) -> list[TextContent]:
    """Initialize multiple sessions from batch file."""

    # Read batch file (CSV or JSON)
    projects = read_batch_file(batch_file)

    results = {
        "successful": [],
        "failed": [],
    }

    for i, project in enumerate(projects, 1):
        try:
            result = await create_session(
                project_name=project["name"],
                documents_path=project["path"],
                methodology=project.get("methodology", "soil-carbon-v1.2.2")
            )

            results["successful"].append({
                "project": project["name"],
                "session_id": result["session_id"]
            })

            # Progress update
            print(f"✅ {i}/{len(projects)} - {project['name']}")

        except Exception as e:
            results["failed"].append({
                "project": project["name"],
                "error": str(e)
            })

            print(f"❌ {i}/{len(projects)} - {project['name']}: {e}")

    # Format summary
    message = format_batch_results(results)
    return [TextContent(type="text", text=message)]
```

**Testing**:
- Create batch file with 10 projects
- Run batch initialization
- Verify all successful
- Test with some failures (wrong paths)
- Verify error handling

**Success Metric**: Can initialize 20 projects in < 1 minute.

#### P2-3: Upstream Integration (Airtable/SharePoint)

**Problem**: Must manually copy paths from submission systems.

**Solution**: Direct integration with Airtable and SharePoint.

**Implementation**:

```python
async def initialize_from_airtable(
    airtable_record_id: str
) -> dict:
    """Initialize session from Airtable submission."""

    # Fetch from Airtable
    record = await airtable_client.get_record(
        base=settings.airtable_base_id,
        table="Project Submissions",
        record_id=airtable_record_id
    )

    # Extract metadata
    project_name = record["fields"]["Project Name"]
    documents_url = record["fields"]["Documents Link"]
    methodology = record["fields"]["Methodology"]

    # Download or link documents
    documents_path = await fetch_documents_from_url(documents_url)

    # Create session
    return await create_session(
        project_name=project_name,
        documents_path=documents_path,
        methodology=methodology,
        project_id=record["fields"].get("Project ID"),
        proponent=record["fields"].get("Proponent"),
        submission_date=record["fields"].get("Submission Date")
    )
```

**Use Case**: Initialize directly from Airtable submission notification.

**Testing**:
- Create test Airtable record
- Initialize from record ID
- Verify metadata extracted correctly

**Success Metric**: Zero manual data entry for Airtable submissions.

---

## 10. Testing Scenarios

### Functional Test Suite

#### Test 1: Happy Path

**Setup**:
- Valid project name: "Test Project 2024"
- Valid documents path: `/tmp/test-project/` (with 5 PDFs)
- Default methodology

**Steps**:
1. Run `/initialize Test Project 2024, /tmp/test-project`
2. Verify session created
3. Verify session.json exists
4. Verify documents.json exists
5. Verify findings.json exists
6. Verify workflow_progress.initialize = "completed"

**Expected Result**: Success message with session ID.

**Pass Criteria**:
- Session ID returned
- All files created
- No errors or warnings

#### Test 2: Duplicate Detection

**Setup**:
- Create session for "Test Project 2024"

**Steps**:
1. Run `/initialize Test Project 2024, /tmp/test-project` again
2. Verify duplicate warning shown
3. Verify offered options (resume/create/replace)

**Expected Result**: Duplicate warning with options.

**Pass Criteria**:
- Warning displayed
- Existing session details shown
- No new session created automatically

#### Test 3: Invalid Path

**Setup**:
- Invalid path: `/nonexistent/path`

**Steps**:
1. Run `/initialize Test Project, /nonexistent/path`
2. Verify error message
3. Verify recovery guidance provided

**Expected Result**: Clear error with troubleshooting steps.

**Pass Criteria**:
- Error message displayed
- Path shown
- Troubleshooting steps listed
- No session created

#### Test 4: Empty Directory

**Setup**:
- Empty directory: `/tmp/empty-dir/`

**Steps**:
1. Run `/initialize Test Project, /tmp/empty-dir`
2. Verify warning about empty directory

**Expected Result**: Warning with options to continue or cancel.

**Pass Criteria**:
- Warning displayed
- User can choose to continue or cancel
- If continue, session created with warning logged

#### Test 5: Path is File

**Setup**:
- File path: `/tmp/project-plan.pdf`

**Steps**:
1. Run `/initialize Test Project, /tmp/project-plan.pdf`
2. Verify error indicating file vs directory

**Expected Result**: Error explaining file vs directory.

**Pass Criteria**:
- Error clearly states "file" vs "directory"
- Guidance on using parent directory
- No session created

#### Test 6: Special Characters

**Setup**:
- Project name with special chars: "O'Brien Farm / Ranch"

**Steps**:
1. Run `/initialize O'Brien Farm / Ranch, /tmp/test`
2. Verify validation error or sanitization

**Expected Result**: Error or name sanitized.

**Pass Criteria**:
- Problematic characters identified
- Suggested alternatives shown
- Or: Name automatically sanitized

#### Test 7: Very Long Name

**Setup**:
- 250-character project name

**Steps**:
1. Run `/initialize [very long name], /tmp/test`
2. Verify length validation

**Expected Result**: Error or warning about length.

**Pass Criteria**:
- Warning displayed
- Suggested shortened names
- User can choose

#### Test 8: Network Path

**Setup**:
- Network mount: `/mnt/sharepoint/project`

**Steps**:
1. Run `/initialize Test, /mnt/sharepoint/project`
2. Verify network path warning

**Expected Result**: Warning about network reliability.

**Pass Criteria**:
- Warning displayed
- Recommendation to copy locally
- User can choose to continue

#### Test 9: Session Health Check

**Setup**:
- Create session
- Corrupt session.json

**Steps**:
1. Run `/session-status [session-id]`
2. Verify health issues detected

**Expected Result**: Health check shows corruption.

**Pass Criteria**:
- Corruption detected
- Specific issue identified
- Recovery options provided

#### Test 10: Methodology Selection

**Setup**:
- Initialize without methodology parameter

**Steps**:
1. Run `/initialize Test Project, /tmp/test`
2. Verify methodology selection prompt
3. Select methodology

**Expected Result**: Interactive methodology selection.

**Pass Criteria**:
- Available methodologies listed
- User can select
- Correct checklist loaded

### Integration Test Suite

#### Integration Test 1: Initialize → Discovery

**Setup**: Fresh session

**Steps**:
1. Initialize session
2. Immediately run `/document-discovery`
3. Verify discovery uses correct session
4. Verify documents_path from initialization is used

**Expected Result**: Seamless handoff.

**Pass Criteria**:
- Discovery auto-selects session
- Correct path used
- No errors

#### Integration Test 2: Multiple Sessions

**Setup**: None

**Steps**:
1. Initialize Session A
2. Initialize Session B
3. Run `/document-discovery`
4. Verify auto-selection picks most recent (Session B)

**Expected Result**: Most recent session selected.

**Pass Criteria**:
- Session B selected
- User notified which session is active

#### Integration Test 3: Resume After Days

**Setup**: Session created 3 days ago

**Steps**:
1. List sessions
2. Find old session
3. Resume with next stage

**Expected Result**: Can resume old session.

**Pass Criteria**:
- Old session listed
- Can be resumed
- State preserved

### Performance Test Suite

#### Performance Test 1: Initialization Speed

**Setup**: Valid inputs

**Measure**: Time from invocation to response

**Target**: < 1 second

**Steps**:
1. Run initialize 10 times
2. Measure average time
3. Verify under 1 second

**Pass Criteria**: Average < 1000ms

#### Performance Test 2: Duplicate Detection Speed

**Setup**: 100 existing sessions

**Measure**: Time to check for duplicates

**Target**: < 2 seconds

**Steps**:
1. Create 100 sessions
2. Run initialize (duplicate scenario)
3. Measure duplicate check time

**Pass Criteria**: Check time < 2000ms

#### Performance Test 3: Large Directory

**Setup**: Directory with 1000 files

**Measure**: Path validation time

**Target**: < 3 seconds

**Steps**:
1. Create directory with 1000 files
2. Run initialize
3. Measure validation time

**Pass Criteria**: Validation < 3000ms

### User Acceptance Test Suite

#### UAT 1: First-Time User

**Scenario**: New user following quick-start guide

**Steps**:
1. User reads documentation
2. Runs example command
3. Sees success message
4. Understands next step

**Evaluation**:
- Can user complete without help?
- Is success message clear?
- Does user know what to do next?

**Pass Criteria**: User successfully initializes session and proceeds to discovery.

#### UAT 2: Returning User

**Scenario**: User returning after interruption

**Steps**:
1. User forgot session ID
2. Runs `/list-sessions`
3. Identifies correct session
4. Resumes workflow

**Evaluation**:
- Can user find their session?
- Is session identification clear?
- Can user resume easily?

**Pass Criteria**: User finds and resumes session in < 2 minutes.

#### UAT 3: Error Recovery

**Scenario**: User makes typo in path

**Steps**:
1. User enters wrong path
2. Sees error message
3. Identifies correction
4. Retries successfully

**Evaluation**:
- Is error message helpful?
- Can user self-correct?
- Is retry process smooth?

**Pass Criteria**: User corrects error and succeeds on second attempt.

#### UAT 4: Batch Workflow

**Scenario**: Power user initializing 20 projects

**Steps**:
1. User prepares batch file
2. Runs batch initialize
3. Reviews results
4. Handles errors

**Evaluation**:
- Is batch process efficient?
- Are errors clearly reported?
- Can user retry failures?

**Pass Criteria**: User initializes 20 projects in < 5 minutes.

---

## 11. Summary and Action Items

### Critical Issues Identified

1. **Duplicate session creation** - No detection or prevention
2. **No session discovery** - Users can't list or find existing sessions
3. **Limited error guidance** - Errors are clear but lack recovery steps
4. **No workflow preview** - Users don't see what's ahead
5. **No content validation** - Empty directories pass validation
6. **Opaque auto-selection** - Users don't know which session is active

### Quick Wins (< 1 Day Implementation)

1. Add workflow roadmap to success message
2. Enhance error messages with recovery steps
3. Add session listing to initialization prompt
4. Show duplicate warning before creating

### Short-Term Priorities (1-2 Weeks)

1. Implement duplicate detection with options
2. Add `/list-sessions` prompt
3. Add `/session-status` health check
4. Implement methodology selection
5. Add documents path content validation

### Long-Term Enhancements (1+ Months)

1. Batch initialization
2. Session templates
3. Upstream integrations (Airtable, SharePoint)
4. Advanced auto-recovery
5. Predictive path validation

### Success Metrics

**User Experience**:
- 90%+ of users complete initialization without errors
- Zero accidental duplicate sessions
- < 2 minutes average time to initialize and start discovery
- < 10% of users need external help with errors

**System Quality**:
- 100% of error messages include recovery steps
- 95%+ of error scenarios have automated suggestions
- Zero session corruption incidents
- All sessions resumable after interruption

**Documentation Quality**:
- Every error has troubleshooting guide
- Quick-start guide covers 90% of use cases
- User can understand full workflow from initialize stage

### Next Steps

1. **Review this analysis** with team and Becca
2. **Prioritize recommendations** based on impact and effort
3. **Implement P0 items** in current sprint
4. **Schedule P1 items** for next sprint
5. **Create tracking issues** for all recommendations
6. **Update documentation** based on findings
7. **Plan user testing** for implemented improvements

---

## Appendices

### Appendix A: Example Improved Messages

#### Example 1: Successful Initialization

```markdown
# Welcome! Your Review Session is Ready ✅

Great news! We've created your session and loaded everything you need to review Botany Farm 2022-2023.

**Session Details**
Session ID: session-a1b2c3d4e5f6
Project: Botany Farm 2022-2023
Documents: /home/becca/projects/botany-farm-2023
Methodology: Soil Carbon v1.2.2
Created: Just now (2025-11-14 10:30)

**What We Set Up**
✅ Session workspace created
✅ Checklist loaded (23 requirements for Soil Carbon projects)
✅ Document path validated and accessible
✅ Workflow tracking initialized

## Your Review Workflow

1. ✅ **Initialize**
   Create session and load checklist

2. ⏸️ **Document Discovery** ← NEXT STEP
   Scan and classify project documents

3. ⏸️ **Evidence Extraction**
   Map requirements to evidence

4. ⏸️ **Cross-Validation**
   Verify consistency across documents

5. ⏸️ **Report Generation**
   Generate review report

6. ⏸️ **Human Review** (optional)
   Review flagged items

7. ⏸️ **Complete**
   Finalize and export review

## Next Step: Document Discovery

Run: `/document-discovery`

**What This Will Do**:
- Scan all files in /home/becca/projects/botany-farm-2023
- Identify document types (project plan, baseline report, GIS files, etc.)
- Extract metadata (page counts, dates, file sizes)
- Generate document inventory

**Expected Time**: 10-30 seconds

The prompt will auto-select your session - no need to specify the session ID!

---

**Need Help?**
- View all sessions: `/list-sessions`
- Check session health: `/session-status session-a1b2c3d4e5f6`
- Documentation: https://docs.regen.network/registry-review
```

#### Example 2: Duplicate Session Warning

```markdown
# ⚠️ Session Already Exists

We found an existing session for this project:

**Existing Session**
Session ID: session-a1b2c3d4e5f6
Project: Botany Farm 2022-2023
Documents: /home/becca/projects/botany-farm-2023
Created: 1 day ago (2025-11-13 10:30)
Status: in_progress
Last Activity: 4 hours ago

**Current Progress**:
1. ✅ Initialize (completed)
2. ✅ Document Discovery (7 documents found)
3. 🔄 Evidence Extraction (in progress - 15/23 requirements mapped)
4. ⏸️ Cross-Validation (not started)
5. ⏸️ Report Generation (not started)
6. ⏸️ Human Review (not started)
7. ⏸️ Complete (not started)

## What Would You Like to Do?

### Option 1: Resume Existing Session (Recommended)

Continue where you left off. Just run the next workflow stage:

`/evidence-extraction`

**When to choose this**:
- You're continuing work on this project
- Documents haven't changed
- You want to preserve existing progress

### Option 2: Create New Session

Start a fresh review for the same project. The existing session will remain.

`/initialize Botany Farm 2022-2023, /home/becca/projects/botany-farm-2023 --force`

**When to choose this**:
- Documents have been updated
- You're doing a re-review
- You want to compare two different approaches

### Option 3: Replace Existing Session

Delete the old session and create a new one.

**⚠️ Warning**: This will permanently delete session-a1b2c3d4e5f6 and all its progress (7 documents discovered, 15 requirements mapped).

**Steps**:
1. Delete old session: `/delete-session session-a1b2c3d4e5f6`
2. Create new session: `/initialize Botany Farm 2022-2023, /home/becca/projects/botany-farm-2023`

**When to choose this**:
- Old session is corrupted or stuck
- You're certain you want to start over
- You want to clean up duplicate sessions

### Option 4: View Session Details

See full status, findings, and health before deciding.

`/session-status session-a1b2c3d4e5f6`

---

**Need Help Deciding?**

- If documents are the same and you want to continue → Choose Option 1 (Resume)
- If documents have changed significantly → Choose Option 2 (Create New)
- If you're absolutely sure you want to start over → Choose Option 3 (Replace)
- If you're unsure → Choose Option 4 (View Details)
```

#### Example 3: Path Not Found Error

```markdown
# ❌ Cannot Create Session: Document Path Not Found

**Problem**: The directory you specified doesn't exist or isn't accessible.

**Path Provided**: `/home/becca/projects/wrong-path`

**Why This Happened**:
- The path may have a typo
- The directory may have been moved or renamed
- You may not have permission to access it

**Impact**: We can't create your review session without a valid documents folder.

## How to Fix

### 1. Check for Typos

Did you mean one of these similar paths?
- `/home/becca/projects/botany-farm-2023` (closest match)
- `/home/becca/projects/willow-creek-2024`

### 2. Verify the Directory Exists

List your projects directory to see what's available:

```bash
ls -la /home/becca/projects/
```

### 3. Use an Absolute Path

Make sure you're using a full path starting with `/`:

✅ **Correct**: `/home/becca/projects/my-project`
❌ **Wrong**: `~/projects/my-project` (tilde not supported)
❌ **Wrong**: `projects/my-project` (relative path)
❌ **Wrong**: `./my-project` (relative path)

### 4. Check Permissions

Verify you have permission to access the directory:

```bash
ls -la /home/becca/projects/wrong-path
```

If you see "Permission denied", you may need to:
- Use a directory you own
- Request access from the directory owner
- Copy files to a location you control

## Prevention Tips

- **Copy paths from file manager** instead of typing
- **Use tab-completion** when typing paths in terminal
- **Verify directory exists** before running initialize:
  ```bash
  ls -la /path/to/verify
  ```

## Ready to Try Again?

Once you've identified the correct path, run:

`/initialize Botany Farm 2022-2023, /correct/path/to/documents`

**Example**:
`/initialize Botany Farm 2022-2023, /home/becca/projects/botany-farm-2023`

---

**Still Having Trouble?**
- View documentation: https://docs.regen.network/registry-review/troubleshooting
- Check existing sessions: `/list-sessions`
- Contact support: support@regen.network
```

### Appendix B: State Machine Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        NO SESSION                            │
│                                                               │
│  User has not created any session yet                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ /initialize
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   INITIALIZED                                │
│                                                               │
│  • session.json created                                      │
│  • documents.json created (empty)                           │
│  • findings.json created (empty)                            │
│  • workflow_progress.initialize = "completed"               │
│  • documents_path validated                                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ /document-discovery
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 DOCUMENTS_DISCOVERED                         │
│                                                               │
│  • documents.json populated                                  │
│  • workflow_progress.document_discovery = "completed"       │
│  • 7 documents classified and indexed                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ /evidence-extraction
                            ▼
                           ...

State Transitions from INITIALIZED:

Valid:
- /document-discovery → DOCUMENTS_DISCOVERED ✅
- /initialize (same project+path) → Duplicate warning ⚠️
- /delete-session → NO SESSION ✅

Invalid:
- /evidence-extraction → Error: "Run /document-discovery first" ❌
- /cross-validation → Error: "Run /document-discovery first" ❌
- /report-generation → Error: "Complete earlier stages first" ❌
```

### Appendix C: Data Flow Diagram

```
User Input
    │
    ├─ project_name: str
    ├─ documents_path: str
    └─ methodology: str (optional)
    │
    ▼
Validation Layer
    │
    ├─ Pydantic Schema Validation
    │  ├─ project_name: 1-200 chars
    │  ├─ project_id: pattern match (optional)
    │  └─ documents_path: exists, is_dir
    │
    ├─ Duplicate Detection
    │  └─ Check list_sessions() for matches
    │
    └─ Content Validation (optional)
       └─ Check directory has files
    │
    ▼
Session Creation
    │
    ├─ Generate session_id (UUID)
    ├─ Load checklist for methodology
    ├─ Create Session object
    └─ Initialize WorkflowProgress
    │
    ▼
State Persistence
    │
    ├─ Create session directory
    ├─ Write session.json (atomic, locked)
    ├─ Write documents.json (empty array)
    └─ Write findings.json (empty array)
    │
    ▼
Response to User
    │
    ├─ Session ID
    ├─ Creation confirmation
    ├─ Workflow roadmap
    └─ Next step guidance
```

### Appendix D: User Research Questions

**For Becca (Current User)**:

1. How often do you accidentally create duplicate sessions?
2. What's the longest you've had between starting and resuming a session?
3. How do you currently keep track of multiple active sessions?
4. What path-related errors have you encountered?
5. Do you ever need to initialize multiple projects at once?
6. What would make initialization faster/easier for you?
7. How often do you need to change methodology mid-review?
8. What session metadata would help you identify projects?

**For New Users**:

1. What was unclear about the initialization process?
2. Did you understand what would happen after initialization?
3. Were error messages helpful when you encountered them?
4. What additional guidance would have helped?
5. How long did it take you to successfully initialize your first session?
6. What documentation did you reference?
7. What surprised you about the process?

**For Power Users**:

1. What batch operations would save you the most time?
2. How do you manage sessions for related projects?
3. What keyboard shortcuts or aliases would help?
4. What session templates would be most useful?
5. How could upstream integration (Airtable) improve your workflow?
6. What session metadata do you wish you could query?

---

**End of Analysis**

This comprehensive analysis provides a foundation for improving the Initialize stage UX. Implementation should prioritize P0 items for immediate impact, followed by P1 enhancements to round out the experience.

The ultimate goal: make session initialization so intuitive and robust that users can focus on the substantive review work, not on managing session state.
