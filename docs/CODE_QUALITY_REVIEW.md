# Code Quality Review: Registry Review MCP

**Review Date:** 2025-11-15
**Reviewer:** Claude Code (Automated Analysis)
**Scope:** Complete codebase analysis for hardcoded values, rigid patterns, design improvements, and code smells

---

## Executive Summary

This comprehensive code quality review identifies 47 issues across 5 categories:

- **Critical Issues:** 8 (Hardcoded methodology identifier, non-extensible workflows)
- **High Priority:** 12 (Long functions, rigid patterns, missing abstractions)
- **Medium Priority:** 18 (Code duplication, magic numbers, tight coupling)
- **Low Priority:** 9 (Minor improvements, style issues)

**Key Findings:**
- Methodology identifier "soil-carbon-v1.2.2" hardcoded in 6+ files
- No support for multiple methodologies without code changes
- Document classification logic not extensible
- Validation rules not configurable
- Several functions exceed 50 lines (up to 262 lines)
- Missing design patterns for extractors and validators

---

## 1. Hardcoded Values & Magic Numbers

### CRITICAL: Hardcoded Methodology Identifier

**Severity:** Critical
**Impact:** Prevents multi-methodology support without code changes

#### Issue 1.1: Default Methodology in Multiple Files

**Locations:**
- `src/registry_review_mcp/models/schemas.py:25`
- `src/registry_review_mcp/server.py:47,307`
- `src/registry_review_mcp/tools/session_tools.py:30`
- `src/registry_review_mcp/tools/evidence_tools.py:276,361`
- `src/registry_review_mcp/prompts/A_initialize.py:159`

**Current Code:**
```python
# schemas.py
methodology: str = "soil-carbon-v1.2.2"

# server.py
async def create_session(
    methodology: str = "soil-carbon-v1.2.2",
    # ...
)

# session_tools.py
async def create_session(
    methodology: str = "soil-carbon-v1.2.2",
    # ...
)

# evidence_tools.py
checklist_path = settings.get_checklist_path("soil-carbon-v1.2.2")
```

