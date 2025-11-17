# Claude Code Pro Tips: Asymmetric Engineering in the Generative AI Age

## Introduction: Systems That Build Systems

What's up, Engineers! Indy Dev Dan here.

In this exploration of Claude Code, I'll share six pro tips that will help you achieve asymmetric engineering in the generative AI age. But the deeper theme behind these techniques is this: tools like Claude Code, MCP, and AI coding assistants enable you to build systems that build systems for you. This is the advantage you and I have as engineers.

Vibe coding is the lowest hanging fruit. System building enables you to reuse the value you create over and over and over. With this lens, let me share my top six Claude Code tips for agentic coding that you can use to accelerate your engineering in the Gen AI age.

## The Foundation: Shipping in the Shadows

The Claude Code team is shipping in the shadows. Let's cover some of their new releases and explore techniques you can use to ship faster than ever.

## Tip One: Context Priming

Let's open up Cursor and fire off Claude. You can see I have five MCP servers—we're going to cover a few of those in this video. But first, what is context priming, and how can it help you use Claude Code in a more efficient, effective way?

When you first start up Claude, it's effectively an empty agent. It doesn't see what you see. It can't see your codebase. It doesn't know what you know. It's basically a blank page—a blank agent. We need to let it know what you're working on.

I've started adding this inside all of my READMEs. If we open up the README and search for "context priming," you can see I have this simple prompt. Let's copy this and paste it into Claude and fire it off. This is going to let Claude read the essential files of the codebase and then run `git ls-files` to understand the codebase.

You can see here the Claude Code engineers have implemented a couple of new awesome features. We're doing parallel reads with this cool sub-agent call tool. All these items are now getting added to Claude Code's context window at application startup. You can see here it's giving us a nice summary, but most importantly, it now has this information inside of its context window.

If we type `/cost`, you can see—of course, this is not a cheap tool. You're going to have to pay to play with Claude Code. But you can see we've done some operations already. We have 40 cents worth of work that is now context—active memory for Claude Code.

This lets you set up your AI coding assistant to win right away by downloading the essential elements of your codebase. I highly recommend you add something like this to your README so that you can get started quickly when you have to reset your Claude Code instances, especially when you're nearing that 200K context token window limit.

As you'll see in a moment when we run an AI coding prompt, this small tweak speeds up your work quite a bit. If we run `git ls-files`, we can now see a general structure of the codebase. I also like to run `tree` sometimes and pass that into Claude.

As you can see here, we are operating in the single file agents codebase—something we've worked on on the channel. All the work we're doing here is going to be available to you (link in the description). We're using UV to build out these powerful single file agents. We're going to look at these in just a moment.

## Tip Two: Context Is King

This is not new. If you've been working in the AI coding space and working with language models, you always want to be feeding Claude Code and your AI coding tools the context they need to get the job done.

If we type `/mcp` here, you can see I have five MCP servers in this current project. The winning engineers in the Gen AI age will always be thinking from the perspective of their AI agents: What can they see? If someone were to prompt me with this context and this tool, would I be able to accomplish the task?

Having the right tools and the right MCP servers gives your Claude Code instances what they need to succeed.

### Collectors and Executors

I think of MCP servers and tools in two classes: we have **collectors** and we have **executors**. First, you collect context with your collectors, and then you execute CRUD operations—you update files, you update databases, you operate on information. You have collectors and you have executors.

Right now, I have two primary tools for collection. I use the out-of-the-box fetch tool right from the Anthropic servers, and I also use Firecrawl MCP. Firecrawl is a simple tool—I'm not sponsored by them or anything, but they are my recommendation if you want to scrape and crawl single websites, extract key information, or traverse multiple pages. They also help you get around some of the SSR and server rendering issues and blocking that tools like fetch are limited by.

### The New File Editor Agent

