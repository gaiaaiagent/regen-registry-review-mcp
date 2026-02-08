# Project Status

Last updated: 2026-02-07

## Production State

The Registry Review MCP runs on the GAIA server (`202.61.196.119`) managed by **PM2** (not systemd) on port 8003, proxied through nginx at `https://regen.gaiaai.xyz/api/registry`. A Custom GPT and Darren's web app (`https://regen.gaiaai.xyz/registry-review/`) both consume this REST API. The MCP server is also available for direct Claude Desktop/Code integration via stdio.

**Deployed version:** `0513c8b` (task-12, Jan 26) — confirmed via SSH on Feb 7. All of Becca's 6 feedback items are live in production. The strategy directory commit (`c53aebf`) has also been pulled to production.

**Production health:** Verified healthy on Feb 7. API responds on port 8003. PM2 shows `registry-review-api` online for 11 days (PID 502414), 46MB memory, 8743 restarts total. Last service restart was Jan 27. Seven active sessions on the server including Clackson and Blaston Soil Carbon projects. Server uptime: 163 days.

**Other services on this server:** koi-api, koi-mcp-knowledge, regen-koi-mcp, regen-network-api, regenai-agents, koi-event-bridge. All managed via PM2 under the `shawn` user.

## What Works

The 8-stage workflow (Initialize through Completion) is functional for PDF-based registration reviews. The system processes the Botany Farm test project end-to-end: document discovery, requirement mapping against the soil-carbon-v1.2.2 checklist (23 requirements), evidence extraction with page/section citations, cross-document validation, and report generation in markdown and DOCX formats. The web app provides a professional UI with one-click review, side-by-side PDF viewing, and evidence highlighting.

Specifically verified:
- Per-farm land tenure validation
- Citations with document name, section number, and page reference (task-12)
- Value vs Evidence distinction in output (task-12)
- Supplementary evidence from multiple documents (task-12)
- Evidence text in Comments column beneath confidence scores (task-12)
- Sentence-boundary truncation (task-12)
- Project ID prefixed in document references (task-12)
- Confidence scores always visible in report comments
- Human review flagged only where needed
- Session persistence and recovery
- File upload via signed URLs and path-based ingestion
- 246 tests passing (fast suite)

## What's Broken or Missing

### Blocking for Carbon Egg (registration imminent)

1. **Mapping bug** — Diagnosed (Feb 7): naming convention split between classifier (underscores: `land_tenure`) and mapping lookup (hyphens: `land-tenure`). Three document types missed: `land_tenure`, `ghg_emissions`, `gis_shapefile`. Fixed in commit `467695e` with regression tests. (See: review-agent-readiness.md, item 2.1)

2. **Spreadsheet ingestion** — Implemented (Feb 7). System now processes .xlsx, .xls, .csv, .tsv alongside PDFs. New `spreadsheet_extractor.py` converts tabular data to markdown tables with sheet markers. Integrated into discovery, classification, extraction, and requirement mapping. 7 new tests added. (See: Jan 20 standup, Jan 27 standup)

3. **~~Meta-project architecture~~** — Implemented (Feb 7). Scope-based filtering: `scope="farm"` loads 4 per-farm requirements (REQ-002/003/004/009), `scope="meta"` loads 19 meta-project requirements. Centralized `load_checklist()` utility replaces 5 scattered `json.load` patterns. Knowledge doc at `data/knowledge/carbon-egg-multi-project.md`. 11 new tests. (See: review-agent-readiness.md, item 2.2)

4. **CarbonEg-specific requirements** — Addressed via scope filtering. The soil-carbon-v1.2.2 checklist now has scope tags on every requirement. No separate Carbon Egg variant needed.

### Blocking for demos and BizDev

5. **~~Report formatting~~** — Fixed (Feb 7). Emojis removed from all report prose (summary stats, section headers, requirement headings, validation summaries). Text labels (`PASS:/WARNING:/FAIL:`, `[Review]`) replace emoji status indicators. Dead code with old patterns removed.

6. **PDF download** — Not implemented (raises `NotImplementedError`). Requires a rendering library (e.g., weasyprint). Deferred — markdown and DOCX downloads work correctly.

7. **~~Duplicate value field~~** — Fixed (Feb 7). The `**Value:**` label removed from Submitted Material in both markdown and DOCX paths. Extracted value now stands alone before "Primary Documentation:".

8. **Supplementary evidence quality** — Unclear how well the system pulls supplementary evidence beyond primary documentation. Needs testing. (See: review-agent-readiness.md, item 2.3)

### Needed but not blocking

9. **Google Drive ingestion bot** — Darren built an email-based bot that can be added to Drive folders. Not yet integrated with the review workflow. Question open: does it work with third-party drives?

10. **Airtable integration** — Carbon Egg maintains land tenure data in spreadsheets, team considering Airtable migration. Samu exploring.

11. **Bypass workflow stages** — Ability to skip document discovery and requirement mapping, starting directly at evidence extraction. Requested in readiness checklist.

12. **Issuance Review Agent** — Scoped by Becca (updated-registry-spec.md) but not implemented. Covers monitoring reports, sampling data, lab analysis, SOC%, accreditation checks. Post-registration priority.

13. **Geospatial processing** — Stub exists. GIS-el proposed polygon overlap checking across registered projects. Ecometric protocol requires .tif, .shp, .shx, .dbf, .prj, .mat files. Terrasos requires .gdb, .mxd, and shapefiles. Long-term.

## Key Dates and Context

- Carbon Egg registration: described as "this month" on Feb 3
- ETHDenver/Boulder hackathon: starting around Feb 7 (Shawn, Darren, Eve attending)
- Next team check-in target: Wednesday Feb 11
- BizDev calls potentially starting as early as first week of Feb
- Last code change: Feb 7 (Phases 1a, 1b, 1c, 1d)

## Immediate Next Actions

See ROADMAP.md for the phased plan. The critical path is:
1. ~~Verify production deployment state (SSH to server)~~ — Done (Feb 7)
2. ~~Reproduce and fix the mapping bug~~ — Done (Feb 7, commit `467695e`)
3. ~~Add spreadsheet ingestion (.xlsx, .csv)~~ — Done (Feb 7)
4. ~~Clean up report output formatting~~ — Done (Feb 7, Phase 1c)
5. Test with Carbon Egg data
6. Deploy latest changes to production
