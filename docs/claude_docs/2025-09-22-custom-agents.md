# The Path to Custom Agents: A Journey Through Agentic Engineering

## The Natural Progression of Engineering with Agents

Agentic engineering leads every engineer down one single path: better agents, more agents, and then custom agents. If you can prompt engineer and context engineer a single agent successfully, then the next step is to add more agents. Scale your compute to scale your impact. Then once you learn to delegate work to sub-agents and new primary agents, there's only one place left to go: custom agents.

### The Limitation of Out-of-the-Box Solutions

But why isn't Claude Code, Cursor CLI, or the Gemini CLI enough? The out-of-the-box agents are incredible, but there's a massive problem with these tools: they're built for everyone's codebase, not yours. This mismatch can cost you hundreds of hours and millions of tokens, scaling as your codebase grows.

This lesson is about flipping that equation. Here we master custom agents so your compute works for your domain, your problems, your edge cases. This is where all the alpha is in engineering—it's in the hard, specific problems that most engineers and most agents can't solve out of the box.

In this advanced lesson, we showcase eight unique custom agents built on the Claude Code SDK. Each one shows you how to deploy across your stack, products, and engineering lifecycle. The agents are on the horizon. It's time to master agents by going all the way to the bare metal, to the custom agent, so you can scale your compute far beyond the rest.

## The Pong Agent: Understanding System Prompts

In the building specialized agents codebase, inside of apps, you can see eight custom agents. Let's start simple with the Pong Agent.

### The Most Important Lesson

Here is a simple agent that's going to showcase the most important aspect of custom agents. We have a simple, concise user prompt and agent response, along with some session stats. When we run this agent, something curious happens. No matter what we prompt—"hello," "summarize this codebase," "can you do anything other than pong?"—the response is always the same: pong.

This silly agent encapsulates the most important concept when you're building custom agents. No matter what we prompt, the response is always pong. Why is that?

### The Power of the System Prompt

The first and most important concept is none other than the system prompt. We are using the Claude Code SDK and we're setting up only two things. We're modifying just two aspects of this agent, but it changes everything.

When we examine the dedicated load system prompt method and open the path to the prompt, we see that we have completely overwritten the Claude Code system prompt with the title of our agent purpose. We have a simple three-line instruction: "You are a pong agent. Always respond exactly with pong." That's it.

**The system prompt is the most important element of your custom agents, with zero exceptions.** We are modifying the core prompt specifically. But now we have two very important prompts to pay attention to: system prompts and user prompts. The system prompt affects every single user prompt the agent runs. Every single one. So all of your work is multiplied by your system prompt.

### How the Claude Code SDK Works

The SDK works like this: you set up your options, you set up your agent, you run the query, and then you handle the response. The Claude Code SDK is a powerful tool for putting together agents, as you'll see as we progress. All the pieces are there and they're incrementally adoptable.

The simple 150-line Pong Agent demonstrates this clearly. Most of the code is just logging. We're setting up the agent, querying the agent, and handling the response of the agent. Take note of these specific blocks that you can report: agent message blocks and result messages. You can parse specific information out of these as you'll see as we progress.

This showcases the power of the system prompt. Remember all that work that the Claude Code team has put into making a great agent? The Claude Code agent that you know and love is now gone. You have to be very careful with the system prompt. We now have a new product. This is not Claude Code anymore. It might be using the same model, but the system prompt is truly what builds the agent.

Of course, we are still using the tools. That's important to call out here, as you'll see as we progress into more and more capable custom agents.

## The Echo Agent: Adding Custom Tools

Inside of our Echo Agent, you can see a similar structure. We have a single Python script that we're going to execute. But here we have something different: a custom tool. Our agent says "I'll use this tool," and then we have the tool call block, followed by the response of the tool call and our agent response.

### The Core Four Elements

These are all unique elements coming out of our agent. You want to be keeping track of these. Keep track of the Core Four: user prompts, system prompts, tool definitions, and agent responses. If you understand the Core Four and how each element flows and controls your agent, you will understand compute and you'll understand how to scale your compute.

Let's echo ourselves. When we ask it to "echo this string and then I want it in reverse in uppercase, repeat two times," we're just playing with the tool that our custom agent has. The agent correctly processes the request, calling the tool in reverse, transforming the text "custom agents are powerful," repeating it and converting to uppercase. We're scaling up a little more, adding a few more capabilities to our agent as we explore custom agents.

### Building Custom Tools

When we examine the Echo Agent structure, we always love collapsing everything so you can quickly understand what's going on. We have main, we have a tool, and we have our system prompt. Always look for the system prompt and then look for the custom tools.

Something special happens here. We can search for Claude Code options. We have an MCP server built in this script—create SDK MCP server—and we're passing in a single tool. This builds an entire MCP server in memory for our agent. This is super powerful.

Tools for your Claude Code SDK are built like this: a decorator, then the name, then the description. Keep in mind the description of your tool tells your agent how to use it, in addition to the actual parameters that get passed into your tool and the actual arguments. You just pass in a dict and then you do whatever you want to do inside of your tool. Here we step back into traditional deterministic code. It's a tool call. Do whatever you want, but be sure to respond in the proper format.

This is a custom agent with a custom tool set. Something interesting here as well: you can see we are running Claude Haiku. We have downgraded our model to a cheaper, less intelligent, but much faster model. This is a simple agent. It doesn't need powerful intelligence, so we've dropped down the model.

### Continuous Conversations

As we progress through each agent, keep in mind we have the twelve leverage points of agent coding that we're paying attention to. But whenever you see Claude Code options, isolate the Core Four. How will the Core Four be managed given this setup?