Let's go ahead and take a look at the new file editor agent using Sonnet 3.7. This is really cool—a new simple file editing agent that can edit files using the brand new text editor for 3.7 Sonnet specifically. This is a brand new text editor tool that enables you to build agents that can edit files precisely. This is a massively important tool for agents.

This is a great example of an executor tool. We have this brand new tool inside of this agent. I can just copy this—we're using UV single file scripts. I'll open up a new terminal instance here and just say: summarize into a new `readme-summary.md`.

This is a simple file editing agent. It can read and write. Let's go ahead and full screen this. You can see we're calling the view tool here—it read the README, it has those 20 lines, and now it's written that file. With three agent loops (really just two), it read a file, created a file, and then reported the results. You can see the token output here.

Now we should be able to open up this new README summary, and you can see we have exactly that—a nice concise summary of what's been done. This is all built on top of Anthropic's brand new text editing tool built specifically for 3.7 Sonnet. Anthropic realizes how important file editing is for building out—you guessed it—effective agents.

### Token-Efficient Tool Use

There's a new additional feature that I want to add to this agent. Anthropic has also shipped this brand new token-efficient tool use beta flag. Let's go ahead and pull this content and add this to our existing agent.

This is a single page, so it's really simple. Normally you could just copy this, but I want to show off how important it is to have these tools embedded in Claude Code. Let's say we needed a couple of pages of documentation. What I'll do here is copy this, open up a new file, paste that there, and then copy this URL as well.

Then I'll write a prompt right in this file: "Fetch, combine, and then do this." I'm going to copy this, and we have our fetch tool inside of Claude Code MCP, so now we can just paste and let this fire off. This is going to run fetch on both of these and create a new markdown document.

We've talked about this in previous videos, but I want to highlight this one more time: it's super important to think of your tools as collectors and executors. You can see here we have Claude Code's new parallel run subtask—it just ran both of those at the same time. It's now looping through the actual content and going to create a new file.

Let's go ahead and look at our AI docs. You can see we have several docs in here already, and this is going to create a new markdown document for us with this content collected automatically. Fantastic!

We're going to go into YOLO mode—we want Claude Code operating in its full agentic form. We'll hit yes, and you can see this new document added here. It has both the tool use docs and the efficient tool use combined. This is great. Now that we have collected the context for this, we can go ahead and write a follow-up AI coding prompt to update our existing single file agent file editor with the new Sonnet 3.7 file editing tool, and we can have it update to actually use the new flag.

Let me go ahead and collapse everything so you can see what we have here. You can see all the file editing tools, and we can go ahead and update this to use the new flag. I'm going to use my file reference hotkey (for me it's Command+Shift+R—I highly recommend you set this). I'm going to paste that in and then say: "Update via --efficiency flag."

We're going to kick that off. To be super clear, we don't need to reread this file because it is in fact already in the context window—Claude just wrote that, so it has it in its context window. You always want to be thinking from your agent's perspective.

You can see it's running the read tool here to create a Flask API with three endpoints with the efficiency token flag. We're also passing in the thinking tokens and max compute loops. There we go—there's the code coming in with the `--efficiency` flag. That looks great.

## Tips Three and Four: Release Notes and Thinking Mode

Let me give you tip three and four together. We're going to have Claude Code review and actually execute this code. We've already covered that in previous videos—we're closing the loop, letting our AI coding tools get the feedback they need by actually executing the command.

### Tip Three: Release Notes

But there are a couple of key commands inside of Claude that you should be aware of. If we type `/release`, you can see that there are release notes now. That's tip three. It might seem simple, but the Claude Code engineers are really shipping in the shadows here, and you want to be keeping track of everything they're releasing.

If we hit enter here, I want to point out something really cool that was just released. You can ask Claude to make a plan with thinking mode. Obviously they're tapping into Claude's hybrid base reasoning model capabilities. If you say "think," "think harder," or "ultra think," you will tap into these.

### Tip Four: Thinking Mode

