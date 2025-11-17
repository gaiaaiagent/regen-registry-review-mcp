# MCP Server Slash Command Bug Investigation

The specific bug you described—holding enter for several seconds or pressing it multiple times when using MCP server prompts—doesn't appear documented exactly as stated. However, **multiple closely related bugs collectively create this frustrating user experience**, affecting Claude Code versions 0.2.62 through 1.0.93+ across all platforms. The core issues involve argument handling failures and enter key behavior that makes MCP prompts feel broken or unresponsive.

## The primary culprit: optional arguments break enter key functionality

**GitHub Issue #5597** represents the most direct match to your reported problem. When MCP prompts have only optional arguments (all marked as `required: false`), pressing Enter without typing anything **does absolutely nothing**. The prompt appears in the slash command list, users press Enter expecting execution, but the command fails silently. The only way to invoke these prompts is typing at least one character—even just a period—before pressing Enter. This affects **Claude CLI 1.0.73+ on all platforms** and remains an open bug with no official fix.

One affected user described it precisely: "The prompt appears in the slash command list but pressing Enter without typing any arguments does nothing. The prompt can only be invoked by typing at least one character (even just '.')." This bug fundamentally breaks the expected behavior of optional parameters, effectively making them required for invocation despite being designed as optional.

## Arguments disappear when pressing enter

**Gemini CLI Issue #5700** documents another dimension: when users type custom MCP commands with arguments and press Enter, **the command text gets overwritten with formatted argument placeholders**, causing typed arguments to vanish. A user would type `/find lions`, press Enter, and watch it transform into `find --animal=""`, losing their input entirely. This P1-severity bug affects CLI version 0.1.17 on Linux.

Meanwhile, **VS Code Issue #251803** showed that MCP tool prompts with optional arguments would close the dialog entirely when users pressed Enter without input, canceling the entire prompt flow. This has been **fixed in VS Code Insiders**, but the fix hasn't propagated to Claude Code.

## Multi-word arguments compound the problem

Claude Code's argument handling suffers from a fundamental design limitation: **it cannot process multi-word arguments containing spaces**. The system treats each word as a separate invalid argument. For example, `/commit "feat: add cool new button"` fails completely. Users must work around this by replacing spaces with underscores: `/commit feat:_add_cool_new_button`. This limitation, documented extensively in troubleshooting guides, makes MCP commands feel awkward and error-prone, contributing to the perception that commands aren't working properly.

## Critical crashes and command recognition failures

**Issue #3524** reveals that triggering certain MCP prompts causes **Claude Code to crash immediately** after tab-completing and pressing Enter. Instead of displaying a message about missing parameters, Claude Code exits with a stack trace. This affects version 1.0.51 on macOS.

**Issue #6657** shows MCP slash commands work alone (`/zen:chat`) but fail when followed by prompt text (`/zen:chat foo`), returning "Unknown slash command" errors. **Issue #7464** documents that when MCP prompt titles contain spaces, Claude Code incorrectly sends the title rather than the name property, causing "unknown slash command" errors despite the prompt appearing correctly in the list.

## Affected versions and platforms

The bugs span a wide range of versions and platforms:

- **Claude Code**: versions 0.2.62 through 1.0.93+
- **Claude Desktop**: Windows and macOS (Issue #8830 shows regression)
- **VS Code with Copilot**: version 1.101.0 (partially fixed in Insiders)
- **Gemini CLI**: version 0.1.17
- **Cline extension**: multiple versions affected
- **Platforms**: macOS, Windows, Linux—issues confirmed across all major operating systems

First reports date back to at least April 2025, with the most recent reports from August 2025, indicating **ongoing, unresolved problems** spanning multiple months.

## Root causes identified

Research into GitHub issues and developer discussions reveals several technical root causes:

**Input validation logic** requires at least one character for prompt execution, even when all arguments are optional. This explains why pressing Enter appears to do nothing—the validation fails silently without user feedback.

**Argument parsing** uses space-delimited parsing that conflicts with natural language input, making it impossible to pass sentences or phrases as arguments without workarounds.

**Command registration confusion** between title and name properties causes misidentification of commands, particularly when titles contain spaces.

**Protocol notification failures** mean the `notifications/prompts/list_changed` message doesn't reliably trigger UI updates, leading to "stale commands" that require full application restarts.

## Workarounds that actually work

While no official fixes exist for most issues, several community-discovered workarounds provide relief:

1. **For optional arguments**: Type at least one character (even ".") before pressing Enter to invoke the prompt
2. **For multi-word arguments**: Replace all spaces with underscores in your input
3. **For stale commands**: Restart Claude Code completely to force re-scanning of MCP servers
4. **For debugging**: Use the `--mcp-debug` flag to capture detailed error logs
5. **For argument discovery**: Check the MCP server source code directly to understand expected arguments, as the UI provides no guidance

The Arsturn troubleshooting guide emphasizes that argument handling problems are "HUGE" issues that make prompts feel like they're being ignored, noting there's "no easy way in UI to see what arguments a command accepts" or whether they're required or optional.

## General issue or server-specific?

The evidence strongly indicates **these are general client-side bugs affecting all MCP servers**, not issues with specific server implementations. Problems occur with:

- Custom MCP servers using @modelcontextprotocol/sdk
- Official servers (filesystem, GitHub, Playwright)
- Community servers (Brave Search, Firecrawl)
- All transport types (stdio, SSE, HTTP)
- Multiple MCP SDK implementations (Python, Kotlin, TypeScript)

The consistency across diverse server types confirms the bugs originate in Claude Code's MCP client implementation rather than individual server problems.

## Official acknowledgment and tracking

**Most issues remain open** on GitHub with no developer comments explaining root causes or planned fixes. The anthropics/claude-code repository tracks multiple open bugs labeled with "area:mcp" and "bug" tags. Notable tracked issues include #5597, #6657, #7464, #3524, and #2089.

Some fixes have shipped in recent changelog entries:
- **v1.0.73** (Aug 12, 2025): "MCP: Press Esc to cancel OAuth authentication flows"
- **v1.0.43** (July 3, 2025): "Fixed a bug where MCP tools would display twice in tool list"
- **v0.2.63**: "Fixed an issue where MCP tools were loaded twice, which caused tool call errors"

However, **no changelog entries address the core argument handling or enter key issues**, suggesting these remain unresolved in current releases.

## Conclusion

While the exact symptom of "holding enter for several seconds" wasn't documented verbatim, multiple interconnected bugs create an experience where MCP prompts feel unresponsive or broken when pressing Enter. Issue #5597 (Enter does nothing with optional arguments), Issue #5700 (arguments disappear on Enter), and related validation/parsing bugs combine to frustrate users attempting to use MCP slash commands. These affect all Claude Code versions from 0.2.62 through 1.0.93+ across all platforms, with workarounds available but no official fixes announced. The severity ranges from workflow annoyance to completely broken functionality, depending on the specific MCP server and argument configuration.
