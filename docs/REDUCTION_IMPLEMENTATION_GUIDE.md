# Code Reduction Implementation Guide

**Purpose:** Step-by-step guide for implementing the architectural consolidation identified in the reduction analysis.

**Target:** Reduce `llm_extractors.py` from 1,281 lines to ~754 lines (41% reduction) while improving maintainability.

---

## Quick Reference

| Phase | Focus | Lines Reduced | Time Estimate | Risk |
|-------|-------|---------------|---------------|------|
| Phase 1 | Helper Methods | 79-99 lines | 1-2 days | Low |
| Phase 2 | Unified Extractor | 300-400 lines | 3-5 days | Medium |
| Phase 3 | Prompt Externalization | 127 lines | 1-2 days | Low |
| **Total** | **Full Consolidation** | **506-626 lines** | **5-9 days** | **Medium** |

---

## Phase 1: Extract Helper Methods (Quick Wins)

**Goal:** Move duplicate patterns from 3 extractors into BaseExtractor shared methods.

### Step 1.1: Message Content Builder

**Create method in BaseExtractor:**

```python
# extractors/llm_extractors.py - BaseExtractor class

def _build_message_content(
    self,
    chunk: str,
    chunk_images: list[Path],
    chunk_name: str,
) -> list[dict]:
    """Build message content with text and images.

    Args:
        chunk: Text content chunk
        chunk_images: Images for this chunk
        chunk_name: Human-readable chunk identifier

    Returns:
        List of content blocks for Anthropic API
    """
    content = [
        {
            "type": "text",
            "text": f"Document: {chunk_name}\n\n{chunk}",
        }
    ]

    for img_path in chunk_images:
        if not img_path.exists():
            continue

        try:
            img_data = base64.standard_b64encode(img_path.read_bytes()).decode("utf-8")

            # Detect media type
            media_type = "image/jpeg"
            if img_path.suffix.lower() == ".png":
                media_type = "image/png"
            elif img_path.suffix.lower() == ".webp":
                media_type = "image/webp"

            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": img_data,
                },
            })
        except Exception as e:
            logger.warning(f"Failed to load image {img_path}: {e}")

    return content
```

**Update DateExtractor._process_date_chunk:**

```python
# BEFORE (lines 497-522):
content = [
    {
        "type": "text",
        "text": f"Document: {chunk_name}\n\n{chunk}",
    }
]

for img_path in chunk_images:
    if img_path.exists():
        try:
            img_data = base64.standard_b64encode(img_path.read_bytes()).decode("utf-8")
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": img_data,
                    },
                }
            )
        except Exception as e:
            logger.warning(f"Failed to load image {img_path}: {e}")

# AFTER (1 line):
content = self._build_message_content(chunk, chunk_images, chunk_name)
```

**Repeat for:**
- `LandTenureExtractor.extract` (lines 695-726)
- `ProjectIDExtractor.extract` (lines 886-916)

**Reduction:** 87 lines → 35 lines (52 lines saved)

---

### Step 1.2: Response Parsing Helper

**Create method in BaseExtractor:**

```python
def _parse_extraction_response(
    self,
    response,
    extractor_type: str,
) -> list[dict]:
    """Parse and validate extraction response.

    Args:
        response: Anthropic API response
        extractor_type: Type of extractor ("date", "tenure", "project_id")

    Returns:
        List of validated extraction dictionaries

    Raises:
        ValueError: If response is invalid
    """
    response_text = response.content[0].text
    json_str = extract_json_from_response(response_text)
    return validate_and_parse_extraction_response(json_str, extractor_type)
```

**Update all extractors:**

```python
# BEFORE (appears 3× in different extractors):
response_text = response.content[0].text
json_str = extract_json_from_response(response_text)
extracted_data = validate_and_parse_extraction_response(json_str, "date")

# AFTER:
extracted_data = self._parse_extraction_response(response, "date")
```

**Reduction:** 9 lines → 3 lines (6 lines saved per extractor = 18 lines total)

---

### Step 1.3: Deduplication Helper

**Create method in BaseExtractor:**

