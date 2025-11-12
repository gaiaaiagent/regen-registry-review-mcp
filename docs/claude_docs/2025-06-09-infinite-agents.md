# Breaking Claude Code: The Infinite Agentic Loop

*A demonstration of scaling compute through parallel AI agents*

## The Discovery

Engineers, I think I just broke Claude Code—the best agent coding tool in the game. The amount of value you can create in a single prompt is incredible. The amount of value you can create in two prompts is insanely mind-blowing and not well understood.

Here I'm running a Claude Code infinite agentic loop. Inside this five-directory codebase, I'm generating infinite self-contained UIs that self-improve on each iteration. If I open up the commands directory, you can see I have this `infinite.md` prompt that's fueling this Claude Code agent, which has fired off five sub-agents. You can see them all working here live right now. This one just wrote 1,000 lines. We have another thousand lines here. And you can see, this is wave two with five agents in parallel, and more are getting queued up right now. You can see it just finished wave two.

How can just two prompts make Claude Code run forever? You can see wave three is getting set up right now—iterations 16 through 20. If we scroll down here, you can see a new set of iterations loaded up. This task list is just going to keep running.

## The Infinite Agentic Loop Pattern

Back to the question: how is this possible? This powerful pattern is fueled by just two prompts. It's fueled by the infinite prompt that we're going to explore in detail, and of course, your spec—your plan, your PRD. If we open this up, you can see I have just three specs where we're inventing some new UIs. I have three versions of them.

Let's go ahead and kick off another infinite agentic loop. While it's dedicating work to multiple sub-agents for us, we can talk about how you can use this to generate a virtually unlimited set of solutions for a specific problem. I'll create a new terminal instance, fire up Claude Code, and update the model. I want to fire this off on Opus—clearly state-of-the-art—and then we'll use the infinite custom slash command.

I'll type `/infinite` and you can see we have the infinite agentic loop command. Now we need to pass in a few variables. The first parameter is the plan we want to fire off. I'm going to get the path to this and paste it in. You can see we're still running in the background—agents 16 through 20 still running. It takes a new directory, so our first agent is operating in the source directory. Let's set this directory to `source_infinite`. And lastly, it takes a count or the information-dense keyword "infinite." We're going to pass in "infinite," of course.

## Firing Off a New Wave

Now we're going to have two agents running in parallel. Our second infinite agentic loop is starting to fire off here. If I close this and open up the second directory, you can see that got created. In our plan, you can see Claude Code writing up this plan for infinite generation.

We need to dive into the prompt—this is the most important thing. It's the pattern here that's so valuable. Let's understand how this infinite agentic loop works with our two-prompt system, and then let's talk about how this breaks down. If you've been using long-running Claude Code jobs, you already know exactly how this breaks. There's a natural limit that we're starting to bump into over and over, and it completely breaks this infinite agentic loop workflow.

Let's start with the infinite prompt. We have our initial command and then a really important part: the variables. With Claude Code custom commands, you can pass in arguments like this and they'll be placed in position. Our first argument gets replaced with `spec`, then we get `infinite_source`, then we get `infinite`. These variables get replaced throughout the prompt, and the Claude 4 series is smart enough to know that it should replace the variables we placed in here with the actual variables passed in. You can see the spec file throughout this prompt and the output directory as well. Then we have count, which is going to be one to n or, of course, infinite.

In this first step of the infinite agentic loop prompt, we're reading the spec file. This is a really interesting pattern: we're treating prompts—our specs—as first-class citizens that can be passed into other prompts. This is a really powerful technique. There's a lot of untapped value here. We explored this a little bit in our parallel agent decoding with git work trees video we put out a couple weeks ago. What we're doing here is a little different because we're running infinitely and we're generating a single file—although to be completely clear, we could rewrite this prompt to generate any set of files.

So we have argument parsing. Our agent is going to first read the spec file to understand what's going on. Then it's going to understand where it's going to output all these files. Then it's going to fire off parallel agents in groups of five. This is going to speed up the output of our agent. Our first round files have already been created for that infinite loop.

And this is really important: we're actually specifying what each sub-agent receives. It's getting the spec, it's getting the directory, it's getting its iteration number—you can see they all have their own iteration number—and it's getting their uniqueness directive. We want these all to be unique. We want each example to grow on each other. This is really cool. We're actually passing in a prompt for our sub-agents. That's what's getting written out here—a concise prompt for the sub-agent.

