## Opening: Technical Context and Rapid Evolution

Gregory opened the call while navigating the complexities of Google Cloud Platform administration, noting the persistent challenges of finding the right permissions and views within GCP's labyrinthine interface. The simple task of accessing service accounts requires being in the project view rather than the organizational view—a seemingly trivial distinction that can cost significant time. He acknowledged that while GCP's cloud assistant provides some help, the learning curve remains steep.

As the team assembled—Sean, Darren, Sam, and eventually Zach—Gregory framed the meeting's purpose: a product reboot similar to their previous standup call, where they would review roadmap thinking and milestones. The goal was to maintain focus on achievable deliverables while keeping sight of the broader architectural vision for their AI systems, ensuring modularity and flexibility across different platforms and models.

Gregory emphasized an extraordinary shift in their technical landscape: the work was now happening in a technology environment moving faster than he'd ever witnessed. Recent developments, particularly around Google's infrastructure, were reshaping their strategic approach. The data center of gravity phenomenon meant that building KOI-like agentic infrastructure within Google itself, where much of their data already resided, presented a potentially shorter path forward than initially anticipated.

The benchmark landscape had shifted dramatically as well. Gemini 3's recent release showed an "insane jump" in agentic benchmarking—not just in the quality of answers, but crucially in tool use capability. This distinction mattered profoundly for their work, as Gregory explained: an agent is fundamentally "an AI in a loop taking action through tool use." The quality of that tool use becomes paramount when wiring these systems into organizational workflows. While the models provided the intelligence for tool use, the team's responsibility was to design the tools themselves and the loops that employed them.

## Strategic Tensions: Infrastructure vs. Immediate Value

The team found themselves navigating a fundamental tension: maintaining their longer architectural vision of model-agnostic systems while delivering quick wins to demonstrate value. This proved more complex than traditional platform-agnostic development. As Gregory observed, achieving model agnosticism felt like being "personality agnostic"—each AI system had its own characteristics and quirks that made abstraction challenging.

Gregory described how he found himself getting "sucked in" and frustrated by these personality differences. Yet he saw a path forward through KOI—their knowledge organizing infrastructure. By building robust tooling and custom agents with good tool access, they could maintain optionality while leveraging the massive intelligence upgrade these systems represented.

The team had distributed responsibilities across several parallel efforts. Sam held the architectural vision, maintaining focus on integration with Regen Ledger and the infrastructure needed for creating auditable ecological claims, running audit agents, and connecting to the ledger MCP. Sean concentrated on building the first-draft registry agent to automate specific tasks currently performed manually by their team member Becca. Darren managed the library of tools and the KOI infrastructure—the sensors and agents that populated their RAG (retrieval-augmented generation) database, structuring the vector world into something usable across their data platforms and sources.

Gregory positioned himself as the project manager navigating these parallel streams, with Sam serving as technical liaison to Regen Ledger, ensuring the Gaia AI team had access to existing tooling and infrastructure.

## MCP Server Architecture: Three Pillars of Infrastructure

Sean shared their consolidated architectural direction, which had crystallized around creating reusable MCP (Model Context Protocol) servers rather than focusing primarily on standalone agents. This shift emerged from their previous conversations—they had initially envisioned a web UI where team members could interact with agents, but lacked clear definition of who would use that interface and when.

The pivot to MCP servers proved more productive: these reusable tools could be passed to agents or used directly in workflows by team members. This approach provided deployment flexibility—agents could be deployed across multiple platforms, whether ElizaOS, Google Cloud, or other systems—because the focus remained on their own tool library rather than platform-specific implementations.

Their infrastructure now centered on three core MCP servers, each serving distinct but interconnected purposes:

### The KOI MCP: Knowledge Organization Infrastructure

The KOI MCP represented their knowledge organizational infrastructure—a comprehensive set of eleven sensors pulling data from social media platforms including Telegram, Twitter, GitHub, GitLab, and various websites. This data underwent two parallel processing paths: vector embeddings for semantic search and RDF (Resource Description Framework) structured graphs for relationship mapping.

The system stored this information in two databases: Apache Jena for the structured graph and Postgres for the vector embeddings. The KOI MCP made all this information semantically searchable through a clean interface centered primarily on a "search knowledge" tool. Initially, they had coupled this directly with the backend of their ElizaOS agents, providing them with dynamic retrieval from the knowledge network. However, they extracted this functionality into a standalone MCP server, making it accessible to any interface—Claude, Cloud Code, or user-preferred tools.

Sean described the interface structure: MCP servers offer three feature types—resources, tools, and prompts. For KOI, the primary tool was semantic vector querying across their knowledge network. The system worked effectively and had become quite convenient; Sean used it directly in Cloud Code, and it remained integrated with their Eliza agents.

