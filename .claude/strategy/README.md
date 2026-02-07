# Strategy Directory

This directory is the living command center for the Regen Registry Review MCP project. Every document here is a working artifact meant to be read, updated, and committed through git as the project evolves.

## How to Use This Directory

**STATUS.md** is the first thing to read. It answers: where are we right now? What's deployed? What's broken? What's next?

**ROADMAP.md** is the phased development plan. It breaks work into sequenced phases with clear acceptance criteria. Update it as phases complete or priorities shift.

**plans/** contains detailed implementation plans for each development phase. A plan is created before work begins and updated as work progresses. Completed plans are kept as historical record.

**indexes/** contains reference material that maps the project's information landscape: the codebase structure, API surface, infrastructure topology, team roles, and a master index of all planning documents, transcripts, and specifications. These get updated whenever the underlying reality changes.

**runbooks/** contains step-by-step operational procedures: how to deploy, how to test, how to debug production issues. These are the instructions you hand someone at 2am when something breaks.

**insights/** contains the decision log and lessons learned. When a significant architectural, product, or process decision is made, record it here with context and rationale so future-you (or teammates) understand why.

## Principles

Git is the source of truth. Every meaningful change to strategy, plans, or status gets committed with a clear message. This directory should be as well-maintained as the source code it governs.

Documents should be concise and current. Delete or archive information that is no longer true. A stale strategy document is worse than no document at all.

Cross-reference liberally. Use relative paths to link between documents in this directory and to source files, specs, and transcripts elsewhere in the repo.

## Directory Layout

```
strategy/
  README.md              you are here
  STATUS.md              current project state (living document)
  ROADMAP.md             phased development plan
  plans/                 detailed phase plans (created as work begins)
  indexes/
    codebase.md          source code structure and module map
    infrastructure.md    production deployment and architecture
    api-surface.md       REST API and MCP tool reference
    team.md              people, roles, and communication channels
    documents.md         master index of all project documents
  runbooks/
    deploy.md            production deployment procedures
    testing.md           testing procedures and cost management
  architecture/
    first-principles-redesign.md   from-scratch architectural rethinking
  insights/
    decisions.md         architectural and product decision log
```
