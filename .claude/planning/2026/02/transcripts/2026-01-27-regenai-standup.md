January 27, 2026 — Regen Network / Gaia AI Standup
https://claude.ai/chat/44fe1e75-cd2e-4e78-aa76-65d0a87f380b
Team standup focused on the Registry Review Agent's evolution toward integrated data pipelines, the challenge of enabling multiple developers to "vibe code" simultaneously without conflicts, and business development strategy for AI services in the environmental/ESG sector. The agent was transitioning from simple PDF processing to integrated data pipeline automation.

# Regen AI Standup: Collective Intelligence and Coordinated Creation

*A conversation about building shared infrastructure, scaling registry automation, and nurturing an ecosystem of regenerative AI services*

---

## Opening: The Beautiful Chaos of Collaborative Development

The call opened with a confession familiar to anyone who has fallen down the rabbit hole of AI-assisted development. "I'm deep in the Claude hole," came the greeting, followed by news that Christian had just been set up with MCP servers and all the associated tooling. The implication was clear: things were about to get chaotic.

The immediate concern was architectural—how to enable multiple people to vibe code on interrelated projects without the whole endeavor devolving into a dumpster fire. The morning had been spent wrestling with Eliza agent architecture, GitHub workflows, and the fundamental question of coordination: how do you let a bunch of people hack on the same ecosystem without stepping on each other's toes?

The proposed solution was elegantly simple. Upon starting Claude Code for Regen work, everyone would authenticate into GitHub and pull from a shared `claude.md` source. This way, the team could collectively upgrade their shared AI with skills and abilities, cultivating a single intelligent assistant that everyone contributes to and benefits from.

"Claude told me to do it," came the sheepish admission about this architecture. Someone noted that the inventor of Claude Code had suggested something similar. "Like father, like son," they laughed. "Might be a good t-shirt: Claude told me to."

---

## First Steps into the Code: Becca's Baptism

Becca joined fresh from running Claude Code for the first time—that particular mixture of excitement, overwhelm, and tentative pride that comes with crossing a new technical threshold. She had gotten connected to the MCP servers and authenticated with her Regen email, but hadn't yet prompted the system. The Hard Fork podcast had been her inspiration; they'd challenged listeners to build something with Claude Code, and the responses from people who had never coded before were remarkable.

"Is this vibe coding? Is this what it is?" she and a colleague had wondered while using a coworking session to get things moving. Then it failed. "This sucks," they'd concluded. But failure is part of the process. It fails a lot. It also works.

---

## The Agenda Takes Shape

Three themes emerged for the standup. First, a quick check-in on the Claude Code onboarding experience. Second, the Registry Review Agent—status, next steps, and the path forward. Third, and perhaps most expansive: business development, future agents, tools, and the emerging business logic of AI services for environmental markets.

Beyond these immediate concerns loomed a broader energy building in the community. People were eager to start using MCP and Claude to charge hard on ambitious projects—complete overhauls of Regen token economics, vibe-coded application extensions, and other initiatives that had captured people's imaginations. The challenge was coordination: how to channel this distributed creative energy without creating chaos.

---

## Registry Review Agent: From PDFs to Integrated Data Pipelines

The conversation turned to the Registry Review Agent's evolution. The team had just met with the technical group running the geospatial platform that houses much of the relevant data. They were exploring an Airtable automation flow that would reduce the need to access numerous documents beyond PDFs and spreadsheets.

For registration purposes, the nearer-term use case involved reviewing over one hundred farm entities and cross-checking them against an equal or greater number of land tenure documents. The architectural question was whether to treat this as a meta-project—cross-checking all hundred farms at once—or running the process separately for each farm.

Sam had created a specification based on the Carbon Egg relationship and their desired data pipeline. This represented a leap beyond simple PDF review toward a fully integrated system that could check in with monitoring tool APIs. The team had walked through all the specific data types, their storage locations, movement patterns, and access points or blockers.

The question this raised was fundamental: Is this a different agent type, or a capability built into the existing agent? Should there be a specialized agent for technically sophisticated projects that aren't using PDFs and Excel spreadsheets, or should the existing agent handle both modalities?

The documents flowing through the agent would include project plans pulling data from all hundred farms into single documents, monitoring reports aggregating various data types, and references to supplementary evidence like laboratory reports and sampling spreadsheets. The lowest common denominator was pre-populating checklists and reviewing monitoring reports—checking whether information matches up and satisfies requirements—before extending to other data types.

On the ledger side, each farm would be represented individually on-chain, but credits would pool into a meta-project structure. This allows granular farm-level data while presenting a unified project page. The checklist produced by the agent would associate with the pooled project, with drill-down capability to individual farm granularity.

---

## Technical Onboarding: Marie and the Codex Frontier

A quick check on Marie's progress revealed she was still in the setup phase, working through Slack to get things configured. She was breaking new ground by connecting MCP to Codex—territory no one else on the team had explored yet. There might be edge cases to discover. She was also potentially using an IDE like Cursor, which added another variable to the configuration puzzle.

The eval system was set up and running; the next step was reviewing the output of the automated tests to assess their usefulness.

---

## Business Development: AI Services for a Contracting Industry

With Zach on the call, the conversation pivoted to business development vision. Extensive research and conversations with players in the ESG world had revealed a tremendous window of opportunity. Three main sectors would need services going forward: compliance buyers pursuing net-zero commitments, and carbon credit developers—work that aligns directly with infrastructure Regen has built over five years.

The market is worth billions, and while some businesses have begun to tap it, few are as well-positioned as the combined Regen-Gaia team. Given the regulatory environment in the US, this would necessarily be an international enterprise, with Canada, the UK, and other markets potentially needing these services even more than most American markets. California and New York remain notable exceptions.

