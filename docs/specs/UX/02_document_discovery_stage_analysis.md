# Stage 2: Document Discovery - UX Analysis from First Principles

**Date:** 2025-11-14
**Author:** Development Team
**Status:** Draft - Ready for Review

---

## Executive Summary

Stage 2 (Document Discovery) is where the Registry Review workflow transitions from intent to reality. Becca has initialized a session, and now the agent must find, classify, and index all relevant project documents. This stage is deceptively complex because it operates at the boundary between messy real-world file systems and the structured data the workflow needs downstream.

**Core Finding:** Document discovery is not just about finding files—it's about building trust. Becca needs to know exactly what was found, how it was classified, and critically, what might have been missed. The UX must transform uncertainty into confidence.

---

## Stage Overview

### What Happens in This Stage

1. **Recursive directory scan** of the configured `documents_path`
2. **File filtering** by supported extensions (PDF, GIS, images)
3. **Classification** via filename pattern matching
4. **Metadata extraction** (file size, dates, page counts, table detection)
5. **Document indexing** with unique IDs and confidence scores
6. **State persistence** in `documents.json`

### Inputs
- Session ID (explicit or auto-selected)
- OR: Project name + documents path (creates session inline)
- OR: No parameters (uses most recent session)

### Outputs
- Discovered document list with classifications
- Classification summary by type
- Updated session state (`document_discovery: "completed"`)
- Confidence indicators for each classification

### Success Criteria
- All accessible files discovered
- Accurate classification (≥80% confidence for most documents)
- Clear feedback on what was found vs. expected
- Graceful handling of edge cases

---

## User Experience Framework Analysis

### 1. Mental Model Alignment

#### What Becca Expects

**"Show me everything in this folder that matters for the review."**

Becca's mental model is grounded in manual review work:
- Open a file browser
- See all PDFs, shapefiles, and images
- Skim filenames to understand what's what
- Open ambiguous files to verify contents

The agent must replicate this experience while adding value through automation and structure.

#### What the System Delivers

The system presents:
- A count of discovered documents
- A classification breakdown (project_plan: 2, baseline_report: 1, etc.)
- A detailed list with confidence scores
- Document IDs for downstream reference

**Gap Analysis:**

✅ **Well-aligned:**
- Clear counts and categories match manual scanning
- Confidence scores acknowledge uncertainty
- Document IDs provide traceability

⚠️ **Misalignment risks:**
- **Hidden complexity:** Recursive scanning may find files Becca didn't know existed (e.g., in nested subdirectories)
- **Classification opacity:** Pattern matching is fast but opaque—why was this file classified as "project_plan" vs "baseline_report"?
- **No preview:** Unlike manual review, Becca can't quickly skim the first page of a PDF

**Recommendations:**
- Show **directory structure** in output (which subdirectories were scanned)
- Include **classification reasoning** (e.g., "Matched pattern: 'project plan'")
- Offer **quick preview links** for classified documents
- Highlight **unexpected finds** (files in unusual locations)

#### Information Scent

The system provides strong information scent through:
- **Icons:** ✓ for high confidence (≥80%), ~ for lower confidence
- **Structured output:** Clear sections for summary, breakdown, and details
- **Next steps guidance:** Explicit instructions on how to proceed

**Potential improvements:**
- Add **visual hierarchy** (e.g., group by classification type, then list documents)
- Show **file locations** relative to documents_path (helps verify expected structure)
- Include **timestamp** of discovery for audit purposes

---

### 2. Interaction Patterns

#### Primary Flow

```
User runs: /document-discovery Botany Farm 2022-2023, /path/to/documents

System:
1. Creates session (if new) or loads existing
2. Scans directory recursively
3. Classifies each file
4. Extracts metadata
5. Presents results with summary and details
```

**Interaction Characteristics:**
- **One-shot operation:** No user input during execution
- **Fire-and-forget:** User waits for complete results
- **Deterministic:** Same path always produces same results (idempotent)

**UX Implications:**
- **Progress feedback needed:** For large document sets (>50 files), show progress
- **Time expectations:** Set expectations for scan duration
- **Interruption handling:** What if user cancels mid-scan?

#### Alternative Flows

**Flow 2: Re-discovery (Idempotent Run)**

```
User: /document-discovery (session already has documents)

Expected behavior:
- Re-scan documents_path
- Update documents.json with new findings
- Preserve document IDs for unchanged files
- Detect and report changes
```

**Current implementation:**
- ✅ Overwrites documents.json
- ❌ No change detection
- ❌ No preservation of previous classifications or manual overrides

**Critical UX Issue:** If Becca manually corrected a misclassification, re-running discovery erases that work.

**Solution:** Implement delta detection:

```python
# Pseudocode
previous_docs = load_previous_documents()
new_docs = discover_documents()

for new_doc in new_docs:
    previous_doc = find_by_filepath(previous_docs, new_doc.filepath)

    if previous_doc:
        # Preserve manual overrides
        if previous_doc.classification_method == "manual":
            new_doc.classification = previous_doc.classification
            new_doc.classification_method = "manual"
        # Preserve document ID
        new_doc.document_id = previous_doc.document_id
```

**Flow 3: Session Auto-Selection**

When no parameters provided:
- Use most recent session
- Show "Note: Auto-selected most recent session"

