# First-Principles Architecture Redesign

Created: 2026-02-07
Status: Draft for discussion

## The Irreducible Job

Strip away every implementation detail. The system's job is:

> Given documents and a fixed checklist, determine whether each requirement is satisfied by evidence in the documents, and produce an auditable report.

That's one sentence. Everything else is infrastructure. Every architectural decision should be tested against: does this make that sentence execute faster, cheaper, more reliably, or more accurately?

## Why the Current 8-Stage Pipeline Falls Short

The current architecture models the workflow as a linear batch pipeline:

```
A: Initialize → B: Discover → C: Map → D: Extract → E: Validate → F: Report → G: Review → H: Complete
```

This model has seven structural problems:

**1. It assumes all documents arrive at once.** Carbon Egg's documents will arrive incrementally (100+ farms, different timelines). Adding one document shouldn't mean re-running everything.

**2. It forces sequential processing where parallel is possible.** Document extraction and requirement loading are independent. Classification and metadata extraction are independent per-document. Nothing prevents extracting evidence while still classifying the last few files.

**3. The mapping stage is fragile and unnecessary as a separate step.** The heuristic mapping (Stage C) uses string matching between classification labels and expected document types. It fails on naming convention mismatches (the bug we found: `"land_tenure"` vs `"land-tenure"`). More fundamentally, mapping requirements to documents is an LLM task, not a pattern-matching task. It should be part of the evidence extraction, not a separate stage.

**4. Validation is not a stage; it's a property of evidence.** Cross-validation (Stage E) checks whether evidence across documents is consistent. But this should happen at extraction time. When you extract a project start date from Document A, you should simultaneously check whether it matches Document B. Making it a separate stage means the LLM loses context.

**5. It does expensive work eagerly.** Every document gets classified, mapped, and extracted, even if a cheaper heuristic could determine that a requirement is trivially satisfied (or obviously missing).

**6. It has no memory across projects.** Carbon Egg has 100+ farms sharing the same methodology document, the same program guide, the same credit class. The system re-processes these shared documents for every farm.

**7. It provides no partial results.** The user sees nothing until the pipeline completes. A better system would show fast heuristic results immediately, then progressively upgrade them.

## Proposed Architecture: Layers, Not Stages

Instead of 8 sequential stages, the system should have 4 concurrent **layers**, each operating at a different cost/quality tier. Think of it like a CPU cache hierarchy:

```
Layer 1: Document Intelligence     (instant, free)     — L1 cache
Layer 2: Requirement Intelligence  (instant, free)     — L2 cache
Layer 3: Evidence Analysis         (seconds-minutes)   — Main memory
Layer 4: Reporting & Review        (instant, deterministic) — Output
```

### Layer 1: Document Intelligence

**Purpose:** Convert raw files into a form the system can reason about.

**Operations (in order of cost):**
1. **File inventory** — Scan directory, identify files by extension (instant)
2. **Metadata extraction** — File size, page count, creation date (instant, cached by content hash)
3. **Classification** — What type of document is this? (fast heuristic, upgradeable by LLM)
4. **Text extraction** — Convert PDF/XLSX/CSV to text (seconds per file, cached by content hash)
5. **Section detection** — Identify headings, tables, structure (derived from extracted text)
6. **Content fingerprint** — Key terms, entities, dates found in document (cheap NLP or regex)

**Cache strategy:** Content-addressable by file hash. If the same file appears in 100 projects, extract it once. Cache lives indefinitely until the file changes.

**Key principle:** This layer runs eagerly. The moment a document appears, start processing it. Background jobs handle HQ extraction. By the time the user asks for analysis, the documents are already ready.

### Layer 2: Requirement Intelligence

**Purpose:** Understand what the checklist is asking for and what evidence would satisfy it.

**Operations:**
1. **Checklist loading** — Parse the methodology's requirement JSON (instant)
2. **Evidence pattern compilation** — For each requirement, pre-compute what to look for: keywords, expected document types, validation rules (done once per checklist version)
3. **Requirement dependency graph** — Which requirements corroborate each other? REQ-002 (land tenure) and REQ-004 (project area) both deal with geographic boundaries. REQ-007 (start date) and REQ-010 (crediting period) both reference dates. Understanding these relationships enables cross-validation as a natural byproduct of extraction, not a separate pass.

**Cache strategy:** Immutable per checklist version. Compute once, use forever.

**Key principle:** This layer is pre-computed. The checklist doesn't change during a review. All intelligence about what to look for should be ready before any documents are analyzed.

