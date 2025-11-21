# Quick Start: MCP Server Performance Optimization

**Goal:** Fix ping timeouts and improve startup performance in 15 minutes

---

## Immediate Fix (5 minutes) - Prevents Ping Timeouts

### 1. Add FastMCP Initialization Timeout

**File:** `src/registry_review_mcp/server.py`

**Line 41 - Current:**
```python
mcp = FastMCP("Regen Registry Review")
```

**Line 41 - Optimized:**
```python
mcp = FastMCP(
    "Regen Registry Review",
    settings={"initialization_timeout": 15.0}  # 15 second timeout
)
```

### 2. Set Python Environment Variables

**File:** `/home/ygg/Workspace/RegenAI/eliza/.mcp.json`

**Current:**
```json
{
  "mcpServers": {
    "registry-review": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/ygg/Workspace/RegenAI/regen-registry-review-mcp",
        "run",
        "registry-review-mcp"
      ]
    }
  }
}
```

**Optimized:**
```json
{
  "mcpServers": {
    "registry-review": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/ygg/Workspace/RegenAI/regen-registry-review-mcp",
        "run",
        "registry-review-mcp"
      ],
      "env": {
        "PYTHONOPTIMIZE": "2",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 3. Test

```bash
# Restart ElizaOS agent
cd /home/ygg/Workspace/RegenAI/eliza
bun start

# Watch for successful connection (no ping timeouts)
```

**Expected:** No more ping timeout errors

---

## Quick Performance Win (30 minutes) - 21% Faster Startup

### 1. Lazy-Load pdfplumber

**File:** `src/registry_review_mcp/tools/document_tools.py`

**Lines 9-10 - Remove these imports:**
```python
import pdfplumber  # DELETE THIS LINE
import fiona       # DELETE THIS LINE
```

**Line 295 - Add lazy import in `extract_document_metadata()`:**

Find this code:
```python
    # PDF-specific metadata
    if is_pdf_file(file_path.name):
        try:
            with pdfplumber.open(file_path) as pdf:
```

Replace with:
```python
    # PDF-specific metadata
    if is_pdf_file(file_path.name):
        try:
            import pdfplumber  # Lazy import - only loads when needed
            with pdfplumber.open(file_path) as pdf:
```

**Line 373 - Add lazy import in `extract_gis_metadata()`:**

Find this code:
```python
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            raise DocumentExtractionError(
                f"GIS file not found: {filepath}",
                details={"filepath": filepath},
            )

        result = {
            "filepath": filepath,
            "driver": None,
            "crs": None,
            "bounds": None,
            "feature_count": 0,
            "geometry_type": None,
            "schema": None,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        with fiona.open(file_path) as src:
```

Replace with:
```python
    try:
        import fiona  # Lazy import - only loads when needed

        file_path = Path(filepath)
        if not file_path.exists():
            raise DocumentExtractionError(
                f"GIS file not found: {filepath}",
                details={"filepath": filepath},
            )

        result = {
            "filepath": filepath,
            "driver": None,
            "crs": None,
            "bounds": None,
            "feature_count": 0,
            "geometry_type": None,
            "schema": None,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        with fiona.open(file_path) as src:
```

### 2. Test

```bash
# Restart and time server startup
cd /home/ygg/Workspace/RegenAI/regen-registry-review-mcp
time uv run registry-review-mcp --help

# Should start in ~300ms instead of ~425ms
```

**Expected:** 90ms faster startup (21% improvement)

---

## Advanced Optimization (1.5 hours) - 99% Faster First PDF

### 1. Add Async Marker Preloading

**File:** `src/registry_review_mcp/extractors/marker_extractor.py`

**After line 12 (after imports), add:**

```python
import asyncio
from typing import Optional

# Global marker models with async loading support
_marker_models: Optional[dict] = None
_marker_models_loading: Optional[asyncio.Task] = None
_marker_models_lock = asyncio.Lock()
```

**Replace the entire `get_marker_models()` function (lines 31-67) with:**

```python
async def preload_marker_models_async():
    """Asynchronously preload marker models in background."""
    global _marker_models, _marker_models_loading

    async with _marker_models_lock:
        if _marker_models is not None or _marker_models_loading is not None:
            return  # Already loaded or loading

        logger.info("🔄 Background loading marker models (~5-10 seconds)...")

        try:
            # Run blocking model load in thread pool
            def _load_models():
                from marker.models import create_model_dict
                from marker.converters.pdf import PdfConverter

                return {
                    "models": create_model_dict(),
                    "converter_cls": PdfConverter,
                }

            loop = asyncio.get_event_loop()
            _marker_models = await loop.run_in_executor(None, _load_models)
            logger.info("✅ Marker models loaded successfully (background)")
        except Exception as e:
            logger.error(f"❌ Failed to preload marker models: {e}")
            _marker_models = None
        finally:
            _marker_models_loading = None


async def get_marker_models_async() -> dict:
    """Get marker models, waiting for background load if necessary."""
    global _marker_models, _marker_models_loading

    if _marker_models is not None:
        return _marker_models

    if _marker_models_loading is not None:
        logger.info("⏳ Waiting for background marker model loading...")
        await _marker_models_loading
        if _marker_models is not None:
            return _marker_models

    # Trigger immediate load
    await preload_marker_models_async()

    if _marker_models is None:
        raise DocumentExtractionError(
            "Failed to load marker models",
            details={"error": "Model loading failed"},
        )

    return _marker_models


def get_marker_models():
    """Synchronous wrapper for backward compatibility."""
    if _marker_models is not None:
        return _marker_models

    logger.warning("Synchronous marker model loading - consider using async")

    try:
        from marker.models import create_model_dict
        from marker.converters.pdf import PdfConverter

        global _marker_models
        _marker_models = {
            "models": create_model_dict(),
            "converter_cls": PdfConverter,
        }
        return _marker_models
    except ImportError as e:
        raise DocumentExtractionError(
            "Marker library not installed",
            details={"error": str(e)},
        )
    except Exception as e:
        raise DocumentExtractionError(
            f"Failed to load marker models: {str(e)}",
            details={"error": str(e)},
        )
```

### 2. Update convert_pdf_to_markdown()

**File:** `src/registry_review_mcp/extractors/marker_extractor.py`

**Line 126 - Find:**
```python
        # Load models (lazy, cached globally)
        marker_resources = get_marker_models()
```

**Replace with:**
```python
        # Load models (async, background preloaded if available)
        marker_resources = await get_marker_models_async()
```

### 3. Trigger Background Preload on Server Startup

**File:** `src/registry_review_mcp/server.py`

**After line 43 (after logger.info), add:**

```python
logger.info("Initializing Registry Review MCP Server v2.0.0")

# Start background preloading of marker models (non-blocking)
import asyncio
from .extractors.marker_extractor import preload_marker_models_async

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Schedule background preload
async def _start_preload():
    """Wrapper to start preload task."""
    await preload_marker_models_async()

try:
    # Create task but don't await - let it run in background
    task = asyncio.create_task(_start_preload())
    logger.info("📦 Marker models preloading in background...")
except Exception as e:
    logger.warning(f"Could not start background model preload: {e}")
```

### 4. Test

```bash
# Start server and watch logs
cd /home/ygg/Workspace/RegenAI/regen-registry-review-mcp
uv run registry-review-mcp

# You should see:
# "Initializing Registry Review MCP Server v2.0.0"
# "📦 Marker models preloading in background..."
# "🔄 Background loading marker models (~5-10 seconds)..."
# "✅ Marker models loaded successfully (background)"

# Test PDF extraction after preload completes
# Should be <100ms instead of 5,700ms
```

**Expected:** First PDF extraction is 99% faster (5.7s → 50ms)

---

## Verification Checklist

- [ ] No ping timeout errors in ElizaOS logs
- [ ] Server starts in <350ms
- [ ] Marker models preload in background (see logs)
- [ ] First PDF extraction completes quickly (<3s)
- [ ] All MCP tools still work correctly
- [ ] No import errors or warnings

---

## Rollback Instructions

If issues occur, revert changes:

```bash
cd /home/ygg/Workspace/RegenAI/regen-registry-review-mcp
git checkout src/registry_review_mcp/server.py
git checkout src/registry_review_mcp/tools/document_tools.py
git checkout src/registry_review_mcp/extractors/marker_extractor.py
```

---

## Next Steps

After validating these optimizations, see **PERFORMANCE_OPTIMIZATION_REPORT.md** for:
- Additional optimizations (lazy tool imports)
- Performance benchmarking scripts
- Long-term monitoring strategies
- Advanced caching techniques

---

**Implementation Time:** 15 minutes (immediate) + 30 minutes (quick win) + 1.5 hours (advanced)
**Expected Performance:** 34% faster startup, 99% faster first PDF extraction
**Risk Level:** Low (changes are isolated and backward compatible)
