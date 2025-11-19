# Registry Assistant Agent Development Meeting

*A development sync on the Regen Registry Assistant Agent between the Gaia AI and Regen Network teams*

## Opening and Context

The team gathered for a development call, with Dave grabbing lunch and noting that Becca was joining to dig into the registry assistant agent. After brief pleasantries about the weather—peak fall conditions and dreams of raking leaves—the conversation turned to the main agenda item: the registry assistant agent that had been in active development.

Darren mentioned he'd been working on the agent and had put out a specification, asking if others had seen it. The document existed on GitHub, distinct from a roadmap that Sam had shared on Notion. Gregory noted he would need to board a flight partway through the call, so the team agreed to front-load his needs and interactions.

## Administrative Items

Before diving deep into the technical work, a few housekeeping items surfaced. Darren had posted on the Regen AI forum about starting weekly posts, but his post had been flagged. Dave explained this was an automatic spam filter triggered by too many edits, and he'd already released it and reposted it on Regen's Twitter account.

Gregory raised two practical matters: he needed to update roles for Darren and Sean within Google, and he wanted to schedule a meeting with Sam, Zach, and the team for the following day at 10:30 Pacific. The purpose would be to ensure user stories remained front and center, preventing the team from getting lost in the technical weeds. Dave agreed to send calendar invitations while they talked.

## Technical Demonstration: The Registry Assistant Agent

With Gregory's immediate needs addressed, the team turned to the heart of the meeting: the registry assistant agent itself. Darren shared a link to the private GitHub repository and explained that the work represented a consolidation of three different specifications. The original had been put together by Becca, Sam had contributed one placing the agent within the context of greater infrastructure, and Gregory had provided a more recent version focusing on user stories and interface interactions.

Darren outlined that the first pass would be more focused than the full vision. Rather than building a dedicated web interface immediately or worrying about Google Drive connectivity, they were starting with a drag-and-drop approach where users could drop in a folder or specify a local directory. The agent would then conduct its review process through data extraction and cross-referencing information.

For development and testing, Darren had been working with an example directory that Becca had provided—a 2022-2023 farm project. He shared his screen to demonstrate the agent in action.

### The Seven-Stage Process

The agent operated through a seven-stage workflow: initialize, verify documents, extract information from those documents, cross-reference that information for accuracy, prompt for human review, generate a final report, and finally close the project if everything received approval.

Darren demonstrated the initialization process, where users would upload documents to begin the workflow. The system would create a dedicated directory locally on the server to store those documents and check for duplicates. If someone tried to upload the same documents again, the agent would recognize them and note that the workflow had already been initialized. The system tracked progress through all seven stages and could incrementally move forward.

However, the demonstration hit a snag. The agent that had been working the previous day was now experiencing connection issues. Darren explained he'd been improving the PDF processing component of the MCP server, which seemed to have disrupted something. The agent should have been able to access blockchain data and the KOI knowledge base for contextualization, but it couldn't connect during this particular session.

Despite the hiccup, Darren remained optimistic about having something live for testing by the end of the week or early the following week. The MCP server worked well throughout the whole workflow when used directly in Claude Code, which provided a solid foundation even if the web interface needed more work.

## Application to Real-World Projects

Becca raised an important practical question about scaling: if she were reviewing land tenure documentation for thirty farms against a project plan, would there be a threshold on how many documents the system could handle?

This opened a discussion about how to define a "project" within the agent's framework. The team was dealing with over one hundred farms being aggregated into grouped projects because many were small. A project definition might encompass multiple farms with shared characteristics, generating both farm-specific and project-wide documentation.

Darren asked how Becca would structure directories if working manually, seeking to understand the natural organizational patterns. Becca explained they were currently working with partners using a platform called Big Terra to manage geospatial information, with widget-like activities for tracking things like crop history. Ideally, they would move toward API integration with such platforms rather than manually moving folders. But for the initial phase, the workflow would involve uploading collections like land tenure documents for thirty farms alongside a single project plan, then asking the agent to verify everything matched accordingly.

