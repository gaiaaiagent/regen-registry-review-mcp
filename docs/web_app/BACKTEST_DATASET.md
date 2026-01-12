# Backtest Dataset: Botany Farm

## Overview

To ensure the Registry Review Web Application accurately replicates and accelerates the manual review process, we have established a **Ground Truth Backtest Dataset**. This dataset consists of the actual documents from the **Botany Farm Partnership (C06-006)** project, along with the final completed review performed by a human Registry Agent (Rebecca Harman).

**Location:** `regen-registry-review-mcp/examples/22-23`

---

## Dataset Contents

### Input Documents (The "Unseen" Data)

These are the files the web app (and AI) should process. They cover the project lifecycle from planning to monitoring.

| Document Type | Filename | Purpose |
|---------------|----------|---------|
| **Project Plan** | `4997Botany22_Public_Project_Plan.pdf` | Core project details, methodology compliance, land tenure. |
| **Baseline Report** | `4997Botany22_Soil_Organic_Carbon_Project_Public_Baseline_Report_2022.pdf` | Initial soil states, stratification. |
| **Monitoring Report** | `4998Botany23_Soil_Organic_Carbon_Project_Public_Monitoring_Report_2023.pdf` | Year 1 performance data. |
| **GHG Data** | `4998Botany23_GHG_Emissions_30_Sep_2023.pdf` | Quantitative emission calculations. |
| **Methodology** | `Methodology_of_the_Farm_Carbon_Calculator_April_2024.pdf` | The ruleset against which the project is checked. |
| **Credit Issuance** | `Botany_Farm_Credit_Issuance_Registry_Agent_Review_2023_Monitoring.pdf` | Verification of credits. |

### Ground Truth (The "Answer Key")

**File:** `Botany_Farm_Project_Registration_Registry_Agent_Review.pdf`

This document contains the final, human-verified decisions for every requirement in the checklist.

*   **Review Outcome:** Approved
*   **Checklist:** A complete table (pages 3-8) listing every requirement (e.g., "Land Tenure," "Project Start Date") with:
    *   **Status:** "Approved"
    *   **Accepted Evidence:** Specific citations (e.g., *"Project Plan, Section 1.7"*, *"Deeds, lease agreements..."*).
    *   **Comments:** Registry Agent notes explaining the decision.

---

## Usage Guide

### 1. Benchmark for AI Extraction
Run the `evidence_extraction` stage against the Input Documents. Compare the AI-extracted snippets against the **Accepted Evidence** column in the Ground Truth PDF.

*   **Pass:** AI finds the same section (e.g., "Section 1.7").
*   **Fail:** AI misses the section or hallucinates a different one.

### 2. End-to-End Workflow Test
Use this dataset to validate the full web app flow:
1.  **Upload:** Ingest the 6 input PDF files.
2.  **Mapping:** Verify the system correctly identifies `4997Botany22_Public_Project_Plan.pdf` as the "Project Plan".
3.  **Extraction:** Check if the "Land Tenure" requirement is automatically populated with a link to Page 5 (or relevant page) of the Project Plan.
4.  **Review:** Manually "Accept" the AI suggestions.
5.  **Report:** Generate a PDF report and compare it visually and structurally to the Ground Truth PDF.

### 3. Methodology Configuration
The project uses the **Soil Organic Carbon Estimation in Regenerative Cropping and Managed Grassland Ecosystems v1.2.2** methodology.
*   **Checklist Definition:** `regen-registry-review-mcp/data/checklists/soil-carbon-v1.2.2.json`

---

## Known Nuances
*   **Project ID:** Listed as `C06-006` in the review.
*   **Crediting Period:** 01/01/2022 - 12/31/2031.
*   **Action Items:** The review notes a request for "land cover maps dating back to 2012," which was resolved. The system should ideally flag this missing data initially if the 2012 map isn't in the input bundle, simulating the "Request Revision" flow.
