# MCP Server Primitives: Unlocking the Full Power of Agentic Coding

## The Evolution of Engineering with AI

As we know, MCP servers enable us to build tools for everything. They represent one of the three most important innovations for evolving engineering from AI coding to agentic coding. With new models like Claude 4 and the brand new DeepSeek R1.1, we have more intelligence to build with than ever before. 

But the models are no longer the limiting factor for engineering output. This forces us to ask: what's limiting us as engineers from creating more value faster than ever? The answer lies in our ability to create capabilities for our agentic coding tools like Claude Code. That brings us full circle back to MCP servers.

## Beyond Tool Calling: The Three Primitives

In this exploration, we'll understand the most underutilized capability of MCP servers. Most engineers stop at tools. But once you understand this one simple idea, you'll be able to craft rich MCP servers that dramatically increase your engineering velocity as well as your team's.

The three primitives, in reverse order of capability, are:
- **Resources**
- **Tools** 
- **Prompts**

Most engineers skip resources. They go all in on tools and completely miss out on the highest leverage primitive of MCP servers: prompts. Tool calling is just the beginning of your MCP server. Let me show you how to maximize the value of your MCP servers.

## A Practical Demonstration: The Quick Data MCP Server

By typing `/mcp`, you can see the available MCP servers. For this demonstration, we'll operate in the Quick Data MCP server, which gives your agent arbitrary data analysis capabilities on JSON and CSV files.

We all know how tools work, but let's run a few to understand the Quick Data MCP server and showcase how limited tool calls really are. Running this on Sonnet 4—our fast workhorse model—we immediately encounter a problem: without documentation, there's no way to know what this MCP server can do.

Opening the codebase reveals a complete documented set of all the tools, resources, and prompts available. Let's start with simple operations. We'll run the load dataset command, passing in a JSON file. Using an e-commerce orders file from the codebase, we load the data set successfully. The JSON response shows columns, rows, and the dataset name—everything looks great.

### Exploring with Tools

Getting a dataset breakdown reveals the shape and key information about our data. Running the suggest analysis tool provides several ideas based on our e-commerce data. Executing the first command gives us a segment breakdown by product category. 

The analysis reveals that electronics are producing significant value in this e-commerce orders file. From a business strategy perspective, this insight suggests we could cut down on sports and home garden product categories and focus on electronics.

There's another powerful capability: executing arbitrary code. We can have Claude Code running on Claude 4 Sonnet execute custom code for us. Asking it to find the top three regions by order value, we see custom code getting written based on our prompt. The executed response shows East Coast, West Coast, and Midwest as our top regions by order volume—pretty accurate for training data.

We can reuse that same MCP tool call to create a pie chart labeled by region value and percent. Within moments, we have a visual breakdown showing East Coast, West Coast, Midwest, and South—all quickly created and managed with our MCP server for quick data analytics against JSON and CSV files.

## The Limitations of Tools Alone

Tools are great. We all know about their capabilities. We can build tools for anything and everything. But tools only scratch the surface of what you can do with your MCP server. To unlock the full capabilities, we need to build MCP server prompts.

## MCP Server Prompts: The Game Changer

To showcase these capabilities, let's reset the Claude Code instance and start from scratch. Instead of looking through documentation—that readme that thankfully detailed all our tools, resources, and prompts—instead of relying on codebase architecture and structure, we can use MCP server prompts to guide the entire discovery and use of the Quick Data MCP server.

### Discovering Prompts

To find all prompts associated with this MCP server inside Claude Code, we type `/quick-data`. This is the name of the MCP server, and autocomplete reveals a ton of prompt suggestions built into the MCP server.

Let's run something really useful that I highly recommend you set up inside all your MCP servers: "List available MCP server capabilities, including prompts, tools, and resources." This prompt provides a clear breakdown of everything we can do with this tool.

Claude Code, our agentic coding tool, has now consumed everything available with this tool. It's loaded fresh in the context window, and we have a quick start flow to get started. We can simply ask Claude Code to list the components as bullets. Here are the prompts. Here are the tools. This is everything we saw before.

### Guided Workflows Through Prompts

Let's continue firing off prompts to understand what they can do for us. Typing `/find` reveals another prompt: "Find data sources." This discovers available data files in the current directory and presents them as load options.

Notice how much more helpful these prompts are than just having tools hidden somewhere. The prompt automatically discovers all available JSON and CSV files for our Quick Data MCP server—an agentic workflow doing this work automatically.

Critically, we're getting suggestions for direction and next steps for what we can do with this MCP server. With just typing two words—"load ecom"—using the current context that we've set up thanks to our prompts and Claude Code running on Claude 4 Sonnet, we can be nearly 100% sure this will run the right tool with the right information.

### The Big Three Never Disappear

Notice how we just ran through the big three of AI coding: context, model, prompt. These never go away. That's why they're a principle of AI coding—they're always there whether you realize it or not. The more you can look and think from your agent's perspective with the current available context, model, and prompt, the more you'll be able to hand off tons of engineering work, which results in increased engineering velocity.

With just a few pre-existing prompts, we're moving much faster than if we were looking through documentation, going back and forth. This is really important: we haven't left the terminal. We haven't left Claude Code. We're focused. We're moving quickly. And we're operating inside this MCP server with minimal information.

### Following the Workflow