Darren confirmed the system should be able to handle this use case. The first phase involved dragging in or dropping directories of files, but the team was actively working on dynamic connections to Google Drive, with direct API access being the long-term direction.

## Protocol-Specific Checklists

The conversation then turned to a crucial architectural question: training the agent on specific checklists. Becca asked whether it was already trained on the registration checklist specific to particular credit classes, noting that different protocols would require different approaches.

Within Regen's protocol library, there were eight to ten different protocols. Some focused on different aspects of soil organic carbon—perhaps emphasizing grasslands versus cropping systems—while others addressed biodiversity. Each protocol would have its own registration checklist and issuance checklist, amalgamating requirements from the program guide that affected all protocols with specific protocol requirements.

The immediate focus was on the protocol that would be hyper-scaling, which made it the logical starting point. For any other projects using this particular protocol, they would follow the same checklist and process. But the question remained: how would the agent handle the variety of protocols?

Gregory suggested that the agent should be able to query by MCP—users would specify which protocol to check against, and the agent would retrieve the appropriate checklist. However, Becca noted that manually creating these checklists and attempting to use AI to develop them had revealed considerable nuance. Determining what constituted an actual requirement and what evidence was needed wasn't as cut and dry as it might seem. For now, at least, the agent would need to use the checklist directly rather than referencing other documents.

Gregory pushed for clarity: there should be a work package dedicated to generating a library of checklists. Every protocol should have an approved checklist that made sense, derived not just automatically from documents but through careful curation. This library should ideally be available through the Regen general MCP, held in the data module or credit class metadata where it could be accessed optimally.

Becca agreed enthusiastically. For example, someone named Tika was currently developing a checklist for green infrastructure. Having a library of different checklists was exactly what they wanted to work toward. Gregory suggested a conversation with Sam about how to bring this infrastructure online so it would be optimally accessible.

## Next Steps and Testing

With the architectural questions addressed, the conversation turned to immediate next steps. Darren aimed to have the agent live on the platform by the end of the week, or early the following week at the latest. While the MCP worked well throughout the workflow when used directly in Claude Code, he preferred to get it working in the web interface, as that was ultimately the direction for these tools.

Becca committed to being completely ready for testing whenever the system went live. The plan was to start with project registration and the associated checklist, then move to the issuance checklist. This progression would allow them to test how well the agent handled different kinds of documents and data formats—various types of spreadsheets, different organizational structures, and diverse content.

Currently, the example data consisted entirely of PDFs. When Becca mentioned they typically received documents in multiple formats—PDFs, spreadsheets, TIFF files, shape files, and KML files—Darren asked for additional example directories with more diverse data types. Becca agreed to send them through, noting she hadn't wanted to overwhelm initially but was happy to provide more varied examples.

The agent could also extract images from PDFs and analyze them, which would be particularly useful for testing with maps embedded in documents.

## Broader Implications

As the meeting drew toward a close, Becca reflected on the potential for an iterative feedback loop. Testing the agent and learning from its performance could inform how they worked with partners on workflows and information organization. Rather than forcing particular approaches or being unable to work with certain formats, there was openness and desire from everyone to make the system work effectively.

The team confirmed they felt clear about focus areas and lacked significant blockers. Darren noted he needed access to Google Drive for API connectivity and authentication, and mentioned reaching out to Max about the Regen Economics website to get API access to the Notion database it was built from. He was also working on software engineer agents and the authentication and permissioning layer.

## Conclusion

The meeting captured a moment of transition from concept to implementation. The registry assistant agent represented more than just automation—it embodied a vision of human-AI collaboration that could scale Regen Network's capacity to process carbon credit projects while maintaining rigor and accuracy. With clear next steps, collaborative spirit, and a pragmatic approach to iterative development, the team moved forward with cautious optimism toward their testing phase.
