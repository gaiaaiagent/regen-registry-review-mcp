# The Fundamental Unit of Engineering: A Guide to Agentic Prompt Mastery

## The New Paradigm

The prompt has become the fundamental unit of engineering. In the age of agents, every prompt you craft becomes a force multiplier—one well-designed prompt can generate tens or hundreds of hours of productive work. Yet the inverse holds equally true: one poorly constructed prompt compounds failure at the same rate.

How do you consistently create prompts that deliver 2x, 5x, 10x, even 100x returns on your time investment? The answer begins with a profound mindset shift—one that senior engineers must embrace.

## Engineering for the Trifecta

You must ask yourself: who am I creating these prompts for? The answer is no longer singular. We now engineer for three distinct audiences: yourself, your team, and your agents. This is the stakeholder trifecta for the age of agents—the agentic shift that most engineers have yet to make.

The winners in this new paradigm are building libraries of reusable, battle-tested agentic prompts with composable sections that work like Lego blocks. You can swap these components in and out as needed, scaling your engineering impact through compute.

The landscape has fundamentally changed. We now inhabit the realm of agentic prompt engineering, where every prompt you write can invoke tens or hundreds of tool calls and execute for minutes to hours. Understanding the seven most powerful agentic prompt formats—and crucially, the exact sections that compose them—becomes essential. These are the building blocks of your prompts, varying in usefulness and operational complexity for you, your team, and your agents.

Let us elevate our agentic prompt engineering abilities by mastering these prompts and their composable sections.

## Level 2: The Workflow Prompt

The workflow prompt represents a sequential workflow enriched with additional sections you can leverage. Of all the agentic prompt formats we'll explore, this stands as the most important. Why? The answer lies in the workflow section itself.

When we evaluate the workflow section, it earns S-tier usefulness—the most valuable section available—while requiring only C-tier difficulty to implement. The workflow prompt itself ranks A-tier in usefulness with C-tier skill requirements. Both are immensely powerful and accessible.

Consider the prime command, a foundational example you've likely encountered. This command prepares your agent to understand the codebase before beginning work. It introduces several key sections: a metadata section (specific to Claude Code but with equivalents in other agent tools), the familiar title and purpose, followed by two new elements—the workflow and the report.

The workflow section functions exactly as you'd expect: a sequential list of tasks for your agent to execute. When we invoke the prime command, the agent follows precisely these steps. The purpose statement explicitly directs it: "Execute the workflow and report sections to understand the codebase and summarize your understanding."

### Evaluating Prompt Components

The metadata section, while important, doesn't contribute substantially to your prompt's effectiveness for your team or agent. Among all sections across all prompt levels, metadata belongs in C-tier usefulness with C-tier skill requirements. It enables a few powerful capabilities—like specifying exact tools or models—but offers limited value beyond that.

The report section proves considerably more valuable. It controls how your agent responds: whether to output strict JSON or YAML, to structure reports in specific ways, or to include particular information. This is your output section, your format section.

To be clear: you can name these sections whatever you prefer. I use the most consistent, information-dense keywords to represent each section. Across the tens of thousands of prompts I've examined, used, and executed, these sections recur consistently. Regardless of what you call them, they'll remain essential as you scale the sophistication of your agentic prompts.

This represents the foundation of the workflow prompt—executing a series of steps that can grow complex and invoke numerous tools.

### Variables: The Power of Reusability

Examine the build prompt. Notice the enhanced metadata: this prompt restricts itself to read, write, and bash tools. It includes an argument hint, leading to a critically underappreciated section: variables.

The variables section proves immensely important. This is where your prompts become exponentially more valuable. Much of our work consists of repetitive tasks executed in sequences—precisely what agentic workflows currently solve for us. You can embed these workflows directly into workflow prompts, scaling them with ADWs as we've discussed extensively in TAC.

The variable section matters because we're parsing syntax and creating dynamic content. When executed, the prompt updates with whatever value you've provided. We reference the variable name throughout our prompt, building our own natural language variable syntax that we can reference consistently. Modern language models running in agents are sophisticated enough to understand exactly what you mean when you maintain this consistent syntax.

This benefits not only your agent but also you and your team. Consider how easily understandable this becomes: we have a variable representing the path to the plan. This exemplifies a dynamic variable, contrasting with static variables.