**UX Risk:** User might not notice which session is active.

**Mitigation:**
- Make auto-selection notice **prominent** (not just a footnote)
- Include session metadata (project name, creation date) in notice
- Offer **escape hatch** (e.g., "To use a different session, run: /document-discovery <session-id>")

---

### 3. Error Handling & Edge Cases

#### Missing/Corrupted Files

**Scenario 1: File exists but cannot be read**

```python
# Current behavior: Logs warning, continues processing
print(f"Warning: Failed to process {file_path}: {e}", flush=True)
continue
```

**User experience:**
- ⚠️ Error is **silent** to user—only visible in server logs
- Becca has no indication a file was skipped
- Downstream stages may fail when referencing missing document

**Solution:** Track and report skipped files:

```python
skipped_files = []

try:
    # ... process file ...
except Exception as e:
    skipped_files.append({
        "filepath": str(file_path),
        "error": str(e),
        "error_type": type(e).__name__
    })
    continue

# Include in response
if skipped_files:
    warnings = "⚠️ **Warnings**\n\n"
    warnings += "The following files could not be processed:\n\n"
    for skip in skipped_files:
        warnings += f"- `{skip['filepath']}`\n"
        warnings += f"  Error: {skip['error']}\n\n"
```

**Scenario 2: Corrupted PDF**

```python
# pdfplumber.open() raises exception
try:
    with pdfplumber.open(file_path) as pdf:
        metadata.page_count = len(pdf.pages)
except Exception:
    # Silent failure - metadata.page_count remains None
    pass
```

**User experience:**
- Document is indexed but without PDF-specific metadata
- No indication the file might be corrupted
- May cause issues in evidence extraction stage

**Solution:** Separate classification confidence from file health:

```json
{
  "document_id": "DOC-abc123",
  "filename": "project-plan.pdf",
  "classification": "project_plan",
  "confidence": 0.95,
  "health_status": "corrupted",
  "health_message": "PDF could not be opened - file may be corrupted"
}
```

#### Classification Confidence Edge Cases

**Low Confidence Classifications (<80%)**

Current behavior:
- Documents with confidence <80% marked with ~ icon
- No guidance on what to do about them

**User experience issue:**
- Becca sees "~ unknown (50% confidence)" but doesn't know if:
  - The file is irrelevant (can ignore)
  - Classification failed (needs manual review)
  - Multiple classifications are equally likely (needs disambiguation)

**Solution:** Provide actionable guidance:

```markdown
## Low Confidence Classifications

The following documents could not be confidently classified:

1. ~ misc-data-2023.pdf
   Type: unknown (50% confidence)
   **Action needed:** Review file and manually classify, or mark as "other"

2. ~ report-final.pdf
   Type: monitoring_report (70% confidence)
   **Alternative matches:** baseline_report (65%)
   **Suggestion:** Check document date/content to disambiguate
```

**Ambiguous Classifications**

Some filenames match multiple patterns:

```python
filename = "project-monitoring-baseline-2023.pdf"

# Matches:
# - PROJECT_PLAN_PATTERNS (contains "project")
# - MONITORING_PATTERNS (contains "monitoring")
# - BASELINE_PATTERNS (contains "baseline")
```

Current implementation: First match wins (specificity order)

**UX issue:** No visibility into alternative classifications

**Solution:** For close matches, show runner-up:

```json
{
  "classification": "project_plan",
  "confidence": 0.95,
  "classification_method": "filename",
  "alternative_classifications": [
    {"type": "monitoring_report", "confidence": 0.90},
    {"type": "baseline_report", "confidence": 0.95}
  ]
}
```

#### GIS File Handling

**Scenario: Shapefile components**

A shapefile consists of multiple files:
```
field-boundaries.shp
field-boundaries.shx
field-boundaries.dbf
field-boundaries.prj
```

Current behavior:
- All four files discovered as separate documents
- All classified as "gis_shapefile"
- No indication they're related

**UX issue:**
- Clutters document list
- May confuse downstream mapping (one logical file, four entries)

**Solution:** Group shapefile components:

```json
{
  "document_id": "DOC-abc123",
  "filename": "field-boundaries",
  "classification": "gis_shapefile",
  "file_type": "shapefile_group",
  "components": [
    {"extension": ".shp", "filepath": "..."},
    {"extension": ".shx", "filepath": "..."},
    {"extension": ".dbf", "filepath": "..."},
    {"extension": ".prj", "filepath": "..."}
  ]
}
```

**Scenario: Large raster files**

TIFF files may be very large (>1GB):
- Slow to process
- Memory intensive
- May not need metadata extraction

**Current behavior:**
- Attempts to extract metadata (basic file stats only)
- May timeout or crash on very large files

**Solution:**
- Size-based metadata extraction strategy
- For files >100MB, skip advanced metadata
- Report file size prominently for user awareness

#### Document Changes Between Runs

**Scenario: Files added/removed/modified between discovery runs**

```
Discovery Run 1 (Day 1):
- project-plan-v1.pdf
- baseline-report.pdf

Discovery Run 2 (Day 5):
- project-plan-v2.pdf   (NEW)
- baseline-report.pdf   (MODIFIED - new timestamp)
- monitoring-report.pdf (NEW)
(project-plan-v1.pdf was deleted)
```

