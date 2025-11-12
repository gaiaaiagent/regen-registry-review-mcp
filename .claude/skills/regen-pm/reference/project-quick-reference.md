# Regen Registry Review MCP - Quick Reference

## Project Overview

**Goal**: Automate Regen Network registry review process to save 50-70% of manual review time

**Primary User**: Becca (Registry Agent)

**Current Pain**: Manual document organization, cross-checking, evidence extraction for every project

**Solution**: AI agent handles tedious tasks; human handles judgment and approval

## Key Numbers

- **Target Time Savings**: 50-70% reduction
- **Target Escalation Rate**: <10%
- **Target Capacity**: 100+ projects/year (currently Ecometric alone has 100+)
- **Typical Review Time**: 3-4 hours per project (manual)
- **Batch Sizes**: Up to 70 farms in a single aggregated project

## MVP Scope (Phase 1)

8 User Stories for Project Registration Review:

1. **Project Initialization** - Create session, upload/link docs, select checklist
2. **Document Discovery** - Scan, normalize, classify, pin/ignore
3. **Requirement Mapping** - Match docs to checklist requirements
4. **Completeness Check** - Identify covered/partial/missing requirements
5. **Evidence Extraction** - Pull key snippets with citations
6. **Report Generation** - Structured JSON + human-readable output
7. **Human Review & Revisions** - Edit, request changes, re-run
8. **Commons Integration** - Store with basic permissioning

## Architecture Stack

- **MCP Layer**: Model Context Protocol servers (tools for agents)
- **Agent Framework**: ElizaOS
- **Knowledge Base**: KOI (semantic search + graph)
- **Storage**: PostgreSQL (non-graph), Apache Jena (RDF graph)
- **Provenance**: Regen Ledger x/data module
- **UI**: Initially agent interface, potentially custom dashboard

## Document Types

### Governing Documents
- Credit Class (e.g., GHG Benefits in Managed Crop and Grassland Systems v1.5.1)
- Methodology (e.g., Soil Organic Carbon Estimation v1.1)
- Program Guide v1.1

### Project Documents
- Project Plan (registration)
- Monitoring Reports (issuance)
- GHG Emissions Reports
- Baseline Reports

### Supporting Evidence
- Shapefiles (field boundaries, sample locations)
- Land registry documents
- Historical management records
- Soil sample results
- Laboratory certifications

## Review Checklist Categories

### Registration Review (19 categories)
General | Land Tenure | Project Area | Project Boundary | Project Ownership | Project Start Date | Ecosystem Type | Crediting Period | GHG Accounting (Additionality, Leakage, Permanence) | Regulatory Compliance | Registration on Other Registries | Project Plan Deviations | Monitoring Plan | Risk Management | Safeguards

### Issuance Review (11 categories)
Project Boundaries | Data Reporting | Project Monitoring | Monitoring Period | Soil Sampling Methods | SOC Analysis | AI Training/Accuracy | Image Processing | Results | Emissions | Risk/Leakage | GHG Accounting | Disclosures | Deviations | Verifier Requirements

## Example Project: Botany Farm 2022-23

- **Location**: Northamptonshire, UK
- **Size**: 82.08 ha
- **Baseline (2022)**: 6,251.40 tSOC (MAPE 7.10%)
- **Monitoring (2023)**: 6,449.88 tSOC (198.48 t change)
- **GHG Emissions**: 121.90 tCO2e
- **Net Balance**: 596 tCO2e (596 credits after buffer)
- **Methodology**: Ecometric Soil Carbon + Farm Carbon Calculator for emissions

## Key Stakeholders

- **Becca Harman** - Registry Agent (primary user)
- **Gregory Landua** - Access/permissions gatekeeper
- **Ecometric** - Largest project developer (100+ projects)
- **Verifiers** - Third-party validators (potential future users)
- **Project Developers** - Submit documentation

## Success Metrics