Variables rank A-tier in usefulness with B-tier difficulty. We're now referencing both static and dynamic variables throughout our prompt—a simple 23-line prompt that will scale in complexity.

### The Quick Plan Example

When working with prompts, I recommend opening them fully, then collapsing to the second level. This reveals all sections consistently, giving you an immediate sense of the prompt's complexity and power. The quick plan prompt demonstrates this: metadata, model, argument hint, description, allowed tools, title, and purpose.

Notice the language: "Create a detailed implementation plan based on the user's requirements." We speak directly to our agent. This dry, direct language contrasts deliberately with conversational prose, allowing you and any engineer on your team to collapse everything and read just the upper section to understand exactly what this accomplishes and its capabilities.

Then you can examine one piece at a time. The variables section shows the user prompt arriving as an argument, alongside the plan output directory—a static variable. This is a powerful distinction: static variables remain fixed in the prompt, unchangeable by passing arguments. The user prompt, conversely, is a dynamic variable that changes with each invocation.

This prompt writes to the specs directory. Want it to write to the PRDs directory instead? Simply update the static variable, save it, and you're done. No need to hunt through the entire prompt updating references. Notice the time saved by maintaining a single static variable referenced throughout. Notice, too, how easy this is to understand.

Great prompting is great communicating. We're communicating efficiently with ourselves, our future selves, our team, and our agents. Two sections tell you exactly what this prompt accomplishes.

### Instructions: Supporting the Workflow

The instruction section appears next. How does this differ from the workflow? The workflow provides the step-by-step play of exactly what you want your agent to do. In tools like Claude Code, agents often create concrete lists in their to-dos or plans that map directly to your workflow. This structure aligns perfectly with modern agent coding tools.

The workflow delivers a play-by-play sequence of desired actions. The instructions provide surrounding information about individual workflow steps—an excellent place to add auxiliary information on how your workflow should function. Often, you can combine these approaches, creating nested bullet points beneath workflow steps. In upcoming prompts, you'll see this pattern exactly. But instructions allow you to quickly append useful information that aids the workflow.

Instructions rank alongside the report section: similarly useful and similarly challenging to use. It's a bulleted list of additional information supporting the workflow—not ultra-difficult to implement, but often unnecessary when the workflow alone suffices. These represent two distinct patterns, particularly important when discussing system prompts versus user prompts. Instructions prove more valuable for system prompts, while the workflow excels for reusable agentic prompts, providing the actual play-by-play you want your agent to execute repeatedly.

### Context Mapping

The prime tier list prompt introduces another section with no metadata. Notice the format: title, purpose, then codebase structure—a distinct section. The workflow grows slightly more complex, followed by a simple report.

The codebase structure section (really a context map, though engineers typically call it codebase structure) serves a specific purpose: you're not instructing your agent to read these files, but providing a quick map of where files are located and what the structure looks like. For the prime tier list, we're priming against a specific application part, specifying exactly what each file does at a high level.

Our previous prime command ran those files, but now we clear that and prime the tier list. The tier list executes not on those files, but on the specific files we've designated in the workflow. We read these files exclusively. We strengthen our language with the information-dense keyword "important," which carries more weight with agents and their underlying models. We're reading only these specific files, but our agent now possesses—thanks to our prompt engineering—a map for quickly finding relevant files. Instead of manual searching, running additional tools, or consuming extra tokens, it has a quick, simple map.

Codebase structure ranks just below metadata: C-tier usefulness and C-tier difficulty. Agents can perform this mapping themselves, but the benefit lies in speed—it accelerates agent comprehension.

The interesting development appears in our workflow. Examining it via regex reveals a more developed list. Your workflow can be as detailed as necessary. We still maintain our numbered list, but beneath it we're adding granular details—even lists within lists. This pattern is common in prompts where workflow steps contain substantial information. The principle: keep these clear and concise. We could potentially refine this section, perhaps converting it to an instruction set, but it functions well as-is.

At the end, in step six, we execute what our original start prompt does: boot the application, install dependencies, launch it, open the browser. We're scaling up the value and utility we extract from our prompts through consistent, swappable prompt structures. The workflow prompt wields tremendous power.

