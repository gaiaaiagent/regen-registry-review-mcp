# The Registry Review Agent: A Comprehensive Vision

*Synthesized from conversations spanning September through November 2025*

---

## The Challenge: Manual Review at Breaking Point

The story begins with a stark reality: one person, Becca, manages the entire registry review process for Regen Network's carbon credit projects. What works at small scale becomes untenable when Ecometric alone brings 100+ annual projects, with batches sometimes containing 70 individual farm submissions at once. The mathematics are unforgiving—this is fundamentally a full-time role that cannot scale without transformation.

The pain lives in the details. Document names must be transcribed into checklists by hand. File locations must be copied into requirement fields one by one. Each submission arrives through different pathways—some through the Airtable form, others through Ecometric's SharePoint, still others from individual developers via Google Drive. The reviewer downloads folders from Microsoft systems, reorganizes them in Google Drive, creates registry review templates for each project, updates project names and IDs, verifies the presence of required documentation, cross-references land ownership claims against registry documents, checks date alignments between imagery and sampling (which must align within four months), and ensures completeness against methodology-specific requirements.

This is the lowest-hanging fruit for automation, yet it represents the most time-consuming aspect of the work. Writing document names into checklists. Copying them into requirement squares. Cross-checking multiple documents for consistency. Date verification and data extraction. Land tenure validation. These repetitive tasks consume hours that could be spent on substantive analysis—the work that truly requires human expertise and judgment.

## The Vision: Human-AI Collaboration

From the earliest discussions in September, the vision was never full automation but thoughtful collaboration. The agent would handle documentation organization, validation, and initial compliance checks. The human reviewer would focus on substantive analysis, interpretation, and final approval. This collaborative model emerged as the central design principle.

The visual language of this partnership became clear: AI writes in blue, humans write in black. The agent populates a collaborative document—perhaps a Google Doc—with its findings distinctly formatted. The human reviewer verifies the agent's work, adds their own analysis, corrects any errors, and finalizes the review. The goal isn't to replace human judgment but to free it for the work that matters most.

Success metrics crystallized around time savings: a 50-70% reduction in manual review time, enabling one reviewer to handle what would otherwise require dedicated full-time staff. The target escalation rate sits below 10%—meaning the vast majority of submissions should flow smoothly through automated checks to human validation, with only exceptional cases requiring deeper investigation.

## The Workflow: From Submission to Approval

### Entry Points and Organization

Projects enter the system through multiple pathways. The ideal flow runs through an Airtable submission form capturing essential metadata: submission date, contact person and role, organization name, project name, proposed start date, and the protocol being used. Developers must attach required documentation—project plans, land tenure records, evidence of no land use change over the past decade, and supplemental information as needed.

Reality diverges from this ideal. Ecometric, as the largest project developer with long-standing relationships, operates differently. They simply notify the team when projects are ready, and staff access their SharePoint to retrieve documentation. This partnership model reflects the practical accommodation of established relationships and high-volume workflows.

All projects ultimately organize within structured folder hierarchies. Ecometric's SharePoint organizes by registration year, with projects strictly ordered by project ID. This organizational discipline proves critical—IDs embed in on-chain metadata when projects instantiate on the blockchain and when credit batches are created, establishing queryable connections throughout the data lifecycle.

### The Registration Checklist: Heart of the Review

The comprehensive Google Sheets checklist serves as the definitive record of the review process, documenting exactly what was reviewed, by whom, when, and with what outcomes. Several key sections structure this record:

**Project Details** capture essential metadata—project name, ID, administrator name, developer name, methodology, protocol version, protocol library link, and credit class. The monitoring section tracks monitoring rounds, credit issuance information, and related details.

**Registry Documents** section details all required documentation with space to indicate whether each document was submitted, where it's located, and when it was reviewed. For carbon farming projects, this typically includes project plans, land eligibility documents (land registry documentation and evidence of no land use change over the past decade), GIS files, field boundaries, and management histories.

**Protocol-Specific Requirements** vary significantly across methodologies and versions. The review must verify that all protocol-specific documentation is present and complete—a critical check that cannot be generalized across project types.

### Document Discovery and Validation

The agent's first responsibility is discovering and cataloging all submitted documents. It identifies files within the project folder structure, extracts metadata, determines document types, and creates an inventory with locations. This seemingly simple task represents enormous time savings—no more manually writing document names into checklists.

Validation follows discovery. The agent checks document completeness against protocol requirements, verifies file accessibility and readability, confirms naming conventions match organizational standards, and flags any missing or mislabeled materials. Each validation produces a structured record: document name, location, type, compliance status, and any issues detected.