### Layer 3: Evidence Analysis

**Purpose:** Match documents to requirements, extract evidence, validate consistency.

This is the expensive layer. It uses LLM inference. The design principle is: **never send more to the LLM than necessary, never ask it the same question twice, and always provide the best context.**

**The evidence extraction loop:**

```
For each requirement:
  1. Can this be resolved without LLM? (confidence cascade)
     - Check Layer 1 content fingerprints against Layer 2 evidence patterns
     - If a document classified as "land_tenure" exists and REQ-002 asks for land tenure → high-confidence heuristic match
     - If heuristic confidence > 95%: mark as "heuristic_pass", skip LLM
     - If heuristic confidence < 30%: mark as "likely_missing", flag for human review
     - If between 30-95%: needs LLM analysis

  2. LLM analysis (only for ambiguous requirements):
     - Send only relevant document sections (not entire documents)
     - Include requirement context from Layer 2
     - Extract evidence with citations
     - Cross-validate against related requirements simultaneously
     - Return structured result with confidence score
```

**Batching strategy:** Don't send one requirement at a time. Group related requirements and relevant document sections into a single LLM call. The current "unified analysis" approach is close to right, but it should be smarter about what it sends:

- **Dense projects** (many documents, many requirements): Send requirement clusters with targeted document sections
- **Sparse projects** (few documents, many requirements): Send everything in one call (current approach)
- **Incremental updates** (one new document added): Only re-evaluate requirements that the new document could affect

**Cache strategy:** Cache at the `(document_content_hash, requirement_id, checklist_version)` level. If the same project plan is used for 15 requirements, the extraction results are cached individually. If one requirement's definition changes in a new checklist version, only that requirement is re-extracted.

**Key principle:** Every LLM call should be the minimum necessary to answer a specific question with maximum context. The system should be able to explain exactly why each call was made and what it cost.

### Layer 4: Reporting & Review

**Purpose:** Present evidence analysis as a structured, auditable report.

**Operations:**
1. **Report assembly** — Combine evidence results into structured tables (deterministic, instant)
2. **Human review flagging** — Identify items that need expert judgment (rule-based from evidence confidence)
3. **Export** — Generate Markdown, DOCX, PDF from the same structured data (template-based)
4. **Audit trail** — Record what was checked, what was found, what was flagged, who approved

**Cache strategy:** Report is derived data. Invalidated whenever evidence changes. Re-generated instantly.

**Key principle:** This layer adds zero intelligence. It's pure presentation. If the report looks wrong, the problem is in Layer 3, not here.

## Performance Strategy Matrix

Ten strategies for radical performance improvement, evaluated across four dimensions:

| # | Strategy | Speed | Cost | Reliability | Complexity |
|---|---------|-------|------|-------------|------------|
| 1 | Content-addressable document cache | +++ | +++ | ++ | + |
| 2 | Evidence confidence cascade | ++ | +++ | + | ++ |
| 3 | LLM-guided mapping (replace heuristics) | + | - | +++ | + |
| 4 | Incremental processing | ++ | ++ | ++ | +++ |
| 5 | Smart chunking (send relevant sections only) | ++ | +++ | + | ++ |
| 6 | Background pre-computation | +++ | 0 | + | ++ |
| 7 | Shared document library | +++ | +++ | + | ++ |
| 8 | Progressive quality (fast results → LLM upgrade) | +++ | 0 | + | ++ |
| 9 | Warm start for batch projects | ++ | +++ | + | +++ |
| 10 | Requirement dependency graph | + | + | +++ | ++ |
| 11 | Prompt template caching (Anthropic API) | 0 | +++ | 0 | 0 |
| 12 | Unified analysis with targeted context | + | ++ | ++ | + |

Legend: `+++` = major improvement, `++` = moderate, `+` = minor, `0` = neutral, `-` = slight cost, `---` = major cost

### Strategy Details

**1. Content-addressable document cache.** Hash every file. Store extraction results keyed by hash. If Carbon Egg's methodology document (same file, same hash) appears in 100 farm project folders, extract text once. For a 100-farm project, this could reduce document processing from 500 files to 50 unique files (90% reduction). This is the single biggest efficiency win.

**2. Evidence confidence cascade.** Not every requirement needs LLM analysis. "Does REQ-013 mention a 10-year permanence period?" can be answered by regex search in the extracted text. If the text literally says "10-year permanence period" in a document classified as a project plan, the confidence is >99% without ever calling an LLM. Reserve LLM for genuinely ambiguous cases: "Does the monitoring plan in Section 5 adequately describe sampling protocols?" Estimated LLM call reduction: 40-60%.

