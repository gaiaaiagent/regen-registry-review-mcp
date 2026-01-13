# Registry Review Agent: A Walkthrough Session

## Opening Notes

The call began with a moment of technical comedy—Becca had both a Zoom call and a Google Meet running simultaneously, a fitting metaphor for the Thursday they were navigating. The conversation quickly turned personal as Shawn asked about Becca's mother. Her voice softened with gratitude as she shared the good news: her mom, in her mid-seventies, would likely be discharged on Saturday—a small miracle after a frightening few days. While surfing wasn't on tomorrow's agenda, simply getting better felt monumental.

Becca thanked Shawn for his flexibility and understanding during this difficult time. The gift of a flexible schedule, they both acknowledged, carried its own grace.

## Reflections on the Community Call

The recent community call had been electric. Shawn described it with the visceral metaphor of whitewater rafting—that moment of "white knuckling" when you grip the oars so tightly your knuckles blanch. Fitting all the momentum into an hour felt nearly impossible, but the live updates painted a vivid picture: real projects, real people wanting to use these systems. This, after all, was the why beneath all the technical problem-solving.

Becca appreciated the grounding. The team excelled at solving intricate puzzles but sometimes struggled to land the fundamental purpose. She tried to anchor every discussion in reality: these tools mattered because people needed them. The message had resonated, and now they could jump back into the work wherever felt most relevant.

## The Technical Landscape

Shawn shared his screen, noting his computer had frozen several times during the call—likely from too many browser tabs. He'd spent the past two weeks hardening the server infrastructure, building in resilience so services would automatically restart if they crashed. It had been steady patchwork, one problem after another, tracking issues as closely as possible and addressing them as they surfaced. They were reaching a more stable state, though as Shawn quipped: talk is cheap.

The demo began simply. Shawn shared a link to the GPT—not publicly searchable on the GPT marketplace, but accessible to anyone with the URL. When it opened for Becca, she laughed at the avatar icons drawn from team members. Shawn had taken creative liberties but welcomed feedback if anything felt uncomfortable.

## The Eight-Stage Workflow

Shawn walked through his practice workflow, curious whether it mapped to Becca's reality. The system centered on *sessions*—each typically corresponding to a single project. Every session progressed through eight carefully designed stages, a journey Shawn likened to playing Mario, trying to reach level eight.

Behind the interface hummed GPT-5.1's thinking capabilities. In theory, you could ask anything—the system even had web search to pull supplementary information from the internet. But this wasn't just another chatbot. It came pre-loaded with specific instructions and connected to a custom API that orchestrated the eight stages: managing sessions, uploading documents, scanning content, mapping requirements, extracting evidence, cross-checking consistency, producing reports, and requesting human review. The human reviewer could send the session back to any stage or mark it complete.

When Shawn asked the system to describe its stages, it responded clearly:

**Stage One: Initialize**—assign a project ID, load it, confirm the methodology version.

**Stage Two: Document Discovery**—classify and map all uploaded documents.

**Stage Three: Requirement Mapping**—connect each checklist requirement to supporting documents, outputting a mapping matrix with coverage and confidence scores.

**Stage Four: Evidence Extraction**—scan through documents to find what the checklist requires.

**Stage Five: Cross-Validation**—check consistency across documents, ensuring dates align and details match.

Subsequent stages would generate reports and route through human review before completion.

Becca found herself enchanted: "It's like Christmas," she said, watching the system describe its own architecture.

## Understanding Document Classification

When the system mentioned classifying documents, Becca asked a practical question: did documents need specific naming conventions? Shawn confirmed it read filenames for initial context. The naming standardization function was simple right now—mostly replacing spaces with underscores—but could be refined. The system performed initial mapping just from document names, creating a list of which documents to examine for each checkpoint. Then in the evidence extraction phase, it would actually open and search through everything, reporting what it found and what remained missing.

The cross-validation stage emerged as particularly crucial. As Becca noted, people rarely tried to do something wrong—inconsistencies simply crept in. The AI could catch these patterns, perhaps even generating automated approval statements once items were reviewed and verified.

## The Technical Architecture

Shawn dove deeper into the mechanics. The GPT worked through API requests—a distinction worth understanding. Their usual approach involved building MCP (Model Context Protocol) tools that could be handed directly to agents. But GPTs didn't work directly with MCPs; that required platform-level approval, almost like getting into an app store. Instead, they created API wrappers around their MCP tools, exposing functionality the GPT could access through standard API calls hitting the MCP server.

Becca appreciated the clear explanation of this architecture—the layers and connections that made the system work.

## The Demo Session

