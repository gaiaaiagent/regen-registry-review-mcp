# Levels of Context Engineering: A Guide to High-Performance Agent Development

## Introduction: The Power of Focus

A focused engineer is a performant engineer, and a focused agent is a performant agent. Context engineering is the name of the game for high-value engineering in the age of agents. How good are your context engineering skills? Do you have a skill issue? Let's find out and fix it.

There are three levels of context engineering and a fourth hidden level if you're on the bleeding edge, pushing into agentic engineering. But first, we must ask: why are context engineering techniques so important?

Context engineering enables you to manage the precious and delicate resource that is the context window of your agents—tools like Claude Code. There are only two ways to manage your context window: **R and D**. Let's break down each technique at each level and use the R&D framework to maximize not what you can do, but what your agents can do for you.

## The R&D Framework: Reduce and Delegate

When you boil it down, there are only two ways to manage your context window: **R and D—reduce and delegate**. Every technique we'll explore fits into one or both of these buckets. Let's start at the beginner level and move up to more technical levels of context engineering.

## Beginner Level

### Technique 1: Avoid Unnecessary MCP Servers

Do not load MCP servers unless you need them. Consider how much of your Claude Code Opus tokens are being consumed by MCP tools—sometimes as much as 24,000 tokens, which is 12% of the entire available context window. It's very likely you're wasting tokens with MCP servers you're not actively using. This is a simple, easy, beginner context engineering mistake to make.

Thankfully, the solution is simple: be very purposeful with your MCP servers. We often have a bad practice of context engineering inside our codebases—a default `MCP.json` file that is always loading into the context window of our agents, chewing up expensive, valuable Claude Opus tokens. These numbers stack up against you very quickly.

The first thing I recommend doing is getting rid of your default `MCP.json`. Just completely delete it. Don't use a default `MCP.json` for your codebase. This immediately clears up your context window. If you type `claude context` now, you've just saved some 20,000 tokens by not preloading any MCP servers.

If you do need these servers, I recommend you fire them up by hand using `claude --mcp-config`. Pass in the config you want—you can have specialized files that pull in just the specific MCP server you need. If you have some globals that you want to overwrite, you can use the strict MCP config flag and fire it off.

Check your context with `slash context`—you'll only get those specific tokens strictly from the MCP server you've chosen. Now you can kick off a specialized agent focused on just that one MCP server. If you do need every single MCP server, explicitly reference it. Be very conscious with the state going into your context window.

There are many places to be wasteful as an engineer to move fast and break things. The context window of your agents is not one of them. Here we are, of course, using the **R** in the R&D framework: we are reducing.

### Technique 2: Context Priming Over Claude.md

This technique is a bit controversial, especially for beginners, but I strongly recommend context priming over using a `claude.md` or any similar auto-loading memory file. What is context priming, and why is it superior to `claude.md`?

Let's first examine `claude.md`. There's nothing inherently wrong with this file. Like most technology, it's how it's used that's the problem. When you boot up a new instance, you might see an error message warning you about file size. Many teams have built up massive `claude.md` files—sometimes 23,000 tokens, consuming about 10% of the entire context window of expensive Opus tokens.

I'm exaggerating my `claude.md` file here to showcase this idea, but I can almost guarantee there's an engineer out there with a `claude.md` file that is 3,000 lines long. Why? Because they and their team have constantly added additional items to their memory over and over again until it's become a massive glob of mess. Even the Claude Code engineers built in a warning: "Large claude.md will impact performance."

The `claude.md` file is incredible for one reason: it's a reusable memory file that's always loaded into your agent's context window. Simultaneously, it's terrible for the exact same reason: it's a reusable memory file that's always loaded into your agent's context window.

The problem with always-on context is that it's not dynamic or controllable. Engineering work inside codebases constantly changes, but the `claude.md` file only grows. So what's the solution? **Context priming**.

Trim down your `claude.md` to something minimal—perhaps 43 lines of things you always want every single agent to have. I have to keep stressing this because this is the reality of the memory file: it will always be added. Now your context window on boot-up looks much better—92% free, with your small memory file down to 0.2%, about 350 tokens. This is great. This is a clearly focused agent.

