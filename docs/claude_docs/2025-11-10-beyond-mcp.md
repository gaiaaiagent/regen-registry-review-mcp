# Beyond MCP: Three Proven Alternatives for Agent Tool Integration

*A Technical Exploration of Context-Efficient Agent Tooling*

## The Context Window Crisis

What's up, engineers? Indie Dev Dan here. My MCP server just consumed 10,000 tokens before my agent even started working. That's 5% of my agent's context window gone, and my Kalshi prediction market MCP server isn't even that large. Stack up two or three more MCP servers, and I'll be bleeding 20% or more of my context in no time.

This isn't a new problem, but what is new are three proven alternatives to MCP servers. Beyond the skills you already know, we're going to break down two additional approaches you can use to connect your agents to external tools without torching your context window while maintaining control.

These approaches are being used by leading companies in the agent space—including Anthropic itself—and by top engineers who use agent coding tools every single day. We'll break down when to use each approach and their tradeoffs so your agent can ship for hours, not minutes, with focused context.

Let's go beyond MCP.

## The Classic Approach: Kalshi Markets MCP Server

The first version is, of course, the classic MCP server. The great part about this approach is that your MCP server manages everything when it comes to the connection to your external data source.

For this demonstration, we're using a Haiku model—we don't need Sonnet, as that would be overkill for this specific problem. What does this MCP server do? It's a Kalshi prediction markets MCP server, giving us agentic access to the Kalshi prediction markets betting platform.

When we search for prediction markets about "OpenAI achieves AGI," our agent dives into the information using the search markets tool. We can examine the market: "When will OpenAI achieve AGI?" The probabilities are very low before the 2030 mark.

There's a lot of information missing from the standard UI. We can have our agent tap into that for us. One of the key value propositions of agents is that they can manipulate and CRUD information on your behalf faster than ever.

When we request recent trades and the order book for this market to understand the data at a deeper level, Haiku does a great job moving at light speed, breaking down the markets for us. Here's the order book: all the shares, total volume on each side, recent trades placed. These agents are powerful at understanding information.

We can ask for a concise summary of bets and market sentiment in a table. This readonly Kalshi marketplace MCP server provides clean sentiment analysis: bearish by 2029, but still only a 43% chance overall. The market is telling us with their dollars that by 2029, they expect only a 43% chance that OpenAI achieves whatever AGI is.

The devil's always in the details here. OpenAI has to announce that they've achieved AGI. Who knows what AGI is anymore? No one really knows. But this is the power of this MCP server—we can understand the markets at light speed.

However, here's the big problem: 10,000 tokens torched immediately for my relatively small, well-built MCP server.

Let's move beyond the MCP server with three new approaches where we can get value without torching our agent's most important resource.

## Alternative One: CLI as Tools

These approaches trade complexity for control, but the theme is the same: use raw code as tools.

For our next approach, we're using the CLI. We prompt our agent with specific instructions that teach them how to use a CLI—a set of functions they can call to access the thing we're trying to interact with.

How does a CLI-first approach work? Let's open up a brand new agent. I've dropped the MCP server, so now we're just running our cheap, fast Haiku model. If we check MCP, there's nothing there.

How does this work without an MCP server? How can we enable and teach our agents to use a specific set of tools? It all boils down to context, model, prompt, and tools.

Prime Kalshi CLI tools. Our fast agent is going to read just two files: a readme and a CLI. Now our agent has summarized how to use this tool exactly. It understands the CLI, its settings, and has broken down the common workflows.

What exactly does this file look like? Inside the Beyond MCP server codebase, we have a concise 25-line prompt that tells our agent how to use these tools. The key line is in our workflow step: read only these two files—the readme of our app and the CLI—and as you work with the user, call the right tools to get the data you need.

Let's search for another market: "trillionaire." Instead of running an MCP tool, our agent is running a CLI command. We've taught our agent how to use the CLI instead of an MCP server.

There's a little more upfront cost here—we are prompt engineering how to use this system—but as a reward, we get to fully control everything the agent can and cannot do. MCP just says, "Here's a bunch of tools, here's all the descriptions, here's all the context you're going to need to consume every time you boot the agent up." Here, we're in full control over everything. Here's the readme, here's the CLI, this is what you should do. And crucially, we said: do not read any other Python files. We're limiting additional context consumption. This is all you need.

