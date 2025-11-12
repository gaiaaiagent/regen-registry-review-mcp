# Claude Code Multi-Agent Observability: A Complete Architecture

## The Scaling Challenge

What you're about to see is simple and powerful. Running a single Claude Code agent is just the beginning. Once you realize this potential and start scaling up the number of agents you have shipping for you, you quickly run into a massive problem: there's too much to keep track of.

When it comes to multi-agent systems, observability is everything. With Claude Code hooks sending events to a minimal client-server architecture, you can see everything. This is a concrete approach to Claude Code multi-agent observability that lets you scale up what you can do with not just one Claude Code instance, but three, five, ten, and beyond.

## The Multi-Agent Observability System

The system takes events in from every Claude Code instance running—it doesn't matter if they're running subtasks, planning, building, web scraping, web searching, conducting deep research, or calling MCP servers. Every event is getting tracked and traced into this simple multi-agent observability application.

Here's what the application architecture looks like: Multiple agents fire their own respective Claude Code hooks. Each one of these hooks hits a Bun server which stores data to a SQLite database for persistence and simultaneously uses websockets to stream the events right to the client. So no matter where your agents are running—if you're running on multiple devices, if you're running five, ten, or more agents—every event's going to get streamed in.

You can see different applications streaming in events with different Claude Code session IDs getting recorded. And every tool call, every hook, every event type is getting recorded. When agents need input, notification events arrive instantly. You can go back to the terminal and see which one needs attention. Stop events come in, tasks complete, and custom features get refined—all visible in real-time.

## The Power of Real-Time Visibility

This is the power of observability. As you scale up your agents, as you specialize and build agents into your agentic workflows, you want to understand what they're doing. Once you start using Claude Code and agentic coding tools, you realize that you can do a lot more by just adding agents, by scaling up the number of agents you have working for you at any time. This is also great for specialization and cross-app usage.

## Application Features and User Experience

At the top of the interface, there are filters. Operating out of multiple codebases simultaneously—like the Infinite Agentic Loop codebase and the Claude Code Hook Multi-Agent Observability codebase—you can filter down to one or more of these codebases, or set it back to all sources. Text-to-speech integration from previous work lets agents notify when they need input or when they're ready for more work.

Session IDs detail the exact Claude Code instance, and event types show all the current available Claude Code hooks you can tap into. A stream of every single event flows through the system. You can easily filter down to see all stop events, post-tool use, notifications, and so on.

Something really cool emerges: a live activity pulse of all the events coming in in real time—all the work agents are doing across every application, across every Claude Code instance. The Infinite Agentic Loop agent might be one of the heavy hitters, with five subtasks operating in parallel, so many events stream in from it.

## Live Activity Monitoring

When an agent builds out a plan, you can implement that plan in real-time. The live activity pulse is great for seeing all the events coming in live throughout all agents, providing a high-level breakdown of the system's work.

The agent event stream shows all events streaming in—potentially dozens of events that cut off and refresh as you scroll. Each event shows the application it's coming out of and the Claude Code session ID. For good UI/UX, there's color coding on the app and session ID—the system hashes the incoming app name and session ID so you can consistently see which agent is posting.

## Intelligent Summarization

On the right side of each event, something really powerful appears: summarizations of the work done. Every event coming in—before the Claude Code hook sends it off—runs a summarization prompt using a small, fast model. Specifically running Haiku to get a summary on all the events that matter. For pre-tool and post-tool events, you want to see what is going on and be able to read at a glance, without clicking in to examine the exact payload (though you can).

For example, an event might show: "Infinite Agentic Loop writes HTML file for MedScan Pro clinical dashboard at a specified project path." That's the post-tool use. Post-tool use fires after the tool has run, while pre-tool use appears right before. These events are tied together—pre-tool, post-tool, sub-agent complete—all from the same agent running in the same codebase.

## The One-Way Data Architecture

This architecture uses a one-way data stream, keeping things really simple. Everything flows from Claude Code agents through their hooks to the server. When they hit the server, they're stored in a SQLite database, and then right after they're saved, they're streamed to the front end. Live events come in constantly.