Now, what do we use instead of the large memory file? We context prime. Type `/prime` and hit enter. **Context priming is when you use a dedicated reusable prompt—a custom slash command—to set up your agent's initial context window specifically for the task type at hand.**

With every codebase, I always set up Claude commands for priming. Priming is just a reusable prompt with a concise structure: we have the purpose, our run step, our read step, and our report step. Now our agent is ready to go—it's read a couple files, understands the structure of the codebase, and has information for this specific problem set.

Instead of relying on a static, always-loaded memory file, we're using context priming to gain full control over the initial context of our agents. This is very powerful. Unlike the memory file, we can prime against several different areas of focus in our codebase. Imagine a `/prime-bug` command for bug smashing, `/prime-chore`, `/prime-feature`, or specialized prompts like `/prime-cc` for operating with Claude Code files.

**Prime, don't default.** Your `claude.md` file should be shrunk to contain only the absolute universal essentials that you're 100% sure you want loaded 100% of the time. See how powerful and strict that conditional is? Be very careful with these memory files. Keep them slim and instead prefer context priming. This way you can build out many areas of focus for your agents, and if you find yourself coming back to a specific area, build out a prime command for that focus—for you and your team.

This is the beginning of a big agentic-level technique that we'll discuss later in this lesson. You can see we have a new experts directory that we'll explore at the end.

## Intermediate Level

### Technique 3: Use Sub-Agents Properly

Now we enter the intermediate zone. It's not just about using sub-agents—it's about using sub-agents properly. When you use Claude Code sub-agents, you're effectively creating a partially forked context window.

If you type `context` in a brand new agent, you'll notice something really interesting: you have custom agents available that only consume perhaps 122 tokens, whereas a single detailed agent might consume 900 tokens. What's the big difference?

The big difference is that when you're working with sub-agents, you're working with **system prompts**. There's a massive difference between system prompts and user prompts. When you're prompting Claude Code directly, you're writing user prompts. When you're building reusable custom commands, you're writing a user prompt that gets passed into the agent. But sub-agents use system prompts, which means they're not directly added to our primary agent's context window.

This advantage of sub-agents continues: with Claude sub-agents, we can delegate work off our primary agent's context window. This is a massive point for the **D** in the R&D framework—delegation. We are keeping contexts out of our primary agent's context window.

For example, you can run `/load-ai-docs`, which loads AI documentation and kicks off sub-agents to do this work for you. Your primary agent reads the file and spawns however many agents are needed to fetch every AI doc URL. A web scrape can consume quite a bit of tokens—perhaps 3,000 tokens per agent times 8 or 10 agents—but this isn't added to our primary agent. This is **sub-agent delegation**: we're leveraging the context windows of our sub-agents to do work and keep it out of our primary agent.

This is a great use case for sub-agents. You have a system prompt that details exactly how to web scrape with tools like Firecrawl or web fetch. These agents run the scrape, consuming their context window, then write the output files. You can use a classic agentic prompt workflow format with purpose, variables, workflow, and report format sections.

All those tokens are not added to your primary agent's context window. We delegated work—we're stepping into the **D** in the R&D framework. There are only two ways to manage your context window: reduce context entering your primary agent and delegate context to sub-agents.

Claude Code sub-agents have limitations. They sit at the intermediate level for a reason: instead of keeping track of just one set of context, model, prompt, and tools, we now have to keep track of as many sub-agents as you spawn. It becomes super important to isolate the work your sub-agents are doing into one concise prompt, one focused effort. Remember: a focused agent is a performant agent.

Sub-agents are also trickier because of the flow of information. Your primary agent is prompting your sub-agents, and your sub-agents are responding not to you but back to your primary agent. Once we start getting into this intermediate and advanced agentic level, we have to keep track of every agent's core four that we spin up.

If you're losing track of a single agent and have a bunch of wasted context, you probably aren't yet ready for sub-agents. You probably want to spend more time cleaning up, managing, and maintaining clean context windows for your existing single primary agent. But once you're ready, sub-agents are a great intermediate technique because you can delegate the entire context window to one or more sub-agents. As we saw, we saved probably 40,000 total tokens and ran all this work much faster than it would have taken a single primary agent.

## Advanced Level