We can do the exact same work. Market search for "trillionaire" pulls up the Kalshi marketplaces about who's going to be the first trillionaire and when Elon Musk will become a trillionaire. We get summaries: highest conviction for Musk by 2030, most liquid and most traded markets. Betting on Elon is pretty high. We can see a lot of sentiment around Elon, but not so much for anyone else.

We can push this further: summarize bets and market sentiment for Elon and the first trillionaire markets. Our agent pulls this information together.

### The Value of Prediction Markets

These betting markets offer something unique. As Vitalik Buterin, creator of Ethereum, said, there are two ways to use these betting markets. For some people, it's a betting site for those looking to make high return on investment decisions. For others looking to understand where to invest their time and comprehend events happening in the world, this is also a news site—a place for finding valuable information.

These markets help us understand the future before it occurs because people are placing their bets. Vitalik calls this "info finance." You can use these betting platforms to understand incentives before things happen. It's a great way to get an edge with agents. These agents can understand this information faster and better, giving you multiple perspectives on the data.

Just by looking at these betting markets, we can see that by 2030, the market becomes bullish that Elon will be a trillionaire. Some of these other prediction markets are actually really interesting. When will OpenAI achieve AGI? This tells you the sentiment of the market around OpenAI achieving its goals and becoming a valuable company. That's the information underneath the data—but only a 43% chance by 2030.

We can continue to prompt our agent: web search 2025 net worth for Jensen, Elon, and Sam. What market cap would their companies need to make them trillionaires? This is all thanks to agents helping us move super fast and understand data.

### The CLI Implementation

Focusing back on the CLI: if we open up the code while our agent works, we can see all the functions. Notice how, via the CLI syntax—using Click, Typer, or whatever you want—our agent can easily understand how this works. As long as you're not using a super new tool that the agent has no idea about, it's pretty straightforward. Here's an option called "limit" with a default. Here's how you can use it.

We effectively have all the capabilities of an MCP server with raw code. This is something Mario mentions—he's a pretty top-tier engineer covering hot topics. He argues: what if you don't need MCP at all? The way he does it is by setting up a prompt through a readme file, telling the agent to look at specific tools in a specific file.

The benefits here are obvious. You can pull in the readme whenever you need it. For this agent, we ran our prime Kalshi CLI tools command—we only activate this, we only set our agent up when we need the specific tool set. This is really powerful and much more dynamic than MCP servers.

Sam Altman is currently reported at $2 billion net worth, while Elon is at $500 billion already, and Jensen Huang is about $175 billion. We get a breakdown of their companies and how much more revenue they would need to hit these marks. Jensen would need a 450% increase—not that much. Elon is only 100% away between all of his assets. Sam is actually a lot further away, not as wealthy as a lot of people think.

### Context Savings

Here's something important I missed at the start. If we clear this agent, restart it, and run the prime command—only reading these two files—we conserve our context window. If we check the context, our tokens are down from 10% to just 5.6%. We've saved roughly 4% of our context window with our CLI approach.

Very powerful, but we can push this further.

## Alternative Two: Scripts as Tools

Scripts look a lot like skills. We have that same setup where you prompt your agent with a specific prime prompt, preparing your agent for something—just like you would set yourself up for a great day in the morning.

The trick here is progressive disclosure. This is something Anthropic mentions in their blog when discussing using direct tool calls to scale better by writing code instead of relying solely on MCP servers.

Interestingly, Anthropic actually ends up calling the MCP server under the hood in their example. I would argue—and Mario would agree—that you don't actually need to go that far. You can just hand them the script or the tools and have them run that directly. The only con is that you have to build out that tool and the interaction versus relying on an existing MCP server.

### How Scripts Work

What is this scripts approach? We boot up our agent and run the file system scripts command, priming our agent with a specific set of information. This time, we only read a readme. Our agent understands when to use each script. This isn't preloaded in the context—it just understands at a high level when to use each script.

We effectively have a condition mapped to files. This is a powerful agentic data structure that you can use to activate or ignore context.

Check this out: our context is less than 1%, just under 2,000 tokens. Here's the key part: "I will not read scripts themselves unless help doesn't provide the information needed." We are prompt engineering this outcome.

