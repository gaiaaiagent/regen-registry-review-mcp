# Project Status

Last updated: 2026-02-07

## Production State

The Registry Review MCP runs on the GAIA server as a systemd service (`registry-review-api.service`) on port 8003, proxied through nginx at `https://regen.gaiaai.xyz/api/registry`. A Custom GPT and Darren's web app (`https://regen.gaiaai.xyz/registry-review/`) both consume this REST API. The MCP server is also available for direct Claude Desktop/Code integration via stdio.

**Last known deployment:** Commits through approximately Jan 13 (the `/api/registry` URL prefix fixes). The Jan 26 commits (task-12, Becca's 6 feedback items) are in `main` locally but deployment to production is unverified. There has been no development activity on this repo since Jan 26.

**Production health:** Unknown. Needs verification via SSH. Becca reported a mapping bug on Feb 3 that may or may not be related to what's deployed.

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
- 229 tests passing (fast suite)

## What's Broken or Missing

### Blocking for Carbon Egg (registration imminent)

1. **Mapping bug** — Becca encounters errors where the system confuses document names. Different variant from the earlier cross-validation bug. Occurs at the mapping step. Needs reproduction and diagnosis. (See: review-agent-readiness.md, item 2.1)

2. **Spreadsheet ingestion** — System only processes PDFs. Carbon Egg has 100+ farms with land tenure records in spreadsheets (.xlsx, .csv). Described as "straightforward to add" but not implemented. (See: Jan 20 standup, Jan 27 standup)

3. **Meta-project architecture** — Carbon Egg has 100+ individual farms plus a meta-project. Decision made (Feb 3): treat each farm as an independent project. Needs implementation guidance: auxiliary knowledge explaining the multi-project structure, differentiated checklists for farms vs meta-project. (See: review-agent-readiness.md, item 2.2)

4. **CarbonEg-specific requirements** — Not pre-loaded. The checklist currently only has soil-carbon-v1.2.2. May need a Carbon Egg specific variant or additional protocol support.

### Blocking for demos and BizDev

5. **Report formatting** — Output still looks like ChatGPT. Needs containerization, emoji removal, and professional formatting. (See: review-agent-readiness.md, item 3.1)

6. **PDF download** — Not working from the web app. Markdown download works. (See: review-agent-readiness.md, item 3.2)

7. **Duplicate value field** — A spurious "value" field appears before "Primary Documentation" in the output table. Needs removal. (See: Feb 3 standup, Shawn checking deployment)

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
- Last code change: Jan 26 (12 days ago as of Feb 7)

## Immediate Next Actions

See ROADMAP.md for the phased plan. The critical path is:
1. Verify production deployment state (SSH to server)
2. Reproduce and fix the mapping bug
3. Add spreadsheet ingestion (.xlsx, .csv)
4. Clean up report output formatting
5. Test with Carbon Egg data