### Technique 4: Use Context Bundles

Notice that with each technique—from beginner to intermediate to advanced and soon agentic—we're doing our R&D: reduce and delegate. We're keeping track of our context window at all times, and we're not outsourcing it. If you want to scale your agents, monitoring and managing the state of your context window is critical for your success.

Just like context priming, you can push in-loop active context management even further with **context bundles**. With Claude Code hooks, you can hook into tool calls to create a trail of work that you can use to reprime your agents for the next run. You can chain together agents after the context window has exploded.

The great part is we've been using context bundles the entire time. Inside your agents directory—which is becoming an additional agentic layer directory for output from your agent operations—you have a context bundles folder. If you click into a bundle, you might see something super simple: `/prime` and `read` commands.

This is powerful: a context bundle is a simple append-only log of the work that your Claude Code instances are doing. These are unique based on the day, hour, and session ID. When you run a prime command, a context bundle is generated. Every read command, every search command gets appended piece by piece. This gives you a solid understanding of 60 to 70% of what your previous agents have done.

Why is this important? It tells a fuller story for subsequent agents to execute. You're getting a full context bundle of your agent's context window. This is a very simple yet powerful idea you can use to remount instances to get them into the exact same state after their context window has exploded. It also gives you a story—the prompt operation explains what the context is and why, based on your user prompt.

Let's say an agent's context window exploded. With a context bundle, you can run `/load-bundle`, copy the path, paste it, and hit enter. This agent now gets the full story of the previous agent. It will deduplicate any read commands and create an understanding of the work done up to this point.

Imagine a context bundle with 50+ lines of reads and writes. We can use it to get a much more accurate replay of what the previous agent was trying to do. The summary message very concisely tells you: the previous agent executed this command and loaded these key findings. You can imagine this getting more complicated with reads, writes, and additional prompts.

With this simple pattern—with session IDs tracked inside context bundles—we're saving a concise execution log thanks to Claude Code hooks that we can reference in subsequent agents. The great part is you can conditionally use this. Often you won't need to reload the entire context bundle because it won't be relevant. But if needed, you can get the entire replay of the agent up to the point the context overloaded, without all the writes and without all the details of all the reads.

The trimmed-down version is super important—we're not recording every operation. If we did that, we'd just end up overflowing the next agent's context window. You do have to use this selectively, but this gets you 70% of where the previous agent was and mounts you and restarts you very quickly. This is another advanced context engineering technique you can use.

## Agentic Level

### Technique 5: Primary Multi-Agent Delegation

The focus should always be: better agents or more agents. When you're adding more agents, you're pushing into the **D**—delegation—in the R&D framework. You're pushing it to the max. You're using one agent for one purpose, and when something goes wrong, you fix that piece of your workflow.

With primary multi-agent delegation, we're entering the realm of multi-agent systems. In advanced courses, each lesson builds up variants of a multi-agent pipeline using this very technique. There are many ways to delegate work at a high level, but when you want to create an on-the-fly primary agent, you have two options: the CLI and SDKs. At the mid and high level, we can kick off primary agents through prompts, through wrapper CLIs, through MCP servers, and through UIs.

You've likely seen cloud code management systems and agent systems built up into their own UIs. That is primary agent delegation. What's the most lightweight version of multi-agent delegation you can use right away and get value from immediately? It's a simple reusable custom command.

In your Claude directory, in your commands directory, you might have `background.md`—a simple single prompt that boots up a background Claude Code instance. This is the simplest, quickest way, other than going right through the CLI, to delegate work to agents. When you use a pattern like this, we're pushing into powerful out-of-loop agent decoding by running a single prompt with a single agent that does one thing, reports its work, and then finishes.

Let me show you exactly what I mean. Run Claude Opus in YOLO mode and type `/background`. This fires off a full Claude Code instance in the background. You can kick off the creation of a plan. There's no reason to sit in the loop prompting back and forth when you can kick off a background agent—when you can delegate this work outside your primary agent's context window.

You can open quotes, paste in your prompt, and kick off a new quick plan. This runs that plan agentic prompt, building out something like an Astro UV Claude Code Python SDK with your specified format. This kicks off a background agent based on the contents of your prompt. You can see a consistent prompt format where you're reusing great prompt structures that get work done.