Then we have phase five, just kind of continuing down the line—infinite cycle. And then I have this line in here (I'm not 100% sure if this works; I don't know if Claude can see the end of its context window, but it seems to work): "Evaluate context capacity remaining. If sufficient, continue with next wave. If approaching limits, complete and finalize."

## The Breaking Point

This is where this pattern completely breaks Claude Code. You can't keep running this—it's going to hit the context window. Of course, we don't actually have infinite context windows. This will generate some 20 or 30 files or sets, depending on your setup. Then we're going to just continue along the lines here. There are some details at the bottom. Not all this matters.

As you can see, I am writing these prompts now with agents. We're entering this interesting zone where you want to be writing prompts that write the prompts for you. You can see both of our lists here are continuing to expand. We now have 10 hybrid UIs inside of `source_infinite`.

## Reviewing the Claude 4 Opus UIs

Let's go ahead and actually look at what the heck is getting generated here. Just to briefly describe the prompt that we're passing in: we have our spec file that we're passing into our infinite agentic loop prompt. We're saying "invent new UI v3." What we're doing is creating uniquely themed UI components that combine multiple existing UIs into one elegant solution. That's basically it—that's the key idea of what we're doing here.

I'm using UI as an example just like with our parallel agent decoding video with git work trees. UI is just the simplest way to show off a powerful pattern like this. We're specifying the naming scheme here with the iteration, and then we have a rough HTML structure that's all self-contained into a single file.

Let's open this up and see what this looks like. If we open up a terminal and get the path to one of these files, we can open it in Chrome. Check this out: Neural Implant Registry—a classified database access terminal. Very clearly it's just a table, but it's got a really cool unique theme to it. We can search—nice, Echo CerebraMax. We can search across columns, we can sort. That looks great. Status filters, active risk level here.

I'm constantly impressed with the caliber of code that the Claude 4 series is producing now. It's mind-blowing that not only was it able to launch off this, it did five versions at the same time. You and I, we really have access to premium compute that we can now scale up infinitely with this pattern.

Very cool UI. Let's go to another example: Adaptive Flow UI Liquid Metal. Obviously some UI issues here, but this is just a simple UI. It looks like nothing special. Oh, interesting—that just adapted. Very interesting. I did not expect that. It's actually creating additional UI here based on what we type in. Oh, I like this kind of error state. Look at this—it's errored right here. This is not a true email address. And we do get email autocomplete here. Very cool. And you can see we also have a progress bar here at the bottom. In particular, I like this active state.

Let's look at another UI that was generated for us. Again, this is all happening in parallel in the background. This compute is solving this problem for us at scale, creating many, many versions. What do we have? Some 20—yeah, 50 versions now with two parallel infinite agentic coding agents. This is crazy. It's really cool, very powerful.

Obviously, the real trick with this pattern is going to be pointing it at a problem where you need multiple potential solutions. That's the real trick. Everything we do on the channel, you need to take it and point it at a problem. There's a ton of value here that you can get out of this interesting two-prompt infinite agentic loop pattern.

We're starting to compose prompts. We already know that great planning is great prompting. And maybe that's an important thing to really highlight here. We're generating all these cool UIs. We can continue to just look at these—so interesting. We can look at UI after UI. Look at this one—so interesting. Look at all these just interesting, creative UIs. There's a lot of likely garbage here, but there's a lot of value here as well. We're literally inventing new UIs as we go along and new UI patterns. We can just keep going. Check this one out. How cool is this?

So this is the power of an infinite agentic loop: multiple solutions, just going to keep going, keep firing. We're using a ton of compute here. You can see we're launching another wave of agents inside of this agent. One tool call, 30k tokens, 30k, 30k, two minutes each. These are shorter jobs. I've run jobs that are 30 minutes plus, and you can fire them all off in a subtask. It's so incredible what we can do with Claude Code and with the right pattern—the right prompting patterns that let us scale compute.

## Great Planning is Great Prompting

Really interesting stuff there. What's important? What's the signal here? A couple things to call out: You can pass prompts into prompts. You can specify variables at the top of your files. You're likely going to want multiple variables that control what happens and what gets done. We have this infinite information-dense keyword. This triggers our agentic coding tool to run infinitely. Of course, you need to phrase things, you need to be more specific with how that works. You can start with this prompt and modify it, build it, make it your own.

A couple more key ideas. This is a classic one: we have been using plans for over a year now on the channel. And every Principled AI Coding member knows that great planning is great prompting. I sound like a broken record bringing this up for over half a year now, but there's a reason for it. We know that tools will change. We know that models will improve. You can't fixate on these things. Claude Code is the very clear winner right now, but it won't always be that way. And we're going to get another model. All that stuff changes.

