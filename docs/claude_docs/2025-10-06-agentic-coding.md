# Agentic Coding Devlog: The Power of Claude 4.5 Sonnet

*A technical exploration of advanced agentic workflows and distributed AI development systems*

## Introduction: A Step-Change in Agentic Tool Use

Welcome to this agentic coding devlog. Let's begin with the facts: the Claude 4.5 Sonnet release speaks for itself. It represents a step-change improvement, clearly trained for agentic tool use and agentic coding. The model itself is powerful, but when you take this model and place it within the right agent architecture—when you deploy it inside Claude Code—this is where we achieve the best agentic coding tool by far, bar none.

Tools like Codeacai and Gemini CLI are nowhere near as capable as many believe. If you doubt this claim, what follows will demonstrate the distinction clearly. I challenge anyone to replicate even half of what you're about to see using those alternative tools. Spoiler: you won't be able to.

## The Challenge: Two Parallel Problems

Today's agentic coding session addresses two distinct problems: one running in-the-loop on a local device, and another delegated to a dedicated agent environment. The specific task involves migrating a codebase from the Claude Code SDK to the newly released Claude Agent SDK. This requires updating deprecated syntax and implementing several structural changes across the repository.

While executing this migration locally, we'll simultaneously delegate prototyping work to agents running on a dedicated device. These agents will build prototypes of real-time agents using the OpenAI tooling—a perfect demonstration of distributed agentic workflows.

## Delegating Work: The AFK Agent Pattern

Let's hand off the prototyping task to our agents right now. Claude Code runs in YOLO mode with a reusable MCP server prompt designed for delegation. The command is simple: `/AFK agents`. This prompt embodies a pattern for passing work to autonomous agents—literally going AFK (away from keyboard) while agents handle the implementation.

The delegation requires three key variables: the prompt itself, the ADW (Agentic Developer Workflow) name, and any necessary documentation. The task specification is straightforward: accomplish these three objectives. We want three distinct agents built as separate scripts, and we need quick validation testing to ensure they function correctly. This creates a closed-loop structure with validation commands embedded directly in the high-level prompt.

The specific ADW plan follows a familiar pattern: plan, build, ship. We pass in precise documentation—the exact specifications needed for the task. On the agent device, you can watch as this job gets picked up immediately. A fleet of agents on that device will now handle this work autonomously. The system sleeps in sixty-second intervals, checking in periodically to monitor job status and performance.

## The Scout-Plan-Build Workflow

Opening the local codebase reveals a private, proprietary repository with eight distinct applications. Firing up a Claude Code instance with MCP JSON and Firecrawl, we immediately enable thinking mode—there's no reason not to leverage additional compute. This workflow has been refined through countless iterations and encoded into a reusable custom slash command: `/scout-plan-build`.

The inputs are elegantly simple: user prompt and documentation URLs. We begin by grabbing the documentation URL and passing it in, along with the core instruction: migrate to the Claude Agent SDK. While writing prompts at this high level, it's valuable to review the exact work that agents will perform. Through practice—adopting your agent's perspective and reasoning through what it will encounter—you'll identify potential gaps in understanding. Claude Sonnet 4.5 handles most scenarios well, but certain details warrant explicit attention.

For instance, the system prompt is no longer the default in the new SDK. If you're using this framework, you must explicitly employ the new syntax. We highlight this specific section with a note: "Pay close attention to this section to ensure our update uses the new syntax correctly." That's all the guidance needed.

## The Power of Composable Prompts

What makes this workflow exceptional? Let's examine what's happening under the hood. This demonstrates capabilities that other agentic coding tools simply cannot match. We have a well-thought-out, carefully constructed, reusable agentic prompt implementing a three-step workflow. The structure is clean: Purpose, Variables, Instructions, Workflow, Report.

First, we scout the codebase for relevant files. Then we plan what needs to be done. Finally, we build. But why include this additional scouting step? Examining the agent execution reveals something remarkable: the first action is running `/scout`. This utilizes one of Claude Code's newest features—the ability to run custom slash commands inside other custom slash commands. In other words, you can compose your agentic prompts. This is transformative.