### The Input-Workflow-Output Pattern

All prompts stack upon each other, and the workflow prompt serves as an absolute pillar for subsequent prompt levels. Notably, every prompt—examine the build prompt as an example—maintains a consistent structure: inputs, workflow, and output. This three-step pattern offers a reliable framework for designing and building your prompts.

Obviously, all this information matters to your agent, but input and output prove specifically useful for you and your team. We can quickly identify what's coming in and what's going out. We'll invest significant time in the workflow, refining it to perform exactly as intended, but this framework—input, workflow, output—provides a valuable foundation for building great reusable agentic prompts consistently.

## Level 3: The Control Flow Prompt

At the next level, we continue building upon our existing sections. Opening build.md reveals something happening on line 17: flow control. Level three introduces the control flow prompt.

We're enhancing our workflow section with new capability. Remember: every prompt format centers on the capability it offers you and your agent. The control flow prompt enables conditions, loops, and early returns. If no path to plan is provided, the agent immediately stops and requests it from the user.

We can test this quickly. The prime tier list has finished, providing a detailed layout for this specific feature. Clear it out and invoke build without passing a path to our plan—the variable is absent. The agent immediately recognizes this and halts, equivalent to an early return requesting feedback. We need information. We cannot proceed without a path to plan.

This represents the simplest version of flow control within your prompts. Imagine this growing far more complex. The most popular extensions include conditionals and loops.

### The Create Image Prompt

The create image prompt runs the same understanding workflow. Collapse everything to level two and analyze the prompt top to bottom: metadata, title, a somewhat informal purpose (though functional), and variables. We employ new syntax with static variables accompanied by bullet points.

We have word plus colon, giving us our variable format. Several variables utilize Claude Code's positional arguments. For example: `/create-image` followed by a file containing image prompts, then a number as positional arguments. Three additional static variables appear—very powerful for agents and for communicating value to your future self and your team.

The image output directory can be quickly located where referenced. We can swiftly update the model we're using to generate images, adjust the aspect ratio, and so forth. We can add arbitrary static and dynamic variables here. The interesting development appears in the workflow.

In control flow prompts, you can request loops using natural language. We're saying "important: then generate number of images" (referencing a variable) "using the image generation prompt following the image loop below." We employ an XML block to add structure, communicating to our agent when the image loop starts and stops—also communicating clearly to our team where the loop exists. We operate in natural language, wanting consistent patterns throughout our prompts for the trifecta.

More workflow details follow: use this tool, pass an argument, use aspect ratio, wait for completion—throughout, we're referencing our variables. This grows increasingly complex. We're accomplishing more with our prompts. The report section shows we're generating images at scale in a loop.

### Ranking Control Flow

The control flow prompt proves slightly more powerful and useful than the workflow prompt, though it requires more skill. Thinking through and analyzing the workflow step to understand the control flow demands deeper expertise. For these reasons, we place this in A-tier usefulness and B-tier skill requirement.

The edit image prompt displays a similar format. Nothing changes in our consistent process: metadata at the top, title, purpose, variables, workflow. Notice: no report section. Every section is swappable—use them only when needed. If you don't care about the output format (remember the three-step workflow: input, workflow, output) or if you don't need incoming variables, omit those sections. This is key to writing great prompts: add only what you need. These are composable pieces of your agentic prompts.

The edit image has no output format. Opening everything reveals variables and a workflow with an embedded loop. We also have a stop command and several conditionals: if the token isn't available, exit immediately; if the B64 command isn't available, exit immediately. This prompt performs a specific task in a specific workflow exceptionally well, with a loop embedded.

## Level 4: The Delegate Prompt

At level four, we encounter the delegation prompt—a prompt that launches other agents to perform work. Notice how distinct each prompt format is, offering a new advantage, a new capability. The key section here: if you're delegating, you'll want variables to pass into your sub-agents.

Opening parallel sub-agents, we follow the same process: collapse, examine the format. There's our metadata, title, purpose. This workflow should feel repetitive—and that's precisely what you want. You don't want novelty every time you open a prompt. That consumes engineering cycles and diminishes your ability to work through more engineering tasks and generate value.