With the dataset loaded, scrolling back reveals the concrete workflow we were given: find dataset to discover data files, then run load dataset, then explore data. Let's run the "first look" MCP prompt. This prompt kicks off one or more tools, giving us a nice breakdown with data set size, columns, and sample data.

Thanks to the existing context window that all these prompts have been providing our agent, we can simply ask: "How can we further explore this data?" From the existing context window, we have tons of ideas for pushing forward. This is really useful when operating outside your MCP server or when handing off your MCP server to your team or exposing it to the public—you want it easy to use, quickly consumable, with guided workflows.

## Anatomy of a Prompt

Let's examine what these prompts look like inside the MCP server. The codebase architecture is important here. The structure includes three essential directories for agentic coding, including a trees directory for multi-agent parallel AI coding. Under the modular architecture, we have our data, then source MCP server with the primitives: tools, resources, and prompts.

Opening the correlation investigation prompt reveals a single function—these are all single-function Python files to keep everything nice and isolated and easily testable. Inside, we're passing in the dataset name and then running arbitrary code, which is effectively our agentic workflow. You can do anything you want here. The most important thing is to gather some type of prompt response and return that back to your agent.

### Prompts Compose Tools

The prompt kicks off tool calls. This is super important: inside your prompts, you can kick off one or more tool calls. The prompt allows you to compose sequences of tool calls very quickly using custom slash commands.

Running the correlation investigation reveals that we need at least two numerical columns for correlation analysis. Our tools are giving us feedback, all guided by our prompt. We can quickly use our slash command to run `/find` and locate other data sources.

Loading all available datasets—employee survey and product performance—we now have multiple numerical columns across datasets for correlation analysis. The correlation investigation prompt exposes potential columns we can correlate. Running the analysis reveals a strong correlation between satisfaction score and tenure years.

This immediately reveals that satisfaction and retention are closely linked—satisfied employees stay longer. Not a mind-blowing revelation, but this could be anything inside your dataset. The example showcases the power of these MCP server prompts, which can then guide us to visualize the findings with charts.

## Why Prompts Matter: The Three Massive Advantages

Why are prompts inside your MCP server so important? By using this MCP server, we were able to move much faster. Prompts let you quickly set up your agent with everything they need to know to operate your MCP server.

Looking at the list MCP assets prompt, notice how simple it is: it's quite literally just returning essential information about this MCP server in a custom way to our agent. This prompt primes both your memory and your agent's memory with everything it needs to know about your MCP server. Every MCP server I build out now has some type of prompt just like this.

Everything is exposed. We can quickly see and operate on things in a much faster way. Prompts allow us to prime our agent in powerful ways and run arbitrary Claude Code tools. The find data sources prompt is running arbitrary code—what Principal AI Coding members know as an ADW (AI Developer Workflow). That's all these prompts are: end-to-end chains of prompts and code coupled together that end up in a simple string return value.

### Offering Suggestions

After scanning directories, we do something really powerful: in multiple use cases and scenarios, we offer the agent suggestions. This is incredibly powerful. Our agent is ready for the next step—it wants the load dataset command. This time around, since our agent is powerful with the new Claude 4 model, we can simply say "load all datasets," and we can move much faster thanks to the prompt.

## The Hierarchy of Capabilities

We have prompts, resources, and tools. Claude Code does not support resources currently, but it has the two that really matter: prompts and tools. You can also substitute your resources for just specific tool calls.

Recentering on the key idea: why do we create prompts? Because prompts allow us to create agentic workflows. They allow us to compose our tools. Tools are individual actions—the load dataset tool just does one thing: it loads the dataset into memory.

**Tools are individual actions. Prompts are recipes for repeat solutions.**

This is the big difference. Your prompts have three massive advantages that your tools don't have:

### 1. Quick Reference and Discovery

With Claude Code, you can reference all of your prompts in a clean, detailed way very quickly. No more guessing—you can quickly get up and running with whatever MCP server you have.

### 2. Tool Composition

Your prompts can compose tools in your MCP server together. This is super powerful. Multiple times we saw our prompt kicking off individual tools that exist underneath the prompts. That's why we have this tier list order of capability: prompts > tools > resources.

### 3. Experience Guidance

A super underutilized element of prompts is that you can guide the experience. Our agent, through the prompt, triggers not just a sequence of tools but also a guide and direction for you, the engineer operating the tool. More importantly, every single day it's giving our agent the next steps.

We can very quickly and calmly say things like "load all datasets" and then continue down the line of data exploration or running whatever other tools or prompts our MCP server exposes to us.

## The Path Forward

With prompts, you can build high-quality MCP servers that do more than just call tools. Tool calling is just the beginning. Tools are the primitives of MCP servers, not the end state. You want to end up with prompts.

Prompts represent end-to-end developer workflows that are truly agentic workflows—or as I like to call them, AI developer workflows. They are quite literally doing developer work that you would do, but powered by generative AI.

You really want to be thinking about MCP servers as a way to solve a domain-specific problem in an automated fashion with repeat solutions embedded inside the prompts. The prompt is what the tools scale into.

## Conclusion

This exploration demonstrates a concrete example of how you can use prompts inside your MCP servers. The key insight is simple but powerful: move beyond individual tool calls to orchestrated workflows guided by intelligent prompts. This is how we unlock the true potential of agentic coding and dramatically accelerate our engineering velocity.

The future of engineering isn't just about having access to powerful AI models—it's about building the right abstractions and workflows that let those models work for us in the most effective way possible. MCP server prompts are that abstraction.

Stay focused and keep building.