**Current behavior:**
- Completely replaces documents.json
- No indication of changes
- Existing evidence mappings may now point to deleted documents

**UX issue:**
- Becca has no visibility into what changed
- Must manually compare lists to spot differences
- Risk of confusion if evidence references stale documents

**Solution:** Change detection and reporting:

```markdown
# Document Discovery - Changes Detected

## Summary
- 2 new documents found
- 1 document modified
- 1 document removed

## Details

### Added Documents
- ✅ project-plan-v2.pdf (project_plan, 95% confidence)
- ✅ monitoring-report.pdf (monitoring_report, 90% confidence)

### Modified Documents
- 🔄 baseline-report.pdf
  - Last indexed: 2025-11-10
  - File modified: 2025-11-13
  - **Action:** Evidence mappings preserved but may need review

### Removed Documents
- ❌ project-plan-v1.pdf
  - **Warning:** This document had evidence mappings in evidence.json
  - **Action:** Manual review recommended

## Recommendations
- Review removed document references in evidence mappings
- Consider running evidence extraction again for modified documents
```

#### Performance Edge Cases

**Large Document Sets (>100 files)**

Current behavior:
- Synchronous processing (blocks until complete)
- No progress indication
- May appear frozen for 30+ seconds

**UX issue:**
- User doesn't know if system is working or stuck
- No way to estimate completion time
- Can't cancel if taking too long

**Solution:** Progress streaming or chunked processing:

```markdown
# Document Discovery In Progress...

Scanning directory: /path/to/documents

Progress: 45/127 files processed (35%)
Current: analyzing project-plan-v2.pdf...

[█████████░░░░░░░░░░]

Estimated time remaining: 2 minutes
```

**Deeply Nested Directories**

```
documents/
  projects/
    2023/
      botany-farm/
        registration/
          submitted/
            archive/
              old-version/
                v1/
                  project-plan-old.pdf
```

**Current behavior:**
- Recurses through all levels
- Finds archived/backup files user may not want

**UX issue:**
- May include irrelevant documents (backups, archives)
- Clutters document list
- User has no control over recursion depth

**Solution:**
- Configurable recursion depth (default: 5 levels)
- Auto-skip common backup/archive patterns (`.git`, `archive/`, `backup/`, `old/`)
- Report skipped directories

#### Empty Directory

**Scenario: documents_path exists but contains no documents**

Current behavior:
```markdown
## Summary
Found **0 document(s)**

⚠ No documents found in the specified directory.
```

**UX evaluation:**
- ✅ Clear message
- ❌ No troubleshooting guidance
- ❌ Doesn't explain *why* nothing was found

**Enhanced response:**

```markdown
# Document Discovery - No Documents Found

**Project:** Botany Farm 2022-2023
**Path:** /path/to/documents
**Status:** ⚠️ No compatible documents found

## Possible Reasons

1. **Empty directory:** The path contains no files
   - Verify this is the correct documents folder

2. **Unsupported file types:** Only PDF, GIS (.shp, .geojson), and images (.tif, .jpg) are supported
   - If documents are in .docx, .xlsx, or other formats, convert to PDF first

3. **Hidden files only:** Files starting with '.' are skipped
   - Check for hidden files: `ls -la /path/to/documents`

4. **Permission issues:** System may not have read access
   - Check permissions: `ls -l /path/to/documents`

## Directory Contents

Scanned: /path/to/documents
Found: 5 files total
- 3 .txt files (not supported)
- 2 .docx files (not supported)

**Next Steps:**
1. Convert unsupported files to PDF
2. Verify you have the correct documents_path
3. Run discovery again once files are ready
```

---

### 4. Feedback & Confirmation

#### Success Feedback

**Current output structure:**

```markdown
# Document Discovery Complete

**Project:** Botany Farm 2022-2023
**Session:** session-abc123
**Documents Path:** /path/to/documents

## Summary
Found **7 document(s)**

### Classification Breakdown
  • project_plan: 2
  • baseline_report: 1
  • land_tenure: 3
  • gis_shapefile: 1

## Discovered Documents
[List of documents...]
```

**Evaluation:**
- ✅ Clear success confirmation
- ✅ Key metrics visible (count, breakdown)
- ✅ Next steps provided
- ⚠️ Missing: discovery timestamp, scan duration, path coverage
- ⚠️ Missing: validation that this matches expectations

**Enhanced feedback:**

```markdown
# Document Discovery Complete ✓

**Project:** Botany Farm 2022-2023
**Session:** session-abc123
**Documents Path:** /path/to/documents
**Discovery completed:** 2025-11-14 10:30:45
**Processing time:** 3.2 seconds
**Directories scanned:** 4 (max depth: 3)

## Summary
Found **7 document(s)** across 4 subdirectories

### Classification Breakdown
  • project_plan: 2 (✓ typical: 1-2)
  • baseline_report: 1 (✓ expected: 1)
  • land_tenure: 3 (⚠️ review: typically 1-2)
  • gis_shapefile: 1 (✓ expected: 1+)

⚠️ **Note:** Found more land tenure documents than typical—please verify all are relevant.

## Quality Indicators
- Average classification confidence: 87%
- High-confidence documents: 6/7 (86%)
- Low-confidence documents: 1 (requires review)
- Skipped files: 0
- Health issues: 0

## Discovered Documents
[List with enhanced metadata...]

## Next Steps

✅ Discovery complete and ready for evidence extraction

**Recommended:**
1. Review the 1 low-confidence document (marked with ~)
2. Verify land tenure documents (3 found)
3. Proceed to evidence extraction:
   `/evidence-extraction`

**Optional:**
- Re-run discovery if documents were added: `/document-discovery`
- Manually reclassify documents: [instructions]
```