In the activity pulse, you can view a one-minute feed, or expand to three minutes or five minutes to see a larger collection of all these events at a larger time frame. Every individual line represents the actual agent that did the work—the session ID hashed into a color.

You want your observability to be fast, easy, and quick. This is why we have the summaries. Scrolling through reveals summaries for post-tool use. If you want to open a sub-agent stop event and see what that looks like, you can see the exact payload for that Claude Code hook.

## Deep Event Inspection

Everything comes together in this one-way data flow architecture where Claude Code uses its hooks after it finishes events. These events then send information to the server. The server takes those events, stores them in SQLite, and then streams them to the client. This one-way data stream keeps things really simple. Every agent is responsible for summarizing their work in the Claude Code hook before they send it off.

This is fundamentally important: If you don't measure it, you can't improve it. If you don't monitor it, how will you know what's actually happening? If you want to scale up your work, if you want to scale up your agents, you need to know what they're doing. It's fascinating to watch this data flow come in and really trail what the agents are doing, to understand how your agentic coding tool actually works.

## The Power of Claude Code Hooks

All of this is powered by Claude Code hooks—an incredible feature that lets you build on top of and understand what's going on in Claude Code's lifecycle. They give us deterministic control over Claude Code's behavior and let us steer, monitor, and control our agents.

This is a big feature worth covering repeatedly. While previous videos covered Claude Code hooks in a more fundamental way, this video puts Claude Code hooks to work for multi-agent observability. If you want to do more, if you want to scale up your agentic coding, if you want to become an agentic engineer, you're going to want multiple agents working for you, accomplishing tasks across all of your code bases.

As you scale that up, another problem emerges—solutions create problems. Another problem emerges where we need a way to track and understand what is going on. The cool part is you don't need to open up terminals or instances to know what's going on anymore. You can keep them closed and just look at what's happening in the observability interface.

## Why Multi-Agent Observability Matters

If you're scaling up your impact, if you're scaling up your engineering work, you need to understand what's happening, where it's happening, and what agent is doing the operation. Because eventually something will go wrong. A system will not do the right thing. And then it's going to be essential to have a trace throughout your system that you can fully control.

This isn't claiming to be the only way to do it—just a way you can start with multi-agent observability. Something cool about the stop event: if you click into it, you can see the entire chat transcript. An agent might have 500 messages, and if you click into this, you can search through them and understand exactly what was happening at a glance.

The stop event is the perfect time to copy the entire log via the transcript path and use it to operate on the work that happened. For instance, if you wanted to find all the read commands, you can quickly filter all the reads and understand where that's happening. You can do the same with all the glob usage, assistant responses, and more.

## The Learning Imperative

Observability is ultra-important. Keeping track of what your tool can do teaches you, the engineer, what you can actually do with these tools. Monitoring lets you tap into the potential that your tool can have.

As features ship—like mobile versions—you can come in and tweak event streams, adjust default sizes and heights, and refine the interface. But the real question is: How does this actually work?

## Codebase Architecture: End to End

From end to end—Claude Code agent to hook to server to client—you can see a clear structure. As covered in previous videos, there's a Claude directory with a newly added hooks directory. Opening up settings reveals what's going on, and it all starts from the hooks.

All events get tracked. Looking at pre-tool use as an example, another hook has been added. So instead of running one hook, we're running two hooks. There's a pre-tool use specific script, using Astral's UV single-file Python scripts—a great way to isolate code and create standalone scripts.

The new script in this directory has a send event method with several arguments: the name of the application we're operating in, the event type, and a summarize flag. The summarize flag creates the summaries using the small, fast Haiku model.

## Hook Implementation Details

The send event method runs in all hooks: post-tool use has it, pre-tool use has it, notification has it, stop has it, sub-agent stop, and pre-compact (the new Claude Code hook that runs right before you compact). They're all running it, all passing in their own information. This enables the script to be dynamic and to handle every one of the hooks.

What happens in send event? There's the event data—whatever JSON payload you want to send to the server. The local server running captures events. The structure includes apps, client, server, and demo directories. The server receives all these events.