Let's understand what this means in practice. The workflow is superficially simple—three steps. But deeper examination reveals that from our simple input, the agent spins up four sub-agents to accomplish work on our behalf. Let's trace this prompt-by-prompt to understand how we're chaining compute together with Claude Code 2 and Claude 4.5 Sonnet.

### The Scout Step: Delegating Search

Dialing into the scout prompt reveals the strategy: search the codebase for files needed to complete the task using fast, token-efficient agents. We're delegating the searching process from the planning step into a dedicated scouting step. This implements the R&D framework—Reduce and Delegate—the only two viable strategies for managing context windows.

Here we're offloading from the plan step and deploying four agents in parallel to run searches. These are fast, inexpensive, yet quality models capable of substantial engineering work outside the primary agent's context window. The sub-agents complete their tasks: Gemini Light runs, CodeX executes, and from these scout searches, sub-agents spawn their own processes. They create a relevant files markdown document.

Our agents quickly search through exactly what needs modification, identifying the precise locations requiring updates. We've scaled up compute to obtain multiple perspectives—crucially, not just running another Claude agent highly aligned with previous outputs, but running Gemini, Open Code, Gemini Flash preview, CodeX, and potentially even Haiku in this workflow. The relevant files collection gets created, capturing not just which files need updating, but the exact offsets and character counts needed to access valuable information. Multiple agents take independent passes at this analysis.

### The Plan Step: Focused Context

We're now moving to step two. The planner reads all relevant files assembled by scouts and begins scraping necessary documentation. We want this locally available for all agents in our pipeline moving forward. This scout prompt resides in the Building Specialized Agents codebase—members of Agentic Horizon will have access to this extended lesson.

There's no reason to do this work manually anymore. No reason to prompt in-the-loop repeatedly. But we're stepping through it piece by piece here for demonstration. To recap the scout workflow: this technique offloads context from the planning step. You want your planner's context window free to focus genuinely on accomplishing the job, not merely reviewing files. File review isn't planning—it's context building, which is important but separate. This scout-build-plan three-step workflow has proven remarkably powerful.

The planner itself isn't particularly novel—you've likely seen similar planning workflows before. The structure is familiar: Purpose, Variables, Instructions, Workflow, Report. The process is straightforward: analyze, scrape docs, design, document the plan, generate, save, and report.

### The Build Step: Execution

When you separate prompts into distinct phases—scout, plan, build, or whatever workflows your work demands—you make it effortless for yourself, your team, and your agents to understand what's happening. This feature in Claude Code is incredible: you can now chain custom commands, which means chaining agentic prompts together. You can isolate and reuse patterns more effectively than ever before, using explicit syntax that agents understand perfectly.

We have this composite agentic prompt broken down clearly: `/scout`, `/plan-with-docs`, and `/build` running at the end. The plan captures everything that needs to happen. We're agent coding—we're setting up the reusable primitives of agentic development. These plans, these prompts, these reusable and encodable pieces of knowledge ensure our agents know how to accomplish tasks. We're deploying compute intelligently.

## Context Window Management: The Hidden Constraint

We cannot blow up our agents' context windows. Consider this workflow carefully—there's a problem lurking here. You'll notice one agent runs all these operations sequentially. Running `/context` on our single agent reveals a significant issue: this agent has consumed considerable context.

One agent working through all the fixes piece by piece—this is not work you should be doing manually. If you're prompting this work back and forth repeatedly, you should be investing in your prompting layer. You need more prompts to scale up compute, and you want these prompts to be reusable. Prompt engineering is critically important—just as important as context engineering. With every agent you spin up, you must manage the core four: context, model, prompt, and tools.

Our plan included tests. The codebase contains eight custom agents—eight individual applications that our agent is updating sequentially, making these migrations one after another. Very powerful work, and I guarantee you're not pushing your prompts far enough. They can do far more than you believe possible.

The agent successfully caught the critical system prompt migration—it identified that the old system prompt syntax needed replacement. Phase five, phase six—everything complete. The pong agent tested successfully. Let's test a few more agents that don't require UI components. Some agents demand UI interfaces we'll skip those. Meanwhile, our dedicated agent device has already finished its task.

