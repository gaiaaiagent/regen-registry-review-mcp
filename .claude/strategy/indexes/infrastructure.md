# Infrastructure Reference

Last updated: 2026-02-07

## Architecture Overview

```
                         Internet
                            |
                        nginx proxy
                     (SSL termination)
                            |
              https://regen.gaiaai.xyz/api/registry/*
                            |
                     +--------------+
                     |  FastAPI     |
                     |  Port 8003   |  <-- chatgpt_rest_api.py
                     |  (REST API)  |
                     +--------------+
                            |
                   Shared backend tools
                  (src/registry_review_mcp/)
                            |
                     +--------------+
                     |  MCP Server  |  <-- server.py (stdio)
                     |  (FastMCP)   |
                     +--------------+

Clients:
  - Custom GPT         --> REST API (HTTPS)
  - Web App            --> REST API (HTTPS)  https://regen.gaiaai.xyz/registry-review/
  - Claude Desktop     --> MCP Server (stdio)
  - Claude Code        --> MCP Server (stdio via .mcp.json)
```

## Production Server

- **Host:** GAIA server (SSH access required)
- **Service:** `registry-review-api.service` (systemd)
- **Port:** 8003 (HTTP, proxied through nginx to HTTPS)
- **User:** `shawn:shawn`
- **Endpoint:** `https://regen.gaiaai.xyz/api/registry`
- **Web App:** `https://regen.gaiaai.xyz/registry-review/`
- **Logs:** `/opt/projects/registry-eliza/regen-registry-review-mcp/logs/rest-api.log`
- **Python:** UV-managed virtual environment

## Service Management

```bash
# Status
sudo systemctl status registry-review-api

# Restart (after deploying new code)
sudo systemctl restart registry-review-api

# Logs (follow)
sudo journalctl -u registry-review-api -f

# Application logs
tail -f /opt/projects/registry-eliza/regen-registry-review-mcp/logs/rest-api.log
```

## Data Storage

File-system based, no external database.

```
~/.local/share/registry-review-mcp/
  sessions/
    session-{uuid}/
      session.json           Session metadata and workflow_progress
      documents.json         Document inventory
      mapping.json           Requirement mappings
      evidence.json          Extracted evidence
      validation.json        Validation results
      report.md              Generated markdown report
      checklist.md           Populated checklist
      checklist.docx         Word document checklist
      human_review.json      Override/annotation data
      audit_log.json         Complete audit trail
      uploads/               Uploaded documents
      .lock                  Session lock file

~/.cache/registry-review-mcp/
  pdf/                       PDF extraction cache (24h TTL)
  llm/                       LLM response cache (7-day TTL)
```

## Configuration

All configuration via environment variables with `REGISTRY_REVIEW_` prefix. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `REGISTRY_REVIEW_ENVIRONMENT` | `development` | `development` or `production` |
| `REGISTRY_REVIEW_ANTHROPIC_API_KEY` | (required) | Anthropic API key |
| `REGISTRY_REVIEW_LLM_MODEL` | haiku (dev) / sonnet (prod) | LLM model selection |
| `REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED` | `false` | Enable LLM-powered extraction |
| `REGISTRY_REVIEW_LLM_TEMPERATURE` | `0.0` | LLM temperature |
| `REGISTRY_REVIEW_ENABLE_CACHING` | `true` | Enable extraction caching |
| `REGISTRY_REVIEW_DATA_DIR` | `~/.local/share/registry-review-mcp` | Data storage root |
| `REGISTRY_REVIEW_SESSIONS_DIR` | (DATA_DIR)/sessions | Session storage |
| `REGISTRY_REVIEW_CACHE_DIR` | `~/.cache/registry-review-mcp` | Cache storage |
| `REGISTRY_REVIEW_LOG_LEVEL` | `INFO` | Logging level |

Full reference: `.env.example` (108 configuration options)

## Development Environment

- **Location:** `/home/ygg/Workspace/regenai/regenai-forum-content/resources/regen-registry-review-mcp`
- **Python:** 3.13.11 (UV-managed)
- **Virtual env:** `.venv/`
- **Run server:** `uv run python -m registry_review_mcp.server`
- **Run REST API:** `uv run python chatgpt_rest_api.py`
- **Run tests:** `uv run pytest` (fast tests only; see runbooks/testing.md)

## Deployment Flow

```
Developer machine (this repo)
  |
  git push origin main
  |
SSH to production server
  |
  cd /opt/projects/registry-eliza/regen-registry-review-mcp
  git pull origin main
  sudo systemctl restart registry-review-api
  |
  Verify: curl http://localhost:8003/sessions
```

See `runbooks/deploy.md` for detailed procedure.

## External Integrations

| System | Connection | Status |
|--------|-----------|--------|
| Custom GPT | REST API via OpenAI Actions | Active |
| Web App | REST API (Darren's frontend) | Active |
| Google Drive | Ingestion bot (email account) | Built, not integrated |
| Airtable | API integration | Planned (Samu exploring) |
| Regen Ledger | On-chain anchoring | Future (Phase 5) |
| KOI MCP | Knowledge graph queries | Available via .mcp.json |
| Regen Network MCP | Ledger queries | Available via .mcp.json |
