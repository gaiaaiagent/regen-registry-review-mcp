# Building the Registry Review Agent: A Conversation on Carbon Credits and Automation

## Opening Connections

The video call opened with pleasantries exchanged across hemispheres—one participant calling in from the west coast of Canada on Vancouver Island, the other from Argentina's eastern coast, 400 kilometers south of Buenos Aires. The Canadian host spoke warmly of their island home, calling it "the best place on earth," while Giselle shared her dream of someday visiting with her family of four, perhaps to see the famous Capilano Suspension Bridge that had captivated her through travel videos.

The conversation carried the gentle asymmetry of seasons: spring turning to summer in Argentina, with the promise of warm Christmases, while Canada prepared for winter. These geographic and seasonal differences set the stage for a technical collaboration that would bridge continents and disciplines.

## Introducing the Project

The Canadian developer expressed eagerness to learn about Giselle's work, explaining their collaboration with Becca on a registry automation project. The project had emerged from the tedious realities of carbon credit project registration—the endless copying of dates, terms, and values into standardized checklists. Becca had shared her workflows generously, providing the foundation for building a specialized AI assistant to streamline data verification. With Becca's mother recently hospitalized and demanding her attention, she had recommended reaching out to Giselle to continue the collaboration.

## Giselle's Journey: Eight Years of Regenerative Science

Giselle introduced herself as a biologist with a PhD in landscape ecology, one of Regen Network's founding team members spanning eight years with the organization. She was the main author of the company's scientific white paper, with deep specialization in ecosystem services evaluation and landscape analysis using GIS and remote sensing technologies.

Her proudest achievement was authoring the Comet-Plata methodology—Regen Network's first in-house methodology. Working alongside a project developer called Impact Ag, they had achieved something remarkable: the largest sale of soil organic carbon credits on Earth at that moment in 2017-2018, measuring soil organic carbon sequestration rates in rotational grazing systems across Australian farms.

The Comet-Plata methodology represented a pioneering approach, harnessing the power of machine learning and satellite remote sensing. They sampled regularly with minimum requirements, calibrating stacks of satellite imagery against geolocated field measurements. This allowed them to analyze error and uncertainty while providing comprehensive metrics. Through GIS analysis, they evaluated ecosystem resilience, vegetation cover, and habitat structure to ensure management practices mimicked conditions favorable for endangered species.

What distinguished their approach was holistic thinking—the methodology accounted for carbon credits while simultaneously measuring numerous co-benefits. Even eight years ago, the vision extended beyond carbon to encompass water quality, biodiversity markets, and flexible tracking of multiple ecological values. Giselle had helped write the program guide, design the original registry structure, and create the first credit class that would eventually accommodate these diverse environmental assets.

## The Role of Collaboration

When Sam Barnes joined the team five or six years ago, it was just as Giselle prepared to submit the first monitoring reports. Sam brought expertise in geographic information systems and a remarkable eagerness to learn about blockchain technology. Giselle recognized him as a crucial bridge between software development, GIS analysis, and methodology design. He started under her scientific umbrella before developing his own pathway through the organization.

Over the years, the team had been working to digitize everything, making systems machine-readable and automating processes wherever possible. But significant challenges remained around what truly required human judgment versus what could be automated.

## The Automation Landscape

Giselle had recently generated a report analyzing which verification tasks could be automated and which still required manual assessment using tools like Google Earth Engine and QGIS. This document identified where automation could accelerate workflows without introducing problematic errors, and where human checks remained essential—at least with current technology.

She explained her evolution from registry agent to methodology and protocol supervisor. As chief scientist, she now focused less on completeness checking and more on technical validation: ensuring shapefiles opened properly in GIS software, checking for land overlap issues, verifying that polygons in land tenure documents matched those in shapefiles, confirming that soil organic carbon sampling points contained actual data rather than empty fields.

The Canadian developer acknowledged this represented a more advanced phase beyond their current scope. Sam had articulated the principle clearly: at this stage, they should check for completeness, not correctness. Giselle agreed, though she noted her work involved more than pure correctness checking—she ensured the fundamental inputs were present and properly structured, catching errors like areas from other projects accidentally included in submission folders.