## The Agent Device: Out-of-Loop Execution

Opening the agent device reveals the workflow sleeping in sixty-second intervals, continuously checking job status. You can observe different agents—the builder, the shipper—appearing in separate sixty-second interview windows, showing the status of this agentic job running on the dedicated device. This is extraordinarily powerful.

Let's recap what happened: we ran a single prompt—scout-plan-build—that triggered an agentic workflow. Why emphasize "agentic prompt"? Because we must recognize how capable these prompts truly are. We're not merely interacting with a chat interface equipped with a few tools that runs briefly. These are agents in the terminal. These are agents that listen. There's high adherence to prompts with powerful models like Claude Sonnet.

To push even further—and this is why tools like Codec CLI and Gemini CLI aren't close competitors—you cannot approach the leader by simply copying their feature set repeatedly. We have powerful compute running especially well inside a custom-built agent harness: Claude Code.

This powerful prompt executes three steps. We have a scout phase searching for files to satisfy the user prompt, extracting that work from the planner's responsibilities. The planner now receives several powerful variables: user prompt, documentation URLs, and the relevant files collection assembled by scouts. We then have static variables—plan output and documentation output—followed by full instructions and workflow specifications. Finally, we have our build phase, which is a higher-order prompt where we pass prompts into prompts.

## The Context Window Crisis

This is the power of a great agentic coding tool like Claude Code—you cannot achieve this with alternative tools. We ran this elegant mid-level prompt and all this work completed agentically. Documentation got processed, everything executed properly.

But something critical demands attention. Running `/context` reveals an important insight: Claude Code has added an auto-compact buffer feature. Twenty-two percent of the context window is completely consumed by this buffer. Let's examine this more carefully.

Looking at message allocation shows fifty-one percent of context used by this agentic workflow. In Tactical Agentic Coding, we solve this problem completely by using dedicated AI developer workflows. We combine the old world of raw code with the new world of agents, putting them together and isolating our agents' context windows. These are substantial concepts explored deeply in Tactical Agentic Coding.

There's a fundamental problem here—limits exist, and that limit is the context window. Our primary agent, even with delegation, still consumed approximately fifty percent of our context window. Imagine pushing this further with a larger codebase or more detailed prompts. This represents a massive limitation of single individual agents, which is why we scale up to out-of-loop agentic systems.

### The Auto-Compact Problem

This chained agentic prompt workflow has limits determined by your agent's context window, amplified and restricted by the auto-compact buffer in Claude Code. There's a setting within Claude Code—opening a new instance and typing `/config` reveals `autocompact: true`. With auto-compact enabled, running `/context` shows twenty-two percent of our context window gone. This is a significant detractor from Claude Code's utility.

However, the Claude Code team recognizes that context is a precious resource for anyone using agents, so you can disable this feature. Turning off auto-compact and running `/context` again reveals the full ninety-one percent free—exactly what we want. The only content present is our custom agents, a few setup messages, and the built-in system prompt and tools. This is ideal: a focused, clear agent with maximum available tokens.

We were fourteen percent away from exploding our context in this large agentic workflow. ADWs (Agentic Developer Workflows) are the solution. The context window is a hard limit in the age of agents. We must respect this constraint and work around it. We must always observe what our agent can see. What is your agent's perspective? Does it have space? Does it have tools? Does it have the right model? Does it have the right core four? These are the critical ideas we must focus on.

As agentic engineers, we need to understand what our tools can do and what their limitations are, so we can understand what we can accomplish and where our boundaries lie. There is a direct causal link between your ability to control, build, and use agents and your engineering output.

## Output Styles and Observability

All four tested agents are now working perfectly. Notice the specialized output style—Claude Code 2.0 represents a fantastic release. However, something observed during use proved problematic: they're hard-truncating substantial output from agents as they run. The intention is keeping things clean, concise, and compact. While understanding this product perspective, this potentially takes Claude Code in too broad a direction, trying to make it the tool for everyone rather than specifically for engineers.

