# Regen Network AI Agents & Registry Review Meeting

## Meeting Context
**Participants:** Representatives from Regen Network, Gaia AI, and Block Science  
**Key Attendees:** Shawn Anderson, Darren Zal, Gregory Landua (mentioned), and others  
**Location Context:** One participant joining from New York during Climate Week  

## Opening Discussion & Introductions

The meeting began with casual conversation about Climate Week in New York, with one participant mentioning an "NYC uncool kids group" on WhatsApp that organizes shared dinners and events for those who can't access all the official Climate Week events.

## AI Agent Integration Overview

### Current Experiments
The team is working on multiple AI agent experiments:
- An AI agent for registry review processes
- Collaboration with Ecometric, described as their biggest project developer with over 20 projects
- Integration work with a data engineering and geospatial specialist from Ecometric's team

The goal is to explore how these different experiments could complement each other, particularly in areas like:
- Proper data ingestion
- Addressing gaps where one system could support the other
- Accelerating processes like soil sampling, analysis, and mapping

## Testing the KOI System Agents

### Agent Access and Capabilities
The team demonstrated four main agents within the KOI system:
- **The Advocate Agent** - Has access to the Regen MCP server and can pull data from the Regen registry
- **The Narrator Agent** - Another agent with specific capabilities
- Additional agents for various functions

Login credentials were shared (Regen AI / regen2025) for testing purposes.

### User Interface Features
- Right panel displays agent details including:
  - System prompts describing the character
  - Core identity and response style
  - Available plugins
  - Avatar settings
- Settings can be modified directly through the user interface
- Users noted the absence of feedback mechanisms (thumbs up/down) in the current interface

### Technical Challenges Identified
- 502 bad gateway errors occurred during testing
- Issues with conflicting definitions of Regen Network entities:
  - Regen Network R&D PBC
  - Regen Registry
  - Ledger systems
- Need for clearer hierarchical definitions within KOI to prevent AI confusion

## Priority Agent Development

### Two Main Focus Areas

#### 1. Registry Agent for Review
This agent would handle project documentation review by:
- Processing standardized project documentation
- Checking against clear requirement checklists
- Evaluating submitted evidence
- Outputting approval status and identifying missing elements
- Addressing gray areas that currently require human judgment

#### 2. Project Developer Concierge Agent
Designed to handle the frequent inquiries from project developers:
- Serves mid to low-tier developers interested in carbon credits
- Provides automated responses to common questions
- Routes inquiries appropriately:
  - Basic information seekers → Educational resources
  - Mature developers → Direct engagement channels
- Collects valuable data on developer interests and willingness to pay

The team has been collecting inquiry data for 6-12 months to inform this agent's development.

## Registry Review Process Deep Dive

### Current Workflow Challenges
The review process begins in Microsoft systems (noted as problematic) and involves:
- Processing submissions from developers submitting 20+ projects at once
- Manual file organization and naming
- Cross-checking multiple documents
- Verifying land tenure documentation
- Checking date alignments between imagery and sampling (must be within 4 months)

### Documentation Review Steps
1. **Initial Setup**
   - Download project folders from Microsoft to Google Drive
   - Create registry review templates for each project
   - Update project names, IDs, and reporting periods

2. **Document Processing**
   - Name all submitted files appropriately
   - Verify presence of required documentation:
     - Project plans
     - Land registry documents
     - Geospatial data and maps
     - Monitoring reports

3. **Verification Tasks**
   - Cross-reference land ownership claims with registry documents
   - Verify dates across different document types
   - Check completeness against methodology-specific requirements
   - Add clarifying comments where necessary

4. **Final Steps**
   - Secondary review by team member
   - Creation of data posts for project pages
   - On-chain registration with document IDs for traceability

### Automation Opportunities

#### Areas Suitable for AI Automation
- Cross-checking documents and tables for mismatches
- Date verification and data extraction
- Land tenure verification
- Mapping metadata analysis
- Shapefile metadata processing
- Legal document parsing
- Emissions calculations verification

#### Challenges for Automation
- Shapefile analysis requiring land cover maps
- Land use history verification
- Complex legal document interpretation
- Risk assessment and responsibility determination

### Verifier Integration Potential
The team identified opportunities to extend the registry review automation to assist third-party verifiers:
- Verifiers currently duplicate much of the completeness checking work
- AI-generated reviews with source tracking could increase trust
- Would enable verifiers to focus on their unique role of checking calculations
- Could reduce costs and enable scaling to serve more projects

## Technical Implementation Considerations

### Data Provenance and Traceability
Key requirements for the system include:
- Maintaining clear provenance of all data sources
- Ability to trace answers back to specific documents
- Creating "receipts" for the data transformation pipeline
- Clear citation of sources in agent responses

### Information Architecture Challenges
- Need for better organization to make data more ingestible for AI
- Current system has information spread across multiple locations:
  - On-chain IDs for documents
  - Project documentation tables
  - Data streams with anchored posts
  - Website databases
- Requirement for a unified system or clear pointing mechanism to access distributed information

### Methodology-Specific Requirements
- Registry agents must be methodology-specific
- Cannot use one agent across multiple methodologies due to different data standards
- Biodiversity projects have significantly different requirements than other types

## Ideal Workflow Vision

The team envisions a streamlined process where:
1. Agent receives project registration request
2. Automatically accesses all relevant documents from source systems
3. Uses methodology-specific templates to check requirements
4. Verifies document presence and cites locations
5. Provides confirming comments for key fields (land tenure, dates, etc.)
6. Outputs completed checklist for human review
7. Human performs final verification and approval

## Next Steps and Action Items

1. **Document Sharing**
   - Send Giselle's memo on automation vs. manual processes
   - Share sample checklist for project registration
   - Provide examples for agent training

2. **Priority Development**
   - Start with project registration reviews (less complex)
   - Progress to credit issuance reviews (more data-intensive)
   - Focus on consistent, templated processes first

3. **Data Collection**
   - Continue gathering project developer inquiries
   - Intern to synthesize additional email data from team
   - Maintain examples of successful reviews for training

4. **System Integration**
   - Explore seamless document access methods
   - Work with Ecometric on testing and integration
   - Develop clearer definitions for Regen Network entities

## Meeting Conclusion

The discussion concluded with appreciation for the detailed dive into the complex review processes. The team acknowledged that while the details can be overwhelming, the systematic approach to automation presents significant opportunities for scaling Regen Network's impact in the carbon credit and ecological project space.