A lot of engineers are obsessed with context engineering. Everyone's jumping on the context train. But even before context comes prompt engineering. This is still a critical skill—in fact, it is THE critical skill for engineers in 2025 and beyond.

The prompt shows up before the context gets into your context window. We have just prompt-engineered out 10,000 tokens that would show up via a default MCP server or even our CLI script. Our CLI script got it down by 50-60%, but our script-based approach is taking it all the way down to about 10% of the original.

### The Prompt Structure

How does this work? We have another great prompt with a typical structure. Every section has a specific purpose. Here's the important part: "Do not read the scripts themselves." Then we have the `--help` flag where we explain that as you work through each script, you use `--help` to understand how to use it.

Here's the cool part: if we look in this directory, every single script is self-contained. If we open up the readme, we can see exactly why we had our agent read this file. These are file system scripts—isolated single-file scripts that you can use on their own or together, with conditions on when to use each file. That's it: a 58-line readme file. We could have put this in the prompt, but having it here in the readme is fine as well.

### Scripts in Action

Now we can prompt as usual. Let's look at another prediction market on Kalshi about government shutdown. We want to understand how long this will last.

The agent runs `uv run app-3-file-system-scripts search --json`. This is effectively the same thing as the MCP server and the CLI server. That's the big kicker—all these approaches help you solve the same problem: give your agent access to tools. The question is how you do that and what it costs.

In the script-based approach, we have dedicated single-file scripts. If we open up our search script, it's self-contained. We're using Astral UV—shout out to Astral, they are the best Python dependency manager. The industry is really picking up on this. We can do powerful things like Python single-file scripts all over the place with dependencies declared at the top.

Each one of these scripts is its own world of code. Of course, the tradeoff here is code duplication all over the place. But that's fine. We're willing to pay that price because it makes our agents more effective. When you have less garbage context, your agent can perform better.

### Understanding the Data

The market we're looking at: how long will the government shutdown last? There's no value in a bet that's 99% certain, or really even 90% certain. But there is more information in the 66-63% bet range. We can pull up the full bet. The interesting places are the 45-52 day mark—this is where the interesting bets are actually happening, where we can actually get real information.

When we ask the agent to summarize bets and predict when the government shutdown will end, based on the information available through people placing real bets on these markets, we can understand the future more deeply. We're pretty much guaranteed it'll last longer than 39 days (since October 1st). Longer than 40 days, but then the probability really drops off. Based on this information, roughly 40 to 50 days is the consensus. Expected end date based on probabilities: November 18-20.

This is a really interesting way to use these markets: as information about a future state in the world.

### The Advantage of Scripts

This is the huge advantage of using these scripts, and it's something Mario points out. Benchmarks have shown that there's no degradation in quality by going right for scripts or CLI—basically handing your agent code versus giving them an MCP server.

Anthropic has a slightly interesting approach with their "call MCP tool" method, where they recommend wrapping and exposing specific functionality in a CLI or individual scripts, then calling the MCP server underneath. I think you can just cut the MCP server out completely if you're going to script it out yourself.

They mention that the big benefit is progressive disclosure. Very interestingly, we're getting that progressive disclosure ourselves by prompt engineering, and it's not a complex prompt. We're saying when to use every single file, and then we're saying don't read them upfront. Here are a couple of tools you can use to understand every single script without blowing up your context window.

I like to call this incremental context.

## Alternative Three: Skills as Tools

Skills look very similar to scripting things out. The big key difference between skills and scripts is how you invoke them.

With scripts, we have to have a priming prompt to fire things off. With skills, the prime prompt IS the skill.md file. You still have to set up the prompt that kicks things off and lets your agent understand the tools available, but how you do it is just a little bit different.

That's a key thing to mention: I talk about this a lot on my channel. Don't give away your understanding of how to write great prompts, because at the end of the day, everything is just the core formula: context, model, prompt, and tools. Every feature just builds on top of your agent's context, model, prompt, and tools.

The interesting thing is where and how the tools are discovered—that's what we're really focused on here.

### Skills Implementation

If we close all of our approaches and open up the skills app, all we have here is a `.claude` file. We can have our agent look at that file. We boot up Haiku again, check MCP—nothing there. We check context, and here's the best part about skills: they have progressive disclosure.

