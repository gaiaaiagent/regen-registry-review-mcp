# Regen Registry Review Project Manager

A comprehensive project management skill for coordinating development of the Regen Registry Review MCP automation tooling.

## Purpose

This skill embodies the complete project context and serves as the Project Manager for building AI-powered registry review automation. It helps with:

- **Requirements gathering** - Defining what needs to be built
- **Roadmap planning** - Organizing work into phases and milestones
- **Architecture review** - Evaluating technical decisions
- **Implementation tracking** - Monitoring progress and blockers
- **Team coordination** - Managing parallel workstreams
- **Quality assurance** - Ensuring standards are met
- **Delivery management** - Shipping on time with quality

## When to Use

Invoke this skill when you need to:

- Plan features or define requirements
- Create or update development roadmaps
- Review technical architecture or design decisions
- Track implementation status or identify blockers
- Coordinate multiple workstreams or team efforts
- Manage delivery timelines and milestones
- Make strategic project decisions

Natural language triggers include:
- "Let's plan the roadmap"
- "Define requirements for..."
- "Review this architecture"
- "What's our implementation status?"
- "How should we organize the work?"
- "Are we on track for delivery?"

## Project Context

This skill has deep knowledge of:

1. **Vision & Requirements** - From transcripts of meetings Sept-Nov 2025
2. **Technical Specs** - Architecture, MVP workflow, infrastructure plans
3. **Real Examples** - Botany Farm 2022-23 review data showing actual usage
4. **Success Criteria** - 50-70% time savings, <10% escalation rate, 100+ projects/year

The core goal: Help Becca review projects faster by automating tedious tasks (document discovery, requirement mapping, evidence extraction) while preserving human judgment for final approval.

## Templates

The skill provides templates for common PM artifacts:

- **requirement-template.md** - For defining new features/requirements
- **roadmap-template.md** - For planning development phases
- **architecture-decision-record.md** - For documenting design decisions
- **status-update-template.md** - For progress reporting
- **user-story-template.md** - For feature stories with acceptance criteria

## Scripts

Helper scripts for quick insights:

- **check-progress.sh** - Quick project status snapshot (git, todos, structure)

## Key Documents

The skill knows to reference:

| Document | Purpose |
|----------|---------|
| `docs/transcripts/2025-11-11-transcript-synthesis.md` | Complete vision |
| `docs/specs/2025-11-11-registry-review-mvp-workflow.md` | 8 MVP user stories |
| `docs/specs/2025-10-30-regen-knowledge-commons-registry-review-agent-infrastructure.md` | Architecture |
| `examples/22-23/` | Real review data (Botany Farm) |

## How It Works

The skill follows a structured approach:

1. **Context Review** - Checks current project state (git status, recent commits, structure)
2. **Domain Expertise** - References specs, transcripts, examples as needed
3. **Structured Output** - Uses templates to create consistent artifacts
4. **Decision Framework** - Prioritizes user value, MVP focus, technical soundness
5. **Risk Management** - Identifies and escalates red flags
6. **Team Coordination** - Can launch sub-agents for parallel work

## Example Workflows

### Planning a Feature

```
User: "Let's plan the document discovery feature"

Skill:
1. Reads MVP workflow spec for Story 2
2. Examines Botany Farm example documents
3. Creates user story with acceptance criteria
4. Identifies technical tasks and dependencies
5. Estimates effort and suggests priority
```

### Reviewing Progress

```
User: "What's our implementation status?"

Skill:
1. Runs check-progress.sh script
2. Reviews recent commits and changes
3. Compares against roadmap milestones
4. Identifies any blockers or risks
5. Generates status update using template
```

### Making Architecture Decision

```
User: "Should we use PostgreSQL or MongoDB?"

Skill:
1. Reviews data model requirements from specs
2. Considers KOI integration needs
3. Evaluates trade-offs (querying, scaling, complexity)
4. References similar decisions in architecture doc
5. Creates ADR documenting choice and rationale
```

## Success Metrics

The skill helps track:

- **Velocity** - Stories completed per sprint
- **Quality** - Test coverage, defect rates
- **Impact** - Time saved per review (target: 50-70%)
- **Adoption** - % of reviews using automation
- **Satisfaction** - User feedback scores

## Integration

This skill can:

- Use other skills (like skill-builder, mcp-architect)
- Invoke slash commands for specific tasks
- Launch Task sub-agents for complex parallel work
- Read/Write files for documentation
- Run scripts for status checks

## Principles

Guided by these values:

1. **User value first** - Does this help Becca?
2. **MVP focus** - Ship core capability, enhance later
3. **Technical soundness** - Maintainable, scalable, secure
4. **Risk awareness** - Identify and mitigate proactively
5. **Team capacity** - Don't over-commit
6. **Documentation** - Future clarity through written decisions

## Updates

This skill stays current by:

- Reading project files directly (always fresh)
- Using git commands to see recent changes
- Referencing canonical specs and examples
- Tracking decisions in ADRs
- Maintaining roadmap with status

## Contributing

When enhancing this skill:

1. Keep SKILL.md focused on instructions
2. Add new templates to `templates/`
3. Add new scripts to `scripts/`
4. Update README.md with changes
5. Test with realistic project scenarios

## Support

For questions or issues with this skill:

- Check `SKILL.md` for detailed instructions
- Review templates for structure examples
- Examine example workflows
- Test with actual project context

---

**Version**: 1.0
**Last Updated**: 2025-11-12
**Owner**: Regen Registry Review MCP Project Team
