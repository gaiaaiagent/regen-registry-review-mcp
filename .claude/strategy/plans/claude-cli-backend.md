# Spec: Claude Code CLI Backend for LLM Calls

Created: 2026-02-07

## Problem

The Registry Review MCP uses Anthropic's API (`anthropic.AsyncAnthropic`) for all LLM calls — evidence extraction, unified analysis, and validation synthesis. This requires pay-as-you-go API credits loaded at console.anthropic.com, which are currently exhausted ($0 balance). The team has an Anthropic Max plan ($200/month) that includes generous Claude usage, but the standard API SDK cannot use Max plan billing.

## Discovery

Deep research across four subagents confirmed:

1. **Max plan and API credits are separate billing systems.** The `anthropic` Python SDK always uses API credits. There is no way to authenticate with Max plan credentials through that SDK.

2. **Claude Code CLI (`claude -p`) uses Max plan billing** when authenticated via OAuth (`claude login`). It provides non-interactive, single-prompt execution with JSON output, structured schemas, tool permissions, and session continuity.

3. **The Claude Agent SDK (`pip install claude-agent-sdk`)** also uses Max plan billing when authenticated via OAuth. It provides native Python async iteration over agent responses.

4. **If `ANTHROPIC_API_KEY` is set, it takes precedence** over OAuth credentials and silently routes to API billing. This is the most common source of accidental double-billing.

## Design Decision

Implement `claude -p` subprocess calls as an alternative backend, rather than the Agent SDK, because:

- **No new dependency.** Claude Code CLI is already installed on both development and production machines.
- **Minimal code change.** The interface is `prompt in → text out`, matching our existing LLM call pattern.
- **Transparent fallback.** The system tries the standard API first (if key is configured), then falls back to CLI. Both produce the same output format.
- **Debuggable.** CLI calls can be reproduced manually in the terminal.

The Agent SDK is a better long-term choice for complex multi-turn interactions, but for our use case — single-prompt evidence extraction — subprocess calls are simpler and sufficient.

## Architecture

### Current Flow

```
evidence_tools.py  →  AsyncAnthropic(api_key=...)  →  Anthropic API  →  $$ API credits
analyze_llm.py     →  AsyncAnthropic(api_key=...)  →  Anthropic API  →  $$ API credits
llm_synthesis.py   →  AsyncAnthropic(api_key=...)  →  Anthropic API  →  $$ API credits
```

### Proposed Flow

```
evidence_tools.py  →  llm_client.call_llm(...)  →  backend selection:
analyze_llm.py     →  llm_client.call_llm(...)  →    ├─ API key set?  → AsyncAnthropic  → $$ API credits
llm_synthesis.py   →  llm_client.call_llm(...)  →    └─ No key?       → claude -p        → Max plan (included)
```

### Backend Selection Logic

The `llm_client.py` module (already created for error handling) gains a unified `call_llm()` function:

```python
async def call_llm(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = 4000,
    temperature: float = 0.0,
) -> str:
    """Route an LLM call through the best available backend.

    Priority:
    1. Anthropic API (if ANTHROPIC_API_KEY is set) — direct, fast
    2. Claude CLI (if `claude` is on PATH and authenticated) — uses Max plan
    3. Raise ConfigurationError with guidance
    """
```

The function returns raw text — the response content. Error classification and propagation use the same `classify_api_error()` infrastructure already in place.

### Changes by File

**`src/registry_review_mcp/utils/llm_client.py`** (extend existing)
- Add `call_llm()` — the unified entry point
- Add `_call_via_api()` — current AsyncAnthropic path, extracted into a function
- Add `_call_via_cli()` — new subprocess path using `claude -p`
- Add `_detect_cli_available()` — check if `claude` is installed and authenticated
- Add `LLM_BACKEND` setting (auto/api/cli) for explicit override

**`src/registry_review_mcp/config/settings.py`**
- Add `llm_backend: Literal["auto", "api", "cli"] = "auto"` field
- `auto` = try API first, fall back to CLI
- `api` = only use API (fail if no key)
- `cli` = only use CLI (fail if not installed)

**`src/registry_review_mcp/tools/evidence_tools.py`**
- Replace direct `AsyncAnthropic` usage in `extract_evidence_with_llm()` with `call_llm()`
- The prompt construction stays identical — only the transport changes

**`src/registry_review_mcp/tools/analyze_llm.py`**
- The unified analysis calls `analyze_with_llm()` in `unified_analysis.py`, which takes an `anthropic_client` parameter
- Modify to accept either an AsyncAnthropic client or use `call_llm()` directly
- This is the biggest refactor — the unified analysis prompt is already self-contained

**`src/registry_review_mcp/validation/llm_synthesis.py`**
- Replace direct client usage with `call_llm()`

**`chatgpt_rest_api.py`**
- No changes needed — the REST API calls the tools, which call `llm_client`, which routes automatically

### CLI Subprocess Details

The `_call_via_cli()` function:

```python
async def _call_via_cli(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = 4000,
) -> str:
    """Call Claude via CLI subprocess, using Max plan billing."""
    cmd = ["claude", "-p", "--output-format", "json"]

    if model:
        cmd.extend(["--model", model])
    if max_tokens:
        cmd.extend(["--max-turns", "1"])  # Single response, no agent loop
    if system:
        cmd.extend(["--append-system-prompt", system])

    # Disable all tools — we're using Claude as a pure LLM, not an agent
    cmd.extend(["--tools", ""])

    # Run as subprocess with the prompt on stdin
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate(input=prompt.encode())

    if process.returncode != 0:
        raise LLMBackendError(f"Claude CLI failed: {stderr.decode()}")

    result = json.loads(stdout.decode())
    return result["result"]
```

Key design choices:
- **`--tools ""`** disables all built-in tools. We're using Claude as a pure text-in/text-out LLM, not as an agent. This prevents it from trying to read files or run commands.
- **`--max-turns 1`** ensures a single response. No agentic loop.
- **`--output-format json`** gives us structured output with `result`, `session_id`, and token usage.
- **Prompt via stdin** avoids shell escaping issues with large prompts containing quotes, special characters, and multi-line content.
- **Async subprocess** (`asyncio.create_subprocess_exec`) so we don't block the event loop.

### Concurrency

The current system uses `asyncio.Semaphore(5)` for parallel LLM calls. With the CLI backend, each call spawns a subprocess. This is fine for 5 concurrent calls — the OS handles process scheduling. If we hit Max plan rate limits, Claude CLI returns a non-zero exit code that `classify_api_error()` can handle.

### Environment Requirements

For the CLI backend to work:
1. `claude` must be on PATH
2. User must be authenticated (`claude login` completed)
3. `ANTHROPIC_API_KEY` must NOT be set (or `llm_backend` must be explicitly set to `"cli"`)

On the GAIA production server, this means:
- Install Claude Code: `npm install -g @anthropic-ai/claude-code` (or equivalent)
- Run `claude login` once as the `shawn` user
- Unset or remove `ANTHROPIC_API_KEY` from the PM2 environment

### Error Handling

Errors from the CLI backend map to the same `APIErrorInfo` categories:
- Exit code 1 + "rate limit" in stderr → `rate_limit` (transient)
- Exit code 1 + "authentication" in stderr → `auth` (fatal)
- Exit code 1 + "usage limit" in stderr → `billing` (fatal, but means Max plan weekly cap hit)
- Process timeout → `network` (transient)

The existing `classify_api_error()` function is extended with a new `classify_cli_error()` for subprocess failures.

## Testing

### New Tests

- `test_call_llm_prefers_api_when_key_set` — verify API backend selected when key exists
- `test_call_llm_falls_back_to_cli` — verify CLI backend selected when no key
- `test_call_llm_raises_when_nothing_available` — verify clear error when neither works
- `test_cli_backend_disables_tools` — verify `--tools ""` is passed
- `test_cli_backend_passes_system_prompt` — verify `--append-system-prompt` is passed
- `test_cli_error_classification` — verify stderr parsing for exit codes

### Manual Verification

```bash
# Verify CLI backend works with Max plan
unset ANTHROPIC_API_KEY
claude -p "Say hello" --output-format json --tools ""

# Verify evidence extraction with CLI backend
LLM_BACKEND=cli uv run python -c "
import asyncio
from registry_review_mcp.utils.llm_client import call_llm
result = asyncio.run(call_llm('What is 2+2?'))
print(result)
"
```

## Migration Path

1. **Phase A** (this PR): Implement `call_llm()` with dual backend, update `evidence_tools.py` and `llm_synthesis.py`
2. **Phase B** (follow-up): Update `analyze_llm.py` and `unified_analysis.py` to use `call_llm()` instead of passing `AsyncAnthropic` client objects
3. **Phase C** (production): Install Claude Code on GAIA server, authenticate, verify, deploy

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Max plan weekly usage cap hit | LLM calls fail for remainder of week | Surface clear error: "Max plan usage limit reached, resets in X days" |
| Claude CLI not installed on production | CLI backend unavailable | Fall back to API; document installation in deploy runbook |
| `ANTHROPIC_API_KEY` accidentally set | Silently bills API instead of Max | Warn at startup if both API key and CLI are available |
| Subprocess overhead | Slower than direct API | Negligible for our use case (~100ms overhead vs. 2-5s LLM latency) |
| CLI output format changes | JSON parsing breaks | Pin to `--output-format json` which is stable; add version check |
| Anthropic locks down CLI programmatic use | Backend stops working | We retain the API backend as primary; CLI is additive |

## Not In Scope

- Agent SDK integration (future consideration for multi-turn interactions)
- Switching the MCP server itself to use Claude CLI (it already runs inside Claude Code)
- Changing the prompt structure or evidence extraction logic
- Multi-model support (the CLI respects `--model` flag, same as API)

## Success Criteria

1. `uv run pytest` passes with no regressions
2. Evidence extraction runs successfully using Max plan (CLI backend) with no API credits
3. The system auto-detects the best backend and prints which one it's using
4. Fatal errors (no API key AND no CLI) produce actionable guidance
5. Production deployment documented with CLI installation steps