All our agent sees here is the definition of our skill, which is just at the top. This is all the context being consumed right now by our agent.

We can prompt: "Kalshi market search top LLM." This kicks off the skill. Kalshi markets—we're using skills and the scripts inside our skill.

If you look at the structure, it's the same thing as our third approach with the file system scripts. The only difference is that we've embedded, we've bundled all the scripts into the skills directory. Kalshi markets only has skill.md and then has all the scripts it needs to run. It's self-contained, it's isolated. This is a powerful approach to giving your agents specific tools without building an MCP server.

You can see a very similar structure to our scripts. Kalshi market instructions, the `--help` flag. All of our scripts are self-contained and they're useful and informative for agents. If we open up a random one, you can see the detail we're putting into this. The agent doesn't even need to look at the top of the file, but we have all this code self-contained in a single-file script. Our skill is telling our agent when to use each.

### Market Analysis Example

The agent searched and found the top language models by the end of the year, with Gemini ranking early. We can open this up and see Gemini is hugely favored here. There's a lot of information missing from this.

Let's open this bet: best AI end of year. You're probably raising your eyebrows already. We generally know that Gemini is not the best model. So why is this showing that? Again, the devil's always in the details. It's looking at a single benchmark here—not the whole story. Claude models are also tied for first place, but they have "style control" removed. You really have to understand the details in these betting markets to understand what they're really about. There are a lot of specific settings that change the actual leaderboard.

We can see the bets and have our agent summarize market sentiment. Early top rankings, not a lot of volume though. Overwhelming consensus: everyone's saying Gemini is going to dominate this leaderboard.

### Skills Flexibility

We have a skill-based approach to accessing and running tools through scripts. To be super clear: your skill could also be a CLI. Your skill could call right to the API endpoints. Instead of these skills here, we could have additional markdown files that detail how to run these commands directly via bash and curl.

If our endpoint doesn't require a lot of security or authentication, there are many approaches you can take when building out your custom skills and file system scripts. You can do anything under the sun.

## Understanding the Tradeoffs

Everything has tradeoffs. It's not just that we want to go beyond MCP and that MCP is bad and you should never use MCP. That's almost never the case with engineering. Everything has tradeoffs. There's no one winner-takes-all approach. There are options and tradeoffs.

### Comparison Matrix

**Who Invokes This?**
- MCP: Agent invoked, yes
- CLI Scripts: No, you need to run a slash command to set your agent up
- Skills: Happens automatically

**Context Window Consumption**
- MCP: High (the big loser, especially with external MCP servers where you have no control)
- CLI Scripts: Low
- Skills: Low

**Customizability**
- MCP: No (unless you own it)
- CLI Scripts: Yes (full control because you own the CLI)
- Skills: Yes (full control because you own the scripts and skill)

**Portability**
- MCP: Super low
- CLI: Higher
- Scripts: Even higher (single file, can copy/paste)
- Skills: High (single directory)

**Composability**
All of these are composable. The key thing to mention is that you need to build out local prompts, sub-agents, and system prompts for CLI scripts and skills that are separated from the actual core code.

This is where MCP wins—with MCP servers, there are a bunch of features that engineers completely gloss over. Everyone thinks it's just for tools (yes, tools are the most powerful piece), but if we look at the feature set, you can see: tools, resources, prompts, elicitation, completion, sampling. There are tons of features people miss in MCP servers all the time.

**Simplicity**
- MCP: Super high
- CLI/Scripts/Skills: More complex (you need to manage and roll everything out yourself)

The tradeoff is that you get more customizability and control.

**Engineering Investment**
Following that same vein with simplicity: the great part about MCP servers is that if it's an external MCP server, you're just done. They have everything done for you. Just use the tools and get running right away. This is why MCP is so great. It's standard, it's open-source, no one controls this.

Skills are very different. Let's be super clear: this is Claude ecosystem lock-in. It's great, there's a lot you can do with it, but it IS Claude ecosystem lock-in.

On the other hand, CLI and scripts—you're in full control. You can do whatever you want with these. You can share them however you like, and it's relatively simple to set this up and maintain this.

## Recommended Approach

These are the key differences you'll want to know. How am I using all of these different approaches?

### My Tool Belt Strategy

