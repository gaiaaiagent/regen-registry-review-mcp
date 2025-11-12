# High-Level Specs for Registry AI Agents

Created Date: September 9, 2025 11:12 AM
Object Type: memo
Relevance: relevant
Ready for AI: No
Created by: Becca Harman

# **High-Level Specs for Registry AI Agents**

## Exec  Summary

Regen Network is interested in developing AI agents to streamline registry compliance reviews and provide automated support to prospective methodology and project developers. This document defines the high-level specifications, functional requirements, success criteria, and integration considerations for two core agents:

1. **AI Registry Review Agent** — supports program compliance reviews by automating completeness, cross-validation, and technical checks of project documentation
2. **Prospective Developer Support Agent** — serves as a first-line guide for new and experienced project developers, reducing staff time while capturing market intelligence

## 1. AI Registry Review Agent

### Purpose

Automate the initial review of project registration and monitoring documentation for Regen Registry, checking compliance with the Program Guide, Credit Protocols, and associated evidence requirements. Produce structured, auditable review outputs for human sampling and approval.

### Inputs

- **Governance docs:** Program Guide & Credit Protocols (e.g., Version 1.1, methodology 1.2.2)
- **Project documents**: submitted from projects: Project Plans, Monitoring Reports, Sampling Plans, GIS files, lab analyses, deeds/titles, emission reports
- **Pre-developed requirement checklists**: Registry Agent Review Checklists, structured by category (land tenure, ownership, sampling, GHG accounting, safeguards, etc.)

### Core Functions

1. **Completeness Check (in line with the stated role of the Registry Agent review in the PG)**
    - Verify presence of all required documents for registration and monitoring.
    - Cross-reference ownership claims in Project Plan with deeds/titles.
    - Check that monitoring periods and crediting periods are correctly defined.
2. **Evidence Cross-Validation**
    - Compare stated ownership in Project Plan with registry/title documents.
    - Validate sampling methods: stratification, sample depth, number of cores, GNSS accuracy.
    - Confirm lab analysis includes SOC % and accreditation.
3. **Technical Verification**
    - Note MAPE between baseline and monitoring results; flag if >20%.
    - Check temporal alignment: sampling dates vs. imagery dates within ±4 months.
    - Confirm buffer pool contributions, leakage tests, and additionality evidence.
4. **Output Generation**
    - Structured report mapping each requirement to:
        - **Status**: Approved / Not Approved
        - **Section reference**: Where the evidence is found in documents (page, section, appendix).
        - **Comments**: Notes on deficiencies or clarifications needed.

### Non-Functional Requirements

- Accuracy target: ≥95% alignment with human review
- Integration with Regen Ledger back-office and internal review dashboards

### Human-in-the-Loop

- 5–10% of AI-reviewed cases are manually audited
- Feedback loop improves model performance on edge cases
- Enforce consistent submission formatting

### Success Criteria

- ≥70% reduction in first-pass review time.
- Consistent, auditable compliance assessments

### User Stories

- *As a Registry Agent, I want the AI to flag missing deeds so I don’t need to manually search for them.*
- *As a **Registry Agent**, I want the AI to highlight where in the submission evidence is located so I can quickly verify compliance*
- *As a **Team Leader**, I need to scale registry review services with a small team so we can handle more projects without proportional headcount increases.*
- *As a **Program Manager**, I want to build automation as a product offering so Regen can position itself as a leader in digital MRV and compliance.*
- *As a **Project Proponent**, I want timely and consistent reviews so I can move faster toward credit issuance without uncertainty from variable human feedback.*

---

## 2. Prospective Developer Support Agent

### Purpose

Act as a front-line resource for incoming inquiries from prospective project and methodology developers. Reduce staff time spent answering repetitive questions by providing guidance, resources, and structured next steps. Learn more about market draw of Regen for project developer audience for potential offerings. 

### Inputs

- **Training Data**: Historic inquiry emails and responses (have been documenting for 3 months)
- **Knowledge Base**:
    - Program Guide, handbook and protocol library
    - Builder Lab resources
    - Email templates
    - Documentation on concept note submission, registry processes, market FAQs
    - Contact points for methodology developers and partnership leads

### Core Functions

1. **Contextual Inquiry Handling**
    - Classify user type:
        - **Newcomer** (little to no context)
        - **Experienced developer** (technical team, capital, familiarity with standards)
    - Identify their primary goals (methodology development, project registration, collaboration)
2. **Adaptive Guidance**
    - Provide tailored next steps (e.g., review Program Guide, join Builder Lab, submit methodology concept note, schedule a call).
    - Link to relevant documentation, templates, or external resources.
3. **Conversation Management**
    - Handle FAQs on:
        - Registry’s role and offerings
        - Methodology alignment & uncertainty requirements
        - Monitoring/verification frequency and verifier recommendations
        - Permanence and risk buffer contributions
        - Market and buyer interest in credit types
    - Escalate complex cases to Regen staff when human expertise is required
4. **Data Capture & Analytics**
    - Log inquiry type, user background, questions asked, and steps recommended
    - Aggregate analytics for:
        - Common confusion points
        - Potential areas for new methodologies
        - Patterns in developer needs and market interests

### Non-Functional Requirements

- ≥75% reduction in staff response burden
- ≥80% positive feedback from developers on clarity of next steps
- Analytics available in internal dashboard or CRM?

### Human-in-the-Loop

- Staff review a subset of AI–handled interactions to refine guidance
- Escalation pathways ensure critical partnerships or unique opportunities are not missed

### Success Criteria

- Demonstrated time savings in inquiry handling.
- Data outputs enable identification of 2-3 potential revenue opportunities

### User Stories

- *As a **Newcomer Developer**, I want clear guidance on where to start so I don’t feel overwhelmed by registry requirements*
- *As an **Experienced Developer**, I want quick access to detailed methodology information so I can assess feasibility without waiting for a call*
- *As a **Partnership Manager**, I want the AI to escalate strategic inquiries (e.g., large capital, unique pilots) so I don’t miss high-value opportunities.*
- *As a **Regen Staff Member**, I want the AI to handle repetitive FAQ responses so I can focus on complex cases and relationship building.*
- *As a **Product Manager**, I want analytics on developer questions so I can identify where our documentation or processes need improvement.*
- *As an **Executive**, I want to see patterns in inbound interest (regions, project types, methodologies) so we can spot new market opportunities early.*
- *As a **Marketing/Comms Lead**, I want visibility into common confusion points so we can improve our external messaging and reduce friction.*