## The Shapefile Challenge

The conversation turned to shapefiles—those spatial data files that remained difficult to process automatically. Giselle wasn't sure AI could handle these validations yet, though she had seen APIs and scripts being developed in Google Earth Engine that might make it possible. The developer admitted they hadn't tackled shapefiles yet, starting instead with PDFs from Becca's test directory—a simple baseline. Becca had mentioned that submissions often included CSVs and spreadsheets as well, representing a "level two" complexity. Eventually, they hoped to work with shapefiles.

Giselle outlined her typical workflow for historical land use verification. To approve a project plan, she needed to confirm no deforestation or natural ecosystem destruction had occurred in the past ten years. She would input shapefiles into Google Earth and examine historical satellite imagery, looking for evidence of crops, wetlands, forests, or other natural ecosystems. This human visual interpretation would likely remain necessary for the foreseeable future.

However, checking for overlaps between projects in Regen Network's system seemed more amenable to automation. And here Giselle introduced a vision that had been fermenting for years.

## A Vision for Global Registry Interoperability

She had long advocated for creating the first global open-source registry where all projects from compliance and non-compliance carbon markets could register their projects and receive a unique geocoded identifier—a stamp of approval confirming no overlap with any other registered project. The concept seemed simple: one website where anyone could upload a shapefile, check for conflicts, and receive verification. This system should be interoperable, open to all governments and organizations, ingesting information from all registries to prevent double-counting and double-registration across the entire ecosystem.

Despite the apparent simplicity, nobody had built it yet. The developer loved the concept immediately, seeing it as an excellent feature to add to their automation system. They could start internally, ensuring projects within Regen Network didn't overlap or have different vintage configurations for the same land areas, then potentially expand the vision globally.

## The Current Tool Architecture

The developer shared their screen to demonstrate the prototype. Built on ChatGPT as a front-end interface, most functionality was implemented as an MCP (Model Context Protocol) server—a new standard published by Anthropic about a year ago for building tools for AI agents. They had designed an eight-stage workflow: initialization, document discovery, requirement mapping, evidence extraction, cross-validation, report generation, human review, and completion.

Each stage had predefined workflows. The system would intake documents, map them to requirements, extract evidence by searching through all files, then perform cross-validation checks. This included verifying date consistency across documents—something Becca had identified as low-hanging fruit for automation despite consuming significant amounts of her time. Two or three other validation checks were included as well, with documentation the developer promised to share later.

After generating reports, the system invited human feedback, allowing reviewers to approve or request changes. The workflow was non-linear—users could jump back to any stage at any time. Sessions mapped one-to-one with projects, creating organized tracking for each carbon credit initiative under review.

## Technical Hiccups and Real Life

The demonstration hit a snag—an error that hadn't appeared moments before. The developer realized they hadn't saved recent changes to the backend. As they worked to update the server configuration, Giselle's children returned from school, creating a moment of domestic reality interrupting the technical discussion.

Then a calendar conflict emerged. Something had appeared on the developer's schedule for the top of the hour. They apologized and suggested a follow-up meeting, expressing appreciation for getting to know each other and encouraging Giselle to experiment with the GPT interface, ask questions, and provide early feedback.

## Scheduling Next Steps

Giselle acknowledged her own pressing work—a methodology that needed review by Friday. Both agreed there was no need to force an immediate follow-up given the backend bugs requiring attention anyway. Giselle offered flexibility around her schedule, noting she had fewer meetings these weeks and more deep work planned. A quick break to discuss the project could actually be welcome when she needed to shift focus. She invited the developer to ping her when the bugs were fixed and they were ready to continue.

The call closed with mutual appreciation—two professionals from opposite hemispheres, working to bring automation and intelligence to the vital but tedious work of verifying carbon credit projects, taking a small step toward systems that could honor both human expertise and computational efficiency in service of planetary regeneration.
