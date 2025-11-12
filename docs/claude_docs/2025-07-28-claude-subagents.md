# Ship More with Sub-Agents: Mastering Claude Code's Multi-Agent Architecture

## Introduction: The Promise of Automation

Welcome back, engineers. Imagine starting your day by opening the terminal, firing up Claude Code, and kicking off a single prompt that accomplishes in minutes what used to take hours. This is the power of Claude Code sub-agents—workflows of specialized agents that do one thing and do it extraordinarily well.

You can even create a meta-agent, where your agents build your agents. Code is a commodity, but your fine-tuned prompts hold real value. Your Claude Code sub-agents can yield extreme value for your engineering—if you know how to avoid the two biggest mistakes engineers are making.

In this guide, we'll break down how to build effective Claude Code sub-agents, use a powerful meta-agent to build new agents, and understand the serious trade-offs and pitfalls you need to know about so you don't waste your engineering time and tokens. Let's take our agentic coding to the next level.

## Understanding Claude Code Sub-Agents

### What Sub-Agents Really Are

Sub-agents probably don't work the way you think they work. The flow of Claude Code agents operates end-to-end like this: it starts with your prompt, your primary agent then prompts your sub-agents, your sub-agents do their work autonomously, and—this is critical—they report back to your primary agent, which then reports back to you.

The flow of information is absolutely critical. You prompt your primary agent, and then your primary agent prompts individual sub-agents based on your original prompt. Your sub-agents respond not to you, but to your primary agent. Many engineers miss this fact, and it fundamentally changes the way you write your sub-agent prompts.

### Anatomy of a Sub-Agent

Inside a Claude Code codebase, sub-agents live in the new agents directory. Let's start simple and understand what sub-agent prompts look like.

When you fire up Claude in yellow mode and say "hi Claude" or "hi CC" or "hi Claude Code," the agent immediately finds the matching description and kicks it off. You'll see your agent name (its unique ID), the description (which is very important), and the tools it can access. You'll also see which sub-agent completed its work and the color associated with it.

The format includes something really important, bringing us to the first big mistake engineers make.

## The Two Big Mistakes

### Mistake #1: Misunderstanding System Prompts

When you open up a sub-agent prompt, you'll see a classic markdown format with sections like "Purpose" and "Report." The first mistake engineers make is not understanding that what you're writing here is the **system prompt** of your sub-agent—not the user prompt for your agent. This is a critical distinction.

It might not seem like an important detail, but it changes the way you write the prompt and what information is available. This is the system prompt, the top-level functionality definition. When you write something like `/prime` in your prime command, that runs as a user prompt directly into your primary agent's context window. The agents directory is very different—these are system prompts.

### Mistake #2: Forgetting Who Responds to Whom

The even bigger mistake: notice that your sub-agents are responding to your primary agent, not to you. This report and response format is critically important. You're explicitly having the sub-agent communicate to the primary agent, saying "Claude, respond to the user with this message."

You don't prompt your sub-agents directly. You can write a prompt for your primary agent to prompt your sub-agents, but you're communicating with your primary Claude Code agent—the top-level agent we'll call the primary agent. It's Claude Code that prompts your sub-agents. It is delegating.

You want to think about your Claude Code sub-agents as tools of delegation for your primary agent. This is why the Big Three is so important: **Context, Model, and Prompt**—and specifically, the flow of context, model, and prompt between different agents. This becomes increasingly important as we scale up to multi-agent systems.

If you make these mistakes, things will eventually go awry, especially as you start scaling up with chains of sub-agents.

## Chaining Sub-Agent Workflows

You can chain the calls and responses—prompt chaining years ago, and we're still prompt chaining now, just with bigger compositional units. You, the user, prompt the primary agent. They can then run tasks, and based on the results, they come back into the primary agent, which can keep cooking, doing important work for you. You can fire off another set of sub-agents.

This is the true flow: your sub-agents respond to your primary agent. When you're doing powerful multi-agent orchestration, you need to understand this deeply. Read the documentation thoroughly. This is the most important technology of the year, probably over the next few years. Agents are how you win as an engineer.

Don't offload all the cognitive work to your agents. Understand the most important technology. There's nothing more important right now than agents, and the leading agent is Claude Code. Every engineer has a superpower—they're cracked at something. One key ability is focusing on the signal and canceling out the noise, constantly obsessed and passionate about finding where the valuable information is.

Copy documentation, use LLMs, but don't offload deep understanding—you're basically just vibe coding then. Deeply understand your tools so you can do more, better, faster, and cheaper.

### Information Flow in Multi-Agent Systems

If you want to scale up, you need to understand the information flow. We're not just prompting a chat interface anymore. We're not dealing with one context-model-prompt agent system. We're dealing with multi-agent systems, and there's a reason to focus on multi-agent observability.

Multi-agent systems are here. The best engineers, the most cracked seniors, are scaling up hard: compute, compute, compute, compute.