As an engineer, you want to understand exactly what your tool can do, and seeing all outputs helps achieve that understanding. A custom output style has been designed—Observable Tools Diffs TTS. This is a three-format output style providing all three diff reports, ordered tool calls, and audio task summaries. You get tools displayed, and since our last prompt only ran tests, there are no diffs to report.

This output style will be linked in the description if you're interested. If you're inside Agentic Horizon, you'll see the updated Claude Agent SDK syntax thanks to this workflow demonstrated here—single prompt, work completed. Additional testing will happen off-screen to ensure everything functions correctly.

## The Out-of-Loop Results

Let's examine our out-of-loop system. What happened? Our agents completed everything end-to-end, shipping the complete implementation. Let's see exactly what was built. Copying the repository path, creating a new temporary clone, opening it in Cursor—let's examine what our agents constructed.

We have our three requested agents. For clarity, reviewing the original prompt shows we wanted three OpenAI Agent SDK implementations: one with a web search tool, another with a function tool (a custom tool), and we wanted to explore the OpenAI real-time agent. This is a common pattern when prompting agents for rapid prototyping: have the agent build something simple, validate it, then build something more complex, validate that, and continue upward. Just like working with an engineer—whether junior, intern, or senior principal—it's far easier to start with a simple working implementation than to skip to potentially complex solutions.

Let's see how this worked. We have several files. Running UV run on our basic agent with web search—without even examining the code—and we need an OpenAI API key. Adding the export command, running again, and we're executing our agent with web search tool. There's the query: "What are the latest developments in AI agents 2025?" There's the result. Two total turns. The lineup looks decent—the top news announcement mentions Claude 4.5 Sonnet, which we can use as ground truth. This is working excellently. We have this web search tool inside the Agent SDK, and remember—out-of-loop on the dedicated agent device, a simple prompt requested: "Set this up for me. Teach me exactly how this works." The agents are doing precisely that.

Let's see how far our agents pushed. Did we achieve the real-time voice implementation? Copying the agent function tools example, running it—it has simple examples of tool use, like getting user info. This demonstrates how to set up OpenAI's Agent SDK with a custom tool.

The real-time implementation is what we really wanted to test. Running this reveals it's easily the most complex component. Processing events in real-time—there's more work needed here. Perhaps some simple string passing can be configured. Spinning up a quick Claude instance to set up audio implementation examples, we'll give this one shot. If it requires multiple prompts, we'll take it to the backend and continue development.

## The Philosophy: Building Systems That Build Systems

The crucial idea here is that with a single prompt, we can set up entire environments and have our agents execute within these environments. You saw it demonstrated: our agent fired off this job, and it went directly to the dedicated agent device running on an M4 Mac Mini. We received live updates in sixty-second intervals from when we initiated the task.

Pulling up the actual agent device log shows top-to-bottom everything that occurred: the GitHub URL that got mounted, all documentation processed, the arguments passed. A full log exists. What I want to emphasize is an advantage you can start building immediately for your engineering work, your team's work, your company's work.

You genuinely want a dedicated agent device that runs, builds, and executes engineering work on your behalf. You don't need to sit in-the-loop for every single task. Scrolling through the logs, we see the plan-build phases, and we see the ship agent that executed the actual git push. You can trace line by line, piece by piece inside the agent device. It completed work, generated output files, and the entire process is traceable and backed by a database.

We explore in tremendous detail how to build your dedicated agent device and how to work out-of-loop inside Tactical Agentic Coding. This represents my comprehensive approach to building with agents—scaling beyond AI coding and vibe coding into advanced engineering so powerful your codebase runs itself.

I know this is a simple example—just setting up some proofs of concept, passing in documentation—but I guarantee you can push this significantly further. I push this much further. I want you to have this massive advantage. Many engineers will miss this opportunity. At first glance, sitting in-the-loop with your agent feels productive—it feels like you're accomplishing substantial work. But once you realize you can set up better agents, more agents, and then custom agents, a different feeling emerges when prompting back and forth with a single agent: "Wow, I'm wasting time. How can I scale this up? How can I add more compute? How can I add more agents? How can I build a custom agent that does this better than any agent running in-the-loop?"

