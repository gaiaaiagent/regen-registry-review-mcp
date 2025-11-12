# Mastering Agent Skills in Claude Code: A Guide to Composition and Modularity

## The Expanding Toolkit

For the past week, I've been working through agent skill issues in Claude Code. Now we have agent skills, sub agents, custom slash commands, output styles, plugins, hooks, memory files, and MCP servers. What is this all for?

I've been using Claude Code since it was first available in February. Since its release, I've generated more code than in my previous 15 years as an engineer. This tool has changed engineering, but this once-simple tool has grown complex over the year. Let's simplify it.

Skills are simple, but they're so similar to MCP, sub agents, and custom slash commands that it's hard to know when to use a skill. There's a right way to think about skills, and there's a wrong way. I want to show you both to make it absolutely clear what this feature can do for your engineering. Skills are powerful, but you should not always build a skill.

## The Wrong Approach: Three Ways to Solve One Problem

Let's first look at the wrong way to use skills to solve an engineering problem. Here we have a skill on the left, a sub agent in the middle, and a custom command on the right. If you're doing parallel agent coding, generating multiple solutions at the same time, you've likely created git work trees. 

Here's a question for you: which one of these three ways is the right way to create or manage your git work trees? To answer this, we need to understand how these features really differ.

### Comparing Core Capabilities

On the top, we have four key features we're going to compare side by side. On the left, we have capabilities. Let's start with the three most important.

**Agent-Triggered Execution**: Skills stand out here right away because they're triggered by your agents. If you give your agents some direction, they will trigger the right skill. Sub agents are very similar in this way, unlike slash commands where you are explicitly kicking this off.

**Context Efficiency**: This is a huge selling point of skills. Unlike MCP servers which explode your context window on bootup, skills are very context efficient. This is something that the Claude Code team talks about extensively, and I think it's super important. I'm glad they're going into detail. There are three levels of progressive disclosure: the metadata level, the actual instructions of your skill.md file, and then all of the resources that your agent pulls in from your skill when it needs them.

**Context Persistence**: The only loser here is sub agents. But of course, this is what makes sub agents great—they isolate and protect your context window. Shareability is not that important; you can use git, you can use plugins, you can share these.

When we test our work trees, we see results: "Your red tree work tree is live on ports 4020 and 5193, ready for parallel development." Sub agents are the big winner if you're looking to parallelize your workflows. "I've successfully created and started your yellow tree work tree on ports 4010 and it's running now." So we have our red tree, blue tree, yellow tree—fantastic.

**Specializability and Modularity**: You would think that specializability is unique to skills, but it's not. You can specialize any one of these features, and of course, you can share all of these any way you want. What is important is modularity. This truly differentiates skills.

Skills are just like MCP servers in that you have a dedicated solution. They're even more modular than MCP servers, frankly, because skills have a dedicated directory structure. If we look at this skill "create-worktree-skill," the most important thing is that we have a dedicated structure for building out repeat solutions that our agent can invoke. That is the primary benefit of skills. The modularity here is really important—it is high. Unlike sub agents and slash commands where you kind of had to roll this capability out yourself, which we have done in previous videos.

**Composition**: Things get interesting at the last level where we start thinking about composition. This is where I think a lot of the confusion comes when we talk about skills, MCP servers, sub agents, and slash commands. Specifically, skills and slash commands are very composable. In fact, you can circularly compose all of these items together minus sub agents, because a sub agent cannot use a sub agent. But when it comes to skills, skills can use prompts, skills can use other skills, skills can use MCP servers, and of course skills can use sub agents.

## The Feature Breakdown

As you can see, there's a ton of overlap. This is important to call out. It's the approach that's new. We get a dedicated modular directory structure, efficient context (which again we had with sub agents), but these are triggered by our agents. This is the distinguishing pattern of when you would use a skill over MCP, sub agent, and slash command.

### When to Use Each Feature

Now, I know this isn't super clear right away, so let's look at some dedicated specific use cases:

**Skills** are truly for automatic behavior.

**MCP** is built for external integrations.

**Sub agents** are for isolated workflows that you can also parallelize.

**Slash commands** are manual triggers—manual units of compute that you can deploy when you need them.

The big battle here I see is between skills and slash commands. To be specific, these are custom slash commands. Let's look through some use cases.

### Practical Use Cases

**Automatically extract text and data from PDFs**: Which of these four do you think this belongs in? As we work through this, make a good guess. I think automatically—there's that keyword "automatic"—you want this to be a skill. If you always want to extract text and data from PDFs, this is a skill.

**Connect to Jira**: This is an external source, so we want of course an MCP server.

**Run a comprehensive security audit**: This one is tricky, but I think because you want this to be able to scale and because you don't really need this in your context window and you don't want this to be automatic—you want this to occur at a specific point in time that you kick off—I think we want this to be a sub agent.

**Generate git commit messages**: We have a simple one-step task here. Here's the tricky part: you could easily make this a skill, a slash command, or a sub agent. But which is best? I think this is best as a simple slash command.

**Query your database**: This is a classic one. You of course want an MCP server—at least you want to start with an MCP server. We'll talk about composability in just a second.

**Fix and debug failing tests at scale**: You of course want to throw this inside of a sub agent. You can scale this up. Just get the job done. I don't care what the errors are. Just fix them and do it at scale.

**Detect style guide violations**: This is an interesting one. I think when you want to encode some behavior, some repeat behavior, you want this to be a dedicated skill.

**Fetch real-time weather data from APIs**: This is obvious—it's MCP. This is a third-party service that you're integrating with.