Here's a simple flow: you prompt your agent, it fires sub-agents, collects results. The next step in that custom command might be: collect the results, fire off more sub-agents that create a concrete solution. This is all fantastic.

## The Meta-Agent: Building Agents That Build Agents

### A Real Problem, A Real Solution

Let's use a meta-agent to solve a real problem. What's the problem? When multi-agent coding at scale, I lose track of what some agents have done.

**Problem statement:** Losing track of completed agent work.

**Solution:** Add text-to-speech to agents so they notify me when they're done and, more importantly, what they've done.

**Technology:** Use Claude Code sub-agents with a meta-agent to build a new text-to-speech agent that communicates what was done.

Order matters: **Problem → Solution → Technology**. Only after you have a problem and solution should you move to the technology. A big issue in the engineering space and Gen AI ecosystem is engineers using technology to create solutions for problems that don't exist. Noobs and beginners start with the technology and work backward. If you want to become a real engineer, work the other way—the way product builders think.

### Setting Up the Workflow

Inside `mcp.json.sample`, we have a setup for the ElevenLabs MCP server, configured with environment variables. First, understand what your agent can do by running "all tools"—a simple reusable prompt that lists all available tools in bullet points with TypeScript function signature format.

We need two things: text-to-speech and a way to play audio. Search for the text-to-speech method and the play audio method. We want the entire definition so we know the exact parameters we're working with.

Now run these in the primary agent's context window, including the voice ID and output directory. Have Claude Code Opus fire off this tool, validating the workflow before encoding it into an agent. Once text-to-speech is working and we have full capability to have our agents communicate with us via a sub-agent, we can move forward.

### Creating the Agent with Meta-Prompt

Now that we know the workflow and the work we want done, we can build a new agent that encapsulates this work. The meta-agent has a system prompt that details how to create a new agent, doing all this work in an isolated context window.

Build a new sub-agent: "Generate a new complete Claude Code sub-agent configuration file from a user's description." Use the information-dense keyword "proactively" encoded by Anthropic. When a user asks you to create a new sub-agent, we want to make sure we have that language inside our prompt.

Detail exactly the flow: get the current working directory, text-to-speech, play. Copy this and fire it off. You'll see the description of the meta-agent get activated. This is very important—you need your description to properly set up when your agent should call a specific sub-agent.

The prompt doesn't just build on zero information—it pulls the Claude Code documentation live. There's a more powerful way to do this: inside AI docs, place a README and then on the fly have a prompt or sub-agent pull in live documentation with some type of refresh command.

### Refining the Agent Description

Through tool uses, the meta-agent successfully creates the new agent and reads to verify—the reasoning model is double-checking the work. The agent exists in the exact format requested.

Always review. Every word must add value. No pleasantries. Add variables like username. Make the concise one-sentence description precise.

Make tweaks specifically to the description, which determines when your primary agent calls your sub-agent. Claude Code has the IDK (information-dense keyword) that they mention: "use proactively" or "must be used." Add concrete tags or triggers: "If they say TTS, TTS summary, use this agent."

Review the user prompt and provide a concise summary of what it does. Coming full circle, remember that your primary agent prompts your sub-agent. What your primary agent can see and has access to is this description—this is how it knows when to call any given sub-agent. You really want to leverage the description and tell your top-level agent how to prompt this agent.

When you prompt this agent, describe exactly what you want them to communicate to the user. Add more detail: "Remember, this agent has no context of any questions or conversations between you and the user."

To increase prompt adherence, Anthropic has another information-dense keyword: **"IMPORTANT:"** Be absolutely clear with this agent. Do these following things: provide a concise summary of what was done. Add best practices: "IMPORTANT: Run only bash pwd and the ElevenLabs MCP tools. Don't use any other tools."

### Testing the Complete System

After adding details about when this should be called, after adding instructions to the system prompt for the work completion summary sub-agent, we now have an operational agent that can quickly summarize in natural language for us anywhere, anytime on any piece of work.

This is the beauty of agents and reusable prompts. Now we have this problem solved for good and can reuse it and improve it when needed. The codebase gets analyzed, text-to-speech is generated, and we receive a structured response: "This codebase demonstrates Claude Code hooks mastery with all six lifecycle events implemented for deterministic control, featuring security filtering, intelligent TTS feedback, automatic JSON logging, and UV single-file architecture."

Thanks to Claude Code hooks, we're recording all the conversation. You can dive in and see your top-level agent prompting your sub-agent and your sub-agent prompting the response back to your top-level agent.

## Sub-Agent Benefits

### Context Preservation

Each sub-agent operates in its own context, preventing pollution of the main conversation. This is powerful. We're booting up fresh agent instances for every task—text-to-speech, meta-agent work. They all have their own isolated context window. You can use this to scale agents across large complex codebases. You could already do this with sub-agents, but now you can do it even better with specialized sub-agents.

