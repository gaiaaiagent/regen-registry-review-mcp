# Environment Configuration Guide

**Version:** 2.0.0
**Last Updated:** November 12, 2025

---

## Quick Start

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your API key:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Add your Anthropic API key:**
   ```bash
   REGISTRY_REVIEW_ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
   REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED=true
   ```

4. **Start the server:**
   ```bash
   uv run python -m registry_review_mcp.server
   ```

---

## Configuration Variables

### LLM Extraction (Phase 4.2)

#### `REGISTRY_REVIEW_ANTHROPIC_API_KEY`
- **Required for:** LLM-powered field extraction
- **Type:** String
- **Default:** `""` (empty)
- **Get your key:** https://console.anthropic.com/
- **Example:** `sk-ant-api03-...`

#### `REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED`
- **Type:** Boolean (true/false)
- **Default:** `false`
- **Description:** Enable LLM extraction vs regex-only
- **When false:** Uses regex extraction (free, fast, limited accuracy)
- **When true:** Uses Claude API (paid, slower, high accuracy)

#### `REGISTRY_REVIEW_LLM_MODEL`
- **Type:** String
- **Default:** `claude-sonnet-4-20250514`
- **Options:**
  - `claude-sonnet-4-20250514` - Best quality, higher cost ($3/$15 per MTok)
  - `claude-haiku-4` - Lower cost, good quality ($0.80/$4 per MTok)
- **Recommendation:** Start with Sonnet, try Haiku if cost is a concern

#### `REGISTRY_REVIEW_LLM_MAX_TOKENS`
- **Type:** Integer (1-8000)
- **Default:** `4000`
- **Description:** Maximum tokens for LLM responses
- **Impact:** Higher = can extract more fields, higher cost

#### `REGISTRY_REVIEW_LLM_TEMPERATURE`
- **Type:** Float (0.0-1.0)
- **Default:** `0.0`
- **Description:** LLM sampling temperature
- **0.0 = Deterministic** (recommended for extraction)
- **Higher = More creative** (not recommended)

#### `REGISTRY_REVIEW_LLM_CONFIDENCE_THRESHOLD`
- **Type:** Float (0.0-1.0)
- **Default:** `0.7`
- **Description:** Minimum confidence to include extracted fields
- **Lower = More fields, more false positives**
- **Higher = Fewer fields, higher precision**
- **Recommendation:** 0.7 is a good balance

#### `REGISTRY_REVIEW_MAX_API_CALLS_PER_SESSION`
- **Type:** Integer
- **Default:** `50`
- **Description:** Maximum API calls per session (cost safety)
- **Impact:** Prevents runaway costs

#### `REGISTRY_REVIEW_API_CALL_TIMEOUT_SECONDS`
- **Type:** Integer (5-120)
- **Default:** `30`
- **Description:** Timeout for each API call
- **Impact:** Prevents hanging on slow responses

---

### Logging

#### `REGISTRY_REVIEW_LOG_LEVEL`
- **Type:** String
- **Default:** `INFO`
- **Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Recommendation:**
  - `INFO` for production
  - `DEBUG` for troubleshooting