A critical architectural consideration emerged around organizational permissioning. Rather than building a bespoke solution for access management across their knowledge infrastructure, they were now leaning into existing systems like Google Drive and Notion, leveraging permissioning that already existed in these platforms.

### Security Considerations: The Dark Triad of Agent Vulnerabilities

Zach raised an important security question about the KOI MCP's internet access. The system didn't have direct internet access—it only queried embedded content. The architecture separated concerns: the KOI MCP hit the KOI server via API calls, while the server maintained scrapers that continuously pulled from sensor nodes.

This separation addressed what Zach termed the "dark triad" of agent prompt injection vulnerabilities. When all three elements—internet access, write permissions, and untrusted content—exist simultaneously, severe security risks emerge. Their architecture had two of the three potential threat vectors open but had closed the third by limiting direct internet access.

This sparked an important discussion about trust boundaries within their knowledge infrastructure. They needed to distinguish between trusted sources—like their own GitHub repositories with PR review processes, or internal knowledge in Notion and Google Drive—versus public forums where prompt injection attacks could theoretically occur if adversaries knew they were scraping that content.

Gregory suggested potentially splitting the KOI MCP into two separate interfaces: a public-facing Regen knowledge MCP and a private one, each with different security rules and interaction patterns. This would allow them to maintain appropriate boundaries while still providing comprehensive knowledge access.

Zach referenced a recent paper on managing this dark triad, promising to share it with the team. The core principle involved controlling write access and information quality: when agents have write permissions, complete control over information quality becomes essential, as current systems cannot guarantee against being compromised by the information they scan. Internet access creates leakage risks, while write permissions enable potentially nefarious actions.

The team could augment security through robust auditing and the ability to undo writes—implementing a commit/uncommit design pattern. As a general principle, all their MCP tools and agent operations started with read-only access. The Regen Registry Review MCP agent maintained some write access on the server—uploading documents and maintaining a checklist in a directory—but this remained limited and controlled.

### The Registry Review MCP: Automation for Carbon Credit Verification

The Registry Review MCP emerged as their highest-impact, most concrete deliverable. Becca, their team member working with Ecometric on carbon credit projects, faced an overwhelming workload: 111 projects requiring registry verification. Without AI assistance, this volume would prove insurmountable. Yet the solution needed to balance quick automation with forward-looking architecture.

The spectrum of options ranged from Becca simply using GPT or Claude projects with custom prompts and character files—essentially hacking together an automation workflow with existing tools—to engineering a full custom UI and specialized agent. The team worked to find the middle ground: something deliverable and actionable for Becca while remaining as architecturally sound as possible.

Sean had worked closely with Becca to break down her workflow into seven detailed steps, building decoupled, independent workflows within the MCP server. The system received a directory of input files—PDFs, spreadsheets, GIS data—and progressed through these stages:

**Project Initialization**: Establishing the review context and preparing the workspace for a new project evaluation.

**Document Discovery**: Identifying all available documents in the directory. While they envisioned this connecting to Google Drive where files typically lived, the current implementation worked with local directories to bypass permissioning complexities during development.

**Data Extraction**: Pulling out required data points and matching them against Becca's 23-item checklist. This represented the high-value automation piece—automatically extracting information from documents to populate the verification checklist.

**Cross-Referencing**: Validating information between the checklist and documents, ensuring consistency and completeness across all submissions.

**Report Generation**: Producing a comprehensive report based on extracted findings, formatted for human review.

**Human Review Prompting**: Creating clear decision points where human judgment determines whether to iterate back to previous steps or move toward completion.

**Completion Phase**: Marking projects as complete once all verification requirements were satisfied.

This well-defined workflow lived in the MCP server, with the agent itself serving as a thin layer—essentially just context and personality. The agent knew it was helping with a registry review process and had access to the MCP server, but the MCP performed the actual work. This design meant the same character prompt could drop into Claude, GPT, Gemini, or the ElizaOS interface seamlessly.

## Evaluation Strategies and Human-AI Collaboration

Zach highlighted a crucial consideration for this non-deterministic development: the role of evaluation and validation. Traditional deterministic development relied on debugging, unit tests, and functional tests to gauge completeness. In the non-deterministic AI world, evaluation ("evals") and rigorous testing of expected behavior became paramount.

The human review step presented an interesting challenge. While LLMs excelled at document discovery and information extraction, the details mattered enormously in carbon credit verification. If the system extracted something adjacent to reality rather than precisely accurate, the consequences could be significant. Zach asked how they planned to help humans quickly verify that the agent had performed correctly, without forcing them into a "needle in a haystack" replacement of their original manual process.

Some LLMs now provided citation interfaces, offering direct source references. Sam jumped in with context from his earlier design work on this system from the summer. His initial vision centered on references and citations throughout the verification process. The approach would codify requirements into machine-readable modular format, citing where each requirement originated—for example, "land tenure requirement is cited in program guide section 8.1 and the credit protocol."

