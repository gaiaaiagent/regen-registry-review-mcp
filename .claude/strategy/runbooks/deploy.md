# Deployment Runbook

Last updated: 2026-02-07

## Prerequisites

- SSH access: `ssh shawn@202.61.196.119`
- Repo on server: `/opt/projects/registry-eliza/regen-registry-review-mcp`
- Process manager: PM2 (service name: `registry-review-api`, ID 0)
- A `.env` file on the production server with `REGISTRY_REVIEW_ENVIRONMENT=production` and the Anthropic API key
- UV installed on the production server

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

# 6. Verify
pm2 show registry-review-api
curl -s http://localhost:8003/ | head
curl -s http://localhost:8003/sessions | head

# 7. Check logs for errors
pm2 logs registry-review-api --lines 20
```

## One-Liner Deploy (from dev machine)

For docs-only or low-risk changes where you just need to pull and don't need to restart:

```bash
ssh shawn@202.61.196.119 "cd /opt/projects/registry-eliza/regen-registry-review-mcp && git pull origin main"
```

For code changes that require a restart:

```bash
ssh shawn@202.61.196.119 "cd /opt/projects/registry-eliza/regen-registry-review-mcp && git pull origin main && pm2 restart registry-review-api"
```

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
curl -s http://localhost:8003/sessions
```

After stabilizing, investigate the issue on dev, fix, and redeploy.

## Checking Production State

```bash
# From dev machine — quick status check
ssh shawn@202.61.196.119 "cd /opt/projects/registry-eliza/regen-registry-review-mcp && git log --oneline -3 && echo '---' && pm2 show registry-review-api | grep -E 'status|uptime|restart' && echo '---' && curl -s http://localhost:8003/"
```

## Known Issues

- The production path is `/opt/projects/registry-eliza/regen-registry-review-mcp` — the "registry-eliza" directory name is historical and predates the current project structure.
- PM2 manages the service. The `install-systemd-service.sh` script in the repo is not used in production. Do not start a systemd service alongside PM2.
- The nginx proxy maps `https://regen.gaiaai.xyz/api/registry/*` to `http://localhost:8003/*`. If the URL prefix changes, both nginx config and the GPT instructions need updating.
- PM2 has logged 8743 restarts total on the registry-review-api process. This warrants investigation if the number grows rapidly.
