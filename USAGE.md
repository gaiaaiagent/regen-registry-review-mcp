# Registry Review MCP - Quick Usage Guide

## Getting Started

Once the MCP server is loaded in Claude, you'll have access to 5 tools and 1 prompt.

### Available Tools

1. **create_session** - Start a new review session
2. **load_session** - Load an existing session
3. **list_sessions** - See all available sessions
4. **update_session_state** - Update progress
5. **delete_session** - Remove a session

### Available Prompts

- **list_capabilities** - Show what the server can do

---

## Example Workflow

### 1. Create a Session

```
Use the create_session tool with these parameters:
- project_name: "Botany Farm"
- documents_path: "/home/ygg/Workspace/RegenAI/regen-registry-review-mcp/examples/22-23"
- methodology: "soil-carbon-v1.2.2"
- project_id: "C06-4997"
- proponent: "Nick Denman"
```

This will return a session_id (e.g., `session-abc123def456`)

### 2. Load the Session

```
Use the load_session tool with:
- session_id: "session-abc123def456"
```

This shows you the current state of the session including:
- Project metadata
- Workflow progress (7 stages)
- Statistics

### 3. List All Sessions

```
Use the list_sessions tool (no parameters)
```

Shows all available review sessions with their status.

### 4. Update Session State

```
Use the update_session_state tool with:
- session_id: "session-abc123def456"
- status: "in_progress"
- workflow_stage: "document_discovery"
- workflow_status: "in_progress"
```

### 5. Delete a Session

```
Use the delete_session tool with:
- session_id: "session-abc123def456"
```

---

## Testing with Example Data

The project includes real test data in `examples/22-23/`:

- **4997Botany22_Public_Project_Plan.pdf**
- **4997Botany22_Soil_Organic_Carbon_Project_Public_Baseline_Report_2022.pdf**
- **4998Botany23_GHG_Emissions_30_Sep_2023.pdf**
- **4998Botany23_Soil_Organic_Carbon_Project_Public_Monitoring_Report_2023.pdf**
- Plus review documents and methodology references

Try creating a session pointing to this directory to test the system.

---

## Current Limitations (Phase 1)

Phase 1 only includes session management. Coming in Phase 2-5:

- ⏳ Document discovery and classification
- ⏳ Evidence extraction from PDFs
- ⏳ Requirement mapping
- ⏳ Cross-document validation
- ⏳ Report generation

---

## Troubleshooting

### Server Not Appearing in Claude

1. Check `.mcp.json` exists in project root
2. Restart Claude Code
3. Check logs: Server writes to stderr

### Session Errors

- Ensure `documents_path` is an absolute path
- Verify the directory exists and contains documents
- Check file permissions on `data/` directory

### Lock Errors

If you see lock timeout errors:
```bash
find data/sessions -name ".lock" -delete
```

---

## Next Steps

Once Phase 2 is complete, you'll be able to:
- Scan and classify documents automatically
- Extract text from PDFs
- Process GIS shapefiles
- Generate document indexes

Stay tuned!

---

**Version:** 2.0.0
**Phase:** 1 (Foundation) - Complete
**Next:** Phase 2 (Document Processing)