When the verification tool evaluated a project, it would indicate: "We think this met this requirement, and here are the citations showing exactly where we found that information and why we believe it's satisfied." This would enable quick human verification—clicking through to project documentation section two or a specific land ownership document to confirm completion. Some verifications would be straightforward with high confidence, requiring minimal human review. Others might have higher margins for error, requiring deeper investigation. But the human reviewer would always understand the agent's logic and know where to look.

Gregory raised an important point from their previous day's discussion with Becca: they needed to ensure that audited items appeared properly in the data layer, not just scraped from documents. The team had to interface with specific on-chain anchors rather than relying solely on document parsing.

Gregory suggested publishing a semantic checklist within the data module for each credit class and method being verified—a precise specification of what needed to be true. Currently, this existed in method documents, but that introduced error. They needed a registered library for the registry agent: a checksum of requirements that needed to be true and reported. This library could identify which items could be checked by agents versus requiring human verification.

This might require a sub-agent workflow: first scraping and developing the review protocol from methods documents, registering that protocol, then having the actual verification agent work against that registered standard. Sam clarified that their current use case optimized for completeness rather than correctness—ensuring submitted information was complete against requirements rather than verifying accuracy. This represented a much more achievable initial goal.

The primary challenge became ensuring precision and accuracy in generating the completeness checklist automatically from method documents—or doing it manually and registering it properly. Once that checklist existed, the verification system could work quite effectively.

## Data Architecture and Integration Challenges

Sam provided context about their blockchain-first approach and the ideal fully-fleshed implementation. In the complete vision, they would anchor information on the ledger for provenance and audit trail—verifying that the same documents passed between parties remained unchanged, with indexing showing where documents lived.

However, the more immediate pain point involved document sharing and resolution across platforms. Currently, partners used Airtable, shared SharePoint links, which Becca downloaded and uploaded to Google Drive, with possible subsequent platform uploads—documents stored in multiple locations without clear authority. The data anchoring and provenance side actually seemed straightforward: posting to the ledger and registering with a resolver. The real challenge was determining where information lived and how to connect to it efficiently.

Could they connect directly to partners' SharePoint instances? Could partners adopt their storage solutions instead? How could they minimize the places information was shared and stored? These file management details—tedious and rarely discussed—consumed significant time in practice.

Sam emphasized the importance of defining requirements, file structures, accepted evidence types, and expectations upfront. For each protocol, knowing that ten specific documents would be submitted in a relatively uniform way allowed them to leverage prompt engineering or structured folder definitions toward more deterministic and accurate solutions.

## Product Development Methodology: Story Mapping for AI Agents

Zach introduced a product management technique he'd found invaluable for agent development: story mapping. This approach, which he'd developed as a variant of a traditional method, excelled at navigating what he called the "doable-desirable dance"—balancing what's desirable with what's actually achievable. This trade-off discussion proved especially valuable in AI agent development.

For agent replacement of existing workflows, the technique worked exceptionally well, providing crisp clarity about human activities and a clear place to describe agent-level functionality. The method layered in release points—defining how much was enough for a first phase or release.

Zach had created an example that took about two hours—a timeline enabled by his familiarity with the process. The story map visualized workflow in layers:

**Top Layer**: Major user steps representing high-level categories of work, with key user activities broken down under each. Zach emphasized completing this top layer first—understanding what major steps users took and detailed activities under each—before moving to implementation planning.

**Middle Rows**: Product development tasks and architectural decisions, organized under the corresponding user activities.

**Bottom Rows**: Different release points where sufficient functionality existed to release and gather user feedback.

This structure created immediate clarity. What seemed like a handful of steps at first glance expanded into numerous detailed activities once thoroughly examined. The visual format made this complexity navigable—showing both the full scope and the incremental path forward.

For the first increment, Zach focused on just three elements—the core "nouns" of the domain—shipping that narrow scope to get feedback. Subsequent increments built out additional functionality systematically. Once developed, he shared it with domain experts for feedback: Was this necessary? Were they heading in the right direction? Had they missed anything critical?

Zach found this approach super clarifying for organizing work, communicating increments, and gathering effective feedback from both domain experts and adjacent stakeholders. He noted that while generally useful in normal product development, the technique proved especially valuable for agent development because it forced viewing the workflow from the person doing the work's perspective rather than a technical viewpoint.

Sean requested a template, and Zach offered to create a Miro board to share. Sean could map his existing interview notes with Becca into this structure, creating a clearer communication tool for discussions with Sam and Gregory about actual scope and incremental delivery.

## Learning-Informed Adaptive Development

