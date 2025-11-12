# The Best Tool For The Job: Mastering Agent Interaction Patterns

## Introduction: Agents Are Already Here

If you're an engineer using the best tool for the job, you know this as fact: agents are not the future. They're already on our desks, in our repositories, woven into our workflows. It's clear that agents are already here. But here's what's not so clear—it's not obvious how to get the most out of them. 

Should you lean on prompts or MCP servers? How do you integrate them with existing APIs, command-line interfaces, or even other agents? The answer to this question can mean the difference between shipping in an hour or shipping in days. You've seen this. You know what you can do with the right context, model, prompt, and tools in the right agent.

That's why we're breaking down the top five agent interaction patterns so you know exactly when to use each pattern and how to turn your agents into your unfair advantage.

## The Agent Pattern Problem

Here's the setup. You're a skilled Gen AI engineer, but as your abilities have grown, you've taken on more responsibilities. The small, lean AI team narrative has taken hold in your company, and that means more responsibility. With responsibility, of course, comes opportunity. 

Right now, you're working on a big presentation. Everyone on your team is depending on you. You're almost finished, but there's one big missing piece: tons of high-quality images. You know that you're in the age of agents. Instead of using Sora, Midjourney, Gemini, or going through some image generation service, you've been learning that agents equal exponential leverage. You also know, of course, that Claude Code equals the best agent.

So you start designing a system. You'll use Claude Code to generate tons of images. You'll go through the Replicate MCP server or you'll hit the API directly—you're not sure yet. This is great because you have access to any image model you need. You'll even use the brand new image editing models for tweaks to get your images just right.

Then a massive problem hits you. Are you building a custom slash command or a Claude Code sub-agent or a custom MCP server that calls the Replicate API? Can't Claude Code just use the Replicate API directly? Is this just an ad hoc one-off prompt? Or maybe you should build a custom MCP wrapper server to hit the API directly, to hit other services you want to embed. Or maybe you should combine some of these approaches, right?

This is the agent pattern problem. You realize you have no idea what the optimal agent interaction pattern is. We have all these nodes, all these resources. We have more compute available to us than ever: agents, reusable prompts, sub-agents, MCP servers, existing APIs, command-line interfaces, applications. And of course, it's all about the outcome—for you, your users, your company, your customers. But how do we put it all together? 

We're making a bet here. We're betting that a majority of the economic value of AI will come from AI agents. If you believe this is true, we can start asking important questions. We can start asking the winning question: What's the best interaction pattern you can use to quickly scale your engineering impact with agents like Claude Code, Gemini, Cursor, and whatever big agent is coming next? What are the best interaction patterns?

## Pattern One: Iterative Human in the Loop

Let's talk about the top five agent interaction patterns with common agentic tooling. But let's start from zero with the first pattern. This is what we all do every single day: iterative human in the loop.

You have your agent that calls some service. Let's keep rolling with this image generation example. You're working on this presentation. Your team's depending on you to get this finished. You're going to integrate with the Replicate MCP server, and this will generate the outcome you're looking for. So this is the simplest version—iterative human in the loop. You're prompting back and forth with your agent, connecting to some service, to some MCP server, and this generates your outcomes. 

Every approach has pros and cons. The pros here: you have direct oversight. This is simple. You can quickly review, ensuring high accuracy and high control. On the con side, you are stuck in the loop. Human in the loop—you are quite literally stuck in the loop. The scalability here is terrible. You are, in fact, the bottleneck. 

So this is the low-hanging fruit. This is a great place to start. This is a terrible place to end.

## Pattern Two: Reusable Prompts

Let's scale this up. What tools do we have? What interaction patterns do we have with our agents to do more with less? We, of course, have reusable prompts. This is a big pattern. This is the 80/20 of agent interaction patterns. 

You have Gemini CLI and Claude Code. Unfortunately, as far as I can tell, Cursor CLI does not support reusable prompts. They need to build that in; otherwise, it is not a viable agentic coding tool—full stop. Because this enables you to reuse your agentic prompts. In the Claude world, it's `.claude/command/name.md`. If you've been watching the channel, you're very familiar with this. In the Gemini world, you use TOML files in a very similar pattern. These are just reusable prompts.

So this is an entirely separate interaction pattern. What we've done here is we've taken prompts and made them reusable. This is fantastic. This is where 80% of all the value is. If you want to be Pareto efficient, if you want maximum value for your time, you just build a reusable prompt. You write it once, reuse it all the time. Version control allows you to iterate and improve at light speed. 