#### Confirmation Mechanisms

**Current:**
- No explicit confirmation step
- Discovery results are final
- User must trust the classification

**Missing:**
- Ability to preview classifications before finalizing
- Batch reclassification UI
- Manual document addition/removal

**Proposed: Two-phase discovery**

Phase 1: Preview Mode
```markdown
# Document Discovery Preview

Found **7 potential documents**. Please review before finalizing:

1. ✓ project-plan-2023.pdf → project_plan (95% confidence)
2. ✓ baseline-2022.pdf → baseline_report (95% confidence)
3. ~ annual-report.pdf → monitoring_report (70% confidence)
   **Alternative:** Could be annual_report or monitoring_report
   **Action:** [Confirm] [Change to: baseline_report ▼] [Ignore]
...

[Confirm All] [Review Changes] [Cancel]
```

Phase 2: Finalization
```markdown
Applied 1 correction:
- annual-report.pdf: monitoring_report → baseline_report (manual)

Finalizing discovery...

[Success output]
```

**Trade-off analysis:**
- **Pro:** Gives user control, reduces downstream errors
- **Con:** Adds friction to workflow
- **Recommendation:** Make preview optional (default: auto-finalize, flag for --preview mode)

---

### 5. State & Progress Visibility

#### Session State Tracking

**Current state updates:**

```python
state_manager.update_json(
    "session.json",
    {
        "statistics": {
            "documents_found": len(documents),
        },
        "workflow_progress": {
            "document_discovery": "completed",
        },
    },
)
```

**What's tracked:**
- ✅ Document count
- ✅ Completion status

**What's missing:**
- Discovery timestamp
- Processing duration
- Directory scan details
- Classification confidence statistics
- Change history (if re-run)

**Enhanced state:**

```json
{
  "statistics": {
    "documents_found": 7,
    "classification_breakdown": {
      "project_plan": 2,
      "baseline_report": 1,
      "land_tenure": 3,
      "gis_shapefile": 1
    },
    "confidence_stats": {
      "average": 0.87,
      "high_confidence_count": 6,
      "low_confidence_count": 1
    }
  },
  "workflow_progress": {
    "document_discovery": "completed"
  },
  "discovery_metadata": {
    "discovered_at": "2025-11-14T10:30:45Z",
    "processing_time_seconds": 3.2,
    "directories_scanned": 4,
    "max_depth_reached": 3,
    "skipped_files": [],
    "health_issues": []
  },
  "discovery_history": [
    {
      "timestamp": "2025-11-10T14:20:00Z",
      "documents_found": 5,
      "changes": null
    },
    {
      "timestamp": "2025-11-14T10:30:45Z",
      "documents_found": 7,
      "changes": {
        "added": 2,
        "removed": 0,
        "modified": 1
      }
    }
  ]
}
```

#### Progress Indicators

**For quick operations (<5 seconds):**
- Simple "Discovering documents..." message
- Completed message with results

**For longer operations (>5 seconds):**
- Show progress bar or count
- Indicate current file being processed
- Show estimated time remaining
- Allow cancellation

**Implementation approach:**

Option A: Server-side streaming (complex)
```python
async def discover_documents_streaming(session_id: str):
    async for progress in scan_directory():
        yield {
            "type": "progress",
            "current": progress.current,
            "total": progress.total,
            "file": progress.current_file
        }

    yield {"type": "complete", "results": results}
```

Option B: Chunked processing (simpler)
```python
async def discover_documents_chunked(session_id: str, batch_size: int = 20):
    all_files = list_all_files()

    for chunk in chunks(all_files, batch_size):
        process_chunk(chunk)
        yield f"Processed {len(chunk)} files..."

    yield "Complete!"
```

Option C: Threshold-based (recommended)
```python
async def discover_documents(session_id: str):
    files = list_all_files()

    if len(files) > 50:
        # Large dataset: show progress
        for i, file in enumerate(files):
            process_file(file)
            if i % 10 == 0:
                print(f"Progress: {i}/{len(files)}")
    else:
        # Small dataset: just process
        for file in files:
            process_file(file)
```

---

### 6. Recovery & Resilience

#### Partial Failure Handling

**Scenario: 50 files discovered, 45 processed successfully, 5 failed**

Current behavior:
- Logs warnings for failed files
- Continues processing
- Saves 45 documents
- **No indication to user that 5 failed**

**Resilience evaluation:**
- ✅ Doesn't fail completely due to one bad file
- ❌ Silent failures may cause confusion downstream
- ❌ No way to retry just failed files

**Enhanced approach:**

