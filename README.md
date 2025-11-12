# Registry Review MCP Server

**Version:** 2.0.0  
**Status:** Phase 1 Complete (Foundation)  
**Target:** Phase 2 (Nov 2025 - Jan 2026)

Automated registry review workflows for carbon credit project registration using the Model Context Protocol (MCP).

---

## Overview

The Registry Review MCP Server automates the manual document review process for carbon credit project registration. It transforms a 6-8 hour manual review into a 60-90 minute guided workflow with complete audit trail and structured outputs.

**Core Value Proposition:** Enable Registry Agents (like Becca) to process project documentation 5-10x faster by automating:
- Document discovery and classification
- Evidence extraction and requirement mapping
- Cross-document validation
- Compliance checking and report generation

---

## Quick Start

\`\`\`bash
# Install dependencies
uv sync

# Run the server
uv run python -m registry_review_mcp.server
\`\`\`

See [Installation](#installation) and [Usage](#usage) sections for details.

---

## Features

### ✅ Phase 1: Foundation (Complete)

- **Session Management** - Create, load, update, and delete review sessions
- **Atomic State Persistence** - Thread-safe file operations with locking
- **Configuration Management** - Environment-based settings with validation
- **Error Hierarchy** - Comprehensive error types for graceful handling
- **Caching Infrastructure** - TTL-based caching for expensive operations
- **Checklist System** - Soil Carbon v1.2.2 methodology with 23 requirements

### 🚧 Phase 2-5: In Development

- Document discovery and classification (Phase 2)
- Evidence extraction and requirement mapping (Phase 3)
- Cross-document validation (Phase 4)
- Report generation - Markdown, JSON, PDF (Phase 4)
- Human review workflow (Phase 5)

---

## Installation

### Prerequisites

- Python >=3.10
- [UV](https://github.com/astral-sh/uv) package manager

### Setup

\`\`\`bash
# Clone repository
cd regen-registry-review-mcp

# Install dependencies
uv sync

# Verify installation
uv run python -m registry_review_mcp.server
\`\`\`

---

## Configuration

### Claude Desktop Integration

Add to \`claude_desktop_config.json\`:

\`\`\`json
{
  "mcpServers": {
    "registry-review": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/regen-registry-review-mcp",
        "run",
        "python",
        "-m",
        "registry_review_mcp.server"
      ],
      "env": {
        "REGISTRY_REVIEW_LOG_LEVEL": "INFO"
      }
    }
  }
}
\`\`\`

Restart Claude Desktop to load the server.

---

## Development

### Running Tests

\`\`\`bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest tests/test_infrastructure.py -v
\`\`\`

### Code Quality

\`\`\`bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/
\`\`\`

---

## Project Structure

\`\`\`
regen-registry-review-mcp/
├── src/registry_review_mcp/   # Main package
│   ├── server.py               # MCP entry point
│   ├── config/                 # Configuration
│   ├── models/                 # Pydantic schemas
│   ├── tools/                  # MCP tools
│   └── utils/                  # Utilities
├── data/
│   ├── checklists/             # Methodology requirements
│   ├── sessions/               # Active sessions (gitignored)
│   └── cache/                  # Cached data (gitignored)
├── tests/                      # Test suite
├── examples/22-23/             # Botany Farm test data
├── docs/                       # Specifications
├── pyproject.toml
├── ROADMAP.md
└── README.md
\`\`\`

---

## The 7-Stage Workflow

1. **Initialize** - Create session and load checklist
2. **Document Discovery** - Scan and classify all documents
3. **Evidence Extraction** - Map requirements to evidence
4. **Cross-Validation** - Verify consistency across documents
5. **Report Generation** - Generate structured review report
6. **Human Review** - Present flagged items for decision
7. **Complete** - Finalize and export report

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed implementation plan.

**Current Status:**
- ✅ Phase 1 (Foundation): Complete
- 🚧 Phase 2 (Document Processing): In Progress  
- 📋 Phase 3 (Evidence Extraction): Planned
- 📋 Phase 4 (Validation & Reporting): Planned
- 📋 Phase 5 (Integration & Polish): Planned

---

## License

Copyright © 2025 Regen Network Development, Inc.

---

**Last Updated:** November 12, 2025  
**Next Milestone:** Phase 2 - Document Processing