- **Efficiency**: Time saved per review (hours)
- **Accuracy**: Agent confidence levels, MAPE for extractions
- **Coverage**: % of requirements auto-validated
- **Escalation**: % of projects needing deep human review
- **Adoption**: % of reviews using the tool
- **Satisfaction**: User feedback (Becca, developers, verifiers)

## Common Tedious Tasks (High-Value Automation)

1. Writing document names into checklists
2. Copying names to requirement fields
3. Cross-checking document locations
4. Verifying date alignments (±4 months for sampling vs imagery)
5. Extracting metadata (project IDs, versions, dates)
6. Matching protocol requirements to evidence
7. Generating provenance records

## Human Judgment Tasks (Not Automated)

1. Assessing evidence "sufficiency"
2. Interpreting legal documents (land tenure)
3. Evaluating safeguard adequacy
4. Determining if deviations are acceptable
5. Making final approval decisions
6. Writing narrative summaries
7. Handling edge cases and exceptions

## Red Flags to Escalate

- Scope creep threatening MVP delivery
- Technical blockers without clear solutions
- Requirements conflicts or ambiguity
- Resource constraints impacting quality
- Stakeholder misalignment on priorities
- Access issues (Google Drive, SharePoint)
- Data quality problems in examples

## Key Decisions to Date

1. **Focus on Registration First** - Simpler than issuance, proves value
2. **Ecometric as Primary Partner** - Largest volume, consistent structure
3. **Human-AI Collaboration Model** - AI in blue, human in black
4. **MCP Architecture** - Modular tools for agents
5. **Progressive Provenance** - Start simple, add ledger anchoring later

## Development Phases

| Phase | Timeline | Focus | Success Metric |
|-------|----------|-------|----------------|
| 1: MVP | Months 1-2 | Core workflow with Ecometric data | 50% time savings |
| 2: Enhancement | Months 3-4 | Accuracy & confidence improvements | 85% agent confidence |
| 3: Issuance | Months 5-6 | Extend to credit issuance reviews | 60% total lifecycle savings |
| 4: Scale | Month 7+ | Multi-protocol, advanced features | 500+ projects/year |

## Quick File Locations

```
docs/
  specs/                        # Requirements & architecture
  transcripts/                  # Meeting notes & vision
examples/
  22-23/                       # Botany Farm real data (markdown versions)
    */                         # Each document includes extracted images
  checklist.md                 # Review template
.claude/
  commands/
    prime/examples.md          # Quick-load all example docs
    development/initialize.md  # Initialize dev session
  skills/
    regen-pm/                  # This project management skill
    marker/                    # PDF to markdown conversion
    mcp-architect/             # MCP development expertise
src/                           # Implementation (TBD)
```

**Note**: All example PDFs have been converted to markdown via the `marker` skill for easier analysis.

## Essential Reading

1. **Vision**: `docs/transcripts/2025-11-11-transcript-synthesis.md`
2. **Refined Spec**: `docs/specs/2025-11-12-registry-review-mcp-REFINED.md`
3. **MVP Stories**: `docs/specs/2025-11-11-registry-review-mvp-workflow.md`
4. **Architecture**: `docs/specs/2025-10-30-regen-knowledge-commons-registry-review-agent-infrastructure.md`
5. **Example Review**: `examples/22-23/Botany_Farm_Project_Registration_Registry_Agent_Review/` (markdown)

## Available Skills & Commands

**Skills** (specialized agents):
- `marker` - Convert PDFs to markdown (examples already converted)
- `mcp-architect` - MCP server development, testing, deployment
- `skill-builder` - Create new skills
- `regen-pm` - Project management (this skill)

**Commands** (quick operations):
- `/prime/examples` - Load all Botany Farm documentation
- `/development/initialize` - Start dev session with mcp-architect and regen-pm

## Contact

- **Project Lead**: TBD
- **Primary Stakeholder**: Becca Harman (Regen Network)
- **Technical Lead**: TBD
- **Repository**: `/home/ygg/Workspace/RegenAI/regen-registry-review-mcp`

---

Last Updated: 2025-11-12