What doesn't change is the principles of AI coding. Many of you know this is why I built Principled AI Coding. Sorry for existing members and for engineers that have already taken this, but the repetition is probably important anyway. It's so important to realize that you want foundational skills that don't change with the next model, with the next tool.

The plan—great planning is great prompting. This is principle four or five. This is so relevant. It's increasingly important. Why is that? It's because we can now scale our compute further, but how we do that is always about communicating to our agents.

Claude Code is the best top agent right now for engineering. Why is that? It's because it operates in the highest-leverage environment for engineers: the terminal. Anything you can do, Claude Code can do. And part of me wants to say "better." We'll debate that more in the channel as time goes on. It's definitely getting there. But you can see we're generating yet another batch of agents here. We have this Ocean File Explorer—very interesting.

But anyways, refocusing here: the spec is super important because this details what we want done inside of this infinite agentic loop. We have this really cool pattern where we're treating our prompts like you can treat functions in certain languages—you can pass the function into a function. That's what we're doing here. The same idea transferred to this domain of agentic coding and really prompt engineering. We're taking a prompt, passing it into a prompt.

The magic is obviously in the pattern of this infinite agentic loop, but it's really in what you ask your spec to do. It's what you ask your agent to do. There's a ton of value in this pattern. I hope you can see how powerful this is.

## When to Use the Infinite Agentic Loop

When do you want to use something like this? Look at all these UIs we have generating. We have two agents going back to back here. Very cool.

You want to use a pattern like this—it's very similar again to our parallel agent coding with git work trees. There we cloned our entire codebase into the work tree directory so that multiple agents can work on their own directories. Link for that video is going to be in the description. I highly recommend you check that out. But what we're doing here is so fascinating, so powerful. We're scaling our compute. We're solving a specific problem with many variations of how it can be solved.

So when do you want to use the infinite agentic loop? You want to use it when there are multiple potential solutions that you want to explore. You want to use it when you're working on a hard problem that you don't know the answer to and you think that having many versions will help you get closer. And so this is all stuff you would encode in your lower-level prompt that the infinite agentic loop prompt will execute on.

And you want to use this when—this is a really big idea, this is like what lead researchers are doing—when you want to set up a self-improving agentic workflow that is trying to achieve some verifiable outcome that increases over time. We've all heard about reinforcement learning. You can take that idea of reinforcement learning, you can take that idea of self-verifiable domains, and you can embed it in an infinite agentic loop prompt like this. This is a really big idea. More on this on the channel in the future. We don't have enough time to cover that here right now, but that's just really important to call out.

Those are kind of the three big use cases for this that I can find right away. I'm sure if you dig into this, if you start using this, you'll find more use cases.

## The Reality Check

Pretty incredible stuff. We have two agents running in Claude Code. You can see I am hitting the limit. I'm breaking Claude Code right now. We're running just straight out of Opus credits. I am running on the Claude Code Max Pro subscription—whatever the top tier is. I'm going to go ahead, I'm going to stop these agents. I need a few more credits for today to do some other engineering work.

You can see we're literally infinitely generating tons and tons of solutions to this problem. That's the trick here. That's the real value proposition of the infinite agentic loop: You want multiple versions, multiple potential futures of an answer to a problem that you have. UI is obviously just the simplest one. That's why I've showed it here a couple times on the channel.

We can just keep looking through these different user interfaces with different ideas and themes blended together. Check this one out—very smooth, very cool. And this is all happening in the background with compute. We're scaling up, doing this again. We're scaling up our compute even further beyond. That's what we do on the channel every single Monday.

## The Path Forward

Check out Principled AI Coding. As many of you know, I am actively working on the second phase course. This is the foundation—I highly recommend you check this out. What comes next after AI coding is, of course, agentic coding. I'll have more details on the next generation course as we move closer to the release date. Looking at a Q3 launch, so stay tuned for that.

This is a really powerful technique. Try this. Don't ignore this, please, for your own good. It's completely free. A lot of the stuff I'm doing here obviously is all free for you guys. Link in the description to this codebase. I'll save some of these generations so you can really see and understand how this works. But it's really about the infinite prompt. Take all this stuff, make it your own, improve on it, solve your problem better than ever with compute.

Big theme on the channel: to scale your impact, you scale your compute. Tune in. Make sure you subscribe, like, all that good stuff. Compute equals success. Scale your compute, you win. You know where to find me every single Monday.

Stay focused and keep building.