```python
def _deduplicate_fields(
    self,
    fields: list[ExtractedField],
    key_fn: Callable[[ExtractedField], Any],
    use_fuzzy_matching: bool = False,
) -> list[ExtractedField]:
    """Deduplicate extracted fields.

    Args:
        fields: List of extracted fields
        key_fn: Function to generate deduplication key
        use_fuzzy_matching: Enable fuzzy matching for names (tenure only)

    Returns:
        Deduplicated list of fields
    """
    if not fields:
        return []

    deduplicated = {}

    for field in fields:
        if use_fuzzy_matching and field.field_type == "owner_name":
            # Fuzzy matching for land tenure names
            matched_key = self._find_fuzzy_match(field, deduplicated)
            if matched_key:
                # Keep higher confidence version
                if field.confidence > deduplicated[matched_key].confidence:
                    del deduplicated[matched_key]
                    deduplicated[key_fn(field)] = field
            else:
                deduplicated[key_fn(field)] = field
        else:
            # Exact matching
            key = key_fn(field)
            if key not in deduplicated or field.confidence > deduplicated[key].confidence:
                deduplicated[key] = field

    return list(deduplicated.values())

def _find_fuzzy_match(
    self,
    field: ExtractedField,
    existing: dict,
) -> Any | None:
    """Find fuzzy match for owner name field."""
    from rapidfuzz import fuzz

    best_key = None
    best_similarity = 0.0

    for key in existing:
        if not isinstance(key, tuple) or key[0] != "owner_name":
            continue

        existing_name = str(key[1])
        current_name = str(field.value)

        partial_sim = fuzz.partial_ratio(existing_name.lower(), current_name.lower()) / 100.0
        token_sim = fuzz.token_set_ratio(existing_name.lower(), current_name.lower()) / 100.0
        similarity = max(partial_sim, token_sim)

        if similarity > best_similarity:
            best_similarity = similarity
            best_key = key

    return best_key if best_similarity >= 0.75 else None
```

**Update all extractors:**

```python
# BEFORE (DateExtractor, lines 633-639):
deduplicated = {}
for field in all_fields:
    key = (field.field_type, str(field.value))
    if key not in deduplicated or field.confidence > deduplicated[key].confidence:
        deduplicated[key] = field
fields = list(deduplicated.values())

# AFTER:
fields = self._deduplicate_fields(
    all_fields,
    key_fn=lambda f: (f.field_type, str(f.value)),
)

# BEFORE (LandTenureExtractor, lines 777-823 - includes fuzzy matching):
deduplicated = {}
for field in all_fields:
    if field.field_type == "owner_name" and settings.land_tenure_fuzzy_match:
        # ... 30 lines of fuzzy matching logic ...
    else:
        key = (field.field_type, str(field.value))
        if key not in deduplicated or field.confidence > deduplicated[key].confidence:
            deduplicated[key] = field
fields = list(deduplicated.values())

# AFTER:
fields = self._deduplicate_fields(
    all_fields,
    key_fn=lambda f: (f.field_type, str(f.value)),
    use_fuzzy_matching=settings.land_tenure_fuzzy_match,
)
```

**Reduction:** 47 lines → 10 lines (37 lines saved)

---

### Step 1.4: Use Existing Retry Utility

**Current:** `_call_api_with_retry` is 75 lines in BaseExtractor
**Available:** `utils/common/retry.py` has `@with_retry` decorator (unused!)

**Remove from BaseExtractor:**

```python
# DELETE lines 109-184 (75 lines)
async def _call_api_with_retry(
    self,
    api_call: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 32.0,
    **kwargs,
) -> Any:
    # ... 75 lines of retry logic ...
```

**Replace with:**

```python
# At top of file
from ..utils.common.retry import with_retry
from anthropic import (
    RateLimitError,
    InternalServerError,
    APIConnectionError,
    APITimeoutError,
)

# In BaseExtractor
@with_retry(
    max_attempts=3,
    exceptions=(RateLimitError, InternalServerError, APIConnectionError, APITimeoutError),
)
async def _call_api(self, **kwargs) -> Any:
    """Call Anthropic API with automatic retry on transient errors."""
    return await self.client.messages.create(**kwargs)
```

**Update all API calls:**

```python
# BEFORE:
response = await self._call_api_with_retry(
    self.client.messages.create,
    model=settings.llm_model,
    max_tokens=settings.llm_max_tokens,
    # ... more kwargs
)

# AFTER:
response = await self._call_api(
    model=settings.llm_model,
    max_tokens=settings.llm_max_tokens,
    # ... more kwargs
)
```