We have something else here that's important to call out. We're using the Claude SDK client class instead of our Pong Agent where we were just using that query command. Query is for one-off prompts, and the Claude SDK client is for continuous conversations.

When we run the agent with a follow-up prompt—"concisely summarize our conversation in bullet points"—our agent quickly responds because it has kept track of the conversation. We're using the Claude SDK client, and because we've written multiple query calls, we have both the original user prompt and the follow-up prompt. We have both the tool use block that we care about and we have the text block. You can stream all the messages coming back out from your agent after you query and just take them in, do whatever you want with them.

### Understanding Tool Context

Here's something interesting that if you're using these agents left and right, you probably haven't been paying attention to. If we run this same agent and ask it to "list your available tools," we are actually still running a lot of the Claude Code baked-in tool set. These are all the Claude Code tools plus our tool. Everything that's going into your agent winds up in the context window at some point.

We have fifteen extra tools, fifteen extra options that our agent has to choose from and select to do the job we've asked it. Now, our Echo Agent does not need any of these tools. As we progress, we're going to fine-tune, we're going to get more control over our agent. If you ever run the context commander, understand what's going into your agent. You know that these fifteen tools consume context. It consumes space in your agent's mind. We're going to learn how to control that knob in our next agent.

The last thing we want to point out here is our Echo system prompt. Very simple. Again, it's important to call out this is not the Claude Code product anymore. As soon as you touch the system prompt and once you start dialing into the tools, you change the product, you change the agent. The title, purpose, Echo Agent—"use the tool when asked." There's not a lot of happening here, but there is a lot that was happening that isn't happening anymore. We have blown away the Claude Code system prompt. We have completely overwritten it.

Now, it is important to mention you can append system prompts. You can just add on to what's already there. This is also powerful. This is more of a way to extend Claude Code versus overwrite it and build a true custom agent.

## Micro SDLC Agents: Multi-Agent Orchestration

Now we arrive at custom micro SDLC agents. Let's understand the structure of this codebase: backend, frontend, reviews, specs, and a couple of test files.

### The Agent Task Board

We have an agent-by-agent task board where we hand off work from one agent to another agent in a kind of micro software development lifecycle. You can see we have a couple tasks already shipped, some errored ones over here. Let's create a new task.

We're going to do something really simple to showcase the workflow and showcase the capabilities that you can build into your user interfaces with agents. The task: "Update titles. Update the HTML title and header title to be plan, build, review, and ship agents."

### Multi-Agent Workflow

We have that task now. We drag it into plan, and the workflow kicks off. The difference here is we have a multi-agent system. We're not just deploying a single agent anymore. We're deploying multiple agents inside of our UI.

Now we have a planner agent. It's noticing, it's thinking. We have planner thinking, planner tool calls, hook interceptions—tool allowed. We have a permission system inside of this. It has the full structure, and now it's going to start updating this code. It's a simple title change, not rocket science, but we should see our title update, and we should see our HTML title update as well. It is operating on itself.

A couple cool things: you can build out your own multi-agent orchestration system however you want. We have the messages on the left, the total messages getting streamed to the frontend via WebSockets. Then we have the total tool calls on the right.

Our agent is working. You can see the planning is incrementing. But you can see here our builder agent is now processing. This is really cool. The planner is done. You'll notice the UI is going to be a little glitchy here because it is updating on itself, actively starting and restarting the server and the client. But that's fine. Our WebSocket should pick this up and continue processing.

There you can see the spec. We're operating on that plan, we're operating in the review now. We can see that we're in the review step. A very cool way to see how agents can work together, and then you package it in a nice UI. Then you can do more than you ever could before, frankly. We have a dedicated workflow working step by step by step: plan, build, review, and handing it off to the next stage in the process.

You can see here our reviewer agent, all of its tools, and you can see it just operating, doing work for us. We're using a lot of the out-of-the-box Claude Code tools. If you don't need to reinvent the wheel, don't do it. Let's be super clear about this: the Claude Code SDK running the base Claude Code agent is incredible. We've been using it since Claude Code was released.

We just moved to shipped. Update titles. And you can see what happened: "Plan, Build, Review, and Ship Agents." Both titles updated. This work shipped with a single prompt outside the loop. This is a perfect example of an out-loop review system using the Peter TAC and the Agentic Path framework.

### The TAC Framework

We dialed into this a ton inside of TAC. If you haven't finished the TAC lessons, you should probably stop watching this video immediately and finish TAC. It's all about transitioning from in-loop to out-loop to eventually ZTE (zero-touch engineering).

## The Path Forward: Deploying Compute at Scale

The agent is compute scaled. You want to know how to deploy this across your tools, products, services—for yourself, for your engineering work, and for your users and customers. The Claude Code SDK and other agent SDKs are all powerful toolkits you can use to control the Core Four within your agents to scale them intelligently.

### When to Use Custom Agents

If you're doing one-size-fits-all work, use the out-of-the-box agent. Don't think super hard about this. Just deploy compute to get the job done. But as your work becomes more specialized, as you deploy agents across all aspects of your engineering, you first want better agents, more agents, and then custom agents.

This is a codebase you're going to want to think deeply about and understand how you can extend and use the ideas we've discussed here. Deploying effective compute and deploying effective agents is all about finding the constraints in your personal workflow and in your products.

Think about repeat workflows that can benefit from an agent inside of a script, a data stream, an interactive terminal, all the way up to user interfaces that can tackle high return on investment problems in your tools, for your team, and for your business.

## Conclusion: Teaching Agents to Work for You

Agent coding is not so much about what we can do anymore. It's about what we can teach our agents to do. This is how we push our compute to its useful limits. Follow this path to unlock massive value for your tools and products: better agents, more agents, and then custom agents.

I'll see you in the next Agentic Horizon extended lesson.
