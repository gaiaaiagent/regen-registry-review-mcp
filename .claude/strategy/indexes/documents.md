# Document Index

Last updated: 2026-02-07

This index catalogs all planning documents, transcripts, specifications, and reference material across the repository. Documents are grouped by type and sorted by date within each group.

## Planning Transcripts

Location: `.claude/planning/2026/02/transcripts/`

| File | Date | Key Topics |
|------|------|------------|
| `2026-01-20-regenai-standup.md` | Jan 20 | Becca's feedback on agent output, naming conventions, scaling for CarbonEgg, seven-step framework, KOI MCP capabilities, knowledge commons authentication |
| `2026-01-27-regenai-standup.md` | Jan 27 | Agent evolution to data pipelines, multi-developer "vibe coding" coordination, BizDev strategy for ESG sector, shared Claude infrastructure, Otter MCP integration |
| `2026-02-03-agent-readiness-strategy.md` | Feb 3 | Carbon Egg readiness, web app vs directory-based agents decision, BizDev agent strategy, story mapping, KOI digest system, ETHDenver booth, milestones and timeline |
| `2026-02-07-slack-history.md` | Feb 7 | Complete Slack history from #project-gaia. Contains Becca's detailed feedback, Dave's KOI testing, Darren's web app announcement, team MCP setup discussions, BizDev workflow questions |

## Notion Documents (exported)

Location: `.claude/planning/2026/02/transcripts/`

| File | Author | Content |
|------|--------|---------|
| `updated-registry-spec.md` | Becca | MVP specification: two agents (Registration + Issuance), capabilities, constraints, demo flow, what-comes-next sequencing. THE product spec. |
| `review-agent-readiness.md` | Becca | Acceptance checklist with checkboxes. Core agent items, demo-ready web app items, data pipeline alignment items. THE readiness tracker. |
| `data-types-for-registry-protocols.md` | Becca | File type inventory for Ecometric (.tif, .json, .mat, .xlsx, .csv, .shp, .shx, .dbf, .prj, etc.) and Terrasos (.jpg, .mxd, .rar, .gdb, .shp, .xml, etc.) protocols. |
| `regen-marketplace-regen-registry.md` | Team | Analysis of renaming "Regen Marketplace" to "Regen Registry." Strategic implications, audience clarity, product alignment, work breakdown (light/medium/heavy lift), risks. |

## Technical Specifications

Location: `specs/`

| File | Date | Content |
|------|------|---------|
| `2025-11-11-registry-review-mcp-server.md` | Nov 11 | Original server specification |
| `2025-11-11-registry-review-mcp-server-FEEDBACK.md` | Nov 11 | Feedback and iterations |
| `2025-11-12-registry-review-mcp-REFINED.md` | Nov 12 | Refined specification |
| `2025-11-12-phase-4.2-llm-native-field-extraction-REVISED.md` | Nov 12 | LLM extraction details |
| `2025-11-12-comprehensive-assessment.md` | Nov 12 | Complete system assessment |
| `workflow-state-and-error-handling.md` | Jan 13 | State machine and error management |
| `2026-01-12-registry-assistant-forum-post.md` | Jan 12 | Forum announcement draft |

## Documentation

Location: `docs/`

| Directory | Content |
|-----------|---------|
| `docs/specs/` | High-level spec, MVP workflow, workflow stages, deployment plan, UX analysis (10 documents) |
| `docs/claude_docs/` | Claude platform guides: multi-agent orchestration, agentic patterns, MCP integration |
| `docs/mcp_docs/` | MCP breakdown, server primitives, UV cheat sheet |
| `docs/transcripts/` | Earlier meeting transcripts and community call notes |
| `docs/refactoring/` | Spec-aligned session API specifications |
| `docs/security/` | Prompt safety documentation |
| `docs/archive/` | 18 historical session summaries and architectural audits (Nov 2025) |

## Development History

Location: `.claude/journal/`

80+ entries from Nov 2025 covering test cost optimization, eight-stage refactoring, phase completion reports, UX analysis, performance optimization, and expensive test implementation.

## Backlog

Location: `backlog/`

34 task files in `backlog/tasks/`, 7 completed in `backlog/completed/`. Notable active tasks: Human Review stage (task-1), Completion stage (task-2), cross-validation E2E (task-3), PDF export (task-4), matrix view (task-6). See `backlog/README.md` for format documentation.

## Strategy Documents (this directory)

Location: `.claude/strategy/`

| File | Purpose |
|------|---------|
| `README.md` | How to navigate this directory |
| `STATUS.md` | Current project state (living document) |
| `ROADMAP.md` | Phased development plan |
| `indexes/codebase.md` | Source code structure reference |
| `indexes/infrastructure.md` | Production deployment reference |
| `indexes/team.md` | People, roles, communication channels |
| `indexes/documents.md` | This file |
| `indexes/api-surface.md` | REST API and MCP tool reference |
| `runbooks/deploy.md` | Production deployment procedures |
| `runbooks/testing.md` | Testing procedures |
| `insights/decisions.md` | Architectural and product decision log |

## External References

| Resource | URL | Description |
|----------|-----|-------------|
| GitHub repo | `github.com/gaiaaiagent/regen-registry-review-mcp` | Source code |
| Web App | `regen.gaiaai.xyz/registry-review/` | Production web interface |
| Forum Post | `forum.regen.network/t/the-registry-assistant-scaling-regenerative-verification-through-intelligent-infrastructure/577` | Public announcement |
| Regen Heartbeat | `gaiaaiagent.github.io/regen-heartbeat/digests/README` | Automated digest system |
| Miro Board | `miro.com/app/board/o9J_ltNDspw=/` | AI Workflow Scoping process map |