#### `REGISTRY_REVIEW_LOG_FORMAT`
- **Type:** String
- **Default:** `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- **Description:** Python logging format string

---

### Paths (Optional)

If not specified, defaults to `./data` subdirectories.

#### `REGISTRY_REVIEW_DATA_DIR`
- **Type:** Path (absolute)
- **Default:** `./data`
- **Description:** Root data directory

#### `REGISTRY_REVIEW_CHECKLISTS_DIR`
- **Type:** Path (absolute)
- **Default:** `./data/checklists`
- **Description:** Methodology checklist files

#### `REGISTRY_REVIEW_SESSIONS_DIR`
- **Type:** Path (absolute)
- **Default:** `./data/sessions`
- **Description:** Active session data (gitignored)

#### `REGISTRY_REVIEW_CACHE_DIR`
- **Type:** Path (absolute)
- **Default:** `./data/cache`
- **Description:** Cached extraction results (gitignored)

---

### Performance

#### `REGISTRY_REVIEW_ENABLE_CACHING`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable caching for PDF/LLM extractions
- **Impact:** Significant performance improvement

#### `REGISTRY_REVIEW_CACHE_COMPRESSION`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Compress cached data
- **Impact:** Saves disk space

#### `REGISTRY_REVIEW_MAX_CONCURRENT_EXTRACTIONS`
- **Type:** Integer
- **Default:** `5`
- **Description:** Max parallel PDF extractions

---

### Validation

#### `REGISTRY_REVIEW_DATE_ALIGNMENT_MAX_DELTA_DAYS`
- **Type:** Integer
- **Default:** `120` (4 months)
- **Description:** Maximum days between dates for alignment validation

#### `REGISTRY_REVIEW_LAND_TENURE_FUZZY_MATCH`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable fuzzy matching for owner names

#### `REGISTRY_REVIEW_PROJECT_ID_MIN_OCCURRENCES`
- **Type:** Integer
- **Default:** `3`
- **Description:** Minimum project ID occurrences for consistency check

---

## Example Configurations

### Development (with LLM)

```bash
# .env
REGISTRY_REVIEW_ANTHROPIC_API_KEY=sk-ant-api03-your-dev-key
REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED=true
REGISTRY_REVIEW_LOG_LEVEL=DEBUG
REGISTRY_REVIEW_MAX_API_CALLS_PER_SESSION=10  # Low limit for dev
```

### Production (with LLM)

```bash
# .env
REGISTRY_REVIEW_ANTHROPIC_API_KEY=sk-ant-api03-your-prod-key
REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED=true
REGISTRY_REVIEW_LOG_LEVEL=INFO
REGISTRY_REVIEW_MAX_API_CALLS_PER_SESSION=50
REGISTRY_REVIEW_LLM_CONFIDENCE_THRESHOLD=0.75  # Higher precision
```

### Testing (regex only)

```bash
# .env
REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED=false  # Use regex
REGISTRY_REVIEW_LOG_LEVEL=DEBUG
```

---

## Cost Estimation

### With Claude Sonnet 4
- **Per extraction call:** ~$0.02-0.05
- **Per session:** ~$0.30-0.50 (15-20 calls)
- **Per 100 reviews:** ~$30-50/month

### With Claude Haiku
- **Per extraction call:** ~$0.005-0.01
- **Per session:** ~$0.08-0.15 (15-20 calls)
- **Per 100 reviews:** ~$8-15/month

### ROI
- **Time saved:** 3-5 hours per review
- **Value:** $150-375 (at $50-75/hour)
- **Cost:** $0.30-0.50 per review
- **ROI:** 300x-1200x

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set" error

**Problem:** API key not loaded from .env

**Solutions:**
1. Verify .env file exists in project root
2. Check variable name: `REGISTRY_REVIEW_ANTHROPIC_API_KEY` (with prefix)
3. Restart your editor/IDE to reload environment
4. Check for typos in .env file

### LLM extraction not working

**Check:**
1. `REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED=true` in .env
2. API key is valid (test at https://console.anthropic.com/)
3. Check logs for error messages
4. Verify API key has sufficient credits

### High API costs

**Solutions:**
1. Lower `MAX_API_CALLS_PER_SESSION` (e.g., 20)
2. Increase `LLM_CONFIDENCE_THRESHOLD` (e.g., 0.8)
3. Use Claude Haiku instead of Sonnet
4. Enable caching (should be on by default)

---

## Security Best Practices

1. **Never commit .env to git** (already in .gitignore)
2. **Use separate API keys** for dev/prod
3. **Rotate keys regularly** (every 90 days)
4. **Monitor usage** at https://console.anthropic.com/
5. **Set billing alerts** to prevent cost overruns
6. **Use read-only keys** if available

---

## Integration with Claude Desktop

Claude Desktop loads environment variables from your shell. To use .env:

**Option 1: System environment variables**
```bash
export REGISTRY_REVIEW_ANTHROPIC_API_KEY="sk-ant-..."
export REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED="true"
```

**Option 2: Source .env in your shell**
```bash
# Add to ~/.bashrc or ~/.zshrc
set -a
source /path/to/regen-registry-review-mcp/.env
set +a
```

**Option 3: Use direnv** (recommended)
```bash
# Install direnv
brew install direnv  # or apt install direnv

# Allow .envrc in project
echo "dotenv" > .envrc
direnv allow

# Automatically loads .env when cd into directory
```

---

## Reference

- **Pydantic Settings Documentation:** https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- **Anthropic API Documentation:** https://docs.anthropic.com/
- **UV Package Manager:** https://github.com/astral-sh/uv