```python
# Track successes and failures separately
results = {
    "successful": [],
    "failed": [],
    "skipped": []
}

for file in discovered_files:
    try:
        doc = process_file(file)
        results["successful"].append(doc)
    except CriticalError as e:
        results["failed"].append({"file": file, "error": str(e)})
    except SkippableError as e:
        results["skipped"].append({"file": file, "reason": str(e)})

# Save successful documents
save_documents(results["successful"])

# Report all outcomes
return generate_report(results)
```

**User-facing output:**

```markdown
# Document Discovery - Partial Results

## Summary
- ✅ Successfully processed: 45 documents
- ⚠️ Failed to process: 5 documents
- ℹ️ Skipped: 2 documents (hidden files)

## Processing Errors

The following files could not be processed:

1. **corrupted-file.pdf**
   - Error: PDF is corrupted or encrypted
   - Recommendation: Obtain uncorrupted version

2. **huge-raster.tif**
   - Error: File too large (2.3 GB exceeds 1 GB limit)
   - Recommendation: Split or compress file

[View all errors]

## What This Means

Document discovery is **partially complete**. You can proceed with evidence extraction for the 45 successfully processed documents, but the review will be incomplete until the failed files are resolved.

**Next Steps:**
1. Resolve the 5 failed files (see errors above)
2. Re-run discovery to pick up fixed files: `/document-discovery`
3. OR proceed with partial results: `/evidence-extraction`

⚠️ **Warning:** Proceeding with incomplete discovery may result in missing evidence for certain requirements.
```

#### Idempotency & Re-run Safety

**Scenario: User accidentally runs discovery twice**

Current behavior:
- Overwrites documents.json
- No confirmation prompt
- No diff shown

**Issues:**
- May erase manual corrections
- No undo mechanism
- Confusing if results change (e.g., due to file modifications)

**Safe re-run approach:**

```markdown
# Re-Running Document Discovery

A previous discovery was completed on **2025-11-10 14:20:00**.

**Previous results:** 5 documents
**Current scan:** 7 documents detected

## Detected Changes
- 2 new files
- 1 modified file
- 0 removed files

## Manual Corrections at Risk
⚠️ **Warning:** You previously made 1 manual classification correction:
- `annual-report.pdf`: monitoring_report → baseline_report (manual)

Re-running will reset this to automatic classification.

**Options:**
1. [Preserve manual corrections] - Only update changed/new files
2. [Full re-scan] - Reclassify everything from scratch
3. [Cancel] - Keep existing discovery results

Recommended: **Preserve manual corrections**
```

#### Crash Recovery

**Scenario: Discovery interrupted mid-process**

Possible causes:
- Server crash
- Network disconnection
- User cancellation
- Out of memory

**Current behavior:**
- Partial processing lost
- documents.json may be in inconsistent state
- Must start over completely

**Resilient approach:**

1. **Atomic writes:**
```python
# Write to temporary file first
temp_path = f"{documents_path}.tmp"
write_json(temp_path, documents_data)

# Atomic rename
os.rename(temp_path, documents_path)
```

2. **Checkpoint-based processing:**
```python
checkpoint = load_checkpoint()

for file in all_files:
    if file in checkpoint.processed:
        continue  # Skip already processed

    process_file(file)
    checkpoint.mark_processed(file)
    save_checkpoint(checkpoint)
```

3. **Recovery detection:**
```python
if checkpoint_exists():
    print(f"""
    # Document Discovery - Resume Available

    A previous discovery was interrupted.

    Progress: 45/100 files processed
    Last processed: project-plan-v2.pdf

    [Resume from checkpoint]
    [Start fresh]
    """)
```

---

### 7. Accessibility & Inclusivity

#### Language & Terminology

**Current terminology:**
- "Document discovery" - ✅ Clear, professional
- "Classification confidence" - ✅ Transparent about uncertainty
- "Indexed at" - ⚠️ Technical jargon (better: "Added on")
- "IRI" - ❌ Too technical (not visible to users, good)

**Recommendations:**
- Keep technical terms in internal data structures
- Use plain language in user-facing messages
- Provide glossary or tooltips for specialized terms

#### Cognitive Load

**Current output cognitive load:**
- **Summary section:** Low load (counts and categories)
- **Classification breakdown:** Low load (simple list)
- **Document list:** Medium-high load (7+ items with metadata)

**Strategies to reduce load:**
- **Progressive disclosure:** Show summary first, expand details on demand
- **Visual grouping:** Group by classification type
- **Filtering:** Allow hiding low-confidence or certain types
- **Search:** For large document sets (>20 documents)

**Example: Progressive disclosure**

```markdown
# Document Discovery Complete

**Found 47 documents** across 8 categories

[Show classification breakdown ▼]
[Show all documents ▼]
[Show low-confidence only ▼]

## Quick Actions
- [Proceed to evidence extraction]
- [Review classifications]
- [Re-run discovery]
```

#### Error Message Quality

**Current error message example:**

```markdown
✗ Error During Document Discovery

Session: session-abc123
Error: [Errno 2] No such file or directory: '/path/to/documents'
```

**Issues:**
- Technical error code exposed
- No explanation in user terms
- No suggested fix

**Improved error message:**