You want to think less about problems solvable through consistency. Consistency is the greatest weapon against confusion for both you and your agent. This is a key idea in both elite context engineering and this lesson: we're communicating clearly, aiming to reduce confusion to the absolute minimum.

As you write these prompts, ask yourself: if I handed this to a coworker, could they complete this work top to bottom? If true, you've probably written a high-quality prompt. Now imagine handing them ten additional prompts—don't change the format each time. This is why consistency matters so profoundly.

### Parallel Sub-Agents

Opening variables in our parallel sub-agents reveals two positional dynamic variables: prompt request and count. You can quickly understand this prompt by reading the purpose: "file workflow launch count in parallel to accomplish task detailed in prompt requests." The workflow provides a step-by-step play with nested bullet points—nothing fancy, very consistent, simply referencing variables throughout.

What's the key advantage of this agentic prompt format? We're handing off work to compute. We're having our agent fire off agents. Many approaches exist here. If you've completed the elite context management extended lesson, you know there are only two ways to context engineer R&D, and here we're using the D of that framework.

We can invoke this. Clear this agent and run `/parallel` with a prompt: "Extract information we'd want to add to our claw.md that we want all future agents to know about. Essentials only, present bullet list. Do not modify the file directly." We want five instances. This is the advantage of spinning up more compute: bump up the number of instances, the number of agents you want to fire off to accomplish a task.

### Non-Deterministic Advantage

What's the advantage of running a prompt like this? LLMs and agents are non-deterministic. When you ask multiple agents to do something, they return different results. We're firing up five agents, each focusing on a different aspect of the codebase. Our primary agent instructs the sub-agents—our primary agent becomes the prompt engineer for our sub-agents. This is where things become truly intricate. Agent delegation is powerful but challenging to use.

The delegate prompt earns S-tier usefulness while requiring A-tier skill difficulty. This is an advanced technique because we're managing multiple agent instances and writing prompts that write prompts. We're specifically instructing our primary agent. In step two of our workflow, we're saying: "Design agent prompts. Create detailed self-contained prompts for each agent. Include specific instructions. Define clear output expectations." We're building out that input-workflow-output three-step structure for our primary agent to pass into all sub-agents.

This prompt wields tremendous power. We're spinning up more compute that can itself build entire prompts and agents. This is a profoundly powerful concept—the future of engineering. Once you build great agents that perform for you and accomplish work, the next question becomes: how many agents can you spin up? How much work can you do? How much compute can you leverage?

This is what TAC is fundamentally about—a major theme inside TAC: spinning up these pipelines of agents that operate with and without us via out-of-loop systems. All this prompt engineering, all this agentic prompt engineering, is about tapping into that better than anyone. For this reason, it's S-tier: ultra useful, ultra valuable, yet very difficult to use. You need consciousness about information flow between your agents.

### Load AI Docs Delegation

The load AI docs prompt demonstrates another delegation approach. Again, with great agentic prompt engineering, we collapse everything, understanding things one step at a time: metadata, title, purpose, input, workflow, output. Every single time. Consistency beats complexity. Consistency accelerates you, accelerates your team, and accelerates your agents when you find the working formula. And I'm handing you the working formula right now with these prompt formats.

Variables show one static variable for this delegation prompt. We'll delete old docs after 24 hours. Our AI docs contain documentation for our agents. Opening it, our agent has deleted these files, now reloading them as they were older than 24 hours. Same pattern: we loop, with an explicit, information-dense keyword we can reference throughout our prompts. We're having our agent call a sub-agent directly.

Five doc scraper agents scrape documentation and write to new files. Documentation flows in one by one. We're delegating, offloading—once again, this is the D in the R&D framework of elite context engineering. Ultra powerful. Then we have a simple but specific report format. Our primary agent will return in this exact format.

### Background Prompt

The background prompt illustrates how every previous level stacks up. You can pull in whatever levels you need into the highest level required to solve the problem. Here we're delegating agents while using control flow—several conditional statements appear in our workflow. This runs in the most powerful section of all your prompts: the workflow.

Our agent returns in that exact format—the AI docs report. Success or failure, URL, markdown path. We have massive control over this agent. We knew exactly what would happen when we invoked this prompt. This is key for transitioning to out-of-loop agentic code: you need to know what your prompts will do. The best way to know is to be consistent and, of course, to test and prove out your agentic prompts.