Reusable prompts are very powerful. You're already aware of this pattern. This is where you should go right after you're sick of running this prompt yourself. You want to get out of the loop and move to reusability as soon as possible. Three times marks a pattern. If you need reusability, build a reusable prompt next.

Of course, we have initial overhead setup. You now need to manage these commands somewhere. You need to keep track of these. I'm working in five to ten code bases over the course of a week, and I lose track of which commands are where all the time. And this is an additional abstraction layer. It is thin, but it is there.

## Pattern Three: Sub-Agents

Let's scale it up. How can we interact? How can we have our agents do more? What's the next layer? We, of course, have the sub-agent pattern with Claude Code. No one else supports this right now, but with Claude Code as your primary agent, you can now spin up sub-agents. 

This is a great way for your agent to interact with outside services because now you can create dedicated, specialized agents. In our image example, we can use a "create image" agent that we can scale up. We can parallelize. We can generate twenty images in no time, or more, depending on what's in our sub-agent's system prompt. We can also spin up "edit image" agents. 

This is a great agent interaction pattern because it allows us to interact with these outside services in a more scaled, specialized way. Write once, reuse with Claude Code, parallelize, and specialize. These are the big advantages of the sub-agent interaction pattern. When you're thinking about having your agent interact with existing tools, services, and endpoints, sub-agents give you a massive edge because you can parallelize and specialize.

But there are cons here. The sub-agent pattern is not a free launch at all. You can isolate the context window. You can do a lot of cool things inside of your sub-agents, but there are problems. Right now, one of the biggest problems I keep my eye on all the time: Claude Code lock-in. A lot of these other patterns—if we back up to reusable prompts—this is not a super unique feature. Claude Code is definitely doing it the best, but Gemini CLI has reusable prompts too. No one's doing sub-agents right now. Claude Code is the best agent coding tool, full stop. We've talked about this on the channel over and over. But there is lock-in here—model lock-in and feature lock-in.

We then, of course, have the gray box problem. It's not a black box, but looking into your sub-agent, analyzing it, debugging it—it's not exactly simple. But most of all, and the biggest issue with the sub-agent pattern, is that you have to be really careful about how these prompts are coming into your sub-agents from your primary agent and how they're coming out of your sub-agent back to your primary agent. 

If you've been watching the channel, you know that your primary agent prompts your sub-agent, and then your sub-agent responds to your primary agent. We created a video on this very idea. That one absolutely exploded, and for good reason. You don't want to make the mistakes that a lot of engineers are going to make when they're building sub-agents. The flow of information in these multi-agent orchestration systems matters more than ever. 

This is another way you can scale up your compute. Notice how we're going from minimal to complex, from low compute to high compute.

## Pattern Four: Prompt to Sub-Agent

What's next? You can, of course, write a prompt that fires sub-agents. Going back to that image generation example, you need to generate a ton of images for your presentation. You want multiple versions so you can pick the best of n—you can pick the best images, the best ideas that your agents generate. 

Prompt to sub-agent is another way you can have your agents interact with outside services. Here you have Claude Code, you have your agent call a prompt, and this prompt contains a bunch of details. This is your workflow definition, which then calls an entire suite, an entire team of agents, to solve a specific workflow very well.

Here we are once again scaling up our compute. I'm just using the Replicate MCP server here as an example. Of course, not sponsored—I'm a third-party actor, no sponsors at all. This is an important example. This could be Replicate MCP. This could be your internal services. It could be other custom MCP servers. It can be APIs, command-line interfaces, anything. Think of this as just the external layer, and your agents are interacting with the external layer, and then you ultimately drive some outcome.

What are the pros here? This is, of course, great because we create workflow reusability as code—really, as prompts. The ability to create a reusable workflow that spawns specialized agents to do specific work is big. This is absolutely big. And our next agent interaction pattern, you can actually scale this even further. This is another huge value point. You can, in fact, pass in the number of agents you want to spin up. You could have three image generation agents spin up, and then you could have your edit agents review the image that was generated against the original prompt. And you can have them do that n times to improve the image, to make it more like you wanted in your original prompt. 

There are tons of ways to use the prompt to sub-agent pattern. The whole idea here is to create more reusability. Now you have an entire workflow with sub-agents. You have more compute.

Of course, speaking of compute, this is very token intensive. It's complex. It's hard to debug. You have agents doing work all over the place. Who knows if it's going to be right? This requires a lot of prompt engineering, a lot of context engineering, a lot of awareness of the problem that you're trying to solve and the compute that you can use along the way. The better and the more you know how your models work, the more successful you're going to be when building out these more complex workflows.