```markdown
# Document Discovery Failed

**Problem:** The documents folder could not be found

**Details:**
- Expected path: `/path/to/documents`
- Error: Directory does not exist

**Possible Solutions:**

1. **Verify the path is correct:**
   - Check for typos in the path
   - Confirm the path is absolute (starts with `/`)

2. **Check the directory exists:**
   - Run: `ls -la /path/to/documents`
   - If not found, locate the correct documents folder

3. **Update the session with correct path:**
   - Load session: `load_session session-abc123`
   - Update documents_path field
   - Try discovery again

**Need Help?**
- [View documentation on session setup]
- [Contact support]
```

---

### 8. Performance & Scalability

#### Expected Performance Characteristics

**Baseline performance targets:**

| Document Count | Expected Duration | Acceptable Duration | UX Impact |
|----------------|-------------------|---------------------|-----------|
| 1-10 | <1 second | <2 seconds | Instant feedback |
| 11-50 | 1-3 seconds | <5 seconds | Brief wait acceptable |
| 51-100 | 3-10 seconds | <15 seconds | Progress indicator needed |
| 101-500 | 10-60 seconds | <2 minutes | Progress + time estimate |
| 500+ | 1-5 minutes | <10 minutes | Consider chunking |

**Current implementation bottlenecks:**

1. **Synchronous processing:** All files processed sequentially
   - Solution: Parallel processing with `asyncio.gather()`

2. **PDF metadata extraction:** Opens each PDF to count pages/tables
   - Solution: Lazy extraction (only when needed for evidence)

3. **No caching:** Re-processes unchanged files on re-run
   - Solution: Checksum-based caching

#### Scalability Strategies

**Incremental Discovery**

For very large document sets, support incremental discovery:

```markdown
# Document Discovery - Incremental Mode

Processing in batches for optimal performance...

Batch 1 of 5: Complete (100 documents)
Batch 2 of 5: In progress... (45/100)

Total progress: 145/500 documents (29%)

[Pause] [Cancel]
```

**Prioritized Processing**

Process high-value documents first:

1. PDFs in root directory (likely key documents)
2. Specifically named files (project-plan, baseline, etc.)
3. GIS files
4. Other PDFs
5. Images

Show initial results before completing full scan:

```markdown
# Document Discovery - Early Results

Found **5 high-priority documents** so far:
- project-plan-2023.pdf (project_plan)
- baseline-report.pdf (baseline_report)
...

Still scanning remaining directories (estimated 2 minutes)...

[View early results] [Wait for complete scan]
```

**Smart Filtering**

For repeated runs, only re-process changed files:

```python
def smart_discovery(session_id: str):
    previous = load_previous_documents()
    current_files = scan_directory()

    # Quick checksum comparison
    unchanged = [f for f in current_files
                 if checksum(f) in previous_checksums]

    changed = current_files - unchanged

    # Only process changed files
    new_docs = process_files(changed)

    # Merge with unchanged
    return merge(previous, new_docs)
```

---

### 9. Trust & Transparency

#### Building Confidence in Classification

**Key question:** "How do I know the classification is correct?"

**Current approach:**
- Confidence score (0.0-1.0)
- Classification method ("filename", "file_type", "default")
- Icon indicator (✓ or ~)

**Trust factors:**

✅ **Positive:**
- Explicit confidence scoring acknowledges uncertainty
- Shows classification method (not a black box)
- Conservative confidence thresholds (≥0.80 for high confidence)

⚠️ **Gaps:**
- No explanation of WHY a classification was chosen
- No way to see alternative classifications considered
- Pattern matching logic is opaque

**Enhanced transparency:**

```markdown
2. ✓ baseline-2022-report-final.pdf
   Type: baseline_report (95% confidence)
   Method: Filename pattern matching

   **Why this classification?**
   - Matched pattern: "baseline[\s_-]?report"
   - Filename contains: "baseline" and "report"
   - File type: PDF (expected for baseline_report)

   **Alternative classifications:**
   - monitoring_report: 45% (less likely - no monitoring keywords)

   [Accept] [Change classification] [View file]
```

#### Audit Trail

**Current tracking:**
- `indexed_at`: When document was discovered
- `classification_method`: How it was classified

**Missing for full auditability:**
- Discovery run ID (links document to specific discovery execution)
- Pattern matched (which specific regex triggered the classification)
- Manual override history (if classification was corrected)
- File checksums (to detect if file changed)

**Full audit structure:**

```json
{
  "document_id": "DOC-abc123",
  "filename": "baseline-report.pdf",
  "classification": "baseline_report",
  "confidence": 0.95,
  "audit_trail": {
    "discovery_run_id": "DISC-2025-11-14-001",
    "discovered_at": "2025-11-14T10:30:45Z",
    "classification_history": [
      {
        "timestamp": "2025-11-14T10:30:45Z",
        "classification": "baseline_report",
        "confidence": 0.95,
        "method": "filename",
        "pattern_matched": "baseline[\\s_-]?report",
        "actor": "system"
      }
    ],
    "file_history": [
      {
        "timestamp": "2025-11-14T10:30:45Z",
        "checksum": "sha256:abc123...",
        "file_size": 2458624,
        "modification_date": "2025-11-10T14:20:00Z"
      }
    ]
  }
}
```

#### Explainability

For each classification decision, the system should be able to answer:

1. **What** was classified?
   - Filename, file type, file size, location

2. **How** was it classified?
   - Pattern matching, heuristics, manual override

