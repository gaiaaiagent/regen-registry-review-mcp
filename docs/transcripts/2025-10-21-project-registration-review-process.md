# Project Registration Review Process Discussion

## Opening and Personal Updates

The meeting began with Shawn and Darren sharing their recent experience with an ayahuasca ceremony over the weekend. The three-night ceremony took place in British Columbia and was facilitated by their friend Mahul, who has been conducting ceremonies for 23 years. This was Mahul's first time leading without his partner in 12 years, as she is currently away studying. The ceremony brought together five participants, all men working in technical fields including data scientists and robotics engineers. Shawn reported feeling lighter and renewed from the experience.

## New Fellows Program

The conversation shifted to organizational updates, with discussion of three newly onboarded fellows who bring fresh perspective to the team. The fellows are being deployed across different areas: one is working with Christian on AI storytelling initiatives, another is focused on data infrastructure development, and the third is being tasked with organizing and collating historical inquiries from project developers. 

This third fellow's work is particularly strategic, as they will be preparing materials to train an AI agent for handling incoming project developer inquiries. The goal is to identify common inquiry patterns, develop appropriate response prompts, and establish routing logic for an AI agent that could assist project developers. This work is intended to support the eventual deployment of a registered agent review system, creating well-organized training data for the agent.

## Project Registration Submission Process

### Airtable Submission System

The ideal workflow begins with project developers submitting their information through Airtable. The submission form captures essential project information including submission date, contact person name and role, contact information, organization name, project name, proposed start date, and the protocol being used. 

Critically, developers must attach required documentation at this stage. The specific requirements vary by protocol, but typically include the project plan or project design document, land tenureship documentation, and evidence that there has been no land use change in the past ten years. Any supplemental information can also be attached at this stage.

### Current Workflow with Ecometric

While the Airtable system represents the target workflow, the current reality is different with established partners like Ecometric. Due to their long-standing relationship and the volume of projects they manage, Ecometric operates differently. They simply notify the team when projects are ready for submission, and staff then access their SharePoint to retrieve the necessary documentation.

Ecometric is unique among project developers in that they manage batches of projects rather than individual ones. Where most developers work with one or two projects at a time, Ecometric handles aggregated portfolios. The current batch includes 21 projects, with an upcoming aggregated project that may contain upwards of 70 individual farm projects. This volume creates significant workload challenges and underscores the urgent need for AI assistance in the review process.

Ecometric serves as an intermediary between the registry and individual farms or estates. They handle all farmer communications, coordinate documentation collection, and arrange soil sampling visits. The registry team never interacts directly with the farms themselves.

## File Organization and Project ID System

### SharePoint Structure

Ecometric's SharePoint is organized by registration year, with projects from 2023 stored together, for example. Within each year, projects are organized strictly by project ID. This organizational system is critical for maintaining data integrity across the entire lifecycle of credits.

### Importance of Project IDs

The project ID system is fundamental to the registry's operations. IDs are embedded in the on-chain metadata when projects are instantiated on the blockchain and when credit batches are created. This creates a tight, queryable connection between all project data and transactions.

The ID system becomes particularly important when dealing with farm expansions. A common scenario involves a farm initially enrolling only 75% of their land to test the program, then later adding the remaining 25%. Without strict ID tracking, these documentation updates could become extremely messy. The batch denomination visible in the credit issuance system includes the project ID, maintaining this critical linkage.

### Project Naming Complexity

Project names themselves can be complex and pose organizational challenges. Names might include special characters, making them unwieldy for file systems. Additionally, projects sometimes undergo name changes mid-process, which could create file management issues if names were used as the primary organizational system rather than IDs.

## Registry Agent Review Process

### Document Organization

The review process begins with organizing materials in Google Drive, mirroring the structure from Ecometric's SharePoint. Each project folder contains several key subdirectories: submitted materials (where project developers place their documents), registry agent review materials, and eventually credit issuance materials.

The submitted materials folder includes the all-important project plan, which contains land registry documentation within it. For projects beyond initial registration, there are also monitoring folders, though these are not relevant for the registration phase.

### The Registration Checklist

The core of the registration review is a comprehensive Google Sheets checklist. This checklist, whether for carbon farming projects or other methodologies, serves as the definitive record of the review process. It documents exactly what was reviewed, by whom, when, and what the outcomes were.

The checklist is organized into several key sections. The project details section captures metadata like project name, ID, admin name, developer name, methodology, protocol version, protocol library link, and credit class. The monitoring section tracks monitoring rounds, credit issuance information, and related details.