That's what Tactical Agentic Coding addresses—it's for engineers who ship.

## Tactical Agentic Coding: A New Paradigm

This course has been available for one week and already has hundreds of engineers enrolled. Tremendous appreciation to everyone who's taken Tactical Agentic Coding, extracted value, and started moving on this new system—which is more important to build than anything else. What if your codebase could ship itself? That's the central idea.

This isn't for everyone. This isn't for beginners. The fundamental concept is straightforward: we need to release old engineering methods and master the new best tool for engineering—agents. The paramount idea discussed throughout Tactical Agentic Coding is this: you want to build the system that builds the system.

What did we just accomplish in this relatively small microcosm example? We used a system that is simply active. We passed a prompt to it, and it performed arbitrary engineering work for us. To be absolutely clear: this codebase did not exist before running this prompt. This workflow created this codebase. I could have prompted anything—literally requested anything. This is a differentiating advantage for engineers.

We're discussing asymmetric returns on your engineering time. I wrote two prompts and then discussed what happened. Some engineers taking Tactical Agentic Coding are starting to build their new layer around their codebases. They're implementing the tactics. Your engineering output will be absolutely mind-boggling once you start using the tactics of agentic coding.

## The Core Principles

Several points deserve emphasis. This is about building the system that builds the system. It's about focusing on the agentic portion—the agentic system in your codebase—and letting that perform the building for you. To be perfectly clear: this starts with your reusable prompts. You saw this inside our Building Specialized Agents codebase—another excellent feature from Claude Code is backtick search. Searching for "AFK" finds our AFK prompt. Searching for "scout" locates the scout prompt we ran.

This prompt was a perfect example of building up incrementally, piece by piece—composing prompts. It's a perfect example that if you invest in the prompt and understand what you can accomplish with agentic prompts, you can have your system build your application. That's the fundamental idea.

We explore serious depth in Tactical Agentic Coding, discussing scaling the core four. We have the eight-lesson core covering the big ideas: Build the System That Builds the System. Then we have Agentic Horizon—mentioned several times—where you'll find elite context engineering, agentic prompt engineering, and the Building Specialized Agents codebase. This is an additional product available inside Tactical Agentic Coding.

Several deals are currently running. By the time you see this, it's probably down to nine or eight or fewer spots remaining. There are two deals: if you're a Principled AI Coding member, you have an additional deal. If you're not a Principled AI Coding member—and you'll know if you are—you're still eligible for the early bird special. If you're not a member, you will not have both discounts. Let me state that clearly and directly. There was some confusion in the previous video, so let me be completely upfront: there are no tricks, no gimmicks. I'm trying to provide great engineers who invest in themselves immediately when they see opportunity the chance to do exactly that.

## Conclusion: The Path Forward

Join this course. We discuss building with agents and scale far beyond the back-and-forth prompting that so many engineers believe is extraordinarily powerful. It is powerful—but it's just the beginning. It truly is just the beginning.

This has been a brief agentic coding session. I only ran two real prompts, plus a couple follow-up prompts for cleanup. I'm curious whether we'll achieve full completion with the real-time API. The starting point looks excellent—remember, my agent assembled this entirely. Two hundred, three hundred, five hundred lines of code to initiate this proof of concept. This appears to be a satisfactory starting point. Of course, an agent lacking audio capability probably wouldn't progress far on a task like this, so additional work will be necessary. But this is fantastic.

Check the links in the description to begin with Tactical Agentic Coding. Keep your focus on the most important tools. Don't get distracted by hype. Claude 4.5 Sonnet is demonstrably the best coding model in the world. Beyond that, inside Claude Code, it is the best agentic coding model—the best agentic model period. You can establish long chains, long workflows that execute end-to-end work on your behalf, on your device, and inside dedicated agent environments.

These are substantial ideas we'll continue exploring on the channel. Make sure you're subscribed and tuned in. We have everything we need to extract massive value from our agents. Now it's time to invest the work and build powerful systems that operate on our behalf.

Thanks for watching. I'll see you in the next one. Stay focused and keep building.