That's tip number four. Let's go ahead and use that tip. We just set up this brand new efficiency flag by pulling in this context using an MCP server. I'm going to update this prompt just a little bit: "Create a Flask API with three endpoints inside of agent workspace."

It's going to run in efficiency mode, and we're also going to have thinking tokens. What I want to do here is create two versions—I want this to run without efficiency and with efficiency so that we can actually see the difference.

I'm not going to run this—there's no reason for me to do this. I'm going to hand this work off to Claude Code. I'm going to hand this work off to my AI coding tools. I'm going to copy this and combine this with a think mode.

Here's what I'll do: I'll move over to our temporary file, paste this command in, and say: "Test out the token-efficient exactly the following command without `--efficiency` and then with." We're getting some great autocompletions from Cursor. Then I want to say: "Record. Think hard in the review process."

I'm going to paste this into Claude Code and fire this off. Now it's going to actually run the agent itself, keep track of the results, and then run both in efficiency mode and without efficiency mode.

After working through some errors and adjustments, you can see Claude Code is giving us a nice analysis. Without token efficiency we got 6K tokens, and with it we got 5.7K—so not a major saving, but not too bad either. Looks like we got a 5.7% reduction. The big savings (which is honestly where you want to have the savings) is in the output tokens, because the output tokens are priced at $15 per million. This is really good—we want to be saving on the output tokens.

This is an example of how several tips and techniques can come together. Context is king—you want to be paying attention to what your AI coding assistant can see, what's actively inside its context window. We also looked at `/release`, which tells you what the Claude Code engineers are cooking up. This is super important. We also then tapped into Claude's thinking tokens—Claude 3.7 reasoning capabilities. This is super powerful.

We've now updated our agent. If I search for `--efficiency`, we can see we have that brand new efficiency flag that enables—you can see here if we use token efficiency, we then add this new cool beta flag. That looks great. It did save us some 5-6% of tokens that will definitely add up over time.

## Tip Five: MCP Server Prompts

If I type `/` and hit down a couple of times, you're going to see something pretty cool. If I scroll to the bottom, you'll see I have a couple of prompts. A couple of my MCP servers have built-in prompts that I can just run.

You can see fetch has the obvious one that you would think. If I hit enter here, it's going to set up Claude Code to have that URL that I can pass in. The key thing I want to show off here is not the fetch tool again—it's the fact that you can use these slash commands to quickly activate one of the prompts.

If we look at the Model Context Protocol servers and go into fetch again, we can see that there's this prompt. This is really cool—I think this is a pretty underused element of MCP servers. You can create predefined prompts where you have your MCP host pass in specific variables. A simple example here is just fetch. We type `/fetch` and this is a prompt that we now have access to.

If we also look, there's another one here for SQLite. Let's hop into something a little bit newer. You can see there's a prompt here that provides a demonstration of how to use SQLite with MCP. If we clear this out and I type `mcp`, you can see that we do have our SQLite MCP, and then I can type `/sql`. You can see here that exact command.

This is a prompt that we can fill in with variables. You can see the argument there is "topic." If I hit enter here with "sales," now it's going to send back to the SQLite MCP server that we have installed, and it's going to start setting up some data. If we scroll up here, it's going to kind of walk through this scenario, walk through this setup. The whole point here is that MCP servers allow you to tap into these different prompts, and that can be pretty powerful.

## Tip Six: Adding MCP Servers via JSON

One more tip I want to give you here is the fact that you can add Claude MCP servers very quickly with JSON format. Let's go ahead and close this Claude instance. You can see we spent $3 there.

Let me go ahead and run `claude mcp list` just as an example. Let me get rid of fetch so we can say `claude mcp remove fetch`. This will remove that, and if we clear and run `mcp list`, we'll see that we no longer have the fetch command there.