The background prompt, once again (and I hope you're growing familiar, even slightly weary of this workflow—that's how you write great prompts at scale repeatedly for you, your team, and your agents: stay consistent), shows metadata, title, purpose. We're using that direct language: "Run a Claude Code instance in the background to perform tasks autonomously while you continue working." Purpose clearly defined in one or two sentences.

Variables reveal three dynamic variables. Instructions contain auxiliary important information for the workflow. The workflow is the step-by-step play. This one grows really complex because we start detailing exactly how to kick off a brand new agent via the CLI, actually updating the system prompt in a massive way. We'll discuss system prompts versus user prompts momentarily. But this agent will kick off another primary agent in the background, which will continue reporting to a report file as it works in the background using whatever model we specify.

This is the delegation prompt: having your agent pass off work to other agents.

## Preparing Your Agents

This is our agentic prompt tier list. All the significant value resides in the top left corner: the workflow and the workflow prompt. I highly recommend pushing to at least B-tier level. Reaching B-tier in your agentic prompt engineering skill captures most of the value.

A key item I stress inside TAC: you'll want to push to understand how to write template meta prompts. Once you unlock this S-tier skill and usefulness level—these template meta prompts at level six—your agentic engineering velocity scales up dramatically for you, your team, and especially your agents, because you've templated your agentic engineering.

But really, 90% of the time for most engineers, all we need is one of the seven levels of agent prompt formats. Then we need to learn how to interchange the right sections—the swappable sections, the swappable Lego blocks—throughout the prompt you're writing, with the most important section by far (I'm highlighting this repeatedly for a reason) being the workflow: your step-by-step play for your agent, for your agentic prompt engineering.

## The Two Big Ideas

Two foundational concepts recur throughout this lesson:

First, communicate extraordinarily well to your agents for optimal results.

Second, use consistent prompt formats and their interchangeable sections so you can CRUD (create, read, update, delete) reusable prompts for you, your team, and your agents. You want to manipulate your prompts at light speed at the right level. Usually level three or level four suffices. Build that great, powerful workflow step inside your prompts.

Be consistent with your reusable prompts so you can invoke them repeatedly, reducing confusion for your future self, your team, and most importantly, your agents. Your agents can reason about many different prompt structures, but engineering isn't just about your agents. It's not just about you. It's not just about your team. You need to hit the trifecta—the stakeholder trifecta for the age of agents.

There's a new user, a new profile, a new type of consumer of the work you're doing: your agent. We need to think about this trifecta. Consistency is king when it comes to writing great agentic prompts.

## Beyond the Basics

Other sections exist that we didn't explore. Other ways exist to express these sections. That's not what's important here. The key idea: you have swappable Lego blocks that are the sections of your agentic prompts, each with distinct uses and capabilities that you can leverage for repeat success in your agentic engineering.

The prompt is the fundamental unit of engineering. Invest in your prompts for the trifecta to achieve asymmetric engineering in the age of agents. Context engineering is vitally important, but your prompts kick off and dictate everything you do.

## Your Next Move

Here's what I recommend you focus on next:

If you haven't finished TAC, finish TAC. That is more important than context engineering, more important than agentic prompt engineering. It establishes the future of engineering, helping you move toward becoming an irreplaceable engineer in phase two of the generative AI age.

Next, I recommend advancing to the third level and diving into writing customizable agents for your domain-specific use case, for your domain-specific problems. Check out the Claude Code SDK mastery to build your own specialized agents.

TAC is about scaling what you can do with agents—getting out of the loop, exiting this simple back-and-forth prompting experience so you can scale by building pipelines that do one thing extraordinarily well.

Use these seven levels of agentic prompt formats to guide your agentic engineering. Use the sections beneath them interchangeably and focus on extracting value from your agents. Start at the lowest level—throw it into a level one ad-hoc high-level prompt—then when you need to, scale it into a workflow prompt. This is where you'll generate the majority of your prompt output: the step-by-step play of what you want your agent to do.

After that, you can scale up and stack your capabilities, leading all the way to the powerful template meta prompt—the prompt that builds the prompt, the agent that builds the agent. This is how you scale hard and fast into the age of agents.
