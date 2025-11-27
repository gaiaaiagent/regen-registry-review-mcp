# Changelog

All notable changes to the Regen Registry Review MCP will be documented here.

## [Unreleased]

### Fixed
- **CRITICAL:** MCP error handling decorator now properly re-raises exceptions instead of returning error strings, fixing silent failures that violated the MCP protocol contract (all 25+ tools affected)

### Added
- Comprehensive error propagation regression tests (`tests/test_error_propagation.py`)
- Documentation of MCP protocol compliance in `with_error_handling` decorator

### Removed
- Unused `format_error()` function from `tool_helpers.py` (14 lines)

---

## [0.1.0] - 2025-11-26

Initial prototype implementation of Registry Review MCP with 8-stage workflow.