### Content Extraction and Cross-Validation

Beyond mere presence, documents must contain correct information consistently expressed across multiple sources. The agent extracts key data points—project names, IDs, dates, land areas, parcel identifiers, ownership information, and baseline measurements. It then cross-references this data, checking for consistency across documents.

Land tenure documentation must align with land registry records. Dates across different document types must correlate appropriately—imagery dates must fall within four months of sampling dates. Geolocation data must match across field boundaries, sampling plans, and monitoring reports. These cross-checks, tedious when performed manually, become systematic when automated.

### The Challenge of Aggregated Projects

Ecometric's batch submissions present unique complexity. A single submission might contain 45 to 70 individual farm projects, each requiring independent review yet sharing common structure. The agent must recognize aggregated projects, parse submitter metadata to identify all constituent farms, create individual project records for each farm or parcel, and link records via aggregation batch IDs.

Parallel processing enables efficiency. The agent runs document ingestion and extraction for each farm independently, applies validation rules to each separately, generates individual data summaries, and aggregates status at the batch level. A master batch review document organizes per-farm review sections with filtering and sorting capabilities, enabling the reviewer to approve entire batches or individual farms as appropriate.

Efficiency optimizations leverage the structural similarity across farms. Batch templates apply when many farms share common structure. The system identifies common document templates across farms, flags anomalies at the farm level for focused review, and suggests bulk approval for farms with identical structure and findings.

### Beyond Registration: Issuance Review

Registration review represents the starting point, but the agent's ultimate scope extends to credit issuance review—a more complex domain requiring deeper analysis. For projects in the issuance phase, documentation expands significantly:

Baseline reports establish initial conditions. Monitoring round reports document carbon sequestration claims between baseline and sampling events. Sampling plans specify approaches for different parcels. Geolocation data pinpoints fields, cores, and sampling blocks. Historic yield data provides context. Emissions-related inputs feed calculations. Most challengingly, input and output data from AI analyses used in project evaluation must be validated—AI checking AI, requiring confidence calibration and clear escalation paths for uncertainty.

The monitoring requirement structure varies by protocol. While some carbon projects monitor on five-year cycles, Ecometric projects require annual monitoring, creating continuous review cycles that would absorb one person's full-time effort if managed manually.

## The Architecture: Building Intelligence in Layers

### The MCP Foundation

The technical architecture centers on Model Context Protocol (MCP) servers—modular tools that any agent can use, creating reusable infrastructure across specialized applications. The Regen Registry Review MCP embodies this modularity, developed specifically with Becca's workflow in mind.

This MCP represents low-hanging fruit with concrete impact potential, simplifying workflows and freeing team members from hours copying data fields between documents. AI excels at such tasks, transforming tedious manual work into rapid automated processes while maintaining human oversight for critical decisions.

Each MCP server comprises three components: resources (data access), tools (function calls), and prompts (user interfaces with predefined workflows). For the registry review agent, workflow prompts guide each sequential process step. Each stage of Becca's workflow becomes its own function—initialize, document discovery, evidence extraction, cross-validation, report generation, human review, and completion.

### The KOI Integration

The KOI MCP serves as the knowledge backbone, providing agents access to Regen Network's collective intelligence. Within KOI, carefully curated prompt sets grab predefined knowledge bundles relevant to specific roles. The registry review agent, when running the appropriate prompt, fetches all relevant knowledge from the knowledge base—protocol requirements, validation rules, historical examples, and organizational standards.

This integration means the agent doesn't operate in isolation but draws on the full context of Regen Network's operations. When encountering an unusual situation, it can search the knowledge base for similar cases. When validating against protocol requirements, it accesses the most current documentation. When preparing review templates, it follows established organizational patterns.

### Data Sources and Integration Points

The agent connects to multiple systems, each requiring appropriate authentication and access control:

**Airtable API** listens for new submissions via webhooks, retrieves submission metadata and project details through queries, and updates records with processing status and agent findings.

**Google Drive API** lists files in project folders, reads document contents (leveraging Google Docs API for structured documents), exports materials as needed, and writes collaborative review documents.

**SharePoint API** serves Ecometric's workflow, listing projects by registration year, retrieving documents from organized folder structures, and extracting metadata from file properties.

**Regen Ledger MCP** queries existing project metadata (project IDs, credit batch information), validates submitted data against on-chain records, prepares validated data for project instantiation, and records review completion to the audit chain. Currently it cannot dereference IRIs on the data module—a key function requiring attention.

**Notification Systems** alert reviewers when new projects are ready for review, notify submitters of validation failures requiring correction, and provide status updates to project tracking systems.