Shawn began testing with a new session called "test fee," though it could be named anything. As the system prepared to create the session with specified project name and methodology, it confirmed: "Session created, methodology checklist requirements loaded. You're in Stage One: Initialization. Next step is to upload and discover your project documents."

Here came the first potential gotcha. The way to upload documents wasn't intuitive—not just hitting the plus button to add files. Instead, you needed to explicitly say you wanted to upload files. When Shawn did so, the system generated a secure upload link.

But then—a snag. The page returned "not found." Shawn remained calm; he'd been modifying things on the server earlier and could likely fix it in real time.

## Debugging with Claude

Shawn secure-shelled onto the server, navigating to their projects directory where the Regen Registry MCP lived. He pulled up Claude Code, marveling at how convenient it was—an AI assistant running directly in the terminal, accessible even on remote servers. "It's such an unblock," he said. "It's weird how some things... I'm sure for you, you're like, why did this take so long?"

What used to require three hours of debugging now moved swiftly with Claude helping parse the code and context. Shawn had been remapping ports, transferring all services to be managed by Supervisor—a Linux utility that watched programs and restarted them if they crashed. In the migration, some IP addresses got swapped and services began overwriting each other. He'd been ironing out these kinks but hadn't retested the data upload service.

Becca watched in fascination as Claude processed the codebase: "It's just kind of crazy to watch it work. Like how many lines of code it can process."

Shawn agreed. Claude had access to bash commands, git operations, anything a system administrator might run—it could slice and dice through all of it. Becca found the linguistic choices interesting too: words like "simmering," "cooking," "worrying" made the AI feel more human somehow.

"There's so much going on here beyond just the transformer models," Shawn reflected. "It's not just a chat message and response system. It's infrastructure managing the whole context, all the tooling and actions the agent can access, its persona and personality."

Becca called it crazy. Shawn called it a new engineering primitive—a fundamental shift in computing, a new substrate people were still learning to grapple with and stretch. Almost like a new operating system.

## The Testing Phase

After the walkthrough, Shawn encouraged Becca to spend time testing—maybe ten to thirty minutes, or even less at first. They were in an alpha phase, pre-beta, where the system worked but remained early-stage. He wanted her to play with it until she hit a snag, screenshot it, send it over with a few words of feedback. He tracked known bugs already: the data upload server issue they'd just encountered, and another problem with cross-validation where the Anthropic API sometimes returned text instead of JSON.

The system worked by converting PDFs to Markdown files, then using Anthropic to scan for structured data. When responses came back as text rather than the expected JSON format, it broke the workflow. Shawn planned to make the prompt more explicit, and thought he could address any bug within one or two days. By week's end, these current issues should be resolved.

Becca felt comfortable with this process—she'd done user testing before, documenting and pushing feedback. She also wanted Giselle involved. Shawn had met with her the previous day for thirty minutes, mostly getting to know each other. She'd seen the demo and was excited, though busy this week. Next week made more sense for her deeper involvement, which aligned perfectly with Shawn's bug-fixing timeline.

## The Why: Ecometric and Scaling Regeneration

As they prepared to wrap up, Becca offered crucial context—the why beneath all this technical work. A group from the Czech and Slovak Republics was working with over one hundred farms committed to regenerative agriculture, expecting carbon gains from their work. They'd tried other programs but wanted to partner with Regen Network, wanting to use their specific methodology.

The scale posed a beautiful challenge. Regen Network was still relatively small, yet this partnership demanded they meet a level of scalability that only this kind of AI-assisted system could provide. The ability to process that many projects would literally trickle down and unlock opportunities for individual farmers trying to improve their landscapes.

Shawn absorbed this context deeply. He wanted these systems reliable and consistent, able to scale to meet demand. Taking on 111 projects from Ecometric—that was the vision. The most cutting-edge tooling, harnessed for tangible regenerative impact.

## Closing Thoughts

Becca would review the video documentation and continue testing, dropping feedback as she went. Despite the technical challenges—or perhaps because of them—both expressed genuine enthusiasm for the work. Shawn was simply having fun with the project, excited about the agents and their potential.

Becca laughed at the absurdity of it all: here she was with a master's in soil science, doing this kind of technical work. But their team was small, resources constrained. The imperative remained clear: must unblock, must scale, must enable.

Necessity, as they say, mothers invention.

They said their goodbyes, Becca still at her sister's house navigating family care, Shawn preparing to continue debugging and refining. The work continued—infrastructure hardening, bugs resolving, systems stabilizing—all in service of farmers in Czech and Slovak Republics and beyond, all working to regenerate the land.

---

*The transcript captures a moment of collaborative technical development where human care, sophisticated AI systems, and ecological regeneration intersect—a Thursday afternoon building tools to help heal the planet, one carbon credit verification at a time.*