3. **Why** this classification?
   - Which pattern matched, confidence calculation

4. **What else** was considered?
   - Alternative classifications, why they were rejected

5. **When** was it classified?
   - Timestamp, discovery run ID

6. **Who** classified it?
   - System (automatic) or human (manual override)

**Implementation:**

```python
class ClassificationExplanation:
    def __init__(self):
        self.decision = None
        self.confidence = None
        self.reasoning = []
        self.alternatives = []

    def add_reasoning(self, factor: str, weight: float):
        self.reasoning.append({
            "factor": factor,
            "weight": weight,
            "contribution": weight * self.confidence
        })

    def add_alternative(self, classification: str, confidence: float, reason: str):
        self.alternatives.append({
            "classification": classification,
            "confidence": confidence,
            "reason_rejected": reason
        })

    def to_markdown(self) -> str:
        # Generate human-readable explanation
        ...
```

---

### 10. Integration Points

#### Downstream Dependencies

**Evidence Extraction Stage** depends on:
- ✅ Document IDs (for referencing)
- ✅ Document classifications (for requirement mapping)
- ✅ File paths (for content extraction)
- ⚠️ Classification confidence (should inform evidence search strategy)
- ❌ Document relationships (e.g., "this monitoring report supersedes that one")

**Cross-Validation Stage** depends on:
- ✅ Document metadata (for date/name checking)
- ⚠️ Document completeness (are all expected types present?)
- ❌ Document version tracking (which is most recent?)

#### Upstream Dependencies

Discovery depends on:
- ✅ Valid session with documents_path configured
- ✅ File system access permissions
- ✅ Supported file types present
- ⚠️ Network access (if documents are on network storage)
- ❌ External services (currently none, but future: cloud storage APIs)

#### Data Contracts

**Output contract (documents.json):**

```typescript
interface DocumentsData {
  documents: Document[];
  total_count: number;
  classification_summary: Record<string, number>;
  discovered_at: string;  // ISO 8601 timestamp

  // Proposed additions:
  discovery_run_id?: string;
  processing_time_seconds?: number;
  skipped_files?: SkippedFile[];
  health_issues?: HealthIssue[];
}

interface Document {
  document_id: string;           // DOC-xxxxxxxx
  filename: string;               // base filename
  filepath: string;               // absolute path
  classification: string;         // document type
  confidence: number;             // 0.0-1.0
  classification_method: string;  // "filename" | "file_type" | "default" | "manual"
  metadata: DocumentMetadata;
  indexed_at: string;            // ISO 8601 timestamp

  // Proposed additions:
  health_status?: "ok" | "warning" | "error";
  health_message?: string;
  alternative_classifications?: AlternativeClassification[];
  file_checksum?: string;
}
```

**Contract guarantees:**
- All documents have unique `document_id`
- All filepaths are absolute and valid at time of discovery
- `total_count` always equals `documents.length`
- `classification_summary` sums to `total_count`
- `discovered_at` is in UTC timezone

**Breaking changes to avoid:**
- Changing `document_id` format (downstream references will break)
- Removing or renaming classification types (evidence mappings will break)
- Changing filepath from absolute to relative (extraction will fail)

---

## Critical UX Issues & Recommendations

### Priority 1 (Must Fix)

1. **Silent file processing failures**
   - **Issue:** Errors logged but not reported to user
   - **Impact:** Incomplete discovery without user awareness
   - **Fix:** Collect and report all skipped/failed files

2. **No change detection on re-run**
   - **Issue:** Overwrites previous results without showing what changed
   - **Impact:** Lost context, manual corrections erased
   - **Fix:** Implement delta detection and change reporting

3. **Missing progress feedback for large sets**
   - **Issue:** Appears frozen during long scans (>50 files)
   - **Impact:** User uncertainty, perceived unreliability
   - **Fix:** Add progress indicator for scans >5 seconds

### Priority 2 (Should Fix)

4. **Low confidence classifications lack guidance**
   - **Issue:** User doesn't know what to do with ~ marked documents
   - **Impact:** Confusion, potential downstream errors
   - **Fix:** Provide actionable next steps for low-confidence docs

5. **No manual classification correction flow**
   - **Issue:** If classification is wrong, no clear way to fix
   - **Impact:** User frustration, incorrect downstream mappings
   - **Fix:** Add reclassification tool or preview/confirm step

6. **Shapefile components treated as separate documents**
   - **Issue:** Clutters list, confuses logical structure
   - **Impact:** Poor UX for GIS-heavy projects
   - **Fix:** Group shapefile components into single logical document

### Priority 3 (Nice to Have)

7. **No directory structure visibility**
   - **Issue:** User can't see which subdirectories were scanned
   - **Impact:** Uncertainty about coverage
   - **Fix:** Show directory tree or list scanned paths

8. **Missing classification reasoning**
   - **Issue:** User doesn't know WHY a classification was chosen
   - **Impact:** Reduced trust in automated classification
   - **Fix:** Add explanation for each classification

9. **No preview or early results for large scans**
   - **Issue:** Must wait for entire scan to see any results
   - **Impact:** Long wait time, poor perceived performance
   - **Fix:** Show high-priority results as they're found

---

## Implementation Recommendations

### Quick Wins (Low Effort, High Impact)