Inside the workflow step, you create the agents background directory, have your default values, and—importantly—create a report file. Then you have this primary agent delegation XML wrapper detailing information for your agent. You're kicking off a Claude Code instance from Claude Code. You have compute orchestrating compute, agents orchestrating agents. This is where everything is headed: better agents and then more agents. Once you master a single context window, you can scale it up.

The important thing here is that this frees up the primary Claude Code instance. You have a background task running. Your agent will report to its designated file, and you can open up a context bundle for this agent to see its work trail. Having this trail—the story of what your agents have done—is an important agentic pattern.

We are building up on every context engineering technique we've used thus far. This agent reports back to its report file, which is a great way to track the progress of your agents as they work in the background. When the task completes, the file gets renamed—a very quick one-prompt agent delegation system.

It's all about the patterns. It's all about taking control of your agent's context windows and scaling to the moon. The more compute you can control, the more compute you can orchestrate, the more intelligence you can orchestrate, the more you will be able to do. The limits on what an engineer can do right now are absolutely unknown. Anyone being pessimistic? Ignore them. Don't even take my word for it—investigate the optimists in the space. See what they can really do. See what we're really doing here.

We have background compute, agents calling agents. We have the R&D framework, twelve context engineering techniques. These are concrete things. Maybe a couple of these techniques fly over your head, or you're not interested, or you think they don't apply to you. That's fine. Just take one, take a couple of these, and improve your context engineering.

The background agent task and multi-agent delegation is super important because it gets you out of the loop. This is a big idea: get out of the loop. Set up many focused agents that do one thing extraordinarily well. In many ways, multi-agent delegation is just like sub-agents, but we get complete control—we're firing off top-level primary agents from our in-loop primary agent.

There's a lot more control here. This background agent and the prompt you pass in could ask for anything. This doesn't need to be a quick plan. You could ask for a multi-agent workflow running sub-agents. There are so many ways to build and use multi-agent systems.

Let's bring it all back to context engineering. The key idea is: you can delegate specialized work to focused agents by building out some type of primary agent delegation workflow. In just one prompt, we have a full Claude Code instance in the background doing work that we know we don't need to monitor anymore. The more you become comfortable and the more your agentic engineering skill improves, the more you can stop babysitting every single agent instance. This is a big theme: we want to scale from in-loop to out-of-loop to fully autonomous.

## Conclusion: Prepare Your Agents for the Future

Let's wrap up with potentially one of the most powerful context engineering techniques: **agent experts**.

Take these twelve techniques and apply them. Get value out of these techniques. Yes, it takes some time. Yes, you have to invest. This is not vibe coding. If it's easy, a vibe coder is probably doing it, and that isn't irreplaceable—that is replaceable work.

Even one of these techniques can save you massive time. But you have twelve here. Pick one. Pick a couple. Dive into them. Deploy them into your agent coding to improve your context engineering. Managing your context window is the name of the game for effective agent coding.

Remember: it's not necessarily about saving tokens. It's about spending them properly. We manage our context window so we don't waste time and tokens correcting our agent's mistakes. We want one-shot, out-of-loop agent decoding in a massive streak with the fewest attempts and large sizes, so we can drop our presence.

We use specialized agents. We delegate and reduce the context window of our agents by building specialized workflows that ship on our behalf. We build specialized agent pipelines. The big idea here is simple: measure and manage one of the most obviously critical leverage points of agent coding—your agent's context window.

What's better than a prompt? A prompt chain. What's better than a prompt chain? An agent. What's better than an agent? Many focused, specialized agents that deliver value for you, for your team, and most importantly, for your customers and users.

Don't miss this trend. You now have everything you need to win and ship with focused, single-purpose agents. All of these techniques are us battling with the fact that there are key scaling laws and algorithms inside these language models, inside generative AI, that decrease performance as context windows grow.

What does that mean? It means you can safely bet on spending your engineering time, energy, and resources on investing in great context management—in great context engineering. It's a safe bet to bet on context engineering.

There is a lot to digest. This lesson will be here for you. Thank you for trusting me. Keep in mind: **a focused agent is a performant agent**.