If we hop back into Claude (I have an alias for Claude—just `cld`, saving a couple keystrokes), and do `/mcp`, you can see our connected MCP servers. If we hop back into the release notes, you'll see that we can add MCP servers as JSON string. This is a simple but very useful way to get up and running with MCP servers inside of Claude Code.

If I just copy this, open up a new file, paste this in—let's get fetch reinstalled. The name for this is going to be `fetch-mcp`, and then all we need now is JSON. How do we set the JSON for this?

If we open up fetch server again, let's just go back here and scroll down to the `uvx`. We have this command here, so we can go ahead and just copy this, paste this, and then we need to just clean this up a little bit. All we need is the content inside of the actual object. We don't need `mcpServers` (this is for your Claude desktop), and we also don't need this kind of starting key-value, so we can get rid of that, get rid of the trailing brace, and then we can just use this. This is valid JSON.

We can then take this and paste it here. What I like to do here is run something like this: `echo "$PBPASTE"`. This will take whatever is on our clipboard and just use that. We can close Claude Code here, paste this value, copy whatever JSON we want to use, hit enter here, and this is going to add that brand new fetch MCP server just as we defined.

Now if I type `claude mcp list`, you're going to see that right here: `fetch-mcp`. Then we can run Claude, and you can see here we found five MCP servers. If I go ahead and type `/mcp`, you're going to see that new fetch MCP server up and running.

You can quickly add MCP servers into Claude Code using JSON format. They also added this `claude mcp add` step-by-step wizard that you can also use. If we clear and run this, you can see that they have a setup command there that you can use to step-by-step walk through adding a new MCP server.

Obviously I like the JSON approach—it's a little bit faster if you know what you're doing. But equally as good, you can just come in here and name them whatever you want, set up the project scope (these are all command line flags), and then path to server and so on and so forth. This is a nice way to walk through the process.

## The Future of Agentic Coding

I think the Claude Code team is really executing here. They're creating a lot of value inside of this tool. It's super important to note, as mentioned in our previous video, Claude Code is seeing massive mass adoption. This tool is really paving the way for the next phase of engineering.

We started with doing everything by hand, typing code manually. We moved to copilots. We then started iteratively writing prompts and using AI coding tools. The next big phase is agentic coding, and at the forefront—really, the poster child for this—is Claude Code, specifically with 3.7 Sonnet. It's a breakthrough tool that's allowing new capabilities for agentic coding.

When you combine it with MCP, you can now equip your AI coding assistant, your agentic coding tool, with all of the capabilities it needs to run not just programming tasks, but to run tools that allow you to collect and execute across various domains.

## Conclusion: Building Systems That Build Systems

As engineers, it's ultra important to take advantage of these tools and focus on building systems that build systems for us. Where we're going on the channel (and a place I highly recommend you spend some time investing) is looking at what agents you can build to multiply your productivity, to help you scale up what you can do. Agents allow you to scale your impact even further.

Remember that Claude Code itself is just an agent. It's an agent for engineering. It's an agent for the terminal. It's the agent for engineering.

A big focus on the channel is going to be building out agents for various use cases and understanding agent design and agent architecture at a fundamental level. If that interests you, join the journey. Make sure you're subscribed. This is how we scale our impact and consume more compute to work on our behalf.

We're barely scratching the surface of what we can do with agents. This is our unique advantage. Do not underestimate this. It's time to start gathering your suite of tools—both collection and execution tools—so that you can continue to scale up what you can do with incredible AI coding tools like Claude Code.

These are just five of several MCP servers that I'm looking at and playing with. Comment down below—let me know what MCP servers are your favorites. A lot of this will depend on the tools and the tooling that you use to engineer. You might be using Postgres, you might be in Docker a lot, so you'll be using the Docker tools. Comment down below, let me know what you're using, let me know what your favorite tools are.

If you made it this far into the video, drop the like, subscribe, join the journey. The key here is to focus on building systems that help you build systems.

Stay focused and keep building.