Service accounts with appropriate read/write permissions handle access, with comprehensive audit logging for all data access and secrets management for API credentials.

### The Agent Workflow: Stage by Stage

The complete workflow unfolds systematically:

**Document Ingestion** catalogs all documents, extracts metadata, and creates a comprehensive inventory.

**Data Extraction** parses project details and extracts requirement data from various document types.

**Validation and Compliance Checking** verifies all required documents are present, checks protocol-specific rules, and cross-references data consistency.

**Branch Point: Issues Found?** If yes, the agent generates a corrective action report, notifies the submitter, and flags the issue in the tracking system, then waits for resubmission. If no issues are found, it proceeds to review template population.

**Review Template Population** compiles agent findings documents, creates collaborative review checklists, and generates data summaries.

**Ready for Human Review** notifies the reviewer and provides comprehensive review materials.

**Human Review and Approval** enables the reviewer to verify agent findings, add their analysis layer, and approve or reject the submission.

**Approved projects** move to completed registration. **Rejected projects** enter correction workflows for iteration.

### Key Decision Points

Throughout the workflow, critical decision points determine the path forward:

**Document Completeness:** Are all required documents present and accessible? If yes, continue to extraction. If no, request specific missing documents.

**Data Quality:** Does extracted data pass validation rules? If yes, continue to review template generation. If no, flag specific issues for human investigation.

**Confidence Level:** Does agent confidence exceed the threshold (typically 85%)? If yes, minimal human review is needed. If no, escalate for deeper review.

These decision points embody the human-AI collaboration philosophy—the agent handles what it can confidently process while surfacing uncertainties for human judgment.

## The Data Models: Structuring Knowledge

### Project Registration Record

Each project maintains a comprehensive record capturing its complete state:

```json
{
  "project_id": "EC-2024-001",
  "registration_year": 2024,
  "project_name": "Regenerative Farm Portfolio",
  "developer": "Ecometric",
  "protocol": "Soil Carbon Protocol v2.1",
  "submission_date": "2024-03-01",
  "submission_status": "pending_review",
  "is_aggregated": true,
  "aggregation_count": 45,
  "documents": {
    "project_plan": {
      "filename": "Project_Plan_EC2024001.pdf",
      "location": "gs://drive/projects/2024/EC-2024-001/submitted_materials/",
      "extraction_status": "complete"
    }
  },
  "validation_results": {
    "land_tenure_verified": true,
    "no_land_use_change": true,
    "baseline_complete": true,
    "overall_status": "pass"
  },
  "agent_flags": [
    {
      "severity": "info",
      "message": "Emissions data uses AI model for prediction; verify model validation"
    }
  ],
  "review_status": "awaiting_assignment"
}
```

### Validation Results

Each validation produces structured findings:

```json
{
  "validation_id": "VAL-EC-2024-001",
  "project_id": "EC-2024-001",
  "validation_timestamp": "2024-03-01T10:30:00Z",
  "protocol": "Soil Carbon Protocol v2.1",
  "rules_evaluated": 12,
  "rules_passed": 12,
  "rules_failed": 0,
  "validation_details": [
    {
      "rule_id": "LAND_TENURE_001",
      "rule_name": "Land ownership documentation",
      "status": "pass",
      "documents_checked": ["Land_Tenure_Farm_A.pdf"],
      "confidence": 0.98
    }
  ],
  "overall_pass": true,
  "next_step": "human_review"
}
```

## Implementation Priorities: Phases and Milestones

### Phase 1: MVP Foundation (Months 1-2)

Focus centers on project registration phase with Ecometric data. Core deliverables include document ingestion modules for Google Drive, basic document extraction using PDF parsing, a validation rule engine for protocol-specific checks, review template generation in Google Docs format, and manual approval workflows.

The deliverable milestone: the agent can process Ecometric batch submissions and generate review documents. Success metric: 50% reduction in manual document organization time.

### Phase 2: Enhancement and Refinement (Months 3-4)

Focus shifts to accuracy and confidence. Improvements include ML-based table and form recognition for better extraction, cross-document validation capabilities, confidence scoring refinement, feedback loop implementation, and error categorization with clear escalation paths.

The deliverable milestone: agent confidence exceeds 85% for compliant submissions. Success metric: 70% of submissions require only minimal human review.

### Phase 3: Issuance Review Extension (Months 5-6)

Focus expands to monitoring rounds and credit issuance. New capabilities include monitoring report extraction, carbon calculation validation, sampling data verification, AI model output checking, and automated credit issuance recommendations.

The deliverable milestone: agent handles end-to-end project lifecycle from registration through issuance. Success metric: 60% reduction in total review time across both phases.