**3. LLM-guided mapping (replace heuristics).** The current heuristic mapping (`_infer_document_types()`) is 60 lines of brittle string matching. Replace it with a single lightweight Haiku call: "Given these 5 documents and 23 requirements, which documents are most likely to contain evidence for each requirement? Return a JSON mapping." Cost: ~$0.02 per project. Reliability improvement: eliminates the entire category of naming-convention bugs.

**4. Incremental processing.** When a user adds a document to an existing session, the system should: (a) extract and classify only the new document, (b) identify which requirements the new document could affect (using Layer 2 patterns), (c) re-extract only those requirements, (d) regenerate the report. This transforms a 2-minute re-run into a 15-second update.

**5. Smart chunking.** Before sending documents to the LLM, use Layer 1 features to identify relevant sections. If REQ-017 asks about "monitoring plan" and the project plan's table of contents has a "Section 5: Monitoring Plan" heading, send only Section 5 (2 pages) instead of the entire 45-page document. Token reduction: 60-80% per call.

**6. Background pre-computation.** The moment documents are uploaded (or pulled from GDrive), start extracting text, computing metadata, running classification, and building content fingerprints. All of this is Layer 1 work: cheap and parallelizable. By the time the user clicks "Run Review," the system is starting from Layer 3, not Layer 1.

**7. Shared document library.** Methodology guides, program guides, and credit class documents are shared across all projects using that protocol. Extract and index these once. When a new project starts, the shared documents are already processed. For Carbon Egg: the credit class, methodology, and PDD are shared across all 100+ farms.

**8. Progressive quality.** Return results at each quality tier as they become available:
- **Instant** (< 1 second): File inventory, basic classification, requirements loaded
- **Fast** (5-10 seconds): Heuristic matching, keyword-based evidence, coverage estimate
- **Full** (1-2 minutes): LLM-extracted evidence, cross-validated, confidence scores
- **HQ** (5-15 minutes per document): Marker-upgraded text, re-extracted if quality matters

The user sees a live-updating dashboard, not a loading spinner.

**9. Warm start for batch projects.** After processing the first Carbon Egg farm, the system has learned what evidence structure to expect. For farms 2-100, use a compressed prompt: "Extract the same fields you found for Farm 1, but for this farm's documents. Here are Farm 1's results as a template." This reduces prompt size by 50% and improves consistency across farms.

**10. Requirement dependency graph.** Model relationships between requirements. REQ-002 (land tenure) and REQ-004 (project area) both reference geographic information. REQ-007 (start date) and REQ-010 (crediting period) both reference temporal information. When extracting evidence for one, automatically cross-reference the other. This makes "cross-validation" a natural byproduct, not a separate pass.

**11. Prompt template caching.** Already partially implemented. The system prompt and checklist requirements are constant across projects. Using Anthropic's `cache_control: ephemeral` on these segments gives 90% input cost savings on cached tokens. This should be extended to include shared reference documents.

**12. Unified analysis with targeted context.** The current unified analysis sends all documents to one LLM call. Better: use Layer 1 heuristics to pre-filter, then send a curated context window. Each LLM call gets exactly the document sections relevant to its requirement cluster, plus the cross-validation context it needs.

## Reliability Matrix

How to make the system never produce wrong results:

| Failure Mode | Current Handling | Proposed Handling |
|-------------|-----------------|-------------------|
| Document extraction fails | Skips document, warns | Retry with fallback extractor, quarantine if fails |
| LLM hallucinates evidence | Not detected | Citation verification: every claim must trace to exact text in extracted document |
| LLM returns malformed JSON | Retry with same prompt | Retry with simplified prompt, then graceful degradation to heuristic result |
| Classification wrong | Silent, propagates | LLM verification of heuristic classification (cheap Haiku call) |
| Cache serves stale results | TTL-based expiry | Content-hash-based: stale results are impossible if hash matches |
| Duplicate document processed twice | Content hash dedup at discovery | Content-addressable cache makes this automatic at every layer |
| Requirement checklist has errors | Trusted as ground truth | Schema validation on checklist load, version tracking |
| Network failure during LLM call | Retry with backoff | Retry with backoff + save partial results + resume from last good state |
| Memory exhaustion during HQ conversion | Wait/timeout | Memory reservation system, graceful queue management |
| Concurrent session state corruption | File locking | File locking + content-addressed immutable artifacts |

