# Carbon Egg Multi-Project Structure

Carbon Egg is a large-scale soil carbon project encompassing over 100 individual farms across the UK, managed by Ecometric under the Regen Registry's soil-carbon-v1.2.2 methodology. The project uses a shared Project Design Document (PDD) that covers methodology, safeguards, and regulatory compliance at the meta-project level, while each farm independently provides land-specific evidence for tenure, boundaries, and ecosystem conditions.

## Architecture

Each farm is treated as an independent review session. The system uses a `scope` parameter to control which requirements apply:

- **`scope="farm"`** loads 4 requirements that need per-farm evidence:
  - REQ-002 (Land Tenure): Each farm's deed, lease, or legal attestation
  - REQ-003 (No Conversion): Each farm's 10-year land use history
  - REQ-004 (Geographic Boundaries): Each farm's GIS shapefiles and maps
  - REQ-009 (Ecosystem Conditions): Each farm's 5-year prior land use proof

- **`scope="meta"`** loads 19 requirements addressed once in the shared PDD:
  - REQ-001 (Methodology version), REQ-005 through REQ-008, REQ-010 through REQ-023
  - Covers methodology compliance, additionality, monitoring plan, safeguards, and all other programmatic requirements

- **`scope=None`** (default) loads all 23 requirements for single-farm projects or full reviews.

## Recommended Workflow

1. Create one session for the meta-project review with `scope="meta"` and the shared PDD plus any supplementary project-wide documents.

2. For each farm, create a session with `scope="farm"` and that farm's specific documents (land registry titles, GIS data, historic yields spreadsheet, land cover maps).

3. Run the standard pipeline (discovery, mapping, evidence extraction, validation, report) for each session independently.

## Document Naming

Farm-specific documents typically follow the pattern `{ProjectID}{FarmName}{Year}`, for example:
- `127224GreensLodge23 Public Project Plan.pdf`
- `104192Fonthill23 Historic 5 Year Management and Average Yields.xlsx`

Land registry documents may be named by title number (e.g., `Official Copy (Register) - LT330529.pdf`).

Shared documents are usually the PDD, methodology document, and any project-wide compliance attestations.
