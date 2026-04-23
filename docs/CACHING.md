# Response caching

The LLM response cache lives under `$XDG_CACHE_HOME/registry-review-mcp/llm/`
(defaults to `~/.cache/registry-review-mcp/llm/` on Linux). Each cached
entry is a JSON file named `<cache_key>.json` storing the extracted
snippet list for a given extraction call, plus a creation timestamp used
for TTL enforcement.

## 1. What goes into the cache key

The cache key is a 16-char hex prefix of a SHA-256 over the JSON-serialized
tuple:

| Field | Source | Phase |
|-------|--------|-------|
| `requirement_id` | checklist row | A |
| `requirement_text` | checklist row | A |
| `accepted_evidence` | checklist row | A |
| `document_id` | document registry | A |
| `document_hash` (first 16 hex of SHA-256 of content) | document | A |
| `model` | `settings.get_active_executor_model()` | F1 — actual executor, not the Anthropic id |
| `temperature` | `settings.llm_temperature` | A |
| `prompt_version` | `evidence_tools.PROMPT_VERSION` | F1.4 — changes evict all entries |

Before Phase F1, the `model` field embedded `settings.get_active_llm_model()` —
the Anthropic model id — regardless of which backend actually served the
call. That meant swapping between GPT-OSS / Gemma / Qwen silently reused a
single cache entry per `(requirement, document)` pair, which broke the F0
model-swap sweep until the `get_active_executor_model()` helper landed.

## 2. Invalidation patterns

### Automatic (preferred)

- **Model swap.** Changing `REGISTRY_REVIEW_OPENAI_MODEL` (or switching
  backends) changes the cache key on the next call. Old entries are not
  deleted — they simply aren't referenced.
- **Prompt change.** Bump `PROMPT_VERSION` in `evidence_tools.py` when
  any prompt template changes output. Old entries become unreachable on
  the next call.
- **Document edit.** Any edit to a source document changes
  `document_hash` and evicts that document's entries.

### Manual

- **Full wipe.** `rm -rf ~/.cache/registry-review-mcp/llm/*` — use when
  debugging a cache-correctness issue. Costs one cold regression run.
- **Per-model wipe.** Not currently supported by a helper; grep the
  cache files for the model id to identify candidates, or wipe all.
  Rare enough to not justify tooling.
- **TTL expiry.** 30 days. Entries older than `settings.llm_cache_ttl`
  are deleted on read. Bumped from the Phase E default of 7 days because
  prompts change at release cadence (weekly, not daily); longer TTL means
  regression re-runs never burn cache unnecessarily.

## 3. CI integration

`.github/workflows/regression.yml` uses `actions/cache@v4` to persist
`~/.cache/registry-review-mcp/llm/` across workflow runs. Cache key is
bound to `hashFiles('src/registry_review_mcp/**/*.py')` so any source
change under `src/` evicts the CI cache. Restore keys let stale caches
seed a cold run instead of starting empty.

`.github/workflows/nightly.yml` runs per-model (`matrix.model`) and
namespaces the cache by model so one failing model never contaminates
the other's warm state.

## 4. Writing cache-safe code

Any change that alters the prompt string sent to the LLM in a way that
affects output MUST be accompanied by a `PROMPT_VERSION` bump in
`evidence_tools.py`. The rule of thumb:

- Editing the prompt template's instructions, schema, or output format?
  Bump.
- Editing comments, docstrings, or internal helpers that don't affect
  the string the LLM sees?  Do not bump.

When in doubt, bump — the cost of an unnecessary invalidation is one
cold regression run; the cost of a missed invalidation is weeks of
stale results the reviewer cannot audit.

## 5. Debugging cache issues

```bash
# How many entries are cached?
ls -1 ~/.cache/registry-review-mcp/llm/ | wc -l

# Find entries for a specific requirement
grep -l "REQ-017" ~/.cache/registry-review-mcp/llm/*.json

# Inspect a specific entry
jq '.response | length, .created_at' ~/.cache/registry-review-mcp/llm/<key>.json

# Force a cache-cold regression run
rm -rf ~/.cache/registry-review-mcp/llm/
uv run pytest -m regression -q tests/evaluation/
```

If two runs of the same fixture produce different `review.json` outputs
despite identical source code: check `PROMPT_VERSION`, then check
`get_active_executor_model()` returns the expected id in your current
environment, then check `document_hash` is stable across runs.
