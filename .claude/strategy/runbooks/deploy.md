# Deployment Runbook

Last updated: 2026-02-09

## Prerequisites

- SSH access: `ssh shawn@202.61.196.119`
- Repo on server: `/opt/projects/registry-eliza/regen-registry-review-mcp`
- Process manager: PM2 (service name: `registry-review-api`, ID 0)
- Config: `ecosystem.config.cjs` in the repo root
- A `.env` file on the production server with `REGISTRY_REVIEW_ENVIRONMENT=production` and the Anthropic API key
- UV installed on the production server at `/home/shawn/.local/bin/uv`

## Standard Deployment (code changes only)

```bash
# 1. Ensure all changes are committed and pushed from dev
git status        # verify clean working tree
git push origin main

# 2. SSH to production
ssh shawn@202.61.196.119

# 3. Pull latest code
cd /opt/projects/registry-eliza/regen-registry-review-mcp
git pull origin main

# 4. Sync dependencies (if pyproject.toml changed)
uv sync

# 5. Restart the service
pm2 restart registry-review-api

# 6. Verify with health endpoint
curl -s http://localhost:8003/health | python3 -m json.tool

# Expected: {"status": "healthy", "version": "2.0.0", ...}
# If you see connection refused, wait 10s and retry (uvicorn startup)

# 7. Check request tracing is working
curl -s -D- http://localhost:8003/health 2>&1 | grep -i x-request-id

# 8. Check logs for errors
pm2 logs registry-review-api --lines 20
```

## One-Liner Deploy (from dev machine)

For code changes that require a restart:

```bash
ssh shawn@202.61.196.119 "cd /opt/projects/registry-eliza/regen-registry-review-mcp && git pull origin main && pm2 restart registry-review-api && sleep 3 && curl -sf http://localhost:8003/health"
```

With dependency sync:

```bash
ssh shawn@202.61.196.119 "cd /opt/projects/registry-eliza/regen-registry-review-mcp && git pull origin main && /home/shawn/.local/bin/uv sync && pm2 restart registry-review-api && sleep 3 && curl -sf http://localhost:8003/health"
```

## First-Time PM2 Setup (or config reload)

If the ecosystem config has changed, delete the old process and re-create from config:

```bash
ssh shawn@202.61.196.119
cd /opt/projects/registry-eliza/regen-registry-review-mcp
pm2 delete registry-review-api
pm2 start ecosystem.config.cjs
pm2 save

# Verify the new config took effect
pm2 show registry-review-api | grep -E 'kill_timeout|listen_timeout|exp_backoff'
```

The `pm2 save` step persists the config so PM2 restores it after server reboots.

## Rollback

```bash
ssh shawn@202.61.196.119

cd /opt/projects/registry-eliza/regen-registry-review-mcp

# Find the previous working commit
git log --oneline -10

# Reset to it
git checkout <commit-hash>

# Restart
pm2 restart registry-review-api

# Verify
curl -s http://localhost:8003/health
```

After stabilizing, investigate the issue on dev, fix, and redeploy.

## Checking Production State

```bash
# Quick status check from dev machine
ssh shawn@202.61.196.119 "cd /opt/projects/registry-eliza/regen-registry-review-mcp && git log --oneline -3 && echo '---' && pm2 show registry-review-api | grep -E 'status|uptime|restart' && echo '---' && curl -s http://localhost:8003/health"
```

## Claude CLI Backend (Phase 1g)

When the Claude CLI backend is deployed, the production server needs Claude Code installed and authenticated:

```bash
# Install Claude Code (once)
npm install -g @anthropic-ai/claude-code

# Authenticate with Max plan (once, interactive)
claude login

# Verify
claude -p "Say hello" --output-format json --tools ""

# Important: ensure ANTHROPIC_API_KEY is NOT set in .env or PM2 env
# If set, it overrides Max plan auth and bills API credits instead
pm2 env 0 | grep ANTHROPIC
```

If `ANTHROPIC_API_KEY` is in the `.env` file and you want to use the Max plan CLI backend, either remove the key or set `LLM_BACKEND=cli` to force CLI routing regardless of API key presence.

## PM2 Restart History (Diagnosed Feb 9)

The 8,749 restart count is explained. 8,703 restarts came from a single port-bind storm on Jan 14: the process crashed, but port 8003 wasn't released before PM2 restarted it. Each restart failed with `[Errno 98] address already in use` and PM2 retried every ~6.5 seconds for 16 hours (05:21 to 22:01 UTC). The remaining ~46 restarts are accumulated from normal deploys over 2+ months.

The `ecosystem.config.cjs` prevents this from recurring:
- `kill_timeout: 10000` — gives uvicorn 10s to release the socket on shutdown
- `listen_timeout: 15000` — waits for the app to actually bind the port
- `exp_backoff_restart_delay: 100` — exponential backoff on failures (doubles each time, caps at ~15min)

No OOM kills were found in the kernel journal. No memory leak. Current process uses ~340MB against a 1GB ceiling.

## Known Issues

- The production path is `/opt/projects/registry-eliza/regen-registry-review-mcp` — the "registry-eliza" directory name is historical and predates the current project structure.
- PM2 manages the service. The `install-systemd-service.sh` script in the repo is not used in production. Do not start a systemd service alongside PM2.
- The nginx proxy maps `https://regen.gaiaai.xyz/api/registry/*` to port 8200 (Darren's web app), NOT directly to port 8003. Direct API access is via `https://regen.gaiaai.xyz/registry` (requires auth_basic) or `localhost:8003` on the server.
- UV at `/home/shawn/.local/bin/uv`, not on non-interactive SSH PATH. Use full path in scripts.