**Reduction:** 75 lines (entire duplicate retry implementation removed)

---

### Phase 1 Testing

**Test checklist:**
- [ ] All existing tests pass
- [ ] Cache behavior unchanged
- [ ] API retry logic works (simulate 429 errors)
- [ ] Fuzzy name matching still works (land tenure)
- [ ] Image loading errors handled gracefully

**Run tests:**
```bash
pytest tests/test_llm_extractors.py -v
pytest tests/test_metadata_extraction.py -v
```

**Phase 1 Completion:**
- Lines reduced: 52 + 18 + 37 + 75 = **182 lines**
- Time: 1-2 days
- Risk: Low (pure refactoring, no behavior change)

---

## Phase 2: Unified Extractor Architecture

**Goal:** Consolidate 3 extractor classes into single configurable class.

### Step 2.1: Create Extraction Configuration

**Create new file:** `extractors/extraction_config.py`

```python
"""Configuration for extraction types."""

from dataclasses import dataclass
from typing import Callable, Any
from pathlib import Path


@dataclass
class ExtractionConfig:
    """Configuration for a specific extraction type."""

    name: str  # "date_extraction", "land_tenure_extraction", etc.
    field_type: str  # "date", "tenure", "project_id"
    prompt: str  # System prompt for extraction
    cache_key_suffix: str  # Suffix for cache keys
    verification_fn: Callable[[list[dict], str], list[dict]] | None = None
    post_process_fn: Callable[[list[dict]], list[dict]] | None = None


def _filter_invalid_project_ids(data: list[dict]) -> list[dict]:
    """Filter invalid project IDs (imported from llm_extractors)."""
    from .llm_extractors import _filter_invalid_project_ids as filter_fn
    return filter_fn(data)


# Import prompts (will move to YAML in Phase 3)
from .llm_extractors import (
    DATE_EXTRACTION_PROMPT,
    LAND_TENURE_EXTRACTION_PROMPT,
    PROJECT_ID_EXTRACTION_PROMPT,
)
from .verification import verify_date_extraction


EXTRACTION_CONFIGS = {
    "date": ExtractionConfig(
        name="date_extraction",
        field_type="date",
        prompt=DATE_EXTRACTION_PROMPT,
        cache_key_suffix="dates",
        verification_fn=verify_date_extraction,
    ),
    "tenure": ExtractionConfig(
        name="land_tenure_extraction",
        field_type="tenure",
        prompt=LAND_TENURE_EXTRACTION_PROMPT,
        cache_key_suffix="tenure",
        verification_fn=None,
    ),
    "project_id": ExtractionConfig(
        name="project_id_extraction",
        field_type="project_id",
        prompt=PROJECT_ID_EXTRACTION_PROMPT,
        cache_key_suffix="project_ids",
        verification_fn=None,
        post_process_fn=_filter_invalid_project_ids,
    ),
}
```

---

### Step 2.2: Create Unified Extractor

**Create new file:** `extractors/unified.py`