We have the access layer: MCP, scripts, CLI, and skills. Here's my approach, and this is what I recommend to engineers as well.

**For External Tools (Tools You Don't Own):**
- **80% of the time**: Just use MCP servers. Don't think about it. Don't waste your time trying to reinvent the wheel. It's simple to get started and running with this.
- **15% of the time**: Dial into a CLI if you need to modify, extend, or specifically control tools. The problem here is that you need to either interface into the MCP server via code or rebuild the MCP server as a CLI. I don't do this often, but when I do, I go for CLI.
- **5% of the time**: Go for scripts or skills, and only if you need context preservation. This is really the value-add of scripts or skills—the progressive disclosure that Anthropic mentions. You give your agent just a little bit of information because very rarely are you actually using every single tool every single time.

If we look at our MCP server example with 13 tools: are you really using all 13 tools every single time? The answer is clearly no. So you can use progressive disclosure with scripts or skills to just see and use the tools you need for that one instance, saving a ton of context.

With a single MCP server, no one really cares—even at the beginning, chewing up 5% of context is fine. The problem is when you stack up two or three more larger ones and 20% of my context window is gone. That's a problem. When that becomes a problem, you can push to CLI and control tools and context. If that's still a problem, you can go all the way to scripts or skills.

**For New Tools (Tools You Build):**
- **80% of the time**: Just use CLI. I give a prime prompt to set my agent up with how to use the tools. This isn't complicated. Look at what we're doing: it's a basic prompt with a few instructions and a simple three-step workflow:
  1. Read just these files
  2. Run the report section
  3. As you work, call the right tools

Step three really isn't even necessary—I'm just being super clear with my agent and having it report back to add more weight to the tokens.

I'm telling my agent how to use these tools by showing it the exact file. That's it.

The nice part is that CLI works for you, your team, AND your agents. The trifecta can be met here. You're not just building for you or your team—you're building for all three. CLI gets you all three out of the box.

- **10% of the time**: I will wrap an MCP server. Why? When I need multiple agents at scale and don't want to focus on context. Usually the MCP server problem isn't a problem at all if you're using dedicated, focused, one-purpose agents. This is something we talk about in tactical agent coding: you can sidestep every single context engineering problem by just focusing your agents on one problem and then deleting them when they're done.

But sometimes you do need to stack MCP servers and have larger tool sets. When you need that, I go from CLI to MCP server in a very specific way: I build CLI first so that it's very simple to then wrap an MCP server.

If you look at my MCP server implementation, all of my methods—all 13 tools—just call right into the CLI. I get interoperability with MCP because I have a CLI server first. So I always build CLI servers instead of MCP servers when building new tools.

Then 10% of the time, if I need agents at scale and I just want to pass it an `mcp.json` file, I will wrap it in an MCP server.

- **10% of the time**: I'll use a script or skill, again for the same reason—if I need context preservation. If you really need to protect the context and you have lots of MCP servers, then you go all the way to scripts or skills.

But most of the time, I recommend for your new skills you just roll out a CLI. Why? Because it works for you, works for your team, and your agents understand it as well.

### The Simplest Approach

There's an even simpler version of all these prompts: a CLI prompt. You can get rid of every other section if you're really being super lazy and rolling out that first version of your CLI prompt. You can just do this five-line prompt:
1. Just read these files
2. Summarize these tools
3. Go

No MCP server, no anything else. You just actually build against the use case you're focused on. This is what I recommend most of the time. Then if you need to, you go to scripts or skills.

Now, this order changes if you're deep in the Claude Code ecosystem—then you can of course go right for skills. But I like to keep a balanced approach. As much as I love the Claude Code ecosystem and the Claude ecosystem, I am always aware of lock-in, and skills is a Claude-specific lock-in mechanism. That's fine—these are just tradeoffs that we need to manage.

## Conclusion

This is how I think about alternatives to MCP servers. This codebase is available to you—link in the description. Everything's detailed out here so you can understand each of these approaches. You'll be able to get quickly up and running with this.

Read through this code before you start it. There are a couple of caveats in this codebase. I highly recommend you check out these three blogs:
- Vitalik's post on info finance
- Mario's technical breakdown
- The Anthropic team's documentation

There's a lot of rich information in each one of these.

You know where to find me every single Monday. Stay focused and keep building.