But we can scale this even further. What's the next version of this? We start getting into the deterministic land. We start combining code with agents.

## Pattern Five: Wrapper MCP Server

How do we do that? We build a wrapper MCP server. What does that look like? Claude Code, Gemini, Cursor—they're all calling your wrapper MCP server. It's not just reusable prompts or sub-agents. Those are all just prompts at the end of the day—system prompts or user prompts. What we're doing here is building out a dedicated wrapper MCP server that then calls the APIs directly. They call your custom APIs, your custom services, and so on and so forth. 

This is a dead giveaway for when you should use MCPs. Do you need specific functionality? Do you need to add deterministic code? Do you have proprietary services that you're trying to build? And do you need a concrete agent layer? And then, of course, this all drives our outcome.

There are tons of pros here. MCP servers are ultra-powerful, mostly because they create the interface layer. Really, that's what this is. What is the MCP server? It's an interface layer to give your agents the ability to solve the problem at hand with various services. 

To be super clear, of course, you can build out reusable prompts that just call multiple MCP servers, whatever tools you have—command-line tools can run bash commands directly. But when you want to start building out an encapsulated, reusable solution that serves a domain set of problems very well, the wrapper MCP server is the place to go.

Why is that? It's because you have a single integration point for all agents. Continuing with our image generation example, you'll now have "generate image" and "edit image" as tools and prompts inside of your dedicated wrapper MCP server. This is great because you get full control. It's controllable and it's customizable. 

A huge, huge, huge callout here—something that is still super underrated. I don't see enough engineers, I don't see enough MCP servers written out there with custom slash commands. Everyone's so focused on tools. Resources are decent, but the real value of the MCP server is in the prompts that represent the reusable workflow of specific tool calls. This is the big advantage of creating a dedicated wrapper MCP server. You get one place to call a set of tools, prompts, and resources that you define, and you get to expose just those pieces for your agent.

For example, going back to iterative human in the loop—you're just calling the Replicate MCP server. Now, you have to call the Replicate MCP server based on whatever tools they have defined, whatever prompts, whatever resources they have defined. You have to do it their way, or your agents have to do it their way. You have to understand their tools and their prompts. 

When you build out your MCP server, you get to do it your way. When you build your MCP server, you can create a "generate image" tool, and then you can create a reusable prompt—a custom slash command inside your MCP server—that is "generate prompt batch" or "generate then improve" or something like "generate in this style," "generate in Ghibli style." You can define exactly what things look like. Highly customizable and controllable.

Of course, there are cons. You have to maintain this MCP server. And if you're not embedding an agent inside of your MCP server—which is another advanced pattern we'll talk about in just a moment—you have to build these integrations by hand. Now you need to grok the Replicate MCP server. And by hand, I of course mean you have to have your agent do it, and you have to know what to prompt and what to instruct your agent to do. You basically have to build these integrations by hand. You have to integrate with the services' APIs the exact way you want it. This, of course, is a good thing. You're being more specific and explicit with what you want done. But there is still a cost to that. Control costs time. Control costs effort. Control costs your engineering resources.

This is, of course, built for agents, not humans. This is an MCP server. It's not a UI. It's not a command-line interface. It's not an API. It's an MCP server. This is built for agents.

## Pattern Six: Full Application

That leads us to the highest level: the application pattern. If you need the big guns, this is where you end up. You end up basically creating a super interface layer. You end up with a super interface layer here where you have an entire application layer. You have your own command-line interface, MCP server, user interface, API—just whatever you want. This is a full-on application. 

Of course, here you get full control over what this calls. You can just do anything. It's a full-on application. Now, the trick here is that in order to make this useful for your agents, in order for your agents to run your application and to do things with your application, you either need to expose some specific command-line interface methods, you can expose an MCP server for your application—this is a big, big idea we're going to be discussing on the channel, so make sure you're subscribed—and then, of course, you have your UI and your API. 

Your agent can operate on all of these dimensions to call specialized sub-agents and application code and really anything under the sun. When you get to this level, you're basically going full-out, guns blazing.

The pros and cons are exactly what you would imagine: full control, infinitely extensible, multiple access patterns, multiple access layers—command-line interface, MCP, UI, API. But of course, the cost is just through the roof. To go back to our image generation example, you need to build a presentation, you need to generate image assets. This is extreme overkill for that use case.

## The Decision-Making Framework

That brings us to our decision-making framework. How do we choose between all of these levels? How much compute do you really need to solve the problem at hand? I think this is a great place to bring back a fundamental engineering principle: keep it simple, scale when needed. 