```python
"""Unified extractor with configuration-based specialization."""

import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import Literal

from anthropic import AsyncAnthropic

from .llm_extractors import (
    BaseExtractor,
    ExtractedField,
    extract_json_from_response,
    validate_and_parse_extraction_response,
    _track_api_call,
)
from .extraction_config import EXTRACTION_CONFIGS, ExtractionConfig
from ..config.settings import settings

logger = logging.getLogger(__name__)


class UnifiedExtractor(BaseExtractor):
    """Unified extractor for all field types.

    Replaces DateExtractor, LandTenureExtractor, and ProjectIDExtractor
    with a single configurable class.

    Example:
        >>> date_ext = UnifiedExtractor("date")
        >>> dates = await date_ext.extract(markdown, images, "doc.pdf")
    """

    def __init__(
        self,
        extraction_type: Literal["date", "tenure", "project_id"],
        client: AsyncAnthropic | None = None,
    ):
        """Initialize unified extractor.

        Args:
            extraction_type: Type of extraction ("date", "tenure", "project_id")
            client: Optional AsyncAnthropic client
        """
        self.config = EXTRACTION_CONFIGS[extraction_type]
        super().__init__(cache_namespace=self.config.name, client=client)

    async def extract(
        self,
        markdown_content: str,
        images: list[Path],
        document_name: str,
    ) -> list[ExtractedField]:
        """Extract fields from markdown and images.

        Args:
            markdown_content: Document text in markdown format
            images: List of paths to images
            document_name: Name of the document being processed

        Returns:
            List of extracted fields
        """
        # Check cache
        cache_key = f"{document_name}_{self.config.cache_key_suffix}"
        if cached := self.cache.get(cache_key):
            logger.debug(f"Cache hit for {document_name} {self.config.field_type}")
            _track_api_call(
                model=settings.llm_model,
                extractor=self.config.field_type,
                document_name=document_name,
                usage={},
                duration=0.0,
                cached=True,
            )
            return [ExtractedField(**f) for f in cached]

        # Split content and distribute images
        chunks = self._chunk_content(markdown_content)
        chunk_images = self._distribute_images(images, len(chunks))

        # Process chunks in parallel
        chunk_tasks = []
        for i, chunk in enumerate(chunks):
            chunk_name = (
                f"{document_name} (chunk {i+1}/{len(chunks)})"
                if len(chunks) > 1
                else document_name
            )
            task = self._process_chunk(chunk, chunk_images[i], chunk_name, i)
            chunk_tasks.append(task)

        chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)

        # Collect successful results
        all_fields = []
        for i, result in enumerate(chunk_results):
            if isinstance(result, Exception):
                chunk_name = (
                    f"{document_name} (chunk {i+1}/{len(chunks)})"
                    if len(chunks) > 1
                    else document_name
                )
                logger.error(f"Extraction failed for {chunk_name}: {result}", exc_info=result)
            elif result:
                all_fields.extend(result)

        # Deduplicate
        use_fuzzy = (
            self.config.field_type == "tenure" and settings.land_tenure_fuzzy_match
        )
        fields = self._deduplicate_fields(
            all_fields,
            key_fn=lambda f: (f.field_type, str(f.value)),
            use_fuzzy_matching=use_fuzzy,
        )

        # Cache results
        self.cache.set(cache_key, [f.model_dump() for f in fields])

        logger.info(
            f"Extracted {len(fields)} unique {self.config.field_type} fields "
            f"from {document_name} ({len(all_fields)} total before dedup)"
        )
        return fields

    async def _process_chunk(
        self,
        chunk: str,
        chunk_images: list[Path],
        chunk_name: str,
        chunk_index: int,
    ) -> list[ExtractedField]:
        """Process a single chunk."""
        # Build message content
        content = self._build_message_content(chunk, chunk_images, chunk_name)

        # Call API
        try:
            start_time = time.time()
            response = await self._call_api(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                system=[{
                    "type": "text",
                    "text": self.config.prompt,
                    "cache_control": {"type": "ephemeral"}
                }],
                messages=[{"role": "user", "content": content}],
                timeout=settings.api_call_timeout_seconds,
            )
            duration = time.time() - start_time

            # Track cost
            _track_api_call(
                model=settings.llm_model,
                extractor=self.config.field_type,
                document_name=chunk_name,
                usage=response.usage.model_dump() if hasattr(response, "usage") else {},
                duration=duration,
                cached=False,
            )

            # Parse response
            extracted_data = self._parse_extraction_response(response, self.config.field_type)

            # Post-process if configured
            if self.config.post_process_fn:
                extracted_data = self.config.post_process_fn(extracted_data)

            # Verify if configured
            if self.config.verification_fn:
                extracted_data = self.config.verification_fn(extracted_data, chunk)

            # Convert to ExtractedField objects
            chunk_fields = [ExtractedField(**data) for data in extracted_data]

            logger.info(f"Extracted {len(chunk_fields)} fields from {chunk_name}")
            return chunk_fields

        except ValueError as e:
            logger.error(f"Invalid response from LLM for {chunk_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Extraction failed for {chunk_name}: {e}", exc_info=True)
            raise


def create_extractor(
    extraction_type: Literal["date", "tenure", "project_id"],
    client: AsyncAnthropic | None = None,
) -> UnifiedExtractor:
    """Factory function for creating extractors.

    Args:
        extraction_type: Type of extraction
        client: Optional AsyncAnthropic client

    Returns:
        Configured UnifiedExtractor instance
    """
    return UnifiedExtractor(extraction_type, client=client)
```

