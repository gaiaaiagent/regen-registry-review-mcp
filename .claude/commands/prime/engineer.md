# Get the full software Context

RUN:
!git ls-files

READ MODULES:

## Configuration
@src/registry_review_mcp/config/settings.py

## Core Server
@src/registry_review_mcp/server.py

## State Management
@src/registry_review_mcp/state/__init__.py

## Models
@src/registry_review_mcp/models/base.py
@src/registry_review_mcp/models/schemas.py
@src/registry_review_mcp/models/evidence.py
@src/registry_review_mcp/models/report.py
@src/registry_review_mcp/models/responses.py
@src/registry_review_mcp/models/validation.py
@src/registry_review_mcp/models/errors.py

## Tools
@src/registry_review_mcp/tools/base.py
@src/registry_review_mcp/tools/session_tools.py
@src/registry_review_mcp/tools/document_tools.py
@src/registry_review_mcp/tools/evidence_tools.py
@src/registry_review_mcp/tools/upload_tools.py
@src/registry_review_mcp/tools/analyze_llm.py
@src/registry_review_mcp/tools/report_tools.py
@src/registry_review_mcp/tools/validation_tools.py

## Extractors
@src/registry_review_mcp/extractors/llm_extractors.py
@src/registry_review_mcp/extractors/marker_extractor.py
@src/registry_review_mcp/extractors/verification.py

## Prompts
@src/registry_review_mcp/prompts/helpers.py
@src/registry_review_mcp/prompts/unified_analysis.py
@src/registry_review_mcp/prompts/A_initialize.py
@src/registry_review_mcp/prompts/B_document_discovery.py
@src/registry_review_mcp/prompts/C_evidence_extraction.py
@src/registry_review_mcp/prompts/D_cross_validation.py
@src/registry_review_mcp/prompts/E_report_generation.py
@src/registry_review_mcp/prompts/F_human_review.py
@src/registry_review_mcp/prompts/G_complete.py

## Utilities
@src/registry_review_mcp/utils/state.py
@src/registry_review_mcp/utils/cache.py
@src/registry_review_mcp/utils/cost_tracker.py
@src/registry_review_mcp/utils/patterns.py
@src/registry_review_mcp/utils/tool_helpers.py
@src/registry_review_mcp/utils/common/errors.py
@src/registry_review_mcp/utils/common/retry.py

## Resources
@src/registry_review_mcp/resources/__init__.py