Basically, solve the problem first. And if you can't solve it with that level of operation, with that much compute, with the simple mechanism, with the simple agent interaction pattern, then you scale it up. Scale when needed.

Everything should start with an ad hoc prompt. This is your first encounter. When do you use this? When you're encountering a new problem—for an image generation problem where you're building out this presentation, you need a ton of images. We're talking ten, fifty, hundreds of images generated very quickly. You don't want to go through the UI. And in fact, more and more, you want to be doing things the agentic way. Let your agents do it. Find the interface and build the interface for your agent. Why? Because your agent can use more compute. And if you're using compute, you're doing more digital work. 

We're in the age of agents, not the age of large language models, not the age of prompts, not the age of chats. It's all about the agent right now. But you still want to start at the lowest level. And this is also helpful. There's that saying: do things that don't scale. This is important so that you understand how to actually solve the problem yourself with your agent.

### When to Use Reusable Prompts

Then we get to reusable prompts. You want to tap into this when you've spotted a pattern. I like the rule of three. Once you've done something three times as an engineer, automate it. Stop doing it. Stop wasting time. Three times marks a pattern. Codify it. Create a custom command—aka a reusable prompt.

### When to Use Sub-Agents

What about sub-agents? I've come to a concrete answer here for when you should use sub-agents. Only use sub-agents when you need specialization and parallelization. If you don't need to parallelize and you don't need to specialize, just create a reusable prompt. Keep it in your primary agent, because as soon as you start messing with sub-agents, you now have to manage multiple context windows. Even if you don't think you do, there is another context model prompt that you need to manage. 

You want to do the least amount to get the greatest value. This is all about finding that sweet spot. Understanding your agent interaction patterns is how you decide where that sweet spot is for the problem you're trying to solve. You want to keep it simple, scale when needed.

Let's go back to our image generation example. We definitely don't want to stay at ad hoc prompts because we need to generate ten, fifty, hundreds of images, and we might need to edit them. Already we're talking about repetition and we're talking about specialization. So we're talking about reusable prompts or sub-agents. We could stop at two, we could stop at three. Do we need four or five?

### When to Use MCP Servers

What is four? Four is the MCP wrapper. I am combining prompt workflows that call sub-agents—that's still all just the sub-agent pattern. MCP servers—when do you use this? You need to expose your agent to services. Calling a command-line tool is not good enough. If hitting an API with curl is not good enough, if you need to be more specific, then you build an MCP server. Also, if you're starting to increase the number of services you're interacting with, you probably don't want to be managing all that in a reusable prompt or in sub-agents. You probably want something that pulls it all together and then re-exposes it through a simple tool or prompt via your MCP server.

And I am talking about MCP server tools and MCP server prompts. Prompts are insanely underrated, insanely underused. If you're building an MCP server, you should build MCP prompts that expose the common workflows you will use with the tools. Or, of course, if you have some unique asset, some unique internal service that you want your agents to be exposed to.

So this is when you upgrade to an MCP server wrapper. Now the question is: do you need to upgrade from a sub-agent or from reusable prompts up to MCP servers? I think the answer here is unless you know you need to integrate with some personal information for this presentation—you have some types of personal sales assets, maybe for this client you have some information on them, or maybe you're bringing these images for multiple presentations, each for a different client that you're working with or working for—then you might want to create an MCP wrapper that puts together the Replicate image functionality with your internal services, and then you expose it through a single or a set of "generate image" tool calls and prompts. 

I think that's the big differentiation here. Only if you need to integrate with multiple services, multiple assets, would you upgrade from sub-agents and reusable prompts to the MCP server.

### When to Use Full Applications

Then, of course, we have the final level: the full application. Complete integration. You have full control, and you have a long-term vision. Basically, you're building a product. If you're building an image generation product, or if you see an opportunity here to solve this problem for good in your organization, for your team, then you would build a full application.

Why is that really the full application now? It's just a way to expose many ways to do something. What do I mean by many ways? I'm talking about the interface layer. What's the difference between a customer-facing application and a developer tool? It's the interface layer. If we want to move fast, if we want to get something done, we go through the terminal. But if a customer wants to do something, it's all UI that hits an API. 

So if you need full control, if you need multiple interface layers, and you have a long-term vision for a solution for generating tons of images and editing them with a big UI, you want the full application.

## Key Principles