A pattern emerges that gets adopted in every video and every codebase: the actual application is wrapped inside our generative AI scaffolding. We're starting to build out an agentic layer around the codebase, and there are essential folders that make up that agentic layer. More of these agentic directories will be discussed in future content. This new layer around your codebase is going to change the way you engineer forever, but you need to know where to put the right thing.

## Server and Database Architecture

In the apps section, the server contains the SQLite database—nice and portable. In the source, there's a Bun server. The Claude Code event gets kicked off no matter where Claude Code is running. The hook fires off an HTTP request with the event, so it can go anywhere you want it to. That's what the send event is doing—that's the Claude Code and Claude Code hook side of things.

The event then gets passed off to the server. Opening up the server and running a quick collapse reveals a simple manual Bun server with a `/events` endpoint. The system inserts this into the database and then broadcasts the event to the websocket client. Nice and simple.

## Client-Side Implementation

The client side has a use-websocket implementation that mounts and handles the websocket—classic stuff. This example uses Vue.js, but every frontend framework has their own version of this code. You can easily use an agent with a powerful model to completely convert this to whatever frontend framework you want. These things don't matter anymore. Frameworks are irrelevant when it comes to raw productivity. Your agent knows all of them.

The key is the connection: after it's connected, there's a websocket on-event handler taking all events, slicing them (because we don't want to overflow with too many events), and adding them to a reference. This reference becomes available via the composable hook use-websocket, and then the frontend consumes this. In `app.vue`, the websocket event gets used, and then events are passed to anyone interested in the components. The rest is frontend component work—nothing special for observability systems.

## The Principle of Simplicity

The key is keeping it simple. You want to put something up right away. The quickest way to do that is a one-way data flow from your Claude Code agents to your server. The server stores to both the SQLite database and broadcasts to the websocket client.

Hopping into the database, you can see exactly what this looks like: all the data being stored, with source app, session ID, event, and the raw payload visible. Some stop events will have the entire chat attached. This is what the data structure looks like at a high level, and the system emits all events to the frontend.

## A Starting Point, Not a Prescription

The readme explains how to get the setup on your own. The goal here isn't to prescribe exactly how to observe your agents—it's to show what you can do, to help tap into potential with this powerful generative AI technology. This codebase will be available as a starting place to understand what you can do with Claude Code, the best agentic coding tool in the game.

We're taking the big three principles of agentic coding and starting to put them to work. The key is that as you scale up the number of agents doing work for you—specialized agents working on specific codebases, solving specific problems very well—you want a way to observe them. You want a way to monitor your agents. You want a concrete way to monitor success.

## The Essential Truth

None of this generative AI technology matters if you have no idea what's going on. If you don't know how to steer, correct, and control your agentic systems, it's as good as garbage.

The summaries are so powerful, so useful—just quick, high-level insights from small, fast language models. This is a great use case for these small, fast, cheap models. Sending a thousand of these events in testing costs less than 20 cents on thousands of events. This is where small, fast models really shine: these one-off quick summaries, these quick prompts.

## Scaling Beyond Single Machines

Once you start scaling up from one agent running on your machine to multiple agents running on your machine to multiple agents running on different machines, you get something really incredible. You start pushing into true off-device agentic coding. This is the future of engineering. You want to be on this trend. You want to be writing this. You want to be pushing toward this.

Prompting back and forth, one prompt at a time, is not the way to engineer. It's a great place to start. It's a terrible place to finish. Things are going to continue to progress, and we're going to continue to progress beyond the curve.

## Looking Forward

We're always looking at where the ball's going, not where the ball is. Pay attention to what your agents are doing. Understand what your agents can do. Use multi-agent observability. Start spinning up multiple agents focused on one specific task for you. Specialize your agents and then scale them up.

The big idea here is that we want to get out of back-and-forth prompting mode and move into fully trusted, fully agentic, programmable agentic coding. Everything being done in this space is pushing towards something big—hence the Phase 2 Agentic Coding course coming in the next couple of months. What comes next is going to be truly mind-blowing.

Stay focused and keep building.