---

### Step 2.3: Create Backwards Compatibility Wrappers

**Update `extractors/__init__.py`:**

```python
"""LLM extractors with backwards compatibility."""

import warnings
from typing import Any

from .unified import UnifiedExtractor, create_extractor
from .llm_extractors import ExtractedField, extract_fields_with_llm

__all__ = [
    "UnifiedExtractor",
    "create_extractor",
    "ExtractedField",
    "extract_fields_with_llm",
    # Deprecated:
    "DateExtractor",
    "LandTenureExtractor",
    "ProjectIDExtractor",
]


class DateExtractor(UnifiedExtractor):
    """DEPRECATED: Use UnifiedExtractor('date') instead.

    This class is provided for backwards compatibility only.
    It will be removed in version 3.0.0.
    """

    def __init__(self, client: Any = None):
        warnings.warn(
            "DateExtractor is deprecated. Use UnifiedExtractor('date') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__("date", client)


class LandTenureExtractor(UnifiedExtractor):
    """DEPRECATED: Use UnifiedExtractor('tenure') instead.

    This class is provided for backwards compatibility only.
    It will be removed in version 3.0.0.
    """

    def __init__(self, client: Any = None):
        warnings.warn(
            "LandTenureExtractor is deprecated. Use UnifiedExtractor('tenure') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__("tenure", client)


class ProjectIDExtractor(UnifiedExtractor):
    """DEPRECATED: Use UnifiedExtractor('project_id') instead.

    This class is provided for backwards compatibility only.
    It will be removed in version 3.0.0.
    """

    def __init__(self, client: Any = None):
        warnings.warn(
            "ProjectIDExtractor is deprecated. Use UnifiedExtractor('project_id') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__("project_id", client)
```

---

### Step 2.4: Update extract_fields_with_llm

**In `llm_extractors.py`:**

```python
async def extract_fields_with_llm(
    session_id: str, evidence_data: dict[str, Any]
) -> dict[str, Any]:
    """Extract structured fields from evidence using LLM.

    Args:
        session_id: Session identifier
        evidence_data: Evidence JSON with snippets

    Returns:
        Dictionary with extracted fields
    """
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not set - required for LLM extraction")

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Use unified extractors
    from .unified import create_extractor

    date_extractor = create_extractor("date", client)
    tenure_extractor = create_extractor("tenure", client)
    project_id_extractor = create_extractor("project_id", client)

    all_dates = []
    all_tenure = []
    all_project_ids = []

    # ... rest of function unchanged ...
```

---

### Phase 2 Testing

**Test migration:**

```bash
# Run all existing tests (should pass with deprecation warnings)
pytest tests/ -v

# Run specific extractor tests
pytest tests/test_llm_extractors.py -v
pytest tests/test_metadata_extraction.py -v

# Verify deprecation warnings work
pytest tests/test_llm_extractors.py -W error::DeprecationWarning  # Should fail
pytest tests/test_llm_extractors.py -W default  # Should pass with warnings
```

**Phase 2 Completion:**
- Lines reduced: ~300-400 lines (3 classes → 1 unified class)
- Time: 3-5 days
- Risk: Medium (architecture change, but backwards compatible)

---

## Phase 3: Prompt Externalization

**Goal:** Move prompts from code to YAML configuration.

### Step 3.1: Create Prompt YAML Files

**Create:** `config/prompts/date_extraction_v1.yaml`

```yaml
version: "1.0"
name: "Date Extraction"
description: "Extract and classify dates from carbon credit project documents"

system_prompt: |
  You are a date extraction specialist for carbon credit project reviews.

  Extract ALL dates from documents and classify each by type.

date_types:
  - name: project_start_date
    description: "When the project officially began"
  - name: crediting_period_start
    description: "Beginning of crediting period"
  - name: crediting_period_end
    description: "End of crediting period"
  - name: imagery_date
    description: "When satellite/aerial imagery was acquired"
  - name: sampling_date
    description: "When soil/field sampling occurred"
  - name: baseline_date
    description: "When baseline assessment was conducted"
  - name: monitoring_date
    description: "When monitoring report was completed"
  - name: submission_date
    description: "When documents were submitted"

instructions: |
  1. Find ALL date mentions in the document
  2. Use context to determine the correct date type
  3. Parse dates in ANY format (MM/DD/YYYY, "August 15 2022", etc.)
  4. Handle ranges ("January 1, 2022 - December 31, 2031")
  5. Assign confidence based on context clarity (1.0 = explicit, 0.8 = inferred, 0.5 = ambiguous)

  CRITICAL: Only extract dates actually present in the document. Do not infer or assume dates.

output_format: |
  Return JSON array:
  [
    {
      "value": "2022-01-01",
      "field_type": "project_start_date",
      "source": "Section 1.8",
      "confidence": 0.95,
      "reasoning": "Document explicitly states 'Project Start Date: 01/01/2022'",
      "raw_text": "Project Start Date: 01/01/2022"
    }
  ]
```