Now, it's important to note that throughout each level of the agent interaction pattern, you are increasing compute, you're increasing complexity, and you're increasing the time you need to spend to deliver the solution. Very obviously, the time it takes to create a reusable prompt is much less than the time it takes to create an MCP wrapper or full application. Even if you have complete meta-prompts for these problems—which if you've been watching the channel, you probably have meta-prompts for one, two, and three—stay tuned for four and five.

This is a simple pattern decision-making framework that we can use to figure out when we need what level of compute, what level of solution for a specific problem. You want to move from left to right. The big idea here is start simple. Don't make the classic engineering mistake. Don't over-engineer. Let the patterns emerge naturally from usage. 

If you skip step one and two, there are going to be things that you don't know about the problem, and therefore that you don't know about the solution, because you didn't do it by hand. And I should be really clear when I say "by hand" now, because I think that engineering ability is kind of all over the place right now. There's a huge gap, a growing gap. When I say by hand, I mean with your agent. By hand should almost always mean you're having a high-composition-level agent do the work on your behalf. That's what I mean by hand.

I really like this line: complexity should be earned, not assumed. Don't assume your problem is hard. You should never assume that your problem is hard. You're actually causing yourself pain by assuming that you need more compute or a bigger interface layer or more interface layers or a complete solution. Complexity should be earned, not assumed.

There's also a great idea embedded here: larger working systems are almost always built from simple working systems. If you start here at level one, you can generate images through the Replicate MCP server, through whatever server you want, by hand with your agent, prompting back and forth. You know that the solution can be done. Right after you do this a couple of times, you can immediately throw it in a reusable prompt because you've solved the problem. You know the steps you need to go through. 

For instance, for the Replicate MCP server, you need to get the model name. You need to know the model name. You need to know your provider. Then you actually make the prediction, and then you effectively poll back to the API to wait for the image to generate, and then you download it, and then you move it. Generating an image is almost a workflow in itself—almost a reusable prompt.

Then we can push it further. We can go for the sub-agent pattern. Why would we do that? Because we need specialization, and more specifically, we need scale. We need parallel execution. Now, you can definitely accomplish this with a reusable prompt as well. You can say in your prompt, "generate n images." But you can also do this with the sub-agent pattern. 

For this specific problem of generating images for a presentation, I would stop at two. If I didn't have a lot of time, I would go to three if I knew I needed to generate a hundred-plus images. And I would even put the reusable prompt that generates n agents as a sub-agent. I would call five of my sub-agents. I'd say, "Generate ten images each. Here are five different prompts for the images." Then five sub-agents would do that work, and you can build out specialized edit image agents as well.

I would only go to MCP if I needed to involve other services, or if I wanted this to be a repeat solution with a simple interface. I want a "create image" interface. I'll embed which model to use. I'll embed the aspect ratio—details. Then you only go to a full application if you have some long-term vision or you need to expose this tool to your team. By your team, I mean to your non-engineering team.

## The Core Philosophy

The ideas are simple: solve the immediate problem, recognize repeat patterns, scale incrementally. What you don't want to do is premature optimization. Don't build before you validate. Don't go for complex solutions first. If you don't need the compute, if you don't need the interfaces, don't build them. 

Being an engineer is all about solving the problem. I feel like this has gotten lost somewhere. Being an engineer is all about solving the problem. Gen AI gives us brand-new technology to solve the problem better than ever. But we're now faced with this really interesting problem of how do we have our agent interact with new and existing systems—command-line interfaces, applications, APIs, and now the new MCP server prompts, sub-agents, and whatever's coming next?

I think this general framework is how I've been thinking about this: keep it simple, scale when needed, and always go from left to right, never right to left.

Right now, I'm building a ton of reusable prompts. I'm building fewer sub-agents than I was before, unless I need specialization and parallelization. Then every once in a while, I do build out a dedicated MCP server, usually to pull together multiple services or expose repeat functionality. And then, of course, I have a couple of applications that I'm building out to solve problems—full-on, full-scale applications where you have a long-term vision for.

For instance, I have every single layer here built into Agentic Engineer. This is where I host principal AI coding and, of course, the next Phase 2 Agentic Coding course.

## Conclusion

We are in the age of agents, and all the winning engineers are mastering the agent architecture and agent interaction patterns. No matter what, stay focused and keep building. The key is understanding which pattern fits your problem, starting simple, and scaling only when the complexity has been earned through actual need rather than assumed from the start.

Remember: larger working systems are almost always built from simple working systems. Start at level one, validate your approach, then scale intelligently through the levels as your needs genuinely require it. This is the path to building powerful, maintainable agent systems that deliver real value without unnecessary complexity.