Zach added another dimension to the release planning: identifying what he called the "teaching a monkey to recite Shakespeare" element for each phase—the biggest unknowns requiring empirical evidence. This referenced Astro Teller's famous blog post about tackling the hardest problems first rather than building comfortable infrastructure.

For their first release phase, the critical unknown was whether the LLM could coach to a degree reasonable to an expert. For each subsequent phase, they should identify the biggest uncertainty—the "monkey" they needed to teach—and build evidence and learning around that rather than taking a big bang release approach.

Zach described his evaluation framework, derived from Strategyzer's testing cards: What evidence will you observe? What threshold increases your confidence that this is working as intended? What threshold erodes that confidence? Thinking through these questions for each release increment created clear success criteria and learning loops.

When asked about end-user experience for internal tooling versus public-facing features, Zach emphasized the importance of evaluations throughout the development process. What does "good" look like? More importantly in a startup context: what does "good enough" look like? Defining these thresholds created concrete targets and prevented both over-engineering and premature release.

Zach also shared an interesting experiment: after completing his story map, he extracted it into linear textual format for LLMs, then fed that into Cloud Code as context documentation about what they were trying to build. This larger context seemed to improve Cloud Code's assistance, helping it make decisions that aligned with the broader goals rather than just solving immediate problems in isolation—much like humans working without sufficient context.

## Current State and Next Steps

Sean expressed confidence in the registry review agent specification, feeling it was well-defined and ready for heads-down development. The discussion had surfaced citations as a critical focus—something that had been in the spec but needed elevation to top priority. Anything the agent extracted should be cited with source document references.

He felt positioned for several weeks of focused work on two parallel streams: building out the registry review agent and working through Google Drive access and permissioning with Gregory's support. Gregory committed to spending more time that afternoon hopefully resolving the remaining GCP permission issues.

Looking forward, Sean acknowledged that integrating this work into Regen's broader Q4 and Q1 initiatives would require additional planning cycles. Multiple initiatives were converging across the Regen front, and ensuring proper integration would need dedicated attention. But for the current sprint, the focus remained clear: support Becca with the registry review assistant.

The team's challenge was balancing their limited time and budget with high ambitions, shipping functional tools that would enable them to operate as a small team with significant impact. They needed their best collective bang for the buck to live the startup dream—rapid iteration, meaningful delivery, and sustainable architecture that positioned them well for the new year.

Sean committed to building out a story map for their next Tuesday standup, populating it with existing work and taking a crack at generating a couple layers of iteration based on Sam's architectural documentation. The goal was to spend 30-45 minutes in that meeting validating the structure rather than starting from scratch.

The meeting closed with appreciation for Zach's methodology and insights, and renewed focus on the immediate deliverables while maintaining awareness of the longer architectural vision guiding their work.

## Key Technical Principles Established

Throughout the discussion, several core principles emerged for their AI agent development:

**Model Agnosticism Through Tooling**: Rather than coupling to specific AI platforms, focus on building robust, reusable MCP tools that work across any model or interface.

**Security Through Separation**: Maintain clear boundaries between trusted and untrusted data sources, limit write permissions, and prevent the convergence of all three dark triad vulnerabilities.

**Human-AI Collaboration**: Design for human review at critical decision points, with citations and references enabling quick verification rather than full manual re-review.

**Incremental Delivery**: Ship narrow functionality early to gather feedback, with clear evaluation criteria for each release increment.

**Context Architecture**: Maintain larger context about goals and workflow to help both humans and AI make aligned decisions at each step.

**Completeness Before Correctness**: For their registry use case, optimize first for verifying complete submissions rather than tackling the harder problem of accuracy verification.

These principles would guide their development through the coming sprints, helping them navigate the tension between infrastructure investment and immediate value delivery in an extraordinarily fast-moving technological landscape.


The document captures the strategic tensions, technical architecture, security considerations, and product development methodology discussed in this product reboot meeting.

Appendix A: Zach's Notes on Learning Expectations for the Increments:

For each release increment, I like to create 1 to 3 of these Learning Expectations:

    We believe: [describe the hunch/guess/assumption you want to better understand]
    We will try: [describe what you will try to build evidence about your hunch/guess/assumption]
    Our confidence will increase when: [describe the qualitative and/or quantitative evidence that will increase your confidence in your hunch/guess/assumption]
    Our confidence will decrease when: [describe the qualitative and/or quantitative evidence that will decrease your confidence in your hunch/guess/assumption]
    We expect to have sufficient evidence in: [the timeframe you expect to have enough evidence to evaluate this belief]
    [optional] With increased confidence, next we would: [describe with increased confidence what you would try next]
    [optional] With decreased confidence, next we would: [describe with decreased confidence what you would try next]
    [optional] This is safe to try because: [describe how you will detect if what you’re trying is becoming unsafe and how you will recover from any negative side effects]