**Create:** `config/prompts/land_tenure_extraction_v1.yaml`

**Create:** `config/prompts/project_id_extraction_v1.yaml`

---

### Step 3.2: Create Prompt Loader

**Create:** `config/prompts/loader.py`

```python
"""Load and manage extraction prompts from YAML files."""

import yaml
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).parent


def load_prompt_config(prompt_name: str, version: str = "v1") -> dict[str, Any]:
    """Load prompt configuration from YAML.

    Args:
        prompt_name: Name of prompt (e.g., "date_extraction")
        version: Version to load (default: "v1")

    Returns:
        Prompt configuration dictionary

    Raises:
        FileNotFoundError: If prompt file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    prompt_file = PROMPTS_DIR / f"{prompt_name}_{version}.yaml"

    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    with open(prompt_file) as f:
        config = yaml.safe_load(f)

    return config


def build_prompt_from_config(config: dict[str, Any]) -> str:
    """Build full extraction prompt from configuration.

    Args:
        config: Prompt configuration from YAML

    Returns:
        Formatted prompt string
    """
    prompt_parts = [config["system_prompt"]]

    # Add date types if present
    if "date_types" in config:
        prompt_parts.append("\nDate Types:")
        for date_type in config["date_types"]:
            prompt_parts.append(f"- {date_type['name']}: {date_type['description']}")

    # Add field types if present
    if "field_types" in config:
        prompt_parts.append("\nFields to Extract:")
        for field in config["field_types"]:
            prompt_parts.append(f"- {field['name']}: {field['description']}")

    # Add instructions
    prompt_parts.append(f"\n{config['instructions']}")

    # Add output format
    if "output_format" in config:
        prompt_parts.append(f"\n{config['output_format']}")

    return "\n".join(prompt_parts)


def load_extraction_prompt(extraction_type: str, version: str = "v1") -> str:
    """Load and build extraction prompt.

    Args:
        extraction_type: Type of extraction ("date", "tenure", "project_id")
        version: Prompt version (default: "v1")

    Returns:
        Full extraction prompt string
    """
    prompt_name_map = {
        "date": "date_extraction",
        "tenure": "land_tenure_extraction",
        "project_id": "project_id_extraction",
    }

    prompt_name = prompt_name_map[extraction_type]
    config = load_prompt_config(prompt_name, version)
    return build_prompt_from_config(config)
```

---

### Step 3.3: Update Extraction Config

**Update `extractors/extraction_config.py`:**

```python
"""Configuration for extraction types."""

from dataclasses import dataclass
from typing import Callable, Any
from pathlib import Path

# Import prompt loader
from ..config.prompts.loader import load_extraction_prompt


@dataclass
class ExtractionConfig:
    """Configuration for a specific extraction type."""

    name: str
    field_type: str
    prompt: str  # Loaded from YAML
    cache_key_suffix: str
    verification_fn: Callable[[list[dict], str], list[dict]] | None = None
    post_process_fn: Callable[[list[dict]], list[dict]] | None = None


def _filter_invalid_project_ids(data: list[dict]) -> list[dict]:
    """Filter invalid project IDs."""
    from .llm_extractors import _filter_invalid_project_ids as filter_fn
    return filter_fn(data)


from .verification import verify_date_extraction


EXTRACTION_CONFIGS = {
    "date": ExtractionConfig(
        name="date_extraction",
        field_type="date",
        prompt=load_extraction_prompt("date", version="v1"),  # From YAML!
        cache_key_suffix="dates",
        verification_fn=verify_date_extraction,
    ),
    "tenure": ExtractionConfig(
        name="land_tenure_extraction",
        field_type="tenure",
        prompt=load_extraction_prompt("tenure", version="v1"),  # From YAML!
        cache_key_suffix="tenure",
        verification_fn=None,
    ),
    "project_id": ExtractionConfig(
        name="project_id_extraction",
        field_type="project_id",
        prompt=load_extraction_prompt("project_id", version="v1"),  # From YAML!
        cache_key_suffix="project_ids",
        verification_fn=None,
        post_process_fn=_filter_invalid_project_ids,
    ),
}
```