**Create a component** (insert whatever UI framework you use—no one cares anymore and it doesn't matter): This is a simple one-off task that you likely want to encode in a custom slash command.

Here is a keyword: whenever you see "parallel," you should always just think "jump to sub agents." Nothing else supports parallel calling—it's just sub agents. Whenever you see that parallel keyword and whenever you want to isolate the context window (and again, you have to be okay with losing that context afterward because it will be lost), you'll want to throw that into a sub agent.

## The Confusion: Skills vs. Slash Commands

I think MCP is very distinct from skills. Skills versus MCP is very distinct. Skills can of course use MCP servers. You can compose everything into a skill, but you can also compose everything into a slash command. This is where things get interesting.

If you look at this feature set, slash commands and skills are very similar. The only exception is the modularity and who is triggering it. This is actually really interesting. There are a lot of engineers right now that are going all in on skills, converting all their slash commands to skills. I think that's a huge mistake.

I see slash commands as the primitive of agentic coding, of AI coding, and really of language models. You want to be very careful about getting rid of your prompts. Let me show you exactly what I mean. Let me show you how I'm thinking about approaching skills as a compositional unit and not a replacement for MCP, slash commands, or sub agents—because these are all distinct. I think if you're using just one of these, you're not using these features properly. You're not using Claude Code properly.

## The Right Way: Prompts as Primitives

We have our work trees and we can verify this very quickly. If we go to trees, you can see we have three brand new versions of this codebase fully built out. There's the environment variable file. If you go into apps, you can see client and server. Everything is there. Our agents used the prompt, sub agent, and skill to do the exact same work.

This is the wrong way to think about skills. If you can do the job with a sub agent or custom slash command and it's a one-off job, do not use a skill. This is not what skills are for.

### How Should We Think About Skills?

Here's our skill, sub agent, and prompt—the three agentic units of work that we kicked off. We accomplished the same job with three different capabilities. Now, this is where things get tricky and where there's a lot of confusion around this tool.

In engineering, you don't want many ways to do the same thing. You want one dedicated way to get the job done. So this is getting confusing. Claude Code is becoming a larger and larger tool. Successful things tend to grow, and at some point it loses its originality, loses what made it distinct. Now I don't think Claude Code is there. I like this feature. I think it's a net positive for the ecosystem, for the tool, and for engineers.

### The True Answer

Remember in the beginning I asked what's the right way to create a git work tree? Very clearly you can do this in three distinct ways. I think in the end you can build out any one of these. But the true answer is you probably want a prompt to create a git work tree. You want to be able to see what happened. Unless you need to create many of these, we don't need to parallelize this. But if you do need to parallelize, use a sub agent—that's a perfect branching point to go from custom slash commands to sub agents.

If you need to parallelize, you can take your existing custom slash command and throw it in a sub agent. In fact, that's exactly what we've done here. If you actually dial into this sub agent prompt, you can see I'm having the sub agent compose a prompt with the slash command tool—it is calling our prompt. So we're starting to get into a composability chain where we have the base level unit being a prompt, aka a custom slash command.

How you compose these features is very important. You can push this even further. In our skill, guess what we're doing? The instructions say: use the slash command tool. So here we are looking at the prompt as the primitive for all the existing features.

## The Fundamental Truth About Prompts

I've been saying this for years, frankly, ever since the generative AI revolution kicked off: do not give away the prompt. The prompt is the fundamental unit of knowledge work and of programming. If you don't know how to build and manage prompts, you will lose.

Why is that? It's because everything comes down to just four pieces. There are four pieces of agentic coding: context, model, prompt, and tools. If you understand these, if you can build and manage these, you will win.

Why is that? It's because every agent is the core four. Every feature that every one of these agent coding tools is going to build is going to build directly on the core four. This is the foundation. This is the ground level. If you master the fundamentals, you'll master the compositional units, you'll master the features, and then you'll master the tools.

This is why it's so important to always lead with a custom slash command. When you're starting out, I always recommend you just build a prompt. Don't build a skill. Don't build a sub agent. Don't build out an MCP server. Keep it simple. Build a prompt. Everything is a prompt in the end. It's tokens in, tokens out.

### When to Move from Prompt to Skill

If we want to parallelize though, we can go to sub agent. Now, when do we go to a skill? This is the critical question. When do we move from a prompt to a skill for creating git work trees?

We can easily use just a prompt—one prompt solves the problem. But if we want to solve the problem of managing our git work trees, we need a skill. Because dealing with git work trees isn't just about creating them. If I open up trees here, I now have three git work trees to manage, to read from, to merge, to remove. We need a skill to manage our git work trees.

This is where one prompt is not enough. You want to scale it into a reusable solution. We need of course a skill. This is what skills were built for: reusable file system-based resources, Claude-domain specific expertise, workflow context, best practices into specialists.

Skills offer a dedicated solution—an opinionated structure on how to solve repeat problems in an agent-first way.

## Building the Right Solution

Let me show you exactly what I mean. We're going to boot up a new instance and if we go to our skills here, we have a work tree manager skill. This is a lot more built out. We can do something like list skills. You can see here I have a meta skill and a video processor skill.

"I've listed the four available skills you can use in your Claude Code environment."

This is the right way to think about skills. We have a skill that is a manager of a specific problem set—a repeat solution for a specific problem. If we actually just needed to create work trees, we'd use slash create, give the branch, give the additional details to make the branch unique, set up environment variables, set up the right client server ports, and you're done. One-off.

But if we need to manage multiple elements, if you need to manage multiple work trees (stop, remove, create, list), stop manually prompting this, stop firing off these custom slash commands by yourself. Really dial in and build a skill.

Let's run this. I'm going to say: manage git work trees, remove red tree, create purple tree with offset four so that we offset our ports, list our trees. This is a skill set. We have solved the problem of managing our git work trees with a dedicated skill. This is what skills are about.

I'm going to fire that off and our agent is going to get to work on this. This leads us to a great point. Let's look at some definitions while our agent works through this piece by piece. When we come back, we should see red tree removed, we want to see an added purple tree, and then we want to see a summary of our current trees.

## Defining the Capabilities

Let's look at definitions at a high level. Where do all these capabilities fit and when do we use each?

**Agent skills**: You use this to package custom expertise that your agent autonomously applies to your reoccurring workflows. Super important, very distinguished.

**MCP servers**: About connecting your agents to external tools and data sources. To me, there is very little overlap here between agent skills and MCP servers. These are fully distinct.

To be super clear, I like to think about things in composition levels. What should be using what? Skills can have many MCP servers. Skills can have many sub agents. Skills can have many custom slash commands. But an MCP server is a lower level unit—you wouldn't have an MCP server use a skill. So there's a chain of command here.

Very interestingly, I would consider a slash command a super primitive where it acts as both a primitive and a composition, because of course you can take a custom slash command and you can run a set of skills, you can run MCP servers, and you can run sub agents. So it's very interesting how these things compose. There's a lot of circular composition that you can build up here, but I would definitely place your skills at the top of the composition hierarchy.

**Sub agents**: We use sub agents to delegate isolatable specialized tasks with separate contexts that can work in parallel. Sub agents are very distinguished. I think it's very clear when you'd use a sub agent versus when you wouldn't—when you want work out of your primary agent's context window and you can delegate it and you don't care that you're going to lose the context at the end.

**Custom slash commands**: This is for reusable prompt shortcuts that you invoke manually. Now, I am definitely underselling custom slash commands here. I would say if you had to pick one and you just kind of forget about everything else, you definitely want to prioritize your mastery of custom slash commands.

Why? Because this is the closest compositional unit to just bare metal agent plus LLM. You're passing in a user prompt. You must master the prompt. There are no exceptions here. If you avoid understanding how to write great prompts, how to really build these out in a repeatable way, you will not progress as an agentic engineer. You will not progress as an engineer in 2025, in 2026, and beyond.

The prompt is the fundamental unit of knowledge work. There are no exceptions to this. If you understand this, you will win. This is something that comes up over and over. This is a big topic inside of Tactical Agentic Coding and Agentic Horizon. That's the custom slash command. This is the primitive. This is ultra important.

## The Complete Feature Set

What's next? Let's continue breaking down all these features.

**Hooks**: Hooks are great. This is deterministic automation that executes commands at specific lifecycle events. This is where we kind of add determinism rather than always relying on the agent to decide. So we need to balance these things. This is why in Tactical Agentic Coding we push outside of the agents to ADWs (AI Developer Workflows), where you combine the old world of code with the new world of agents. If you really want to scale, you need both. Hooks lets us tap into deterministic automation.

**Plugins**: This is simple. There's no overlap here between any of these other features. Plugins let you package and distribute these sets of work. This isn't super interesting—it's just a way to share and reuse Claude Code extensions.

**Output styles**: Last but not least, we have our output styles. I'm using output styles 24/7. When our agent finishes this work, it's going to actually summarize the work using a text-to-speech output style. If we scroll down here, you can see I have a whole slew of output styles. I'm using the observable tools diff text-to-speech summary.

And you can see here we're on to that last step: list work trees prompt. Very importantly, you can see my skill is using a compositional prompt—it's using a prompt to do the work. Great stuff there.

I hope this helps you distinguish some of these features and when you should be using each. At the end of the day, use whatever works for you. Don't let these features, don't let these Claude Code buzzy features stop you from just shipping work. Use what works for you.

But I would say have a strong bias towards slash commands. And then when you're thinking about composing many slash commands, sub agents, or MCPs, think about putting them in a skill. But your skills again should have a slew of slash commands.

## My Honest Assessment: Pros and Cons

Now that leads me to some opinions that I have about this feature. I like it, but there are also some problems with this feature. Let me work through this pros and cons list.

### The Pros

**Agent-invoked**: I like that this is agent-invoked. We want to lean into the autonomy—dial up the autonomy knob to eleven. This is how we do it. We delegate more work to our agents.

**Context protection**: I like the context protection. This is incremental context window adoption. Progressive disclosure is what they call it. Unlike MCP servers, which just straight up torch your context window.

**Dedicated isolated file system pattern**: I like that this is a dedicated isolated file system pattern. We can now logically compose and group our skills together. This makes it really easy to write, update, create, modify, and then distribute what your agents can do. This is great. This is honestly the biggest value prop right next to agent-invoked for agent skills.

**Can compose other elements**: Can compose other features.

**The agentic approach**: I think it's really important to highlight this is the agentic approach. This is what you want to see. Agent just does the right thing.

Lots to like here, but there are some things that I don't like.

### The Cons

**Doesn't go all the way**: What do I mean by that? I can't nest sub agents and I can't nest my prompts. Why not? Why do we not have the capability inside of our bundle here, inside of our file system VM for my skill—where's my /commands directory? Where's my agents directory?

Why didn't the Claude Code team go all the way here? If you're making this the bundle for repeatable solutions, why can't I embed prompts? The most important feature out of any one of these agents is just prompts. Don't let anyone confuse you with these feature releases. Prompts are the most important thing of all.

"I have successfully managed your git work trees. Removed red tree, created purple tree on ports 4040 and 5013, and listed all three running work trees."

That work's been completed, but let me just finish my rant here. Why can't I put the most important primitive of all inside of skills in a dedicated way? I know I can just engineer this in, but they're creating this pattern, so just go all the way. That's my biggest complaint and my one request for this feature.

**Reliability concerns**: I think that reliability is going to be an interesting one. Will the agent actually use the right skills when chained? I think individually it's less concerning, but when you stack these up—and this is one of the key features that they mention, compose capabilities, combine skills—how reliable is that? Can I actually deploy that into production? Can I actually chain together five skills and expect them to be called back to back to back to back to back? Or should I again just use a prompt? Because I can guarantee you if you run "call slash xyz" then "call slash zyx," this will run in the right order.

So I'm—it's not clear to me how reliable skills are yet. Of course, more testing. Make sure to subscribe. Make sure you like and comment so the YouTube algorithm knows you're interested. We're going to be pushing skills hard and seeing what we can really do on the channel.

**Could do all this before**: The last kind of issue I have with this is that we could do all this with prompt engineering plus custom slash commands plus slash command tool. The problem here is that skills are effectively canyonated prompt engineering plus modularity.

The real question is: what's the actual innovation? What's actually new here? I think the answer is not that much. And at the same time, having a dedicated specific way to operate your agents in an agent-first way is still powerful. So it's very interesting. This is quite a simple feature. It's a kind of thin opinionated file structure, but we could do that before. So I don't know. I'm still kind of working through this. There's nothing actually new here. I think this is the Claude Code team making it easier to bundle together repeat solutions in an agent-first way.

## Final Verdict

So that's my pros and cons list. I've built out several skills for repeat workflows. Right now I'm really stacking up my user directory with a bunch of concrete skills. It's very clear that this release is important. We have this huge banner here at the top. The Claude Code team, the Anthropic engineers, they're really pushing this feature and I think for good reason.

This is powerful and it's a dedicated way across their entire platform to enable engineers and just general users to create repeat agent-first solutions. We're creating domain-specific expertise in an agent-first way.

So I like this feature. I am using it. I give this a solid 8 out of 10. It is very clear this does not replace any existing feature or capability. This is not a replacement for MCP, slash command, or sub agent. It is a higher compositional level that you can use to group these features together to solve a specific problem in a repeat way.

## Resources

This codebase is going to be available to you. Link in the description. You're going to get access to all four of these skills. I also have the meta skill for you. You can use this skill to build other skills. This is a very powerful agentic abstraction you can always use: build the thing that builds the thing. This is a big theme in Tactical Agentic Coding.

Then we have the video processor where we actually have a dedicated script and this skill is dedicated around processing and managing different video files, creating transcriptions, and so on and so forth. I just wanted to give you a few ideas of how you can use skills to push your engineering forward.

Take these, understand skills, make them your own. If you made it to the end, definitely like and comment to let the algorithm know you're interested. I'll see you next Monday with a big idea for your agent coding.

Stay focused and keep building.