The proposal was straightforward: identify targets from within the existing network first. Keep the business logic simple with a 50-50 revenue split—engineering and backend on one side, client development and reputation on the other. Once revenue flows and wins accumulate, explore more complex structures like merging or joint ventures. Defer the complicated business logic for a couple of months and focus on execution.

### A Hard-Nosed View of the Market

But it was important not to set anyone up under illusions. Two of the target segments sit squarely on the demand side of the nature market, and cracking that nut the old-school way is brutally difficult. Cycles are slow, especially at higher tiers.

The strategic approach needed to focus on what already exists versus what would need to be built out—the lowest hanging fruit, the agents and automations that could spin up quickly using existing capabilities.

The reframe was clarifying: this is an industry in contraction. The service being offered is essentially contraction support—graceful landings, stakeholder maintenance, knowledge preservation. Emergency automation for organizations facing the same pressures Regen itself confronts: the need to cut costs while maintaining effectiveness.

"Let's be lean and let's be quick and let's have the shortest cycles possible," came the directive. Before pitching companies on $250K annual contracts, start with $5,000 monthly AI support or $20,000 upgrade packages based on knowledge already accumulated from existing relationships. First loop, concentric circle—harvest what exists in the immediate ecosystem and get some small wins.

Those wins serve multiple purposes: revenue, learning, and infrastructure building. Each engagement helps build out tooling and intelligence while supporting stakeholders with their own automation leaps.

### The Demand That Already Exists

On the demand side, the opportunity lies in replicating what companies currently pay auditors, ratings agencies, and standards bodies to provide—all of which is expensive. A bespoke, rapid alternative could represent real value.

On the supply side, hundreds of people knock on the door monthly seeking readiness support. Even the State of Regenerative Technology call drew hundreds of people hungry for guidance. What they need is a readiness support agent—something to walk them through accessing the nature market from wherever they currently stand.

The experience exists. The knowledge exists. The question is making it accessible. How many people would pay a hundred dollars a month for a practical, hard-nosed nature market assistant that knows how to help right now and can link them to relevant resources?

This has been the truest, most consistent signal over Regen's five-year existence: people coming to the door wanting exactly this kind of support. A thousand people sit in communities like BioFi representing latent demand.

---

## Vibe Coding for Everyone: Beyond Claude Code

A parallel thread emerged around making AI-assisted development accessible to people who aren't comfortable with Claude Code out of the box. A quick specification run had tested whether Replit, Lovable, or other designer-friendly interfaces could work with existing tools.

The answer was yes. Someone could log into Replit, do a couple things, and find themselves in a Regen app development interface. For twenty dollars a month, people who would never touch a terminal could ship real work.

This led to thinking about authentication as a service. Curate and garden with KOI and other services and tools, provide an auth credential, and when people log into these platforms, they get custom markdowns, skills, MCP servers, and other resources that prevent wheel reinvention and enable shipping work that interlinks with existing tooling.

---

## The Shared Claude: Collective Intelligence Infrastructure

The conversation turned to the core coordination challenge. The proposal: a single private GitHub repo that everyone SSHs into, containing the shared `claude.md`, skills, and repository architecture. When Christian starts, when Max starts, when Becca and Dave start—none of them need to spend tokens building out context engineering from scratch. Connect to the Regen AI servers and start working on whatever problem needs solving.

You might log out of that shared context and have your private `claude.md` on your local machine. You might do other things. But you could also push upgrades that you discovered during your own work—it's a Git repo, so pull requests and reviews enable coordination around how people use Claude collectively.

This becomes the meta-KOI object for the intelligence. It never stops upgrading; it just has version control around how those upgrades happen.

Most repos already have a `claude.md`, but expanding to include plugins, skills, and other tooling would create real collective wins. The excitement around Claude skills was palpable—there were wins waiting to be discovered.

The aim was a set of clear instructions for the machines to follow that everyone opts into, upgradeable when something isn't quite right. No one needs to understand every detail of the architecture; they just need to know it works and follow the same instructions.

---

## Small Miracles: Otter Meets Claude

A moment of genuine delight interrupted the proceedings. There's an official MCP connecting Otter directly to Claude desktop, plus an unofficial MCP for Claude Code users.

"I can connect my Otter?"

"Merry Christmas, Gregory."

The ability to search through meeting notes and transcripts directly through the AI assistant—this is the recursive collective intelligence everyone wanted. Every time evidence of meta-learning emerges, the excitement is palpable. This is what it's all about.

---

## Building the Feedback Loop

Testing the MCP servers revealed both capabilities and limitations. Specific requests like credit inventory weren't handled well, but pulling information about current functionality, credit class information, and projects on-chain worked smoothly.

The key insight: flag what isn't working well. These are the places where skills get built out, where `claude.md` gets extended, where MCP capabilities expand. Run a recursive tool-building process and fix problems as they emerge.

Even better: there's a feedback tool built in. Just tell Claude to submit feedback about what's not working with the MCP. The system learns from its own limitations.

"I just want this recursive collective intelligence thing," came the closing sentiment. "Anytime there's evidence of that, I'm so stoked. The meta-learning—that's what it's all about."

More smart. More together. More capable of meeting the moment.

---

*The call closed with an acknowledgment that the agenda had been covered, a note about schedule conflicts, and the usual encouragement to ping each other with questions. The tiger was being held by the tail—four terminal windows open, cloud code desktop running, ADHD fully activated by the five-minute thinking pauses that send attention scattering to other tasks. But the direction was clear, the coordination was improving, and the collective intelligence was growing.*