### The Citation Verification Principle

Every evidence claim the LLM makes must pass a verification check:

```
LLM says: "Project start date is January 17, 2022 (Section 1.2, Page 5)"

Verification:
1. Does the document's extracted text contain "January 17, 2022"?  → Yes/No
2. Is this text on or near page 5?  → Yes/No
3. Is this in a section that matches "1.2" or "Section 1"?  → Yes/No

If all pass: confidence stays high
If any fail: downgrade confidence, flag for human review
```

This is cheap (string matching on already-extracted text) and catches the most dangerous LLM failure mode: confident but wrong citations. It transforms the system from "trust the LLM" to "trust but verify."

## Efficiency Matrix: Where Time and Money Go

Current cost profile for one project (23 requirements, ~5 documents):

| Operation | Time | API Cost | Frequency |
|-----------|------|----------|-----------|
| File scanning and metadata | < 1s | $0 | Once |
| Fast PDF extraction (PyMuPDF) | 2-3s/doc | $0 | Once per document |
| HQ PDF extraction (Marker) | 5-15min/doc | $0 | Once per document (optional) |
| Heuristic classification | < 1s | $0 | Once per document |
| Heuristic mapping | < 1s | $0 | Once |
| Unified LLM analysis | 45-90s | $0.50-0.80 | Once per session |
| Report generation | < 1s | $0 | Instant (derived) |

Total: ~2 minutes, ~$0.70 per project.

**Proposed cost profile with optimizations:**

| Operation | Time | API Cost | Frequency | Savings |
|-----------|------|----------|-----------|---------|
| File scanning + metadata | < 1s | $0 | Once | (same) |
| Text extraction (cached) | 0s if cached, 2-3s if new | $0 | Once per unique file | 90% fewer extractions for batch |
| Classification (cached) | 0s if cached | $0 | Once per unique file | (same) |
| LLM mapping (Haiku) | 2-3s | $0.02 | Once per session | Replaces buggy heuristic |
| Confidence cascade filter | < 1s | $0 | Once | Eliminates 40-60% of LLM needs |
| Targeted LLM extraction | 20-40s | $0.20-0.40 | Only for ambiguous reqs | 50% cheaper, 50% faster |
| Citation verification | < 1s | $0 | Once | New (prevents hallucination) |
| Report generation | < 1s | $0 | Instant | (same) |

Total: ~30-50 seconds, ~$0.25 per project (65% cheaper, 60% faster).

For Carbon Egg (100 farms, shared documents):
- **Current approach:** 100 farms x $0.70 = $70, ~3.3 hours
- **Proposed approach:** 100 farms x $0.25 (with shared document cache + warm start) = $25, ~50 minutes
- **Savings:** $45 and 2.5 hours

## The Bypass Problem, Resolved

Becca requested the ability to "bypass document discovery, bypass requirement mapping, and start at evidence extraction + validation."

In the proposed architecture, this is not a special bypass mode. It's the natural behavior:

- Documents already processed? Layer 1 serves from cache. Cost: 0.
- Checklist already loaded? Layer 2 serves from cache. Cost: 0.
- Previous evidence exists for these documents? Layer 3 serves from cache. Cost: 0.
- Only new evidence needed? Layer 3 processes only the delta. Minimal cost.

"Bypass" becomes "the system is smart enough to not redo work." No special mode needed.

## The Multi-Project Problem, Resolved

Carbon Egg has 100+ farms sharing a methodology document, a PDD, and a credit class.

In the proposed architecture:
1. **Layer 1** extracts and caches these shared documents by content hash. Processed once.
2. **Layer 2** loads the soil-carbon-v1.2.2 checklist once.
3. **Layer 3** for Farm 1: Full analysis, ~$0.40.
4. **Layer 3** for Farm 2: Shared documents already cached. Only farm-specific documents (land tenure, etc.) need processing. Warm start from Farm 1's results. Cost: ~$0.15.
5. **Layer 3** for Farm 100: Same as Farm 2. Cost: ~$0.15.

Total for 100 farms: $0.40 + (99 x $0.15) = $15.25 instead of 100 x $0.70 = $70.

## Becca's Requirements, Mapped to Architecture