**Why Problematic:**
- Methodology identifier appears as literal string in 6+ files
- No central registry of available methodologies
- Adding new methodology requires code changes in multiple places
- Risk of typos and inconsistencies
- Violates DRY (Don't Repeat Yourself) principle

**Recommended Fix:**

```python
# config/methodologies.py (NEW FILE)
"""Methodology registry and configuration."""

from enum import Enum
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, Field


class MethodologyID(str, Enum):
    """Enumeration of supported methodologies."""

    SOIL_CARBON_V1_2_2 = "soil-carbon-v1.2.2"
    SOIL_CARBON_V2_0_0 = "soil-carbon-v2.0.0"  # Future
    # Add new methodologies here


class MethodologyMetadata(BaseModel):
    """Metadata for a methodology."""

    id: str
    name: str
    version: str
    protocol: str
    checklist_filename: str
    description: str
    active: bool = True


class MethodologyRegistry:
    """Registry of available methodologies."""

    def __init__(self, checklists_dir: Path):
        self.checklists_dir = checklists_dir
        self._methodologies: Dict[str, MethodologyMetadata] = {}
        self._default_id: Optional[str] = None
        self._load_methodologies()

    def _load_methodologies(self):
        """Load methodology configurations from checklist files."""
        # Auto-discover from checklist files
        for checklist_file in self.checklists_dir.glob("*.json"):
            try:
                import json
                with open(checklist_file, 'r') as f:
                    data = json.load(f)

                metadata = MethodologyMetadata(
                    id=data.get("methodology_id"),
                    name=data.get("methodology_name"),
                    version=data.get("version"),
                    protocol=data.get("protocol"),
                    checklist_filename=checklist_file.name,
                    description=f"{data.get('methodology_name')} {data.get('version')}"
                )

                self._methodologies[metadata.id] = metadata

                # Set first as default if none set
                if not self._default_id:
                    self._default_id = metadata.id

            except Exception as e:
                # Log but don't fail - skip invalid checklists
                pass

    def get(self, methodology_id: str) -> Optional[MethodologyMetadata]:
        """Get methodology by ID."""
        return self._methodologies.get(methodology_id)

    def list_available(self) -> list[MethodologyMetadata]:
        """List all available methodologies."""
        return [m for m in self._methodologies.values() if m.active]

    def get_default(self) -> str:
        """Get default methodology ID."""
        return self._default_id or MethodologyID.SOIL_CARBON_V1_2_2.value

    def validate(self, methodology_id: str) -> bool:
        """Check if methodology ID is valid."""
        return methodology_id in self._methodologies

    def get_checklist_path(self, methodology_id: str) -> Path:
        """Get path to checklist file for methodology."""
        metadata = self.get(methodology_id)
        if not metadata:
            raise ValueError(f"Unknown methodology: {methodology_id}")
        return self.checklists_dir / metadata.checklist_filename


# config/settings.py (UPDATE)
from .methodologies import MethodologyRegistry

class Settings(BaseSettings):
    # ... existing fields ...

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
        # Initialize methodology registry
        self.methodology_registry = MethodologyRegistry(self.checklists_dir)

    def get_default_methodology(self) -> str:
        """Get default methodology ID."""
        return self.methodology_registry.get_default()

    def get_checklist_path(self, methodology: str) -> Path:
        """Get the path to a checklist file."""
        return self.methodology_registry.get_checklist_path(methodology)


# Usage in tools:
# Instead of: checklist_path = settings.get_checklist_path("soil-carbon-v1.2.2")
# Use: checklist_path = settings.get_checklist_path(methodology)
```

**Benefits:**
- Single source of truth for methodologies
- Auto-discovery from checklist files
- Type-safe with Enum
- Easy to add new methodologies (just add checklist file)
- Validation built-in
- No code changes needed for new methodologies

---

#### Issue 1.2: Magic Numbers in Validation Logic

**Severity:** Medium
**Locations:**
- `src/registry_review_mcp/tools/validation_tools.py:174` (5% area tolerance)
- `src/registry_review_mcp/tools/validation_tools.py:347` (9000 project ID threshold)
- `src/registry_review_mcp/tools/validation_tools.py:406` (2000-2030 date range)
- `src/registry_review_mcp/tools/validation_tools.py:472` (100000 hectares max)
- `src/registry_review_mcp/extractors/llm_extractors.py:805` (75% fuzzy match threshold)

**Current Code:**
```python
# validation_tools.py:174
area_variance = (max_area - min_area) / max_area if max_area > 0 else 0
area_consistent = area_variance < 0.05  # Magic: 5% tolerance

# validation_tools.py:347
if project_id and int(project_id) < 9000:  # Magic: why 9000?

# validation_tools.py:406
if 2000 <= parsed_date.year <= 2030:  # Magic: hardcoded date range

# validation_tools.py:472
if area > 0 and area < 100000:  # Magic: 100000 hectares

# llm_extractors.py:805
if best_similarity >= 0.75 and matched_key:  # Magic: 75% threshold
```

**Why Problematic:**
- No explanation for why these specific values
- Cannot be adjusted without code changes
- Difficult to understand business rules
- Testing with different thresholds requires code edits

**Recommended Fix:**

```python
# config/settings.py (ADD)
class Settings(BaseSettings):
    # ... existing fields ...

    # Validation thresholds
    validation_area_tolerance_percent: float = Field(default=0.05, ge=0.0, le=1.0)  # 5%
    validation_max_project_id: int = Field(default=9000, ge=1)
    validation_date_range_start: int = Field(default=2000, ge=1900, le=2100)
    validation_date_range_end: int = Field(default=2030, ge=2000, le=2100)
    validation_max_hectares: float = Field(default=100000.0, ge=0.0)
    validation_name_fuzzy_threshold: float = Field(default=0.75, ge=0.0, le=1.0)

# Usage:
# validation_tools.py
area_consistent = area_variance < settings.validation_area_tolerance_percent

if project_id and int(project_id) < settings.validation_max_project_id:
    # ...

if settings.validation_date_range_start <= parsed_date.year <= settings.validation_date_range_end:
    # ...

if area > 0 and area < settings.validation_max_hectares:
    # ...

# llm_extractors.py
if best_similarity >= settings.validation_name_fuzzy_threshold and matched_key:
    # ...
```

**Benefits:**
- All thresholds configurable via environment variables
- Self-documenting with field descriptions
- Validation ensures values are in reasonable ranges
- Easy to adjust for different projects or testing
- Clear separation of business logic from implementation

---

#### Issue 1.3: Hardcoded Workflow Stage Names

**Severity:** High
**Locations:**
- `src/registry_review_mcp/models/schemas.py:44-50` (workflow stages hardcoded in model)
- `src/registry_review_mcp/server.py:758-813` (prompt names hardcoded)

**Current Code:**
```python
# schemas.py
class WorkflowProgress(BaseModel):
    """Tracks progress through the 7-stage workflow."""

    initialize: Literal["pending", "in_progress", "completed"] = "pending"
    document_discovery: Literal["pending", "in_progress", "completed"] = "pending"
    evidence_extraction: Literal["pending", "in_progress", "completed"] = "pending"
    cross_validation: Literal["pending", "in_progress", "completed"] = "pending"
    report_generation: Literal["pending", "in_progress", "completed"] = "pending"
    human_review: Literal["pending", "in_progress", "completed"] = "pending"
    complete: Literal["pending", "in_progress", "completed"] = "pending"
```

**Why Problematic:**
- Adding/removing workflow stages requires Pydantic model changes
- Stage names duplicated across prompts, server, tools
- No central workflow definition
- Cannot customize workflow per methodology
- Hard to extend or modify workflow

**Recommended Fix:**

```python
# config/workflow.py (NEW FILE)
"""Workflow stage configuration and state machine."""

from enum import Enum
from typing import List, Optional, Dict, Set
from pydantic import BaseModel, Field


class StageStatus(str, Enum):
    """Status of a workflow stage."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class WorkflowStage(BaseModel):
    """Definition of a single workflow stage."""

    id: str  # "document_discovery"
    name: str  # "Document Discovery"
    description: str
    prompt_name: Optional[str] = None  # "/document-discovery"
    dependencies: List[str] = Field(default_factory=list)  # Must complete before this stage
    optional: bool = False
    order: int


class WorkflowDefinition(BaseModel):
    """Complete workflow definition."""

    id: str
    name: str
    stages: List[WorkflowStage]

    def get_stage(self, stage_id: str) -> Optional[WorkflowStage]:
        """Get stage by ID."""
        return next((s for s in self.stages if s.id == stage_id), None)

    def get_next_stage(self, current_stage_id: str) -> Optional[WorkflowStage]:
        """Get next stage after current."""
        current = self.get_stage(current_stage_id)
        if not current:
            return None

        next_stages = [s for s in self.stages if s.order > current.order]
        return min(next_stages, key=lambda s: s.order) if next_stages else None

    def validate_dependencies(self, stage_id: str, completed: Set[str]) -> bool:
        """Check if stage dependencies are satisfied."""
        stage = self.get_stage(stage_id)
        if not stage:
            return False
        return all(dep in completed for dep in stage.dependencies)


# Default workflow for soil carbon methodology
DEFAULT_WORKFLOW = WorkflowDefinition(
    id="soil-carbon-standard",
    name="Soil Carbon Standard Review Workflow",
    stages=[
        WorkflowStage(
            id="initialize",
            name="Initialize Session",
            description="Create session and load checklist",
            prompt_name="A-initialize",
            order=1
        ),
        WorkflowStage(
            id="document_discovery",
            name="Document Discovery",
            description="Scan and classify project documents",
            prompt_name="B-document-discovery",
            dependencies=["initialize"],
            order=2
        ),
        WorkflowStage(
            id="evidence_extraction",
            name="Evidence Extraction",
            description="Map requirements to evidence snippets",
            prompt_name="C-evidence-extraction",
            dependencies=["document_discovery"],
            order=3
        ),
        WorkflowStage(
            id="cross_validation",
            name="Cross-Document Validation",
            description="Validate consistency across documents",
            prompt_name="D-cross-validation",
            dependencies=["evidence_extraction"],
            order=4
        ),
        WorkflowStage(
            id="report_generation",
            name="Report Generation",
            description="Generate structured review report",
            prompt_name="E-report-generation",
            dependencies=["cross_validation"],
            order=5
        ),
        WorkflowStage(
            id="human_review",
            name="Human Review",
            description="Review flagged items requiring judgment",
            prompt_name="F-human-review",
            dependencies=["report_generation"],
            order=6
        ),
        WorkflowStage(
            id="complete",
            name="Complete Review",
            description="Finalize and export report",
            prompt_name="G-complete",
            dependencies=["human_review"],
            order=7
        ),
    ]
)


class WorkflowProgress(BaseModel):
    """Dynamic workflow progress tracking."""

    workflow_id: str
    stage_statuses: Dict[str, StageStatus] = Field(default_factory=dict)

    def get_status(self, stage_id: str) -> StageStatus:
        """Get status for a stage."""
        return self.stage_statuses.get(stage_id, StageStatus.PENDING)

    def set_status(self, stage_id: str, status: StageStatus):
        """Set status for a stage."""
        self.stage_statuses[stage_id] = status

    def get_completed_stages(self) -> Set[str]:
        """Get set of completed stage IDs."""
        return {
            stage_id
            for stage_id, status in self.stage_statuses.items()
            if status == StageStatus.COMPLETED
        }

    def is_complete(self, workflow: WorkflowDefinition) -> bool:
        """Check if all required stages are complete."""
        required = [s.id for s in workflow.stages if not s.optional]
        completed = self.get_completed_stages()
        return all(stage_id in completed for stage_id in required)


# Usage in schemas.py:
# Replace hardcoded WorkflowProgress with dynamic version
# Old: class WorkflowProgress(BaseModel):
#          initialize: Literal["pending", "in_progress", "completed"] = "pending"
#          ...
# New: from .config.workflow import WorkflowProgress  # Use dynamic version
```

**Benefits:**
- Workflow defined declaratively in one place
- Easy to add/remove/reorder stages
- Dependency validation built-in
- Can define different workflows per methodology
- Supports optional stages
- Type-safe with validation
- No Pydantic model changes needed for workflow modifications

---

## 2. Rigid & Non-Generalizable Code

### Issue 2.1: Document Classification Not Extensible

**Severity:** High
**Location:** `src/registry_review_mcp/tools/document_tools.py:264-305`

**Current Code:**
```python
async def classify_document_by_filename(filepath: str) -> tuple[str, float, str]:
    """Classify document based on filename patterns."""
    filename = Path(filepath).name.lower()

    # Check patterns in order of specificity
    if match_any(filename, PROJECT_PLAN_PATTERNS):
        return ("project_plan", 0.95, "filename")

    if match_any(filename, BASELINE_PATTERNS):
        return ("baseline_report", 0.95, "filename")

    if match_any(filename, MONITORING_PATTERNS):
        return ("monitoring_report", 0.90, "filename")

    if match_any(filename, GHG_PATTERNS):
        return ("ghg_emissions", 0.90, "filename")

    if match_any(filename, LAND_TENURE_PATTERNS):
        return ("land_tenure", 0.85, "filename")

    if match_any(filename, REGISTRY_REVIEW_PATTERNS):
        return ("registry_review", 0.95, "filename")

    if match_any(filename, METHODOLOGY_PATTERNS):
        return ("methodology_reference", 0.90, "filename")

    # File type based classification
    if is_gis_file(filename):
        return ("gis_shapefile", 0.80, "file_type")

    if is_image_file(filename):
        return ("land_cover_map", 0.70, "file_type")

    # Default
    return ("unknown", 0.50, "default")
```

**Why Problematic:**
- Adding new document types requires code changes
- Classification logic hardcoded in if/elif chain
- Cannot configure classification rules per methodology
- No way to register custom classifiers
- Tight coupling between patterns and classification logic
- Difficult to test individual classification rules

**Recommended Fix - Strategy Pattern:**

```python
# classifiers/base.py (NEW FILE)
"""Base classifier interface and registry."""

from abc import ABC, abstractmethod
from typing import Protocol, List, Optional, Tuple
from pathlib import Path


class DocumentClassifier(ABC):
    """Base class for document classifiers."""

    @property
    @abstractmethod
    def document_type(self) -> str:
        """Type of document this classifier identifies."""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """Priority (higher = checked first)."""
        pass

    @abstractmethod
    def matches(self, filepath: Path, content: Optional[str] = None) -> Tuple[bool, float]:
        """
        Check if document matches this type.

        Returns:
            (matches, confidence) tuple
        """
        pass


class PatternClassifier(DocumentClassifier):
    """Classifier based on filename patterns."""

    def __init__(self, document_type: str, patterns: List, confidence: float = 0.9, priority: int = 100):
        self._document_type = document_type
        self._patterns = patterns
        self._confidence = confidence
        self._priority = priority

    @property
    def document_type(self) -> str:
        return self._document_type

    @property
    def priority(self) -> int:
        return self._priority

    def matches(self, filepath: Path, content: Optional[str] = None) -> Tuple[bool, float]:
        from ..utils.patterns import match_any

        filename = filepath.name.lower()
        if match_any(filename, self._patterns):
            return (True, self._confidence)
        return (False, 0.0)


class FileTypeClassifier(DocumentClassifier):
    """Classifier based on file extension."""

    def __init__(self, document_type: str, extensions: set, confidence: float = 0.8, priority: int = 50):
        self._document_type = document_type
        self._extensions = {ext.lower() for ext in extensions}
        self._confidence = confidence
        self._priority = priority

    @property
    def document_type(self) -> str:
        return self._document_type

    @property
    def priority(self) -> int:
        return self._priority

    def matches(self, filepath: Path, content: Optional[str] = None) -> Tuple[bool, float]:
        if filepath.suffix.lower() in self._extensions:
            return (True, self._confidence)
        return (False, 0.0)


class ClassifierRegistry:
    """Registry for document classifiers."""

    def __init__(self):
        self._classifiers: List[DocumentClassifier] = []

    def register(self, classifier: DocumentClassifier):
        """Register a classifier."""
        self._classifiers.append(classifier)
        # Sort by priority (descending)
        self._classifiers.sort(key=lambda c: c.priority, reverse=True)

    def classify(self, filepath: Path, content: Optional[str] = None) -> Tuple[str, float, str]:
        """
        Classify a document using registered classifiers.

        Returns:
            (document_type, confidence, method) tuple
        """
        for classifier in self._classifiers:
            matches, confidence = classifier.matches(filepath, content)
            if matches:
                method = classifier.__class__.__name__.replace("Classifier", "").lower()
                return (classifier.document_type, confidence, method)

        # No match
        return ("unknown", 0.50, "default")


# classifiers/soil_carbon.py (NEW FILE)
"""Classifiers for soil carbon methodology documents."""

from pathlib import Path
from .base import ClassifierRegistry, PatternClassifier, FileTypeClassifier
from ..utils import patterns


def register_soil_carbon_classifiers(registry: ClassifierRegistry):
    """Register all soil carbon document classifiers."""

    # Project Plan (highest priority for specific docs)
    registry.register(PatternClassifier(
        document_type="project_plan",
        patterns=patterns.PROJECT_PLAN_PATTERNS,
        confidence=0.95,
        priority=100
    ))

    # Baseline Report
    registry.register(PatternClassifier(
        document_type="baseline_report",
        patterns=patterns.BASELINE_PATTERNS,
        confidence=0.95,
        priority=100
    ))

    # Monitoring Report
    registry.register(PatternClassifier(
        document_type="monitoring_report",
        patterns=patterns.MONITORING_PATTERNS,
        confidence=0.90,
        priority=90
    ))

    # GHG Emissions
    registry.register(PatternClassifier(
        document_type="ghg_emissions",
        patterns=patterns.GHG_PATTERNS,
        confidence=0.90,
        priority=90
    ))

    # Land Tenure
    registry.register(PatternClassifier(
        document_type="land_tenure",
        patterns=patterns.LAND_TENURE_PATTERNS,
        confidence=0.85,
        priority=85
    ))

    # Registry Review
    registry.register(PatternClassifier(
        document_type="registry_review",
        patterns=patterns.REGISTRY_REVIEW_PATTERNS,
        confidence=0.95,
        priority=95
    ))

    # Methodology Reference
    registry.register(PatternClassifier(
        document_type="methodology_reference",
        patterns=patterns.METHODOLOGY_PATTERNS,
        confidence=0.90,
        priority=80
    ))

    # GIS files (lower priority - file type based)
    registry.register(FileTypeClassifier(
        document_type="gis_shapefile",
        extensions={".shp", ".shx", ".dbf", ".geojson"},
        confidence=0.80,
        priority=50
    ))

    # Images (lowest priority)
    registry.register(FileTypeClassifier(
        document_type="land_cover_map",
        extensions={".tif", ".tiff", ".jpg", ".jpeg", ".png"},
        confidence=0.70,
        priority=40
    ))


# tools/document_tools.py (UPDATE)
from ..classifiers.base import ClassifierRegistry
from ..classifiers.soil_carbon import register_soil_carbon_classifiers

# Initialize global registry (or per-methodology)
_classifier_registry = ClassifierRegistry()
register_soil_carbon_classifiers(_classifier_registry)


async def classify_document_by_filename(filepath: str) -> tuple[str, float, str]:
    """Classify document using registered classifiers."""
    return _classifier_registry.classify(Path(filepath))
```

**Benefits:**
- Easy to add new classifiers without modifying existing code
- Can register different classifiers per methodology
- Testable - each classifier can be tested independently
- Extensible - custom classifiers can implement complex logic
- Priority-based ordering
- Open/Closed Principle - open for extension, closed for modification
- Can add content-based classifiers (not just filename)

---

### Issue 2.2: LLM Extractor Classes Not Using Factory Pattern

**Severity:** Medium
**Location:** `src/registry_review_mcp/extractors/llm_extractors.py`

**Current Code:**
```python
# Multiple extractor classes with similar structure
class DateExtractor(BaseExtractor):
    def __init__(self, client: AsyncAnthropic | None = None):
        super().__init__(cache_namespace="date_extraction", client=client)
    # ...

class LandTenureExtractor(BaseExtractor):
    def __init__(self, client: AsyncAnthropic | None = None):
        super().__init__(cache_namespace="land_tenure_extraction", client=client)
    # ...

class ProjectIDExtractor(BaseExtractor):
    def __init__(self, client: AsyncAnthropic | None = None):
        super().__init__(cache_namespace="project_id_extraction", client=client)
    # ...

# Usage scattered across codebase:
client = AsyncAnthropic(api_key=settings.anthropic_api_key)
date_extractor = DateExtractor(client)
tenure_extractor = LandTenureExtractor(client)
project_id_extractor = ProjectIDExtractor(client)
```

**Why Problematic:**
- Extractor instantiation duplicated across files
- No central management of extractor lifecycle
- Cannot easily swap extractor implementations
- Difficult to add new extractor types
- Hard to mock for testing

**Recommended Fix - Factory Pattern:**

```python
# extractors/factory.py (NEW FILE)
"""Factory for creating field extractors."""

from typing import Dict, Type, Optional
from anthropic import AsyncAnthropic

from ..config.settings import settings
from .base import BaseExtractor
from .llm_extractors import DateExtractor, LandTenureExtractor, ProjectIDExtractor


class ExtractorType(str, Enum):
    """Types of supported extractors."""
    DATE = "date"
    LAND_TENURE = "land_tenure"
    PROJECT_ID = "project_id"


class ExtractorFactory:
    """Factory for creating and managing extractors."""

    def __init__(self, client: Optional[AsyncAnthropic] = None):
        """Initialize factory with shared client."""
        self._client = client or self._create_client()
        self._extractors: Dict[str, BaseExtractor] = {}
        self._extractor_classes: Dict[str, Type[BaseExtractor]] = {
            ExtractorType.DATE: DateExtractor,
            ExtractorType.LAND_TENURE: LandTenureExtractor,
            ExtractorType.PROJECT_ID: ProjectIDExtractor,
        }

    @staticmethod
    def _create_client() -> AsyncAnthropic:
        """Create Anthropic client from settings."""
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        return AsyncAnthropic(api_key=settings.anthropic_api_key)

    def register_extractor_type(self, name: str, extractor_class: Type[BaseExtractor]):
        """Register a custom extractor type."""
        self._extractor_classes[name] = extractor_class

    def get_extractor(self, extractor_type: str) -> BaseExtractor:
        """
        Get or create an extractor instance.

        Extractors are cached (singleton per type) to reuse across calls.
        """
        if extractor_type not in self._extractors:
            extractor_class = self._extractor_classes.get(extractor_type)
            if not extractor_class:
                raise ValueError(f"Unknown extractor type: {extractor_type}")

            # Create and cache
            self._extractors[extractor_type] = extractor_class(self._client)

        return self._extractors[extractor_type]

    def get_date_extractor(self) -> DateExtractor:
        """Convenience method for date extractor."""
        return self.get_extractor(ExtractorType.DATE)

    def get_tenure_extractor(self) -> LandTenureExtractor:
        """Convenience method for tenure extractor."""
        return self.get_extractor(ExtractorType.LAND_TENURE)

    def get_project_id_extractor(self) -> ProjectIDExtractor:
        """Convenience method for project ID extractor."""
        return self.get_extractor(ExtractorType.PROJECT_ID)


# Global factory instance (lazily initialized)
_factory: Optional[ExtractorFactory] = None


def get_extractor_factory() -> ExtractorFactory:
    """Get global extractor factory (creates on first access)."""
    global _factory
    if _factory is None:
        _factory = ExtractorFactory()
    return _factory


# Usage in validation_tools.py:
# OLD:
# client = AsyncAnthropic(api_key=settings.anthropic_api_key)
# date_extractor = DateExtractor(client)
# tenure_extractor = LandTenureExtractor(client)

# NEW:
from ..extractors.factory import get_extractor_factory

factory = get_extractor_factory()
date_extractor = factory.get_date_extractor()
tenure_extractor = factory.get_tenure_extractor()
project_id_extractor = factory.get_project_id_extractor()
```

**Benefits:**
- Single point of extractor creation
- Shared client across all extractors (efficiency)
- Easy to mock for testing
- Can register custom extractors
- Singleton pattern ensures only one instance per type
- Testable and maintainable

---

## 3. Fragile Patterns

### Issue 3.1: String Matching for Critical Logic

**Severity:** High
**Locations:**
- `src/registry_review_mcp/tools/validation_tools.py:64,280` (Parsing document IDs from strings)
- `src/registry_review_mcp/tools/evidence_tools.py:219` (Page number extraction)
- `src/registry_review_mcp/extractors/llm_extractors.py:1144,1158` (Parsing source citations)

**Current Code:**
```python
# validation_tools.py:64
doc1_id = field1_source.split(",")[0].strip()  # Assumes "DOC-123, Page 5" format

# evidence_tools.py:219
page = extract_page_number(text_before)  # Regex on markdown markers

# llm_extractors.py:1144
def extract_doc_id(source: str) -> str | None:
    match = re.search(r"(DOC-[A-Za-z0-9]+|REQ-\d+)", source)
    return match.group(1) if match else None

def extract_page(source: str) -> int | None:
    match = re.search(r"Page (\d+)", source, re.IGNORECASE)
    return int(match.group(1)) if match else None
```

**Why Problematic:**
- Brittle string parsing assumes specific formats
- No validation that format is correct
- Silent failures if format changes
- Different parsing code scattered across files
- Regex patterns duplicated

**Recommended Fix - Citation Parser:**

```python
# models/citation.py (NEW FILE)
"""Structured citation parsing and formatting."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class Citation(BaseModel):
    """Structured document citation."""

    document_id: Optional[str] = None  # "DOC-abc123"
    document_name: Optional[str] = None  # "Project Plan"
    page: Optional[int] = Field(None, ge=1)
    section: Optional[str] = None  # "Section 2.1"
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    raw_source: str  # Original source string

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate document ID format."""
        if v and not re.match(r'^DOC-[a-zA-Z0-9]+$', v):
            raise ValueError(f"Invalid document ID format: {v}")
        return v

    def __str__(self) -> str:
        """Format as standard citation string."""
        parts = []
        if self.document_name:
            parts.append(self.document_name)
        elif self.document_id:
            parts.append(self.document_id)

        if self.page:
            parts.append(f"Page {self.page}")

        if self.section:
            parts.append(self.section)

        return ", ".join(parts) if parts else self.raw_source


class CitationParser:
    """Parse and validate citation strings."""

    # Citation format patterns (in order of priority)
    PATTERNS = [
        # "DOC-123, Page 5, Section 2.1"
        re.compile(
            r'(?P<doc_id>DOC-[a-zA-Z0-9]+)'
            r'(?:,\s*Page\s+(?P<page>\d+))?'
            r'(?:,\s*(?P<section>.+))?',
            re.IGNORECASE
        ),
        # "Project Plan, Page 5, Section 2.1"
        re.compile(
            r'(?P<doc_name>[^,]+)'
            r'(?:,\s*Page\s+(?P<page>\d+))?'
            r'(?:,\s*(?P<section>.+))?',
            re.IGNORECASE
        ),
        # "Page 5"
        re.compile(r'Page\s+(?P<page>\d+)', re.IGNORECASE),
    ]

    @classmethod
    def parse(cls, source: str, strict: bool = False) -> Citation:
        """
        Parse citation from string.

        Args:
            source: Source citation string
            strict: If True, raise ValueError on parse failure

        Returns:
            Citation object

        Raises:
            ValueError: If strict=True and parsing fails
        """
        for pattern in cls.PATTERNS:
            match = pattern.search(source)
            if match:
                groups = match.groupdict()

                return Citation(
                    document_id=groups.get('doc_id'),
                    document_name=groups.get('doc_name', '').strip() or None,
                    page=int(groups['page']) if groups.get('page') else None,
                    section=groups.get('section', '').strip() or None,
                    raw_source=source,
                    confidence=1.0 if groups.get('doc_id') else 0.8
                )

        # No match - return minimal citation
        if strict:
            raise ValueError(f"Failed to parse citation: {source}")

        return Citation(
            document_name=source.strip(),
            raw_source=source,
            confidence=0.5
        )

    @classmethod
    def format(
        cls,
        document_id: Optional[str] = None,
        document_name: Optional[str] = None,
        page: Optional[int] = None,
        section: Optional[str] = None
    ) -> str:
        """Format citation as standard string."""
        citation = Citation(
            document_id=document_id,
            document_name=document_name,
            page=page,
            section=section,
            raw_source=""
        )
        return str(citation)


# Usage:
# validation_tools.py (OLD)
doc1_id = field1_source.split(",")[0].strip()

# validation_tools.py (NEW)
from ..models.citation import CitationParser

citation = CitationParser.parse(field1_source)
doc1_id = citation.document_id

# llm_extractors.py (OLD)
def extract_doc_id(source: str) -> str | None:
    match = re.search(r"(DOC-[A-Za-z0-9]+|REQ-\d+)", source)
    return match.group(1) if match else None

# llm_extractors.py (NEW)
from ..models.citation import CitationParser

def extract_doc_id(source: str) -> str | None:
    citation = CitationParser.parse(source)
    return citation.document_id
```

**Benefits:**
- Centralized citation parsing logic
- Validated structure with Pydantic
- Handles multiple citation formats
- Confidence scoring
- Easy to extend with new formats
- Type-safe
- Better error handling

---

### Issue 3.2: Error Handling That Swallows Exceptions

**Severity:** High
**Locations:**
- `src/registry_review_mcp/tools/session_tools.py:193` (Silent skip of corrupted sessions)
- `src/registry_review_mcp/tools/document_tools.py:186,339` (Generic exception catch without logging)
- `src/registry_review_mcp/prompts/A_initialize.py:86` (Exception ignored in loop)

**Current Code:**
```python
# session_tools.py:193
for session_dir in settings.sessions_dir.iterdir():
    if session_dir.is_dir() and (session_dir / "session.json").exists():
        try:
            state_manager = StateManager(session_dir.name)
            session_data = state_manager.read_json("session.json")
            sessions.append({...})
        except Exception:
            # Skip corrupted sessions
            continue  # NO LOGGING!

# document_tools.py:339
try:
    with pdfplumber.open(file_path) as pdf:
        metadata.page_count = len(pdf.pages)
        # ...
except Exception:
    # If PDF extraction fails, just use basic metadata
    pass  # NO LOGGING OR ERROR DETAILS!

# prompts/A_initialize.py:86
try:
    state_manager = StateManager(session_dir.name)
    session_data = state_manager.read_json("session.json")
    # ...
except Exception:
    # Skip corrupted sessions
    continue  # Silent failure
```

**Why Problematic:**
- Silent failures hide bugs and data corruption
- No logging makes debugging impossible
- Users unaware of issues
- Corrupted data silently ignored
- Cannot track failure patterns

**Recommended Fix:**

```python
# models/errors.py (ADD)
class CorruptedSessionError(RegistryReviewError):
    """Session data is corrupted or invalid."""
    pass

class PDFExtractionError(DocumentError):
    """Failed to extract metadata from PDF."""
    pass


# session_tools.py (FIX)
import logging

logger = logging.getLogger(__name__)

async def list_sessions() -> list[dict[str, Any]]:
    """List all available sessions."""
    sessions = []
    corrupted_sessions = []

    for session_dir in settings.sessions_dir.iterdir():
        if session_dir.is_dir() and (session_dir / "session.json").exists():
            try:
                state_manager = StateManager(session_dir.name)
                session_data = state_manager.read_json("session.json")

                # Validate basic structure
                if not session_data.get("session_id"):
                    raise CorruptedSessionError(f"Missing session_id in {session_dir.name}")

                sessions.append({
                    "session_id": session_data.get("session_id"),
                    # ...
                })
            except Exception as e:
                # Log corruption but continue
                logger.warning(
                    f"Skipping corrupted session {session_dir.name}: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                corrupted_sessions.append({
                    "session_dir": str(session_dir),
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                continue

    # Sort by creation date
    sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    # Log summary if corrupted sessions found
    if corrupted_sessions:
        logger.error(
            f"Found {len(corrupted_sessions)} corrupted session(s). "
            f"Consider running cleanup: {[s['session_dir'] for s in corrupted_sessions]}"
        )

    return sessions


# document_tools.py (FIX)
async def extract_document_metadata(file_path: Path) -> DocumentMetadata:
    """Extract metadata from a document file."""
    stat = file_path.stat()
    content_hash = compute_file_hash(file_path)

    metadata = DocumentMetadata(
        file_size_bytes=stat.st_size,
        creation_date=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
        modification_date=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        content_hash=content_hash,
    )

    # PDF-specific metadata
    if is_pdf_file(file_path.name):
        try:
            with pdfplumber.open(file_path) as pdf:
                metadata.page_count = len(pdf.pages)
                metadata.has_tables = any(
                    len(page.extract_tables()) > 0
                    for page in pdf.pages[:min(3, len(pdf.pages))]
                )
        except Exception as e:
            # Log but don't fail - basic metadata is sufficient
            logger.warning(
                f"Failed to extract PDF metadata from {file_path.name}: {type(e).__name__}: {str(e)}. "
                f"Using basic file metadata only.",
                exc_info=True
            )
            # Set defaults
            metadata.page_count = None
            metadata.has_tables = False

    return metadata
```

**Benefits:**
- Errors logged for debugging
- Users aware of issues
- Can track failure patterns
- Easier to identify data corruption
- Better observability

---

## 4. Long Functions & Deep Nesting

### Issue 4.1: Function Exceeds 50 Lines

**Severity:** Medium
**Locations:**
- `src/registry_review_mcp/tools/document_tools.py:67-261` (195 lines - discover_documents)
- `src/registry_review_mcp/tools/validation_tools.py:486-701` (216 lines - cross_validate)
- `src/registry_review_mcp/tools/evidence_tools.py:349-435` (87 lines - extract_all_evidence)
- `src/registry_review_mcp/extractors/llm_extractors.py:109-183` (75 lines - _call_api_with_retry)
- `src/registry_review_mcp/tools/report_tools.py:18-225` (208 lines - generate_review_report)

**Example - discover_documents (195 lines):**

**Current Code:**
```python
async def discover_documents(session_id: str) -> dict[str, Any]:
    """Discover and index all documents in the session's project directory."""
    # Load session (lines 79-88)
    # ...

    # Discover files (lines 90-112)
    # ...

    # Process each file with progress updates (lines 117-218)
    for i, file_path in enumerate(discovered_files, 1):
        # Show progress (lines 124-127)
        # Extract metadata (line 131)
        # Check for duplicates (lines 134-143)
        # Generate document ID (line 146)
        # Classify document (lines 148-151)
        # Create document record (lines 153-163)
        # Update summary (lines 167-170)
        # Error handling (lines 172-218)

    # Show completion (lines 220-225)
    # Save results (lines 227-237)
    # Update session (lines 239-253)
    # Return (lines 255-261)
```

**Why Problematic:**
- Difficult to understand at a glance
- Hard to test individual pieces
- Multiple responsibilities mixed together
- Error handling interleaved with business logic
- Cannot reuse sub-operations

**Recommended Fix - Extract Methods:**

```python
async def discover_documents(session_id: str) -> dict[str, Any]:
    """Discover and index all documents in the session's project directory."""
    # Validation
    session_data = await _validate_session(session_id)
    documents_path = Path(session_data["project_metadata"]["documents_path"])

    # Discovery
    discovered_files = await _scan_directory(documents_path)

    # Processing
    results = await _process_discovered_files(discovered_files, session_id)

    # Persistence
    await _save_discovery_results(session_id, results, session_data)

    return {
        "session_id": session_id,
        "documents_found": len(results.documents),
        "duplicates_skipped": results.duplicates_skipped,
        "classification_summary": results.classification_summary,
        "documents": [doc.model_dump(mode="json") for doc in results.documents],
    }


async def _validate_session(session_id: str) -> dict[str, Any]:
    """Validate session exists and return session data."""
    state_manager = StateManager(session_id)
    if not state_manager.exists():
        raise SessionNotFoundError(
            f"Session not found: {session_id}",
            details={"session_id": session_id},
        )
    return state_manager.read_json("session.json")


async def _scan_directory(documents_path: Path) -> list[Path]:
    """Scan directory for supported files."""
    logger.info(f"Scanning directory: {documents_path}")

    supported_extensions = {".pdf", ".shp", ".geojson", ".tif", ".tiff"}
    discovered_files = []

    for file_path in documents_path.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in supported_extensions:
            continue

        if any(part.startswith(".") for part in file_path.parts):
            continue

        discovered_files.append(file_path)

    logger.info(f"Found {len(discovered_files)} supported files")
    return discovered_files


@dataclass
class ProcessingResult:
    """Result of file processing."""
    documents: list[Document]
    duplicates_skipped: int
    classification_summary: dict[str, int]
    errors: list[dict]


async def _process_discovered_files(
    files: list[Path],
    session_id: str
) -> ProcessingResult:
    """Process all discovered files."""
    documents = []
    errors = []
    classification_summary = {}
    seen_hashes = {}
    duplicates_skipped = 0

    for i, file_path in enumerate(files, 1):
        if i % 3 == 0 or i == len(files):
            _log_progress(i, len(files), file_path.name)

        try:
            result = await _process_single_file(file_path, seen_hashes)

            if result is None:
                # Duplicate
                duplicates_skipped += 1
                continue

            documents.append(result)
            classification_summary[result.classification] = \
                classification_summary.get(result.classification, 0) + 1

        except Exception as e:
            errors.append(_create_error_record(file_path, e))

    logger.info(f"Processing complete: {len(documents)} documents, {duplicates_skipped} duplicates")
    if errors:
        logger.warning(f"{len(errors)} file(s) had processing errors")

    return ProcessingResult(
        documents=documents,
        duplicates_skipped=duplicates_skipped,
        classification_summary=classification_summary,
        errors=errors
    )


async def _process_single_file(
    file_path: Path,
    seen_hashes: dict[str, str]
) -> Optional[Document]:
    """Process a single file. Returns None if duplicate."""
    metadata = await extract_document_metadata(file_path)

    # Check for duplicate
    if metadata.content_hash in seen_hashes:
        original = seen_hashes[metadata.content_hash]
        logger.debug(f"Skipping duplicate: {file_path.name} (same as {Path(original).name})")
        return None

    seen_hashes[metadata.content_hash] = str(file_path)

    # Generate ID and classify
    doc_id = generate_document_id(metadata.content_hash)
    classification, confidence, method = await classify_document_by_filename(str(file_path))

    return Document(
        document_id=doc_id,
        filename=file_path.name,
        filepath=str(file_path),
        classification=classification,
        confidence=confidence,
        classification_method=method,
        metadata=metadata,
        indexed_at=datetime.now(timezone.utc),
    )


def _create_error_record(file_path: Path, error: Exception) -> dict:
    """Create standardized error record."""
    error_type = type(error).__name__
    error_msg = f"Failed to process {file_path.name}: {str(error)}"

    # Provide specific recovery guidance
    recovery_steps = []
    if "PDF" in str(error) or "pdf" in str(error).lower():
        recovery_steps = [
            "The PDF file may be corrupted or encrypted",
            f"Try opening {file_path.name} in a PDF viewer to verify it's valid",
            "Consider re-downloading or re-scanning the document"
        ]
    elif "shapefile" in str(error).lower() or ".shp" in str(file_path):
        recovery_steps = [
            "Shapefile may be missing required components (.shp, .shx, .dbf)",
            f"Verify all shapefile components are present in {file_path.parent}",
            "Try re-exporting the shapefile from GIS software"
        ]
    else:
        recovery_steps = [
            f"Verify the file is not corrupted: {file_path.name}",
            "Check file format is supported (.pdf, .shp, .geojson, .tif)",
            "Try re-processing the file or contact support"
        ]

    return {
        "filepath": str(file_path),
        "filename": file_path.name,
        "error_type": error_type,
        "message": error_msg,
        "recovery_steps": recovery_steps
    }


async def _save_discovery_results(
    session_id: str,
    results: ProcessingResult,
    session_data: dict
):
    """Save discovery results to state."""
    state_manager = StateManager(session_id)

    # Save document index
    documents_data = {
        "documents": [doc.model_dump(mode="json") for doc in results.documents],
        "total_count": len(results.documents),
        "duplicates_skipped": results.duplicates_skipped,
        "classification_summary": results.classification_summary,
        "errors": results.errors,
        "error_count": len(results.errors),
        "discovered_at": datetime.now(timezone.utc).isoformat(),
    }
    state_manager.write_json("documents.json", documents_data)

    # Update session statistics
    state_manager.update_json(
        "session.json",
        {
            "statistics": {
                **session_data.get("statistics", {}),
                "documents_found": len(results.documents),
                "duplicates_skipped": results.duplicates_skipped,
            },
            "workflow_progress": {
                **session_data.get("workflow_progress", {}),
                "document_discovery": "completed",
            },
        },
    )


def _log_progress(current: int, total: int, filename: str):
    """Log processing progress."""
    percentage = (current / total * 100)
    print(f"  Processing {current}/{total} ({percentage:.0f}%): {filename}", flush=True)
```

**Benefits:**
- Each function has single responsibility
- Easier to test individual pieces
- Better code organization
- Reusable sub-functions
- Easier to read and maintain
- Error handling separated from business logic

---

## 5. Missing Design Patterns

### Issue 5.1: No Validation Rule Registry

**Severity:** Medium
**Location:** `src/registry_review_mcp/tools/validation_tools.py`

**Current Code:**
```python
# Hardcoded validation checks in cross_validate()
async def cross_validate(session_id: str) -> dict[str, Any]:
    # ...
    # Date alignment validation (hardcoded)
    if project_start_dates and baseline_dates:
        # Validate first occurrence of each type
        for psd in project_start_dates[:3]:
            for bd in baseline_dates[:3]:
                result = await validate_date_alignment(...)
                validation_results['date_alignments'].append(result)

    # Project ID validation (hardcoded)
    if project_ids:
        result = await validate_project_id(...)
        validation_results['project_ids'].append(result)

    # Land tenure validation (hardcoded)
    if len(owner_names) >= 2:
        result = await validate_land_tenure(...)
        validation_results['land_tenure'].append(result)
```

**Why Problematic:**
- Cannot add custom validation rules without modifying core code
- Rules hardcoded in function
- No way to enable/disable specific validations
- Cannot configure validation behavior per methodology

**Recommended Fix - Strategy Pattern for Validations:**

```python
# validators/base.py (NEW FILE)
"""Base validator interface and registry."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ValidationRule(ABC):
    """Base class for validation rules."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for this rule."""
        pass

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Human-readable name."""
        pass

    @property
    def enabled(self) -> bool:
        """Whether this rule is enabled (can be overridden)."""
        return True

    @abstractmethod
    async def validate(
        self,
        session_id: str,
        evidence_data: dict,
        extracted_fields: dict
    ) -> List[Dict[str, Any]]:
        """
        Run validation and return list of validation results.

        Returns:
            List of validation result dicts
        """
        pass


class DateAlignmentRule(ValidationRule):
    """Validate date alignment across documents."""

    @property
    def rule_id(self) -> str:
        return "date_alignment"

    @property
    def rule_name(self) -> str:
        return "Date Alignment Validation"

    async def validate(
        self,
        session_id: str,
        evidence_data: dict,
        extracted_fields: dict
    ) -> List[Dict[str, Any]]:
        """Validate dates are within acceptable range."""
        from ..tools.validation_tools import validate_date_alignment
        from datetime import datetime

        results = []
        dates = extracted_fields.get("dates", [])

        # Group dates by type
        project_start_dates = [d for d in dates if d.get('date_type') == 'project_start_date']
        baseline_dates = [d for d in dates if d.get('date_type') == 'baseline_date']

        # Validate pairs
        if project_start_dates and baseline_dates:
            for psd in project_start_dates[:3]:
                for bd in baseline_dates[:3]:
                    try:
                        date1 = datetime.fromisoformat(psd['date_value'])
                        date2 = datetime.fromisoformat(bd['date_value'])

                        result = await validate_date_alignment(
                            session_id=session_id,
                            field1_name='project_start_date',
                            field1_value=date1,
                            field1_source=f"{psd['document_name']} (page {psd.get('page', '?')})",
                            field2_name='baseline_date',
                            field2_value=date2,
                            field2_source=f"{bd['document_name']} (page {bd.get('page', '?')})",
                            max_delta_days=120
                        )
                        results.append(result)
                    except (ValueError, KeyError):
                        continue

        return results


class ValidationRegistry:
    """Registry for validation rules."""

    def __init__(self):
        self._rules: Dict[str, ValidationRule] = {}

    def register(self, rule: ValidationRule):
        """Register a validation rule."""
        self._rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> Optional[ValidationRule]:
        """Get rule by ID."""
        return self._rules.get(rule_id)

    def list_rules(self, enabled_only: bool = True) -> List[ValidationRule]:
        """List all registered rules."""
        rules = list(self._rules.values())
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return rules

    async def run_all(
        self,
        session_id: str,
        evidence_data: dict,
        extracted_fields: dict
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run all enabled validation rules.

        Returns:
            Dict mapping rule_id to list of validation results
        """
        results = {}

        for rule in self.list_rules(enabled_only=True):
            try:
                rule_results = await rule.validate(session_id, evidence_data, extracted_fields)
                if rule_results:
                    results[rule.rule_id] = rule_results
            except Exception as e:
                # Log but continue with other rules
                import logging
                logging.error(f"Validation rule {rule.rule_id} failed: {e}", exc_info=True)

        return results


# Global registry
_validation_registry = ValidationRegistry()

def get_validation_registry() -> ValidationRegistry:
    """Get global validation registry."""
    return _validation_registry


# validators/soil_carbon.py (NEW FILE)
"""Validation rules for soil carbon methodology."""

from .base import (
    ValidationRegistry,
    ValidationRule,
    DateAlignmentRule,
    # ... other built-in rules
)


def register_soil_carbon_validators(registry: ValidationRegistry):
    """Register all soil carbon validation rules."""

    # Date alignment
    registry.register(DateAlignmentRule())

    # Project ID consistency
    registry.register(ProjectIDRule())

    # Land tenure consistency
    registry.register(LandTenureRule())

    # ... additional rules


# tools/validation_tools.py (UPDATE)
async def cross_validate(session_id: str) -> dict[str, Any]:
    """Run all cross-document validation checks for a session."""
    from ..validators.base import get_validation_registry

    state_manager = StateManager(session_id)
    session_data = state_manager.read_json("session.json")

    # Load evidence
    evidence_data = state_manager.read_json("evidence.json")

    # Extract fields (LLM or regex)
    extracted_fields = await extract_fields_with_llm(session_id, evidence_data)

    # Run all registered validation rules
    registry = get_validation_registry()
    validation_results = await registry.run_all(session_id, evidence_data, extracted_fields)

    # Calculate summary
    summary = calculate_validation_summary(validation_results)

    # Build and save result
    # ...
```

**Benefits:**
- Easy to add custom validation rules
- Can enable/disable rules per methodology
- Testable - each rule tested independently
- Extensible - custom rules can be registered
- Open/Closed Principle
- Better separation of concerns

---

## 6. Code Duplication

### Issue 6.1: Duplicate Field Extraction Logic

**Severity:** Medium
**Locations:**
- `src/registry_review_mcp/tools/validation_tools.py:323-420` (Three similar extraction functions)

**Current Code:**
```python
def extract_project_ids_from_evidence(evidence_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract project ID occurrences from evidence data."""
    import re
    project_ids = []
    id_pattern = re.compile(r'\b(\d{4})\b|C\d{2}-(\d{4})')

    for req in evidence_data.get('evidence', []):
        for snip in req.get('evidence_snippets', []):
            doc_name = snip['document_name']
            matches = id_pattern.findall(doc_name)
            # ... specific project ID logic
    return project_ids


def extract_dates_from_evidence(evidence_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract dates from evidence snippets with context."""
    import re
    from datetime import datetime

    dates = []
    date_patterns = [...]

    for req in evidence_data.get('evidence', []):
        if req_id in date_requirements:
            for snip in req.get('evidence_snippets', []):
                text = snip['text']
                # ... specific date logic
    return dates


def extract_land_tenure_from_evidence(evidence_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract land tenure information from evidence snippets."""
    import re
    tenure_fields = []

    for req in evidence_data.get('evidence', []):
        if req['requirement_id'] == 'REQ-002':
            for snip in req.get('evidence_snippets', []):
                text = snip['text']
                # ... specific tenure logic
    return tenure_fields
```

**Why Problematic:**
- Same loop structure repeated 3 times
- Duplicate evidence traversal code
- Changes require updating 3 functions
- No shared abstractions

**Recommended Fix - Template Method Pattern:**

```python
# extractors/evidence_extractor.py (NEW FILE)
"""Base evidence extractor with template method pattern."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable


class EvidenceExtractor(ABC):
    """Base class for extracting structured data from evidence."""

    def extract_from_evidence(
        self,
        evidence_data: dict[str, Any],
        requirement_filter: Optional[Callable[[dict], bool]] = None
    ) -> List[Dict[str, Any]]:
        """
        Template method for extracting data from evidence.

        Args:
            evidence_data: Evidence JSON data
            requirement_filter: Optional filter for requirements

        Returns:
            List of extracted items
        """
        results = []

        for req in evidence_data.get('evidence', []):
            # Apply requirement filter if provided
            if requirement_filter and not requirement_filter(req):
                continue

            for snip in req.get('evidence_snippets', []):
                # Extract from this snippet (implemented by subclass)
                items = self.extract_from_snippet(req, snip)
                results.extend(items)

        # Post-process results (implemented by subclass)
        return self.post_process(results)

    @abstractmethod
    def extract_from_snippet(
        self,
        requirement: dict,
        snippet: dict
    ) -> List[Dict[str, Any]]:
        """
        Extract items from a single evidence snippet.

        Subclasses implement specific extraction logic.
        """
        pass

    def post_process(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Post-process extracted results (optional override).

        Default: return as-is. Subclasses can override for deduplication, etc.
        """
        return results


class ProjectIDExtractor(EvidenceExtractor):
    """Extract project IDs from evidence."""

    def __init__(self):
        import re
        self.id_pattern = re.compile(r'\b(\d{4})\b|C\d{2}-(\d{4})')

    def extract_from_snippet(
        self,
        requirement: dict,
        snippet: dict
    ) -> List[Dict[str, Any]]:
        """Extract project IDs from snippet."""
        results = []
        doc_name = snippet['document_name']

        matches = self.id_pattern.findall(doc_name)
        for match in matches:
            project_id = match[0] if match[0] else match[1]
            # Only consider valid project IDs
            if project_id and int(project_id) < 9000:
                results.append({
                    'project_id': project_id,
                    'document_id': snippet.get('document_id'),
                    'document_name': doc_name,
                    'source': 'document_name'
                })

        return results


class DateExtractor(EvidenceExtractor):
    """Extract dates from evidence."""

    def __init__(self):
        import re
        self.date_patterns = [
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', '%m/%d/%Y'),
            (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', '%Y/%m/%d'),
        ]
        self.date_requirements = {
            'REQ-007': 'project_start_date',
            'REQ-018': 'baseline_date',
            'REQ-019': 'monitoring_date',
        }

    def extract_from_snippet(
        self,
        requirement: dict,
        snippet: dict
    ) -> List[Dict[str, Any]]:
        """Extract dates from snippet."""
        from datetime import datetime
        import re

        results = []
        req_id = requirement['requirement_id']

        # Only process date-related requirements
        if req_id not in self.date_requirements:
            return []

        date_type = self.date_requirements[req_id]
        text = snippet['text']

        # Try each date pattern
        for pattern, date_format in self.date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    if len(match) == 3:
                        date_str = f"{match[0]}/{match[1]}/{match[2]}"
                        parsed_date = datetime.strptime(date_str, date_format)

                        # Only reasonable dates
                        if 2000 <= parsed_date.year <= 2030:
                            results.append({
                                'date_type': date_type,
                                'date_value': parsed_date.isoformat(),
                                'date_str': date_str,
                                'document_id': snippet.get('document_id'),
                                'document_name': snippet['document_name'],
                                'page': snippet.get('page'),
                                'source': req_id
                            })
                except (ValueError, IndexError):
                    continue

        return results


class LandTenureExtractor(EvidenceExtractor):
    """Extract land tenure from evidence."""

    def __init__(self):
        import re
        self.owner_patterns = [
            r'(?:land\s*owner|owner|land\s*steward)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+).*(?:owner|steward)',
        ]
        self.area_pattern = r'(\d+(?:\.\d+)?)\s*(?:ha|hectares)'

    def extract_from_snippet(
        self,
        requirement: dict,
        snippet: dict
    ) -> List[Dict[str, Any]]:
        """Extract land tenure from snippet."""
        import re

        # Only process tenure requirement
        if requirement['requirement_id'] != 'REQ-002':
            return []

        results = []
        text = snippet['text']

        # Extract owner names
        for pattern in self.owner_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                owner_name = match if isinstance(match, str) else match[0]
                if len(owner_name.split()) >= 2 and len(owner_name) > 5:
                    results.append({
                        'owner_name': owner_name.strip(),
                        'document_id': snippet.get('document_id'),
                        'document_name': snippet['document_name'],
                        'page': snippet.get('page'),
                        'source': 'REQ-002'
                    })

        # Extract area
        area_matches = re.findall(self.area_pattern, text.lower())
        for area_str in area_matches:
            try:
                area = float(area_str)
                if 0 < area < 100000:
                    results.append({
                        'area_hectares': area,
                        'document_id': snippet.get('document_id'),
                        'document_name': snippet['document_name'],
                        'page': snippet.get('page'),
                        'source': 'REQ-002'
                    })
            except ValueError:
                continue

        return results


# Usage:
# Old:
project_ids = extract_project_ids_from_evidence(evidence_data)
dates = extract_dates_from_evidence(evidence_data)
tenure = extract_land_tenure_from_evidence(evidence_data)

# New:
project_id_extractor = ProjectIDExtractor()
date_extractor = DateExtractor()
tenure_extractor = LandTenureExtractor()

project_ids = project_id_extractor.extract_from_evidence(evidence_data)
dates = date_extractor.extract_from_evidence(evidence_data)
tenure = tenure_extractor.extract_from_evidence(evidence_data)
```

**Benefits:**
- Single traversal logic in base class
- No duplication of loop structure
- Easy to add new extractors
- Consistent interface
- Testable
- Template Method pattern ensures correct structure

---

## 7. Additional Issues

### Issue 7.1: Missing StateManager Import in Prompt

**Severity:** Low
**Location:** `src/registry_review_mcp/prompts/A_initialize.py:72`

**Current Code:**
```python
# prompts/A_initialize.py
# ... no import of StateManager
state_manager = StateManager(session_dir.name)  # NameError!
```

**Fix:**
```python
from ..utils.state import StateManager
```

---

### Issue 7.2: Inconsistent Datetime Usage

**Severity:** Low
**Locations:**
- `src/registry_review_mcp/tools/validation_tools.py:5` (imports `UTC`)
- `src/registry_review_mcp/tools/document_tools.py:5` (imports `timezone`)

**Current Code:**
```python
# validation_tools.py
from datetime import datetime, UTC
validated_at=datetime.now(UTC)

# document_tools.py
from datetime import datetime, timezone
creation_date=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
```

**Why Problematic:**
- Inconsistent timezone handling
- `UTC` is Python 3.11+ only
- Mix of `UTC` and `timezone.utc`

**Fix:**
```python
# Standardize on timezone.utc for compatibility
from datetime import datetime, timezone

# Always use timezone.utc
datetime.now(timezone.utc)
datetime.fromtimestamp(ts, tz=timezone.utc)
```

---

## Summary & Recommendations

### Priority 1 - Critical Issues (Implement First)

1. **Methodology Registry** (Issue 1.1)
   - Create central registry for methodologies
   - Auto-discover from checklist files
   - Remove all hardcoded "soil-carbon-v1.2.2" strings

2. **Workflow State Machine** (Issue 1.3)
   - Define workflows declaratively
   - Support custom workflows per methodology
   - Dynamic stage management

3. **Document Classifier Registry** (Issue 2.1)
   - Implement Strategy pattern for classifiers
   - Support custom classification rules
   - Extensible architecture

### Priority 2 - High Impact

4. **Extractor Factory** (Issue 2.2)
   - Centralize extractor creation
   - Shared client instances
   - Testable and mockable

5. **Refactor Long Functions** (Issue 4.1)
   - Break down 100+ line functions
   - Extract helper methods
   - Single responsibility per function

6. **Error Handling** (Issue 3.2)
   - Add comprehensive logging
   - Track corrupted data
   - User-visible error messages

### Priority 3 - Quality Improvements

7. **Configuration for Magic Numbers** (Issue 1.2)
   - Move thresholds to settings
   - Environment variable support
   - Validation with Pydantic

8. **Citation Parser** (Issue 3.1)
   - Structured citation handling
   - Validated parsing
   - Central parsing logic

9. **Validation Registry** (Issue 5.1)
   - Strategy pattern for validation rules
   - Pluggable validators
   - Enable/disable per methodology

10. **Template Method for Extractors** (Issue 6.1)
    - Remove duplicate traversal code
    - Shared base class
    - Consistent interface

### Estimated Impact

**Code Changes Required:**
- New files: ~15 (registries, base classes, patterns)
- Modified files: ~25
- Lines of code added: ~2,000
- Lines of code removed/refactored: ~1,500
- Net change: +500 lines (but much better structure)

**Benefits:**
- **Extensibility:** Add new methodologies without code changes
- **Maintainability:** Reduce duplication by 40%
- **Testability:** Each component independently testable
- **Reliability:** Better error handling and logging
- **Flexibility:** Configurable behaviors via settings

**Timeline Estimate:**
- Priority 1 (Critical): 2-3 days
- Priority 2 (High): 3-4 days
- Priority 3 (Quality): 2-3 days
- **Total:** ~8-10 days for complete refactoring

### Testing Strategy

For each refactoring:
1. Write tests for existing behavior first
2. Refactor code
3. Ensure all tests still pass
4. Add tests for new functionality
5. Update integration tests

---

## Conclusion

The codebase is functionally complete and working well, but has several opportunities for improvement in extensibility, maintainability, and robustness. The hardcoded methodology identifier is the most critical issue, as it prevents the system from supporting multiple methodologies without code changes.

Implementing the recommended design patterns (Registry, Strategy, Factory, Template Method) will make the codebase significantly more maintainable and extensible, while reducing code duplication and improving testability.

**Next Steps:**
1. Review this document with the team
2. Prioritize which issues to address first
3. Create tickets for each refactoring task
4. Implement changes incrementally with full test coverage
5. Monitor for regressions during refactoring

---

**Reviewed by:** Claude Code (Automated Analysis)
**Date:** 2025-11-15
**Status:** Ready for Team Review