Saving your context window is a big idea that will keep coming up until we get those 5 million-plus context windows (which aren't coming anytime soon, though I'd love to be wrong).

### Specialized Agent Expertise

You can fine-tune the instructions and tools for each agent. You can see this in the text-to-speech agent—we wrote a rich description on not only when to trigger this, but we're giving our top-level agent instructions on how to prompt it. Many engineers are going to miss this. Don't be one of them. You can instruct exactly how you want the prompt to flow in the description.

### Reusability

By storing agents inside your repository, you can build agents for your codebase. There's a powerful way to use a meta-agent to build specialized localized agents that excel at operating specific parts of your large codebase.

### Flexible Permissions

You can lock down the tools your agent can call. If you're in YOLO mode, you have to be more explicit about what tools can run, which is why we add best practices specifications.

### Hidden Benefits

**Focused agents:** Just like booting up a fresh agent with a single prompt, when you use Claude Code sub-agents, the agent is fresh. It only knows what your primary agent tells it. That means it's less likely to make mistakes given that you design a good system prompt. Why? Because your agent is focused on one thing. Just like a focused engineer, when you're focused on one thing, you perform better. Full stop.

**Simple multi-agent orchestration:** By stacking powerful features—custom slash commands combined with Claude Code hooks combined with sub-agents—you can build powerful yet simple multi-agent systems.

As a concrete example, you can improve the classic prime command with `prime-tts`. Say you want to kick off prime—you can say "when you finish, run the TTS summary agent to let the user know you're ready to build." Chain the text-to-speech summary agent at the end. We're able to guide our primary agent's prompt to our sub-agent.

### Prompt Delegation

You're delegating your prompts to the primary agent, just like in the work completion summary agent description. This means you have to do a little more work guiding your primary agent to call your sub-agent properly. This is powerful, though. We're offloading work, encoding powerful engineering practices into our prompts and now into our sub-agents.

## Sub-Agent Challenges and Trade-offs

### Context Limitations

The opposite of context preservation is that every sub-agent having its own context means there is no context history. It doesn't have the rich context that your primary agent has. It has only what your primary agent prompts it with.

This is the equivalent of firing up Claude in a fresh mode and passing in one prompt. This is what your primary agent is doing when calling sub-agents—it's literally like calling a one-shot prompt to the sub-agent. There's no context. This is both a problem and a benefit, the opposite side of the coin of context preservation.

### Debugging Difficulty

These sub-agents are hard to debug. Every time we run one of these, even with simple prompts, we have no idea what's going on in detail. We get the tool calls, which is nice, but the actual workflows, the prompts, the full parameters for every tool call—we don't get these. This is by design, but it also makes them harder to debug and understand.

### Decision Overload

As you start scaling up the number of agents you have, it's going to be harder and harder for your agent to know which one to call. Commands are a bit different—you the engineer might forget all the commands you've built, all the powerful commands. Agents are different because based on the description and the number of agents you have, your primary agent might get confused.

This is important. You really want to keep track of your agents. Otherwise, it'll come back to bite you, kicking off agents when you don't want to. As a solution, be clear about when to call your sub-agents with the description variable. This is the most important variable right next to the name.

### Dependency Coupling

Once you start setting up prompts, primary agents, reusable prompts or custom slash commands, and once these are calling your sub-agents—this is how you start scaling up into multi-agent systems—it's going to be hard to understand what's going on. You're going to have dependency coupling.

Inevitably, you're going to have an agent depend on output from another agent, depend on the format of the specific response from another agent, on and on. Then one day, you're going to need to change something to improve it or ship something new. You're going to change the planner agent, and it's going to ruin everything else because one thing changed.

We're already operating in non-deterministic systems. When that one thing changes, it could blow up everything else. As you start scaling them up, keep your eye on this. Try to keep them separate. Try to keep them in isolated workflows. Don't overload your sub-agent chain.

### No Nested Sub-Agents

You cannot call sub-agents within your sub-agents—probably for all the reasons just mentioned. It would be cool if we had a "dangerous sub-agent: true" setting, or "sub-sub-agent: true," so that inside an agent we could enable this dangerous powerful setting of calling sub-agents inside sub-agents. That's not actually a real issue, but it's important to note you can't call sub-agents in your sub-agents—at least not yet.

## Conclusion: Principles for Multi-Agent Mastery

This is a very powerful feature. We have quite a few more ideas to explore with the combination of agents and custom slash commands (reusable prompts).

Remember that **perspective matters** as you start scaling up your multi-agent system. The flow of the Big Three—**Context, Model, and Prompt**—matters more and more as you scale up the number of agents shipping work on your behalf.

There's a reason why it's a principle of AI coding. The meta-agent will be available with the Claude Code hooks mastery codebase. No matter what, stay focused and keep building.

---

*This transcript has been cleaned up and structured from a technical tutorial video by Indie Dev Dan on Claude Code sub-agents.*