| What Becca Wants | Architectural Answer |
|------------------|---------------------|
| "Not ChatGPT" — professional output | Layer 4: Template-based, no LLM in report generation |
| Specific citations (doc + section + page) | Layer 3: Citation verification against Layer 1 text |
| No hallucinated evidence | Citation verification: every claim verified against source text |
| Handle 100+ farms | Content-addressable cache + warm start |
| Bypass stages when documents already known | Cache hierarchy: don't redo work |
| Spreadsheet ingestion | Layer 1: Add XLSX/CSV extractors alongside PDF |
| Pre-loaded requirements (not "figuring out what to check") | Layer 2: Immutable, precomputed, ready before analysis starts |
| Human review only where needed | Layer 3: Confidence cascade — high-confidence results skip human review |
| Registry agent, not AI assistant | Layer 3 is the only place LLM runs, and it's constrained by Layer 2's fixed checklist |
| Auditable trail | Every layer writes immutable artifacts keyed by content hash |
| Works with GDrive bot | Layer 1: File watcher or webhook triggers background processing |

## What Changes in the Codebase

This redesign does not require throwing away the existing code. It requires **restructuring** it around the layer model:

### Keep (reposition within layers)
- `document_processor.py` → Layer 1 (dual-track extraction is good architecture)
- `unified_analysis.py` → Layer 3 (the unified LLM approach is right, but needs targeted context)
- `report_tools.py` → Layer 4 (template-based reporting is correct)
- `state.py` → Cross-layer (atomic file operations are solid)
- `cache.py` → Cross-layer (extend to content-addressable)
- `background_jobs.py` → Layer 1 (memory-aware job management is good)
- `settings.py` → Cross-layer (immutable config is correct)

### Replace
- `mapping_tools.py` → Layer 3 (replace heuristic mapping with LLM-guided or merge into evidence extraction)
- `_infer_document_types()` → Eliminate entirely (the naming convention split is a design flaw, not a bug)
- `patterns.py` classification patterns → Layer 1 heuristics (still useful as first pass, but not authoritative)

### Add
- Content-addressable document store (Layer 1)
- Evidence confidence cascade (Layer 3)
- Citation verification (Layer 3)
- Requirement dependency graph (Layer 2)
- Incremental processing controller (orchestrator)
- Progressive result streaming (UX)
- Shared document library (Layer 1)
- Spreadsheet extractor: XLSX/CSV (Layer 1)

### Remove
- Path 1 (legacy multi-call extraction) — Path 2 (unified) is strictly superior
- Stage C as a separate concept — mapping is part of extraction
- Stage E as a separate concept — validation is part of extraction
- Dual naming conventions (`land-tenure` vs `land_tenure`) — normalize to one

## Implementation Sequence

The redesign can be implemented incrementally. Each step delivers immediate value:

**Step 1: Fix the mapping bug and normalize naming** (hours)
Immediate relief. Normalize all classification labels to underscores. Add missing types to the mapping lookup. This fixes Becca's reported bug today.

**Step 2: Add spreadsheet ingestion** (1-2 days)
Unblocks Carbon Egg. Add XLSX/CSV extractors to Layer 1. Straightforward addition to document processor.

**Step 3: Content-addressable document cache** (1 day)
Replace filepath-based caching with content-hash-based. Enables shared document library. Biggest efficiency win for batch projects.

**Step 4: Replace heuristic mapping with LLM-guided** (1 day)
Single Haiku call replaces 60 lines of brittle pattern matching. Eliminates the entire category of mapping bugs. Cost: $0.02 per project.

**Step 5: Evidence confidence cascade** (1-2 days)
Before calling the expensive LLM, check if cheaper heuristics can resolve a requirement. Reduces LLM costs by 40-60%.

**Step 6: Citation verification** (1 day)
After LLM extraction, verify every citation against source text. Catches hallucinations. Dramatically improves reliability.

**Step 7: Clean up report output** (1 day)
Remove duplicate fields, emojis, ChatGPT-style formatting. Pure Layer 4 work. Addresses Becca's output quality concerns.

**Step 8: Progressive result streaming** (2-3 days)
Return fast heuristic results immediately, upgrade with LLM results. Transforms the UX from "wait 2 minutes" to "see results improving in real time."

**Step 9: Incremental processing** (2-3 days)
When documents are added/removed, re-process only what changed. Enables the "bypass" workflow naturally.

**Step 10: Warm start for batch projects** (1-2 days)
Use first farm's results as template for subsequent farms. Enables efficient processing of Carbon Egg's 100+ farms.

Steps 1-4 are the critical path for Carbon Egg readiness. Steps 5-7 improve efficiency and reliability. Steps 8-10 enable scale.