1. **Add skipped files section to output**
   ```python
   # Collect during processing
   skipped_files = []
   # Include in final output
   if skipped_files:
       output += format_skipped_files(skipped_files)
   ```

2. **Show discovery timestamp and duration**
   ```python
   start_time = time.time()
   # ... process ...
   duration = time.time() - start_time
   output += f"Processing time: {duration:.1f} seconds"
   ```

3. **Highlight unexpected results**
   ```python
   # Check against typical patterns
   if classification_summary.get("unknown", 0) > 2:
       output += "⚠️ Note: Found more unclassified documents than typical"
   ```

### Medium Effort, High Value

4. **Implement change detection**
   - Load previous documents.json
   - Compare filepaths and checksums
   - Generate added/modified/removed lists
   - Preserve manual classifications

5. **Add classification explanation**
   - Store matched pattern with classification
   - Generate human-readable reasoning
   - Show in detailed document view

6. **Group shapefile components**
   - Detect .shp files
   - Look for matching .shx, .dbf, .prj
   - Create single logical document with components list

### Larger Efforts (Significant Work)

7. **Preview/confirm workflow**
   - Two-phase discovery (scan → review → finalize)
   - Interactive reclassification UI
   - Batch operations

8. **Progress streaming**
   - Chunked processing with yield
   - Real-time progress updates
   - Cancellation support

9. **Smart caching and incremental discovery**
   - Checksum-based change detection
   - Only reprocess changed files
   - Checkpoint-based resume

---

## Success Metrics

### Quantitative Metrics

- **Accuracy:** Classification accuracy ≥85% (vs. manual review)
- **Coverage:** Discovery finds ≥98% of expected documents
- **Performance:** Processing <0.2 seconds per document on average
- **Reliability:** Error rate <2% (files that fail to process)
- **Idempotency:** Re-running produces identical results for unchanged files

### Qualitative Metrics

- **Confidence:** Becca trusts the classification without manual verification
- **Clarity:** Becca understands what was found and why
- **Control:** Becca can easily correct misclassifications
- **Awareness:** Becca knows when something is missing or wrong
- **Efficiency:** Discovery saves time vs. manual file organization

### User Satisfaction Indicators

Post-discovery survey questions:
1. "The discovery results matched my expectations" (1-5 scale)
2. "I felt confident in the document classifications" (1-5 scale)
3. "I knew what to do when a classification looked wrong" (1-5 scale)
4. "The discovery process felt fast enough" (1-5 scale)
5. "I understood which documents were included and why" (1-5 scale)

Target: Average score ≥4.0 across all questions

---

## Open Questions

1. **Should discovery be automatic or manual-confirm?**
   - Current: Automatic (fire-and-forget)
   - Alternative: Preview classifications, user confirms before finalizing
   - Trade-off: Speed vs. accuracy

2. **How deep should directory recursion go?**
   - Current: Unlimited recursion
   - Alternative: Configurable max depth (default 5?)
   - Trade-off: Completeness vs. performance and relevance

3. **Should we support remote document sources?**
   - Current: Local filesystem only
   - Proposed: Google Drive, SharePoint, S3
   - Complexity: Authentication, permissions, sync

4. **How should we handle document versions?**
   - Current: Treat each file independently
   - Alternative: Detect versions (project-plan-v1.pdf, project-plan-v2.pdf)
   - UX: Auto-select latest version, flag superseded versions

5. **What's the right balance between automation and control?**
   - Full automation: Fast but may make mistakes
   - Full manual: Slow but accurate
   - Hybrid: Automated with preview/override?

6. **Should discovery support incremental updates?**
   - Current: Full re-scan on each run
   - Alternative: "Add documents" command for incremental updates
   - Benefit: Avoids re-processing entire directory

---

## Conclusion

Document Discovery is the foundation of the entire Registry Review workflow. Getting this stage right is critical because errors here cascade through all downstream stages. The UX must balance three competing demands:

1. **Speed:** Fast enough to feel responsive, even with large document sets
2. **Accuracy:** Classification confidence high enough to trust
3. **Transparency:** Clear enough that Becca knows exactly what's happening

The current implementation handles the happy path well but needs enhancement for edge cases, error scenarios, and user confidence-building. The recommended improvements focus on:

- **Visibility:** Show what's happening, what was found, what went wrong
- **Control:** Give Becca tools to correct mistakes and guide the process
- **Resilience:** Handle errors gracefully, support re-runs safely
- **Trust:** Explain decisions, acknowledge uncertainty, provide audit trails

With these enhancements, Document Discovery can evolve from a basic file scanner into a intelligent, trustworthy workflow partner that actively helps Becca understand and organize the project documents.

---

**Next Steps:**
1. Review this analysis with Becca and the team
2. Prioritize issues based on real-world pain points
3. Implement Priority 1 fixes immediately
4. Design and prototype Priority 2 enhancements
5. Gather user feedback after each improvement
6. Iterate based on usage patterns and feedback

**Related Documents:**
- State Machine Analysis (docs/STATE_MACHINE_ANALYSIS.md)
- MVP Workflow Specification (docs/specs/2025-11-11-registry-review-mvp-workflow.md)
- Stage 1: Initialization Analysis (docs/specs/UX/01_initialization_stage_analysis.md)