The registry documents section is particularly detailed, listing all required documentation and providing space to indicate whether each document was submitted, where it's located, and when it was reviewed. Documents are categorized by type, with carbon farming projects requiring items such as project plans, land eligibility documents (including land registry docs and evidence of no land use change in the past decade), GIS files, field boundaries, and management histories.

### Protocol-Specific Requirements

One of the most critical aspects of the review is ensuring alignment with the specific protocol being used. Different versions of protocols may have different requirements, and the agent review process must verify that all protocol-specific documentation is present and complete.

For carbon farming projects using certain protocols, this includes very specific documentation requirements around land eligibility, baseline establishment, and ongoing monitoring. The checklist must be tailored to match these requirements precisely.

### Review Workflow

The actual review process involves going through each requirement in the checklist and documenting compliance. For each item, the reviewer indicates whether the documentation was submitted, notes the specific filename and location, and records when the review was completed.

This process is highly tedious, particularly in three areas: writing document names into the checklist, copying those names into the appropriate requirement fields, and cross-checking that documents are in their expected locations. These represent the most time-consuming yet straightforward aspects of the review, making them ideal candidates for AI automation.

## Credit Issuance Review Process

While the meeting focused primarily on registration review, the issuance review process was also discussed as context for future development. The issuance review is significantly more complex and document-intensive than registration review.

For issuance, reviewers must examine baseline reports, monitoring round reports, sampling plans for all parcels, geolocation data for fields and soil core samples, historic yield data, emissions input documentation, and for projects using AI analysis components, both input and output data from those AI systems.

The monitoring round report is the critical document that supports credit issuance, as it contains the claims about carbon sequestration between baseline and sampling events and justifies the number of credits being requested.

While this represents a deeper analytical dive than registration review, the expectation is that at least half of the issuance review could be automated, with an agent populating straightforward documentation checks before a human reviewer validates the analysis and adds their assessment.

## Strategic Considerations and Pain Points

### Fee Structure Challenges

The current fee structure is based on per-project reviews, which works well for typical scenarios. However, the aggregated project model creates challenges. When one "project" actually comprises 70 individual farms, the review workload is enormous but doesn't fit neatly into the existing fee structure. The organization is working to develop appropriate pricing for these aggregated scenarios.

### Value of Focusing on Ecometric

Despite these challenges, Ecometric represents an ideal focus for AI development for several reasons. First, their portfolio includes over 100 projects that would benefit from AI assistance. Second, they conduct annual monitoring rounds rather than the five-year cycles common with other carbon projects, creating ongoing review needs year after year. For just Ecometric alone, managing these reviews could easily consume one person's full-time capacity if done manually.

### Development Priorities

The group identified project registration as the ideal testing ground for agent development. Once proven there, the same approach could extend to issuance reviews. Starting with registration makes sense because it's somewhat simpler than issuance, yet still represents significant value if automated.

The lowest-hanging fruit for automation includes: automatically populating document names in the checklist, copying names to the appropriate requirement fields, and cross-checking document locations. If an agent could handle these tasks, human reviewers could focus on the analytical work of comparing maps, validating analyses, and adding their expert assessment to agent-generated preliminary reviews.

## Proposed Collaborative Workflow

The discussion concluded with exploration of how humans and AI might collaborate on reviews. The proposed model involves the AI agent working in a different text color within shared Google Docs. This would allow human reviewers to easily distinguish agent work from their own additions, double-check the AI's findings, and add their expert analysis to create a complete review.

This collaborative approach acknowledges that full automation may not be immediately achievable or even desirable, but that meaningful assistance with the most tedious aspects of the work could dramatically improve efficiency and allow human expertise to be deployed where it matters most.

## Next Steps and Access Requirements

To move forward with prototype development, the team identified two critical needs: access to Google Drive to examine past review examples and access to Ecometric's SharePoint to understand their current submission structure. 

The team agreed to create a visual flowchart mapping the entire process and identifying all access points for the agent system. Understanding exactly where the agent would access data and where it would write results was identified as crucial for avoiding development blocks.

A meeting with Gregory Landua was scheduled to discuss Google Drive access, with plans to send preliminary information ahead of that conversation. The team acknowledged that examining multiple past examples in the Drive would allow them to understand patterns and replicate the review process effectively.

The focus remains on developing a prototype that solves the most painful points in the process, which are fortunately also the most straightforward to automate, creating an ideal starting point for AI assistance in registry operations.