### Phase 4: Scaling and Sophistication (Month 7+)

Focus addresses scaling and advanced features. Developments include multi-protocol support beyond carbon farming, verifier integration for third-party review assistance, advanced analytics on project trends and common issues, and predictive modeling for submission quality assessment.

The deliverable milestone: system supports 500+ annual reviews across multiple protocols. Success metric: sub-10% escalation rate maintained at scale.

## The Developer Experience: Integration Considerations

### Access Requirements and Early Coordination

Gregory Landua emerged as the key contact for resolving access requirements before development begins in earnest. The team needs comprehensive access to Google Drive for examining past review examples and SharePoint for understanding Ecometric's submission structure. Historical examples prove invaluable—examining 10-15 completed review projects from Regen Network archives allows the agent to learn patterns and calibrate its validation logic.

Creating visual flow maps of the entire process was identified as valuable preparatory work, allowing the team to verify understanding with stakeholders and identify all system touch points clearly.

### Information Architecture Challenges

Current information organization presents challenges for AI ingestion. Data spreads across multiple locations: on-chain IDs for documents, project documentation tables, data streams with anchored posts, and website databases. The system requires either unification or clear pointing mechanisms to access this distributed information effectively.

Better organization at the source would make data more ingestible for AI. Establishing document formatting standards and providing templates to developers can reduce format variability that causes extraction failures.

### Methodology Specificity

A critical constraint emerged early: registry agents must be methodology-specific. One cannot use a single agent across multiple methodologies due to different data standards. Biodiversity projects have significantly different requirements than carbon sequestration projects. Each protocol and version may have distinct rules.

This specificity shapes the architecture—the agent must dynamically load the appropriate protocol specification and validation rules based on project metadata, maintaining a knowledge base of protocol requirements that updates as methodologies evolve.

## Success Metrics and Performance Targets

### Capacity and Throughput

Annual throughput targets 100+ projects from Ecometric plus 20-30 individual developers—over 120 projects annually. Processing time for initial review document generation should remain under 2 hours per project. Aggregated batch handling must process 70-farm batches in parallel within 3 hours.

### Accuracy and Reliability

Agent accuracy for data extraction must exceed 95%, measured through manual verification of extracted data. Validation coverage should automate over 90% of rules—meaning rules successfully evaluated without escalation. The escalation rate should remain below 10%—only one in ten projects requiring human investigation beyond standard review.

When agent confidence is high, findings should prove correct over 90% of the time—this confidence calibration is critical for building trust in the system. Document extraction should succeed over 85% of the time, with PDFs successfully parsed and structured. False positive rates should stay below 5%—validation failures that submitters dispute should be rare.

### Efficiency Gains

Human review efficiency should improve by 50% minimum, measured in hours per project before and after automation. The agent's processing time per project should remain under 2 hours from submission to review document generation. Success rates should be tracked by document type to identify extraction challenges requiring additional development.

## Risk Mitigation and Governance

### Technical Risks

**Document Format Variability** poses ongoing challenges—agents may fail on non-standard documents. Mitigation strategies include establishing document formatting standards and providing templates to developers.

**Accuracy Degradation** threatens trust if the agent produces incorrect extractions. Extensive testing on past examples combined with human-in-the-loop approval maintains quality.

**API Rate Limits** could throttle the system during batch processing. Exponential backoff, aggressive caching, and efficient batch request patterns address this constraint.

**Data Access Issues** might prevent reading from SharePoint or Google Drive. Testing access early using service accounts with explicit permissions prevents late-stage blockers.

**Protocol Changes** risk making agent logic obsolete when rules update. A modular rule engine allows quick updates while protocol version tracking maintains historical accuracy.

**Over-Reliance on Automation** could allow critical errors to slip through. Maintaining human reviewer involvement for final approval and clear escalation pathways preserves essential oversight.

### Audit and Governance

All agent actions log with timestamps and justifications, creating a comprehensive audit trail. Human review decisions and corrections are recorded for learning. Changes to validation rules are versioned and tracked. Approved projects link to final review documents establishing provenance.

Privacy considerations shape data handling—service accounts access only necessary project folders, data retention policies comply with organizational standards, and sensitive information is handled according to established protocols.

## Extensions and Future Possibilities

### Verifier Integration

Third-party verifiers currently duplicate much of the completeness checking work that the registry performs. AI-generated reviews with source tracking could increase trust while enabling verifiers to focus on their unique role—checking calculations and methodological compliance. This could reduce costs and enable scaling to serve more projects.

### Project Developer Concierge

