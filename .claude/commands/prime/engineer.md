# Get the full software Context

RUN:
!git ls-files

READ MODULES:

## Configuration
@src/registry_review_mcp/config/settings.py

## Core Server
@src/registry_review_mcp/server.py

## Models
@src/registry_review_mcp/models/schemas.py
@src/registry_review_mcp/models/evidence.py
@src/registry_review_mcp/models/report.py
@src/registry_review_mcp/models/validation.py
@src/registry_review_mcp/models/errors.py

## Tools
@src/registry_review_mcp/tools/session_tools.py
@src/registry_review_mcp/tools/document_tools.py
@src/registry_review_mcp/tools/evidence_tools.py
@src/registry_review_mcp/tools/upload_tools.py
@src/registry_review_mcp/tools/report_tools.py
@src/registry_review_mcp/tools/validation_tools.py

## Extractors
@src/registry_review_mcp/extractors/llm_extractors.py
@src/registry_review_mcp/extractors/marker_extractor.py
@src/registry_review_mcp/extractors/verification.py

## Intelligence
@src/registry_review_mcp/intelligence/metadata_extractors.py
@src/registry_review_mcp/intelligence/prior_review_detector.py

## Prompts
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

## Resources
@src/registry_review_mcp/resources/__init__.py