---

### Step 3.4: Remove Embedded Prompts

**Delete from `llm_extractors.py`:**

```python
# DELETE lines 335-470 (127 lines):
DATE_EXTRACTION_PROMPT = """..."""
LAND_TENURE_EXTRACTION_PROMPT = """..."""
PROJECT_ID_EXTRACTION_PROMPT = r"""..."""
```

---

### Phase 3 Testing

```bash
# Test prompt loading
python -c "from src.registry_review_mcp.config.prompts.loader import load_extraction_prompt; print(load_extraction_prompt('date')[:100])"

# Run full test suite
pytest tests/ -v

# Test prompt versioning
python -c "from src.registry_review_mcp.config.prompts.loader import load_extraction_prompt; print(load_extraction_prompt('date', version='v1') == load_extraction_prompt('date'))"
```

**Phase 3 Completion:**
- Lines reduced: 127 lines (prompts moved to YAML)
- Time: 1-2 days
- Risk: Low (prompts unchanged, just moved)

---

## Final Cleanup

### Remove Deprecated Code (v3.0.0)

When ready to remove backwards compatibility:

**Delete from `llm_extractors.py`:**
- `DateExtractor` class (lines 472-646)
- `LandTenureExtractor` class (lines 648-831)
- `ProjectIDExtractor` class (lines 833-996)

**Update `extractors/__init__.py`:**
```python
# Remove deprecated imports
__all__ = [
    "UnifiedExtractor",
    "create_extractor",
    "ExtractedField",
    "extract_fields_with_llm",
]
```

---

## Rollback Plan

If issues arise during migration:

### Phase 1 Rollback
```bash
git revert <commit-hash>  # Revert helper methods
```

### Phase 2 Rollback
```bash
# Deprecation warnings allow keeping old code
# Simply stop using UnifiedExtractor, continue with deprecated classes
# Or: git revert <commit-hash>
```

### Phase 3 Rollback
```python
# In extraction_config.py, switch back to embedded prompts:
from .llm_extractors import DATE_EXTRACTION_PROMPT  # etc.

EXTRACTION_CONFIGS = {
    "date": ExtractionConfig(
        prompt=DATE_EXTRACTION_PROMPT,  # Use embedded instead of YAML
        # ...
    ),
}
```

---

## Success Metrics

Track these metrics before/after:

```python
# File size
wc -l src/registry_review_mcp/extractors/llm_extractors.py
# Before: 1,281 lines
# Target: ~754 lines

# Test coverage
pytest --cov=src/registry_review_mcp/extractors --cov-report=term-missing
# Maintain: >85% coverage

# Performance (run on test project)
time python -m src.registry_review_mcp.tools.evidence_tools <session-id>
# Target: No degradation (±5%)

# Code duplication
# Before: ~472 duplicate lines across 3 extractors
# After: ~28 lines (shared in BaseExtractor)
```

---

## Post-Migration Documentation

Update these docs after completion:

1. **Developer Guide:**
   - How to add new extraction types
   - Prompt versioning workflow
   - Configuration structure

2. **Architecture Decision Records (ADRs):**
   - ADR: Unified Extractor Architecture
   - ADR: External Prompt Management

3. **Migration Guide:**
   - For other projects using old extractors
   - Deprecation timeline

4. **Performance Benchmarks:**
   - Before/after metrics
   - Memory usage comparison

---

## Conclusion

This implementation guide provides a safe, incremental path to reduce code duplication while maintaining backwards compatibility. Each phase delivers value independently and can be deployed separately.

**Key principles:**
- Test after each step
- Maintain backwards compatibility
- Deploy incrementally
- Measure everything

The result will be a cleaner, more maintainable codebase that embraces the principle of subtraction: removing what obscures the essential structure.

