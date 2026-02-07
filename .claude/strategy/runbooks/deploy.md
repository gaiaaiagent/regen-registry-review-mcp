# Deployment Runbook

Last updated: 2026-02-07

## Prerequisites

- SSH access to the GAIA production server
- The production server has the repo cloned at `/opt/projects/registry-eliza/regen-registry-review-mcp`
- A `.env` file on the production server with `REGISTRY_REVIEW_ENVIRONMENT=production` and the Anthropic API key
- UV installed on the production server

## Standard Deployment (code changes only)

```bash
# 1. Ensure all changes are committed and pushed from dev
git status        # verify clean working tree
git push origin main

# 2. SSH to production
ssh <production-server>

# 3. Pull latest code
cd /opt/projects/registry-eliza/regen-registry-review-mcp
git pull origin main

# 4. Sync dependencies (if pyproject.toml changed)
uv sync

# 5. Restart the service
sudo systemctl restart registry-review-api

# 6. Verify
sudo systemctl status registry-review-api
curl -s http://localhost:8003/ | head
curl -s http://localhost:8003/sessions | head

# 7. Check logs for errors
sudo journalctl -u registry-review-api --since "1 minute ago"
```

## First-Time Setup

If the systemd service doesn't exist yet:

```bash
# On the production server
cd /opt/projects/registry-eliza/regen-registry-review-mcp
sudo bash install-systemd-service.sh
```

This creates the service file, enables auto-start on boot, and starts the service.

## Rollback

```bash
# SSH to production
cd /opt/projects/registry-eliza/regen-registry-review-mcp

# Find the previous working commit
git log --oneline -10

# Reset to it
git checkout <commit-hash>

# Restart
sudo systemctl restart registry-review-api

# Verify
curl -s http://localhost:8003/sessions
```

After stabilizing, investigate the issue on dev, fix, and redeploy.

## Checking Production State

To verify what version is deployed:

```bash
# On production server
cd /opt/projects/registry-eliza/regen-registry-review-mcp
git log --oneline -5
git diff HEAD   # check for any uncommitted local changes
```

Compare with local dev:

```bash
# On dev machine
git log --oneline -5
```

If they diverge, document the drift in `STATUS.md` before reconciling.

## Known Issues

- The production path is `/opt/projects/registry-eliza/regen-registry-review-mcp` — the "registry-eliza" directory name is historical and predates the current project structure.
- PM2 was used historically (logs exist in `logs/pm2-*.log`). The current deployment uses systemd. Do not start both simultaneously.
- The nginx proxy maps `https://regen.gaiaai.xyz/api/registry/*` to `http://localhost:8003/*`. If the URL prefix changes, both nginx config and the GPT instructions need updating.