Beyond registry review, a complementary agent could handle frequent inquiries from project developers. This concierge agent would serve mid to low-tier developers interested in carbon credits, provide automated responses to common questions, and route inquiries appropriately—directing basic information seekers to educational resources while connecting mature developers to engagement channels.

The team has been collecting inquiry data for 6-12 months to inform this agent's development. Three new fellows joined the program, with one specifically tasked with collating historical inquiries from project developers and organizing them to inform routing workflows.

### Democratized Crediting Vision

Gregory's long-term vision imagines democratized, open crediting where users can access the system directly. A SaaS model might charge users $1,000 annually to access all Regen Network tools and information. If the system works well enough with sub-agents and MCPs, it could enable self-service eco-crediting.

The system could guide users through qualification requirements for different crediting levels, providing information that currently requires $20,000-$50,000 in consulting fees due to the complexity of navigating the process manually. This runbook automation process could help achieve a more sustainable business model while broadening the community of users.

Clear processes for adding new methodologies and transparent governance for reviews and approvals would support this expansion. The vision extends toward the Regen knowledge commons—potentially inviting other organizations like Regen Coordination, Refideo, and Green Pill to participate in shared infrastructure.

### Token-Gated Access and Sustainability

Business model discussions explored token-gated access as a potential funding mechanism. Level 2 Regen commoners might receive access to the Regen knowledge commons through yearly or monthly subscriptions supporting the commons. This creates a sustainable funding model while maintaining alignment with regenerative principles.

For Regen Network specifically, a subscription model could provide reliable revenue while expanding access to tools and information. If the infrastructure proves valuable enough, other organizations in the regenerative technology space might contribute to or benefit from the shared knowledge commons.

## The Human Element: Collaboration Over Replacement

Throughout all these discussions, one principle remained constant: this is about human-AI collaboration, not replacement. The agent handles the tedious, repetitive, and systematizable aspects of review—document organization, data extraction, consistency checking, and initial validation. The human brings expertise, judgment, contextual understanding, and accountability.

Becca's knowledge doesn't become obsolete—it becomes amplified. Where she previously spent hours on administrative tasks, she can now focus on the substantive analysis that truly requires her expertise. The agent surfaces the information she needs, organized and validated. She provides the final judgment, adds contextual insights, catches edge cases, and maintains accountability for decisions.

The visual language—AI in blue, human in black—embodies this partnership. Both voices appear in the final document. Both contributions are valued. The agent accelerates and systematizes; the human interprets and decides.

## Measuring Success: Beyond Efficiency

While efficiency metrics matter—50-70% time savings, sub-10% escalation rates, 100+ annual project capacity—the deeper success lies in enabling the registry function to scale without compromising quality. Manual review at current volumes is not merely inefficient; it's unsustainable and threatens to become a bottleneck limiting Regen Network's impact.

The agent doesn't exist to eliminate jobs but to enable mission—to allow the registry to serve more projects, more developers, and more land stewards seeking to document and validate their regenerative practices. It removes the administrative friction that prevents good projects from accessing verification and crediting systems.

When a farmer in North Carolina can more easily get their carbon sequestration verified, when Ecometric can efficiently process portfolios of 70 farms, when third-party verifiers can focus on methodological validation rather than administrative completeness checks—these are the true measures of success. The agent becomes infrastructure enabling regenerative action at scale.

## The Path Forward: From Vision to Reality

From September's initial discussions through November's implementation planning, this vision has evolved from abstract concept to concrete architecture. The team now understands the workflow, has identified the integration points, knows the success metrics, and can phase the development to deliver value iteratively.

The foundation rests on proven technologies—MCP servers, ElizaOS framework, established APIs for Google Drive and SharePoint, and the KOI knowledge infrastructure. The challenge lies not in technical possibility but in careful implementation—getting the details right, calibrating confidence appropriately, maintaining human oversight, and building trust through demonstrated reliability.

Becca's needs define the requirements. Her workflow patterns become the agent's procedures. Her expertise informs the validation rules. Her judgment remains the final arbiter. The agent is her tool, amplifying her capacity, freeing her focus, enabling her impact.

The registry review agent represents more than workflow automation. It embodies a vision of how humans and AI can collaborate in service of regenerative outcomes—the AI handling the systematic and repetitive, the human providing the interpretive and contextual, together achieving what neither could accomplish alone.

The work continues—in planning, in code, in testing, in refinement. But the vision is clear, the path is defined, and the commitment is firm. The registry review agent will become real, enabling Regen Network's registry function to scale in service of the living Earth and all who dwell here.

*Compiled from conversations held September through November 2025, documenting the collective intelligence of the Regen Network team as they architect the future of regenerative verification at scale.*
