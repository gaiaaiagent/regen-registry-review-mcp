# Architecture

The Registry Review MCP is a carbon credit project registration review system. It ingests project documents (PDFs, spreadsheets), maps them to methodology requirements, extracts evidence with LLM assistance, cross-validates findings, and generates compliance reports.

The system exposes two interfaces — a REST API for web clients and ChatGPT, and an MCP server for Claude Desktop and Claude Code — both backed by the same tool functions and file-based session storage.

## Nginx Routing

Three URL paths serve different systems on the same server:

```
Internet → nginx (SSL termination, regen.gaiaai.xyz)
  │
  ├── /registry           → port 8003  (Registry Review REST API)
  │                         chatgpt_rest_api.py via PM2
  │                         Requires auth_basic credentials
  │
  ├── /api/registry/*     → port 8200  (Darren's web app backend)
  │                         Proxies API calls from the frontend
  │
  └── /registry-review/   → static     (Darren's web app frontend)
                            Consumes /api/registry/* endpoints
```

The web app backend (port 8200) calls our REST API (port 8003) internally. Both systems read and write the same session files. Direct API access for testing or Custom GPT uses the `/registry` path with auth_basic, or `localhost:8003` from the server itself.

## Dual-Interface Pattern

Both interfaces import the same tool functions from `src/registry_review_mcp/tools/`:

```
src/registry_review_mcp/tools/
  ├── session_tools.py       Session lifecycle
  ├── document_tools.py      Document discovery and classification
  ├── mapping_tools.py       Requirement mapping
  ├── evidence_tools.py      LLM-powered evidence extraction
  ├── upload_tools.py         File upload via signed URLs
  └── human_review_tools.py  Overrides, annotations, determinations

chatgpt_rest_api.py          REST API (FastAPI on port 8003)
  └── Wraps tool functions as HTTP endpoints

src/registry_review_mcp/server.py   MCP server (FastMCP, stdio)
  └── Wraps tool functions as MCP tools
```

This means a bug fix or feature in the tools layer is immediately available through both interfaces. The REST API adds HTTP-specific concerns (CORS, request validation, error mapping to status codes). The MCP server adds MCP-specific concerns (tool descriptions, parameter schemas).

## Session State

All state is file-based. No database.

```
~/.local/share/registry-review-mcp/sessions/
  session-{uuid}/
    session.json         Metadata, workflow_progress, project info
    documents.json       Document inventory from discovery
    mapping.json         Requirement-to-document mappings
    evidence.json        Extracted evidence with citations
    validation.json      Cross-validation results
    report.md            Generated markdown report
    checklist.md         Populated checklist (markdown)
    checklist.docx       Populated checklist (Word)
    human_review.json    Overrides, annotations, determinations
    audit_log.json       Complete audit trail
    uploads/             Uploaded files
    .lock                Session lock file
```

Cache lives under `~/.cache/registry-review-mcp/` with PDF extraction cache (24h TTL) and LLM response cache (7-day TTL).

On production, both our API and the web app read/write sessions under `shawn`'s home directory. There is no separate data store for the web app — the web app backend calls our REST API which manages the session files.

## Deployment Topology

**Server:** `202.61.196.119` (GAIA), SSH as `shawn`

**Code path:** `/opt/projects/registry-eliza/regen-registry-review-mcp`

**PM2 processes on this server:**

| Process | Port | Description |
|---------|------|-------------|
| registry-review-api | 8003 | This project's REST API |
| koi-api | — | KOI knowledge API |
| koi-mcp-knowledge | — | KOI MCP knowledge server |
| regen-koi-mcp | — | Regen KOI MCP server |
| regen-network-api | — | Regen Network API |
| regenai-agents | — | RegenAI agents |
| koi-event-bridge | — | KOI event bridge |

PM2 configuration is in `ecosystem.config.cjs`. Key settings: `kill_timeout: 10000` (gives uvicorn time to release the socket), `exp_backoff_restart_delay: 100` (prevents restart storms), `max_memory_restart: "1G"` (current baseline ~340MB).

**Deployment procedure:**

```bash
# On developer machine
git push origin main

# On GAIA
ssh shawn@202.61.196.119
cd /opt/projects/registry-eliza/regen-registry-review-mcp
git pull origin main

# If ecosystem.config.cjs changed:
pm2 delete registry-review-api && pm2 start ecosystem.config.cjs && pm2 save

# If only application code changed:
pm2 restart registry-review-api

# Verify
curl -s http://localhost:8003/health | python3 -m json.tool
```

**Note:** `uv` on the production server is at `/home/shawn/.local/bin/uv` and is not in the non-interactive SSH PATH. The virtual environment at `.venv/` is pre-built and PM2 uses `.venv/bin/python` directly via `ecosystem.config.cjs`.

## Configuration

All settings use the `REGISTRY_REVIEW_` environment variable prefix. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REGISTRY_REVIEW_ENVIRONMENT` | `development` | `development` or `production` |
| `REGISTRY_REVIEW_ANTHROPIC_API_KEY` | (required) | Anthropic API key |
| `REGISTRY_REVIEW_LLM_MODEL` | haiku (dev) / sonnet (prod) | LLM model |
| `REGISTRY_REVIEW_LLM_BACKEND` | `auto` | `auto`, `api`, or `cli` |
| `REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED` | `false` | Enable LLM-powered extraction |
| `REGISTRY_REVIEW_ENABLE_CACHING` | `true` | Enable extraction caching |
| `REGISTRY_REVIEW_DATA_DIR` | `~/.local/share/registry-review-mcp` | Data root |
| `REGISTRY_REVIEW_LOG_LEVEL` | `INFO` | Logging level |

Full reference: `src/registry_review_mcp/config/settings.py`
