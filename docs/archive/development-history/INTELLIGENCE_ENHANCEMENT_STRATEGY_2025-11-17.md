# Intelligence Enhancement Strategy

**Date:** 2025-11-17
**Status:** 🎯 Strategic Roadmap
**Priority:** HIGH (Next Major Evolution)
**Architecture:** Aligned with Workflow-Oriented, Fail-Explicit Principles

---

## Executive Summary

The Registry Review MCP server has successfully achieved core functionality with robust file handling, evidence extraction, and validation capabilities. The next evolutionary phase focuses on **intelligence enhancement** — making the system more contextually aware, proactive, and capable of inferring information while maintaining its fail-explicit safety principles.

This document outlines a comprehensive strategy for enhancing intelligence across three dimensions:

1. **Contextual Awareness** — Infer project metadata, recognize document types, detect patterns
2. **Proactive Guidance** — Surface relevant insights automatically while keeping deep context queryable
3. **Confidence-Aware Processing** — Communicate certainty levels, escalate uncertainty appropriately

The recommended architecture follows a **"Smart Highlights + Queryable Resources"** pattern that provides essential intelligence automatically (Level 1) while making deep dives available on-demand via MCP resources (Level 2).

---

## Vision: From Reactive to Intelligent

### Current State (Reactive)

The system currently operates in a primarily reactive mode:

```
User: "Initialize review for Botany Farm 2022"
System: "Created session. Run /document-discovery next."

User: "Discover documents"
System: "Found 7 documents. Classifications: unknown, unknown, unknown..."

User: "What methodology should I use?"
System: [No automatic suggestion]

User: "Extract evidence for REQ-001"
System: [Extracts evidence without confidence scoring]
```

### Desired State (Intelligent)

The enhanced system should operate with contextual awareness and proactive guidance:

```
User: "Initialize review for Botany Farm 2022"
System: "✅ Session initialized

📋 Detected Context:
  • Project ID: Likely C06-4997 (found in 3 filenames)
  • Crediting Period: 2022-2032 (inferred from filenames)
  • Methodology: Soil Carbon v1.2.2 (standard for project type)

📄 Documents Classified:
  • Project Plan (high confidence)
  • Baseline Report 2022 (high confidence)
  • Prior Review - 2021 Registry Approval ⭐

💡 Intelligence:
  Prior review found (2021). I can use this as reference for:
  • Requirement interpretation precedents
  • Evidence format expectations
  • Common issues and resolutions

Next: Ready to extract evidence. Run /extract-evidence or query specific requirements."
```

The transformation centers on **inference, recognition, and proactive insight** while maintaining human oversight for uncertain cases.

---

## The 10 Intelligence Factors

### 1. Document Intelligence & Pattern Recognition

**Current:** Filename pattern matching with hardcoded patterns
**Enhanced:** Multi-signal document classification + metadata extraction

**Capabilities:**
- Parse project IDs from filenames (`Botany_Farm_C06-4997_ProjectPlan.pdf` → `C06-4997`)
- Extract years and date ranges (`Baseline_2022-2032.pdf` → crediting period)
- Recognize document versions (`ProjectPlan_v3.2.pdf` → version 3.2)
- Detect prior registry reviews by content signatures
- Classify by filename, content patterns, and metadata

**Implementation:**
```python
# Enhanced classification
class DocumentIntelligence:
    def classify_with_metadata(self, filepath: Path, content: bytes) -> DocumentClassification:
        # Multi-signal approach
        filename_signal = self._classify_by_filename(filepath.name)
        content_signal = self._classify_by_content_patterns(content)
        metadata_signal = self._extract_metadata(content)

        # Combine signals with confidence scoring
        classification = self._combine_signals(
            filename=filename_signal,
            content=content_signal,
            metadata=metadata_signal
        )

        return DocumentClassification(
            type=classification.type,
            confidence=classification.confidence,
            metadata={
                "project_id": metadata_signal.project_id,
                "year": metadata_signal.year,
                "version": metadata_signal.version,
                "is_prior_review": metadata_signal.is_prior_review
            }
        )
```

**Value:** Reduces "unknown" classifications, extracts actionable metadata automatically

---

### 2. Contextual Workflow Understanding

**Current:** Sequential prompts with fixed messaging
**Enhanced:** Context-aware prompts that adapt to session state

**Capabilities:**
- Detect session readiness (all docs classified → ready for evidence extraction)
- Recognize blockers (missing critical documents → suggest upload)
- Understand previous stage results (low confidence classifications → suggest manual review)
- Provide stage-appropriate next steps

**Implementation:**
```python
def generate_context_aware_message(session: Session) -> str:
    """Generate prompts based on current session state."""

    # Analyze session state
    state = SessionStateAnalyzer(session)

    if state.has_prior_review():
        prior_review_guidance = (
            "\n💡 **Prior Review Detected**\n"
            f"Found prior review: {state.prior_review_filename}\n"
            "This can serve as reference for requirement interpretations.\n"
        )
    else:
        prior_review_guidance = ""

    if state.has_low_confidence_classifications():
        classification_warning = (
            "\n⚠️ **Classification Uncertainty**\n"
            f"{state.low_confidence_count} documents have uncertain classifications.\n"
            "Consider manual review before evidence extraction.\n"
        )
    else:
        classification_warning = ""

    # Context-aware next steps
    next_steps = state.recommend_next_steps()

    return f"""
{prior_review_guidance}{classification_warning}

**Recommended Next Steps:**
{next_steps}
"""
```

**Value:** Guides users through workflow intelligently, surfaces relevant context automatically

---

### 3. Proactive Evidence Extraction Strategy

**Current:** Extract evidence per requirement on demand
**Enhanced:** Intelligent document-to-requirement mapping with confidence

**Capabilities:**
- Pre-map documents to likely requirements during discovery
- Suggest optimal extraction order (high-confidence matches first)
- Detect evidence gaps early (requirements with no candidate documents)
- Cross-reference prior review findings

**Implementation:**
```python
class EvidenceStrategy:
    def plan_extraction(self, session: Session) -> ExtractionPlan:
        """Plan evidence extraction based on document intelligence."""

        # Map documents to requirements
        mappings = []
        for req in session.requirements:
            candidate_docs = self._find_candidate_documents(
                requirement=req,
                documents=session.documents,
                prior_review=session.prior_review
            )

            mappings.append(RequirementMapping(
                requirement_id=req.id,
                candidate_documents=candidate_docs,
                confidence=self._calculate_mapping_confidence(candidate_docs),
                prior_review_reference=self._find_prior_evidence(req, session.prior_review)
            ))

        return ExtractionPlan(
            high_confidence=mappings.filter(confidence > 0.8),
            medium_confidence=mappings.filter(0.5 < confidence <= 0.8),
            low_confidence=mappings.filter(confidence <= 0.5),
            gaps=mappings.filter(no_candidates=True)
        )
```

**Value:** Optimizes extraction workflow, identifies gaps early, leverages prior reviews

---

### 4. Intelligent Prompting & User Communication

**Current:** Fixed template messages
**Enhanced:** Dynamic, context-aware messages with actionable intelligence

**Capabilities:**
- Surface high-confidence findings automatically
- Communicate confidence levels explicitly ("high confidence", "uncertain - verify")
- Provide reasoning for classifications and mappings
- Format information hierarchically (essential → details on request)

**Example Enhancement:**

**Before:**
```
Session initialized.
Documents discovered: 7
Run /extract-evidence next.
```

**After:**
```
✅ Session Initialized

📋 **Project Context** (inferred from documents):
  • Project ID: C06-4997 (detected in 3 filenames)
  • Crediting Period: 2022-2032
  • Methodology: Soil Carbon v1.2.2

📄 **Documents Classified** (7 total):
  ✅ High Confidence (5):
    • Project Plan (C06-4997_ProjectPlan.pdf)
    • Baseline Report 2022 (Baseline_2022.pdf)
    • Monitoring Plan (MonitoringPlan.pdf)
    • Site Description (SiteDescription_BotanyFarm.pdf)
    • Prior Review - 2021 Registry Approval ⭐

  ⚠️ Uncertain (2):
    • Document_2023.pdf - appears to be monitoring data
    • BotanyFarm_misc.pdf - needs manual classification

💡 **Intelligence**:
  Prior review found (2021 approval). Available as reference for:
    • Requirement interpretation precedents
    • Evidence format expectations
    • Query via: /prior-review-summary

📊 **Extraction Readiness**:
  • High-confidence mappings: 18/23 requirements (78%)
  • Potential gaps: REQ-015, REQ-019, REQ-022
  • Recommend: Review uncertain docs before extraction

**Next Steps:**
  1. Review uncertain classifications (optional)
  2. Run /extract-evidence to begin automated extraction
  3. Query /evidence-plan for detailed extraction strategy
```

**Value:** Reduces cognitive load, surfaces actionable insights, maintains transparency

---

### 5. Hierarchical Evidence Extraction

**Current:** Single-pass extraction per requirement
**Enhanced:** Multi-level extraction with progressive disclosure

**Capabilities:**
- Level 1 (Auto): Extract high-confidence evidence automatically
- Level 2 (Verify): Flag medium-confidence evidence for review
- Level 3 (Manual): Escalate low-confidence cases to human
- Cross-validate evidence across multiple documents

**Implementation:**
```python
class HierarchicalExtractor:
    async def extract_evidence(self, requirement: Requirement, documents: list[Document]) -> Evidence:
        # Level 1: High-confidence extraction
        primary_evidence = await self._extract_primary(requirement, documents)

        if primary_evidence.confidence >= 0.8:
            # Auto-accept high confidence
            return primary_evidence.with_status("accepted")

        # Level 2: Cross-validation for medium confidence
        if 0.5 <= primary_evidence.confidence < 0.8:
            cross_validation = await self._cross_validate(primary_evidence, documents)

            if cross_validation.confirms():
                return primary_evidence.with_status("accepted_after_validation")
            else:
                return primary_evidence.with_status("needs_human_review")

        # Level 3: Escalate low confidence
        return primary_evidence.with_status("human_review_required")
```

**Value:** Balances automation with safety, optimizes human reviewer time

---

### 6. Learning from Document Corpus

**Current:** Each requirement processed independently
**Enhanced:** Learn patterns from document set and prior reviews

**Capabilities:**
- Recognize common document structures (project plan layouts, baseline formats)
- Learn evidence location patterns (project ID usually in header, dates in section 1.2)
- Build project-specific vocabulary (technical terms, site names)
- Reference prior review interpretations

**Implementation:**
```python
class CorpusLearning:
    def analyze_document_corpus(self, documents: list[Document]) -> CorpusIntelligence:
        """Learn patterns from complete document set."""

        # Extract common structures
        structures = self._analyze_structures(documents)

        # Build vocabulary
        vocabulary = self._build_vocabulary(documents)

        # Identify patterns
        patterns = self._identify_patterns(documents)

        return CorpusIntelligence(
            common_layouts=structures.layouts,
            key_terms=vocabulary.technical_terms,
            evidence_locations=patterns.evidence_locations,
            project_specific_context=vocabulary.site_specific_terms
        )
```

**Value:** Improves extraction accuracy, reduces false negatives, adapts to project conventions

---

### 7. Confidence-Based Reporting

**Current:** Binary present/absent evidence reporting
**Enhanced:** Confidence-scored findings with reasoning

**Capabilities:**
- Score every finding (high/medium/low confidence)
- Explain confidence rationale
- Aggregate confidence across requirements
- Surface uncertainty explicitly

**Implementation:**
```python
class ConfidenceScoring:
    def score_evidence(self, evidence: Evidence) -> ConfidenceScore:
        """Score evidence confidence with explanation."""

        factors = {
            "citation_quality": self._score_citation(evidence.citation),
            "text_relevance": self._score_relevance(evidence.text, evidence.requirement),
            "cross_validation": self._score_cross_validation(evidence),
            "prior_review_alignment": self._score_prior_alignment(evidence)
        }

        # Weighted average
        overall_score = sum(
            weight * score
            for (factor, score), weight in zip(factors.items(), FACTOR_WEIGHTS)
        )

        # Determine level
        if overall_score >= 0.8:
            level = "high"
            recommendation = "Auto-accept"
        elif overall_score >= 0.5:
            level = "medium"
            recommendation = "Verify before accepting"
        else:
            level = "low"
            recommendation = "Human review required"

        return ConfidenceScore(
            level=level,
            score=overall_score,
            factors=factors,
            recommendation=recommendation,
            reasoning=self._explain_score(factors, overall_score)
        )
```

**Example Output:**
```json
{
  "requirement_id": "REQ-001",
  "evidence_found": true,
  "confidence": {
    "level": "high",
    "score": 0.87,
    "recommendation": "Auto-accept",
    "reasoning": "Strong citation (ProjectPlan.pdf, p.2), exact version match, cross-validated in Baseline report"
  },
  "citation": "ProjectPlan.pdf, Section 1.1, Page 2",
  "excerpt": "This project applies Soil Carbon v1.2.2..."
}
```

**Value:** Transparent decision-making, optimized review workflow, reduced uncertainty

---

### 8. Adaptive Methodology Loading

**Current:** Fixed methodology (Soil Carbon v1.2.2)
**Enhanced:** Auto-detect methodology from documents, load appropriate checklist

**Capabilities:**
- Detect methodology version from project plan
- Load corresponding requirements checklist
- Warn about version mismatches
- Support multiple methodologies dynamically

**Implementation:**
```python
class MethodologyDetection:
    def detect_methodology(self, documents: list[Document]) -> MethodologyMatch:
        """Detect methodology from document content."""

        patterns = {
            "soil-carbon-v1.2.2": [
                r"Soil Carbon.*v1\.2\.2",
                r"Soil Enrichment.*v1\.2\.2",
                r"Credit Class: Soil Carbon.*Version 1\.2\.2"
            ],
            "grassland-v1.0": [
                r"Grassland.*v1\.0",
                r"Credit Class: Grassland.*Version 1\.0"
            ]
        }

        matches = []
        for doc in documents:
            for methodology_id, method_patterns in patterns.items():
                if self._match_any_pattern(doc.content, method_patterns):
                    matches.append(MethodologyMatch(
                        methodology_id=methodology_id,
                        document=doc.filename,
                        confidence=self._calculate_match_confidence(doc, method_patterns)
                    ))

        # Return highest confidence match
        return max(matches, key=lambda m: m.confidence) if matches else None
```

**Value:** Supports multiple project types, reduces manual configuration, prevents version errors

---

### 9. Multi-Document Cross-Referencing

**Current:** Extract evidence from single best document
**Enhanced:** Cross-validate findings across multiple documents

**Capabilities:**
- Verify critical facts appear in multiple documents
- Detect inconsistencies across documents
- Build composite evidence from multiple sources
- Flag contradictions for human review

**Implementation:**
```python
class CrossReferencing:
    async def cross_validate_evidence(
        self,
        requirement: Requirement,
        primary_evidence: Evidence,
        all_documents: list[Document]
    ) -> CrossValidation:
        """Validate evidence across multiple documents."""

        # Extract same requirement from other documents
        supporting_evidence = []
        contradicting_evidence = []

        for doc in all_documents:
            if doc.filename == primary_evidence.source_document:
                continue  # Skip primary source

            doc_evidence = await self._extract_from_document(requirement, doc)

            if doc_evidence.supports(primary_evidence):
                supporting_evidence.append(doc_evidence)
            elif doc_evidence.contradicts(primary_evidence):
                contradicting_evidence.append(doc_evidence)

        # Determine validation result
        if contradicting_evidence:
            status = "contradiction_found"
            action = "human_review_required"
        elif len(supporting_evidence) >= 2:
            status = "strongly_validated"
            action = "high_confidence_accept"
        elif len(supporting_evidence) == 1:
            status = "validated"
            action = "medium_confidence_accept"
        else:
            status = "single_source_only"
            action = "verify_recommended"

        return CrossValidation(
            status=status,
            action=action,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence
        )
```

**Value:** Increases accuracy, detects document inconsistencies, builds stronger evidence

---

### 10. Progressive Disclosure of Results

**Current:** All-or-nothing results
**Enhanced:** Stream results as they become available, hierarchical detail levels

**Capabilities:**
- Stream extraction progress (REQ-001 complete, REQ-002 in progress...)
- Level 1: Summary results (23/23 requirements satisfied)
- Level 2: Detailed evidence (citations, excerpts)
- Level 3: Full analysis (confidence scores, cross-validation, reasoning)

**Implementation:**
```python
# MCP Resource hierarchy
resources = {
    # Level 1: Summary
    "session://{session_id}/summary": {
        "requirements_satisfied": 23,
        "requirements_total": 23,
        "confidence_breakdown": {"high": 18, "medium": 4, "low": 1},
        "status": "review_recommended"
    },

    # Level 2: Evidence
    "session://{session_id}/evidence": {
        "REQ-001": {
            "status": "satisfied",
            "confidence": "high",
            "citation": "ProjectPlan.pdf, Section 1.1, Page 2"
        },
        # ... all requirements
    },

    # Level 3: Full analysis
    "session://{session_id}/evidence/REQ-001/detailed": {
        "requirement_text": "Projects shall apply the latest version...",
        "evidence_excerpt": "This project applies Soil Carbon v1.2.2...",
        "confidence_score": {
            "level": "high",
            "score": 0.87,
            "factors": {...},
            "reasoning": "..."
        },
        "cross_validation": {...},
        "prior_review_reference": {...}
    }
}
```

**Value:** Optimizes LLM context usage, enables incremental review, supports different detail needs

---

## The 8 Information Categories to Surface

### Category 1: Session Initialization Context

**What to Surface:**

```markdown
📋 **Project Context** (auto-detected):
  • Project ID: C06-4997 (found in 3 filenames - high confidence)
  • Crediting Period: 2022-2032 (extracted from Baseline_2022.pdf)
  • Methodology: Soil Carbon v1.2.2 (detected in ProjectPlan.pdf, Section 1.1)
  • Project Type: Regenerative Agriculture - Soil Carbon Sequestration
  • Location: Botany Farm, [State] (if detectable)

📊 **Document Overview**:
  • Total Documents: 7
  • Core Documents Present: ✅ Project Plan, ✅ Baseline Report, ✅ Monitoring Plan
  • Supporting Documents: 3
  • Prior Reviews: 1 (2021 Registry Approval ⭐)

⚙️ **Session Configuration**:
  • Methodology Checklist: Soil Carbon v1.2.2 (23 requirements)
  • Evidence Extraction: Enabled
  • Cross-Validation: Enabled
  • Prior Review Reference: Available
```

**How Obtained:**
- Project ID: Regex patterns on filenames (`C\d{2}-\d{4}`)
- Crediting Period: Date range extraction from filenames and content
- Methodology: Content pattern matching in project plan
- Documents: Enhanced classification with confidence scoring

**Value:** User sees immediate context, reduces need to ask basic questions

---

### Category 2: Document Classification Intelligence

**What to Surface:**

```markdown
📄 **Documents Classified** (7 total):

✅ **High Confidence** (5 documents):
  1. Project Plan
     • File: C06-4997_ProjectPlan_v2.pdf
     • Confidence: 0.95 (filename + content patterns)
     • Key Metadata: Version 2, 45 pages, dated 2022-01-15

  2. Baseline Report 2022
     • File: Baseline_Report_2022-2032.pdf
     • Confidence: 0.92 (filename + section headers)
     • Key Metadata: Crediting period 2022-2032, 78 pages

  3. Monitoring Plan
     • File: MonitoringPlan_BotanyFarm.pdf
     • Confidence: 0.89 (filename pattern)

  4. Site Description
     • File: SiteDescription_BotanyFarm.pdf
     • Confidence: 0.87 (filename pattern)

  5. Prior Review - 2021 Registry Approval ⭐
     • File: Registry_Review_2021_Approval.pdf
     • Confidence: 0.94 (content signature match)
     • Intelligence: Can use as reference for requirement interpretations

⚠️ **Medium Confidence** (1 document):
  6. Monitoring Data (likely)
     • File: Document_2023.pdf
     • Confidence: 0.65 (content patterns suggest monitoring data)
     • Recommendation: Manual review suggested

❓ **Low Confidence** (1 document):
  7. Unknown Document Type
     • File: BotanyFarm_misc.pdf
     • Confidence: 0.35 (no clear classification signals)
     • Recommendation: Manual classification required
```

**How Obtained:**
- Enhanced `classify_document_by_filename()` with content analysis
- Metadata extraction (version, date, page count)
- Prior review signature detection
- Confidence scoring based on multiple signals

**Value:** Transparent classification, clear confidence levels, actionable recommendations

---

### Category 3: Prior Review Intelligence

**What to Surface:**

```markdown
⭐ **Prior Review Detected**

📋 **Review Details**:
  • Document: Registry_Review_2021_Approval.pdf
  • Review Date: 2021-08-15
  • Status: Approved
  • Reviewer: Regen Registry Review Team
  • Methodology Version: Soil Carbon v1.2.2 (same as current)

💡 **Intelligence Available**:
  ✅ Requirement Interpretations: 23/23 requirements have precedents
  ✅ Evidence Formats: Examples of accepted evidence available
  ✅ Common Issues: 3 issues flagged and resolved in prior review
  ✅ Approval Conditions: 2 conditions noted for ongoing compliance

📊 **Relevance to Current Review**:
  • Methodology Match: ✅ Same version (v1.2.2)
  • Project Continuity: ✅ Same project (C06-4997)
  • Crediting Period: Previous: 2017-2022, Current: 2022-2032
  • Value: High - direct precedent for requirement interpretation

🔍 **Available Queries**:
  • /prior-review-summary - Full summary of prior review findings
  • /prior-evidence REQ-XXX - See how specific requirement was satisfied previously
  • /prior-issues - Review flagged issues and resolutions
```

**How Obtained:**
- Prior review detection during document classification
- Parse prior review structure (requirements, evidence, findings)
- Extract metadata (review date, status, reviewer)
- Map prior evidence to current requirements

**Value:** Leverage institutional knowledge, maintain consistency, reduce re-interpretation

---

### Category 4: Requirement Coverage Intelligence

**What to Surface:**

```markdown
📊 **Requirement Coverage Analysis**

**Overall Coverage**: 23/23 requirements (100%)

**Confidence Breakdown**:
  • ✅ High Confidence: 18 requirements (78%)
  • ⚠️ Medium Confidence: 4 requirements (17%)
  • ❌ Low Confidence: 1 requirement (4%)

**High-Confidence Requirements** (18):
  REQ-001 ✅ Methodology Version
    • Evidence: ProjectPlan.pdf, Section 1.1, Page 2
    • Cross-Validation: Also referenced in Baseline Report
    • Prior Review: Same evidence accepted in 2021

  REQ-002 ✅ Project Eligibility
    • Evidence: ProjectPlan.pdf, Section 2.1, Pages 5-7
    • Confidence: 0.91 (strong match)

  [... 16 more high-confidence requirements]

**Medium-Confidence Requirements** (4):
  REQ-015 ⚠️ Additionality Documentation
    • Evidence: ProjectPlan.pdf, Section 4.3, Pages 22-24
    • Confidence: 0.68 (evidence present but interpretation uncertain)
    • Recommendation: Human verification recommended
    • Prior Review: Different approach used in 2021

  [... 3 more medium-confidence requirements]

**Low-Confidence Requirements** (1):
  REQ-019 ❌ Social Impact Assessment
    • Evidence: Not found in primary documents
    • Potential: BotanyFarm_misc.pdf (unclassified) may contain this
    • Recommendation: Manual review of misc document required
    • Prior Review: Satisfied with standalone document in 2021

💡 **Recommendations**:
  1. Auto-accept 18 high-confidence findings
  2. Review 4 medium-confidence findings (est. 15 min)
  3. Manual search for REQ-019 evidence (check misc.pdf)
```

**How Obtained:**
- Pre-map documents to requirements during discovery
- Calculate confidence scores per requirement
- Compare to prior review evidence
- Identify gaps and uncertainties

**Value:** Clear roadmap for review, optimized effort allocation, early gap detection

---

### Category 5: Methodology Alignment Intelligence

**What to Surface:**

```markdown
📋 **Methodology Alignment**

**Detected Methodology**:
  • Name: Soil Carbon v1.2.2
  • Detection Source: ProjectPlan.pdf, Section 1.1
  • Confidence: 0.96 (explicit version reference)
  • Checklist Loaded: ✅ soil-carbon-v1.2.2.json (23 requirements)

**Version Consistency Check**:
  ✅ Project Plan: Soil Carbon v1.2.2
  ✅ Baseline Report: Soil Carbon v1.2.2
  ✅ Monitoring Plan: Soil Carbon v1.2.2
  ✅ Prior Review: Soil Carbon v1.2.2

  **Status**: ✅ All documents reference same methodology version

**Methodology Updates**:
  • Current Version: v1.2.2 (2021-06-01)
  • Latest Available: v1.2.2 (up to date ✅)
  • Previous Version: v1.2.1 (2020-03-15)
  • Changes from v1.2.1: Minor clarifications, no requirement changes

**Compliance Status**:
  ✅ Using latest methodology version (REQ-001 satisfied)
```

**How Obtained:**
- Methodology detection from document content
- Cross-check version references across documents
- Compare to available methodology database
- Verify requirement alignment

**Value:** Ensures version consistency, detects outdated references, validates compliance

---

### Category 6: Cross-Document Validation Intelligence

**What to Surface:**

```markdown
🔍 **Cross-Document Validation**

**Validation Summary**:
  • Requirements Cross-Validated: 18/23 (78%)
  • Consistent Evidence: 17/18 (94%)
  • Contradictions Found: 1 ⚠️

**Validation Details**:

✅ **Strongly Validated** (17 requirements):
  REQ-001 - Methodology Version
    • Primary: ProjectPlan.pdf, Section 1.1, Page 2
    • Supporting: Baseline Report, Page 1 ✅
    • Supporting: Monitoring Plan, Page 1 ✅
    • Status: Consistent across 3 documents

  REQ-003 - Project Boundary
    • Primary: ProjectPlan.pdf, Section 3.1, Pages 12-15
    • Supporting: Site Description, Pages 2-5 ✅
    • Supporting: Baseline Report, Section 2.1 ✅
    • GIS File: BotanyFarm_Boundary.shp ✅
    • Status: Consistent across 3 docs + GIS validation

⚠️ **Contradiction Detected** (1 requirement):
  REQ-007 - Baseline Sampling Date
    • Primary: Baseline Report states "2022-03-15"
    • Contradiction: Monitoring Plan states "2022-03-20"
    • Difference: 5-day discrepancy
    • Impact: Medium (may affect compliance)
    • Recommendation: Human review required to resolve discrepancy
    • Prior Review: 2021 review had baseline date of "2017-03-12" (no discrepancy noted)

🔍 **Single-Source Evidence** (5 requirements):
  REQ-015, REQ-018, REQ-019, REQ-021, REQ-023
  • Evidence found in only one document each
  • Recommendation: Acceptable but no cross-validation possible
```

**How Obtained:**
- Extract same requirement from multiple documents
- Compare evidence snippets for consistency
- Detect contradictions and discrepancies
- Score validation strength

**Value:** Catches document inconsistencies, strengthens evidence, identifies conflicts early

---

### Category 7: Actionable Recommendations

**What to Surface:**

```markdown
💡 **Actionable Recommendations**

**Priority Actions**:

🔴 **High Priority** (1 action):
  1. Resolve Baseline Sampling Date Discrepancy
     • Issue: REQ-007 has conflicting dates (2022-03-15 vs 2022-03-20)
     • Documents: Baseline Report vs Monitoring Plan
     • Impact: May affect compliance determination
     • Action: Review source documents and determine correct date
     • Estimated Time: 5 minutes

🟡 **Medium Priority** (4 actions):
  2. Verify REQ-015 Evidence (Additionality)
     • Issue: Medium confidence (0.68) on interpretation
     • Document: ProjectPlan.pdf, Section 4.3
     • Action: Human verification of additionality documentation
     • Estimated Time: 10 minutes

  3. Classify BotanyFarm_misc.pdf
     • Issue: Unknown document type may contain REQ-019 evidence
     • Action: Manual review and classification
     • Estimated Time: 5 minutes

  4-5. [... 2 more medium-priority items]

🟢 **Low Priority** (2 actions):
  6. Review Prior Review Differences
     • Opportunity: REQ-015 used different approach in 2021
     • Action: Compare approaches for consistency (optional)
     • Estimated Time: 5 minutes

  7. Enhance Metadata
     • Opportunity: Add project location, proponent details
     • Action: Extract from documents or query user
     • Estimated Time: 2 minutes

**Workflow Optimization**:
  • Auto-Accept: 18 requirements (high confidence) → 0 minutes
  • Review Priority: Complete 3 high/medium actions → ~20 minutes
  • Optional: Complete low-priority actions → +7 minutes

  **Total Estimated Review Time**: 20-27 minutes
```

**How Obtained:**
- Analyze confidence scores and identify low-confidence items
- Detect contradictions and gaps
- Prioritize by compliance impact
- Estimate effort based on action type

**Value:** Clear action plan, optimized workflow, realistic time estimates

---

### Category 8: Uncertainty and Confidence Signals

**What to Surface:**

```markdown
📊 **Confidence & Uncertainty Analysis**

**Overall Confidence**:
  • High Confidence: 78% of requirements (18/23)
  • Medium Confidence: 17% of requirements (4/23)
  • Low Confidence: 4% of requirements (1/23)

  **Recommendation**: Review recommended for medium/low confidence items

**High-Confidence Indicators** (18 requirements):
  ✅ Strong citation quality (exact page/section references)
  ✅ Cross-validated across multiple documents
  ✅ Aligned with prior review evidence
  ✅ Explicit text matches requirement language

  **Action**: Auto-accept with human spot-check

**Medium-Confidence Indicators** (4 requirements):
  ⚠️ Evidence present but requires interpretation
  ⚠️ Single-source evidence (no cross-validation)
  ⚠️ Different approach than prior review
  ⚠️ Indirect evidence (requires inference)

  **Action**: Human verification recommended

**Low-Confidence Indicators** (1 requirement):
  ❌ No clear evidence found in primary documents
  ❌ Classification uncertainty (unclassified document may contain evidence)

  **Action**: Manual review required

**Confidence Scoring Methodology**:
  We score confidence based on:
  1. Citation Quality (0-25 points): Page/section specificity
  2. Text Relevance (0-25 points): How directly text addresses requirement
  3. Cross-Validation (0-25 points): Evidence consistency across documents
  4. Prior Review Alignment (0-25 points): Match with previous evidence

  **Thresholds**:
  • High: ≥80 points (0.80 score)
  • Medium: 50-79 points (0.50-0.79 score)
  • Low: <50 points (<0.50 score)

**Uncertainty Sources**:
  1. Document Classification (2 documents uncertain)
  2. Requirement Interpretation (4 requirements need verification)
  3. Evidence Location (1 requirement not found in expected documents)
  4. Cross-Validation (1 contradiction detected)

**Transparency Commitment**:
  • All confidence scores include reasoning
  • Scoring factors are visible and auditable
  • Uncertainty is surfaced explicitly, never hidden
  • When uncertain, we escalate to human review (fail-explicit principle)
```

**How Obtained:**
- Confidence scoring system for all evidence
- Aggregate scores across requirements
- Categorize uncertainty sources
- Explain scoring methodology transparently

**Value:** Transparent decision-making, calibrated trust, optimized human oversight

---

## Recommended Architecture: "Smart Highlights + Queryable Resources"

### Design Philosophy

The recommended architecture balances two competing needs:

1. **Reduce Cognitive Load**: Don't overwhelm users with information
2. **Enable Deep Dives**: Make comprehensive context available when needed

This is achieved through a **two-level information architecture**:

- **Level 1 (Auto)**: Smart highlights surfaced automatically in prompt responses
- **Level 2 (On-Demand)**: Deep context available via MCP resources

### Level 1: Smart Highlights (Automatic)

**What:** Essential intelligence surfaced in prompt responses

**When:** Automatically during each workflow stage

**Example - Enhanced `/initialize` Response:**

```markdown
✅ Registry Review Session Initialized

**Session ID:** `session_20251117_C06-4997`

---

## 📋 Project Context (auto-detected)

**Project Identification**:
  • Project ID: C06-4997 (detected in 3 filenames - high confidence)
  • Project Name: Botany Farm Regenerative Agriculture
  • Crediting Period: 2022-2032 (extracted from Baseline_2022.pdf)

**Methodology**:
  • Detected: Soil Carbon v1.2.2 (ProjectPlan.pdf, Section 1.1)
  • Checklist Loaded: ✅ 23 requirements
  • Status: ✅ Latest version (up to date)

---

## 📄 Documents Classified (7 total)

✅ **High Confidence** (5):
  • Project Plan (C06-4997_ProjectPlan_v2.pdf)
  • Baseline Report 2022 (Baseline_Report_2022-2032.pdf)
  • Monitoring Plan (MonitoringPlan_BotanyFarm.pdf)
  • Site Description (SiteDescription_BotanyFarm.pdf)
  • Prior Review - 2021 Registry Approval ⭐

⚠️ **Needs Review** (2):
  • Document_2023.pdf (likely monitoring data - medium confidence)
  • BotanyFarm_misc.pdf (unknown type - needs manual classification)

---

## ⭐ Prior Review Detected

**Review**: 2021 Registry Approval (Registry_Review_2021_Approval.pdf)
**Status**: Approved
**Methodology**: Soil Carbon v1.2.2 (same as current ✅)

**Intelligence Available**:
  • Requirement interpretation precedents for all 23 requirements
  • Examples of accepted evidence formats
  • Query: `/prior-review-summary` or `/prior-evidence REQ-XXX`

---

## 📊 Extraction Readiness

**Requirement Coverage**:
  • High-confidence mappings: 18/23 requirements (78%)
  • Medium-confidence mappings: 4/23 requirements (17%)
  • Low-confidence mappings: 1/23 requirement (4%)

**Potential Gaps**:
  • REQ-019: No clear evidence in primary docs (check BotanyFarm_misc.pdf)

**Recommendations**:
  1. Classify uncertain documents (optional, 10 min)
  2. Proceed to evidence extraction (recommended)
  3. Review medium/low confidence items after extraction

---

## 🔍 Deep Context Available

Query these MCP resources for detailed information:
  • `session://context` - Full project context and metadata
  • `session://documents` - Complete document classifications
  • `session://prior-reviews` - Prior review analysis
  • `session://evidence-plan` - Detailed extraction strategy

---

## Next Steps

**Ready to extract evidence.**

Run one of:
  • `/extract-evidence` - Auto-extract all requirements
  • `/evidence-plan` - View detailed extraction strategy first
  • `/prior-review-summary` - Review prior approval details
```

**Characteristics of Level 1 Information**:
- ✅ Essential context only (project ID, methodology, document count)
- ✅ High-confidence findings (18 requirements ready)
- ✅ Clear action items (classify 2 docs, extract evidence)
- ✅ Uncertainty signals (2 docs uncertain, 1 requirement gap)
- ✅ Next steps guidance (what to do next)
- ❌ Not exhaustive (doesn't list all 23 requirements)
- ❌ Not detailed (doesn't show full evidence excerpts)

**Result**: User gets immediate value without information overload. LLM agent has context to make intelligent next move.

---

### Level 2: Queryable Resources (On-Demand)

**What:** Comprehensive deep-dive information via MCP resources

**When:** On user/agent request via resource URIs

**New MCP Resources to Add**:

#### 1. `session://{session_id}/context`
**Purpose:** Complete project context and metadata

```json
{
  "project": {
    "id": "C06-4997",
    "name": "Botany Farm Regenerative Agriculture",
    "crediting_period": {
      "start": 2022,
      "end": 2032,
      "duration_years": 10
    },
    "location": {
      "site_name": "Botany Farm",
      "coordinates": "extracted from GIS if available",
      "area_hectares": "extracted from docs"
    },
    "proponent": {
      "name": "extracted if available",
      "contact": "extracted if available"
    }
  },
  "methodology": {
    "id": "soil-carbon-v1.2.2",
    "version": "1.2.2",
    "released": "2021-06-01",
    "requirements_count": 23,
    "is_latest": true
  },
  "detection_confidence": {
    "project_id": 0.96,
    "crediting_period": 0.92,
    "methodology": 0.96
  },
  "detection_sources": {
    "project_id": ["C06-4997_ProjectPlan_v2.pdf", "Baseline_Report_2022-2032.pdf", "..."],
    "crediting_period": ["Baseline_Report_2022-2032.pdf"],
    "methodology": ["ProjectPlan.pdf Section 1.1"]
  }
}
```

#### 2. `session://{session_id}/documents`
**Purpose:** Complete document classifications with metadata

```json
{
  "total_documents": 7,
  "confidence_breakdown": {
    "high": 5,
    "medium": 1,
    "low": 1
  },
  "documents": [
    {
      "filename": "C06-4997_ProjectPlan_v2.pdf",
      "classification": {
        "type": "project_plan",
        "confidence": 0.95,
        "signals": ["filename_pattern", "content_sections", "pdf_metadata"]
      },
      "metadata": {
        "version": "2",
        "pages": 45,
        "date_created": "2022-01-15",
        "project_id_references": ["C06-4997"],
        "methodology_references": ["Soil Carbon v1.2.2"]
      },
      "key_sections": {
        "methodology": "Section 1.1, Pages 2-3",
        "project_boundary": "Section 3.1, Pages 12-15",
        "additionality": "Section 4.3, Pages 22-24"
      }
    },
    {
      "filename": "Registry_Review_2021_Approval.pdf",
      "classification": {
        "type": "prior_registry_review",
        "confidence": 0.94,
        "signals": ["content_signature", "review_markers", "registry_watermark"]
      },
      "metadata": {
        "review_date": "2021-08-15",
        "review_status": "approved",
        "reviewer": "Regen Registry Review Team",
        "methodology_version": "Soil Carbon v1.2.2",
        "crediting_period_reviewed": "2017-2022"
      },
      "intelligence": {
        "is_prior_review": true,
        "can_reference_interpretations": true,
        "requirements_covered": 23
      }
    },
    // ... all 7 documents
  ]
}
```

#### 3. `session://{session_id}/prior-reviews`
**Purpose:** Detailed prior review analysis

```json
{
  "prior_reviews_found": 1,
  "reviews": [
    {
      "filename": "Registry_Review_2021_Approval.pdf",
      "review_date": "2021-08-15",
      "status": "approved",
      "crediting_period": "2017-2022",
      "methodology": "Soil Carbon v1.2.2",
      "requirements_evidence": {
        "REQ-001": {
          "status": "satisfied",
          "evidence_location": "ProjectPlan.pdf, Section 1.1, Page 2",
          "reviewer_notes": "Methodology version clearly stated and current",
          "acceptance_rationale": "Explicit reference to v1.2.2"
        },
        "REQ-002": {
          "status": "satisfied",
          "evidence_location": "ProjectPlan.pdf, Section 2.1, Pages 5-7",
          "reviewer_notes": "Eligibility criteria met",
          "acceptance_rationale": "Site meets all eligibility requirements"
        },
        // ... all 23 requirements
      },
      "issues_flagged": [
        {
          "issue": "Minor formatting inconsistency in baseline data tables",
          "resolution": "Corrected in revised submission",
          "impact": "low"
        },
        {
          "issue": "GIS file CRS not specified",
          "resolution": "CRS added as WGS84",
          "impact": "medium"
        }
      ],
      "approval_conditions": [
        "Annual monitoring reports required",
        "Maintain baseline methodology consistency"
      ]
    }
  ],
  "relevance_to_current_review": {
    "methodology_match": true,
    "project_continuity": true,
    "crediting_period_overlap": false,
    "interpretation_precedents_available": true,
    "usefulness_score": 0.95
  }
}
```

#### 4. `session://{session_id}/evidence-plan`
**Purpose:** Detailed evidence extraction strategy

```json
{
  "total_requirements": 23,
  "extraction_plan": {
    "high_confidence": {
      "count": 18,
      "requirements": ["REQ-001", "REQ-002", "..."],
      "strategy": "Auto-extract with high confidence",
      "estimated_time_minutes": 5,
      "document_mappings": {
        "REQ-001": {
          "primary_document": "ProjectPlan.pdf",
          "section": "1.1",
          "pages": [2],
          "confidence": 0.96,
          "supporting_documents": ["Baseline Report", "Monitoring Plan"],
          "prior_review_evidence": "Same location (Section 1.1, Page 2)"
        },
        // ... all 18 high-confidence requirements
      }
    },
    "medium_confidence": {
      "count": 4,
      "requirements": ["REQ-015", "REQ-018", "REQ-021", "REQ-023"],
      "strategy": "Extract with verification recommended",
      "estimated_time_minutes": 15,
      "document_mappings": {
        "REQ-015": {
          "primary_document": "ProjectPlan.pdf",
          "section": "4.3",
          "pages": [22, 23, 24],
          "confidence": 0.68,
          "uncertainty_reason": "Additionality documentation present but interpretation unclear",
          "prior_review_comparison": "Different approach used in 2021 (standalone additionality document)",
          "recommendation": "Human verification of interpretation"
        },
        // ... 3 more medium-confidence
      }
    },
    "low_confidence": {
      "count": 1,
      "requirements": ["REQ-019"],
      "strategy": "Manual review required",
      "estimated_time_minutes": 10,
      "document_mappings": {
        "REQ-019": {
          "primary_document": null,
          "evidence_found": false,
          "potential_locations": ["BotanyFarm_misc.pdf (unclassified)"],
          "prior_review_evidence": "Standalone social impact assessment document (2021)",
          "recommendation": "Classify misc.pdf and search for social impact content"
        }
      }
    }
  },
  "total_estimated_time_minutes": 30,
  "optimization_recommendations": [
    "Start with high-confidence requirements (18) - auto-extract in ~5 min",
    "Review medium-confidence interpretations (4) - ~15 min human time",
    "Classify BotanyFarm_misc.pdf to locate REQ-019 evidence - ~10 min"
  ]
}
```

#### 5. `session://{session_id}/evidence/detailed`
**Purpose:** Complete evidence with confidence scoring

```json
{
  "requirement_id": "REQ-001",
  "requirement_text": "Projects shall apply the latest version of this methodology at the time of credit issuance.",
  "status": "satisfied",
  "confidence": {
    "level": "high",
    "score": 0.87,
    "factors": {
      "citation_quality": 0.95,
      "text_relevance": 0.92,
      "cross_validation": 0.85,
      "prior_review_alignment": 0.90
    },
    "reasoning": "Strong citation (exact section/page), explicit version reference, cross-validated in 3 documents, aligned with prior review evidence"
  },
  "evidence": {
    "primary_source": {
      "document": "ProjectPlan.pdf",
      "section": "1.1 Methodology",
      "pages": [2],
      "excerpt": "This project applies the Regen Network Soil Carbon v1.2.2 methodology, the latest version available as of the credit issuance date (2022-01-20).",
      "relevance_explanation": "Explicitly states methodology version (v1.2.2) and confirms it's the latest version"
    },
    "supporting_sources": [
      {
        "document": "Baseline_Report_2022-2032.pdf",
        "section": "1. Introduction",
        "pages": [1],
        "excerpt": "Methodology: Soil Carbon v1.2.2",
        "consistency": "confirmed"
      },
      {
        "document": "Monitoring_Plan.pdf",
        "section": "Header",
        "pages": [1],
        "excerpt": "Credit Class: Soil Carbon, Version 1.2.2",
        "consistency": "confirmed"
      }
    ]
  },
  "cross_validation": {
    "status": "strongly_validated",
    "documents_checked": 3,
    "consistent": true,
    "contradictions": []
  },
  "prior_review_reference": {
    "2021_review_evidence": "ProjectPlan.pdf, Section 1.1, Page 2 (same location)",
    "2021_reviewer_notes": "Methodology version clearly stated and current",
    "2021_acceptance_rationale": "Explicit reference to v1.2.2",
    "consistency_with_current": "Same evidence location and format"
  },
  "recommendation": {
    "action": "auto_accept",
    "reasoning": "High confidence (0.87), cross-validated across 3 documents, aligned with prior review precedent",
    "human_review_needed": false
  }
}
```

#### 6. `session://{session_id}/contradictions`
**Purpose:** Cross-document inconsistencies detected

```json
{
  "contradictions_found": 1,
  "contradictions": [
    {
      "requirement_id": "REQ-007",
      "requirement_text": "Baseline sampling must be completed within specified timeframe",
      "contradiction_type": "date_discrepancy",
      "severity": "medium",
      "sources": [
        {
          "document": "Baseline_Report_2022-2032.pdf",
          "location": "Section 2.1, Page 8",
          "statement": "Baseline sampling completed on 2022-03-15"
        },
        {
          "document": "MonitoringPlan_BotanyFarm.pdf",
          "location": "Section 1.2, Page 3",
          "statement": "Baseline sampling date: 2022-03-20"
        }
      ],
      "discrepancy": {
        "type": "date_mismatch",
        "difference": "5 days",
        "impact_assessment": "May affect compliance if sampling window is critical"
      },
      "prior_review_reference": {
        "2021_baseline_date": "2017-03-12",
        "2021_discrepancy_noted": false,
        "notes": "No date discrepancy in prior review"
      },
      "recommendation": {
        "action": "human_review_required",
        "priority": "high",
        "estimated_time_minutes": 5,
        "resolution_steps": [
          "Review original field sampling records",
          "Determine correct date",
          "Update document with incorrect date",
          "Document resolution rationale"
        ]
      }
    }
  ],
  "impact_summary": {
    "high_severity": 0,
    "medium_severity": 1,
    "low_severity": 0,
    "blocking_issues": 0,
    "total_contradictions": 1
  }
}
```

**Characteristics of Level 2 Information**:
- ✅ Comprehensive (all details available)
- ✅ Structured (consistent JSON schemas)
- ✅ Queryable (via MCP resource URIs)
- ✅ On-demand (only loaded when requested)
- ✅ Context-efficient (doesn't bloat Level 1 responses)

**Result**: Deep context available without overwhelming default responses. LLM agents can query specific details when needed.

---

### Information Flow Example

**Scenario:** User initializes review for Botany Farm project

**Step 1: User Action**
```
User: "Initialize review for Botany Farm 2022 project"
Agent: [Calls MCP tool: initialize_session]
```

**Step 2: Level 1 Response (Automatic)**
```
✅ Registry Review Session Initialized

## 📋 Project Context (auto-detected)
  • Project ID: C06-4997 (high confidence)
  • Methodology: Soil Carbon v1.2.2
  • Documents: 7 (5 high-confidence, 2 need review)
  • Prior Review: ✅ 2021 approval found

## 📊 Extraction Readiness
  • High-confidence: 18/23 requirements (78%)
  • Potential gaps: REQ-019

## Next Steps
  Ready to extract evidence. Run /extract-evidence
```

**Step 3: Agent Decides to Query Details (Level 2)**
```
Agent: "User, I found a prior review. Would you like me to summarize it?"
User: "Yes please"
Agent: [Calls MCP resource: session://{id}/prior-reviews]
```

**Step 4: Level 2 Response (On-Demand)**
```json
{
  "prior_reviews_found": 1,
  "reviews": [{
    "review_date": "2021-08-15",
    "status": "approved",
    "requirements_evidence": { ... },
    "issues_flagged": [ ... ]
  }]
}
```

**Step 5: Agent Synthesizes for User**
```
Agent: "The prior review from August 2021 approved this project for the 2017-2022 crediting period.
All 23 requirements were satisfied. Two minor issues were flagged and resolved:
1. Baseline data table formatting (corrected)
2. GIS CRS specification (added as WGS84)

I can reference the prior evidence interpretations during extraction. This should streamline the review process."
```

**Step 6: Extraction with Intelligence**
```
Agent: [Calls extract_evidence tool]
System: [Uses prior review reference + cross-validation + confidence scoring]
Agent: "Evidence extraction complete. 18/23 requirements satisfied with high confidence.
4 medium-confidence items need verification (estimated 15 min).
1 requirement (REQ-019) needs manual review - evidence not found in primary docs."
```

**Result**: Intelligent workflow with progressive disclosure. User gets smart highlights automatically, detailed context on request.

---

## Implementation Roadmap

### Phase 1: Foundation (Intelligence Infrastructure)

**Goal:** Build core intelligence capabilities without changing user-facing behavior

**Tasks:**
1. **Enhanced Document Classification**
   - Add content-based classification (not just filename)
   - Implement confidence scoring
   - Extract document metadata (version, date, pages)

2. **Metadata Extraction**
   - Project ID pattern detection
   - Crediting period extraction
   - Methodology version detection

3. **Prior Review Detection**
   - Identify prior registry review documents
   - Parse prior review structure
   - Extract requirement evidence mappings

**Code Locations:**
- `src/registry_review_mcp/tools/document_tools.py` - Enhanced classification
- `src/registry_review_mcp/extractors/metadata_extractors.py` - New file for metadata extraction
- `src/registry_review_mcp/extractors/prior_review_parser.py` - New file for prior review parsing

**Tests:**
- `tests/test_enhanced_classification.py` - Classification with confidence
- `tests/test_metadata_extraction.py` - Project ID, dates, methodology detection
- `tests/test_prior_review_detection.py` - Prior review identification and parsing

**Deliverable:** Intelligence layer that can detect context, classify documents with confidence, identify prior reviews

**Time Estimate:** 2-3 days

---

### Phase 2: Confidence Scoring (Evidence Intelligence)

**Goal:** Score all evidence extractions with confidence levels

**Tasks:**
1. **Confidence Scoring System**
   - Implement 4-factor scoring (citation quality, text relevance, cross-validation, prior alignment)
   - Define scoring thresholds (high ≥0.8, medium 0.5-0.8, low <0.5)
   - Generate confidence explanations

2. **Cross-Document Validation**
   - Extract same requirement from multiple documents
   - Detect evidence consistency vs contradictions
   - Score validation strength

3. **Evidence Quality Assessment**
   - Citation quality scoring (page/section specificity)
   - Text relevance scoring (direct vs indirect evidence)
   - Prior review alignment scoring

**Code Locations:**
- `src/registry_review_mcp/extractors/confidence_scoring.py` - New file for scoring system
- `src/registry_review_mcp/extractors/cross_validation.py` - New file for cross-document validation
- `src/registry_review_mcp/tools/evidence_tools.py` - Modified to include confidence scores

**Tests:**
- `tests/test_confidence_scoring.py` - Scoring accuracy and explanations
- `tests/test_cross_validation.py` - Contradiction detection, consistency checks
- `tests/test_evidence_quality.py` - Citation and relevance scoring

**Deliverable:** Every evidence extraction includes confidence score with reasoning

**Time Estimate:** 2-3 days

---

### Phase 3: Smart Highlights (Level 1 Intelligence)

**Goal:** Surface essential intelligence automatically in prompt responses

**Tasks:**
1. **Enhanced Initialization Prompt**
   - Auto-detect project ID, methodology, crediting period
   - Surface document classifications with confidence
   - Highlight prior review if found
   - Show extraction readiness summary

2. **Enhanced Discovery Prompt**
   - Show confidence breakdown
   - List uncertain classifications
   - Provide actionable recommendations

3. **Enhanced Evidence Prompt**
   - Show confidence-aware results
   - Highlight contradictions
   - Provide prioritized review recommendations

**Code Locations:**
- `src/registry_review_mcp/prompts/A_initialize.py` - Enhanced with auto-detected context
- `src/registry_review_mcp/prompts/B_document_discovery.py` - Enhanced with confidence breakdown
- `src/registry_review_mcp/prompts/C_evidence_extraction.py` - Enhanced with confidence-aware reporting

**Tests:**
- `tests/test_enhanced_prompts.py` - Verify intelligence surfaces correctly
- `tests/integration/test_workflow_intelligence.py` - End-to-end workflow with intelligence

**Deliverable:** All prompts provide smart highlights automatically

**Time Estimate:** 2 days

---

### Phase 4: Queryable Resources (Level 2 Intelligence)

**Goal:** Make deep context available via MCP resources

**Tasks:**
1. **Add New MCP Resources**
   - `session://{id}/context` - Full project context
   - `session://{id}/documents` - Complete document classifications
   - `session://{id}/prior-reviews` - Prior review analysis
   - `session://{id}/evidence-plan` - Detailed extraction strategy
   - `session://{id}/evidence/detailed` - Evidence with confidence details
   - `session://{id}/contradictions` - Cross-document inconsistencies

2. **Resource Implementation**
   - Generate JSON schemas for each resource
   - Implement resource handlers in MCP server
   - Add resource discovery (list available resources)

**Code Locations:**
- `src/registry_review_mcp/resources/` - New directory for resource generators
- `src/registry_review_mcp/server.py` - Add resource handlers

**Tests:**
- `tests/test_mcp_resources.py` - Resource generation and access
- `tests/integration/test_resource_queries.py` - End-to-end resource queries

**Deliverable:** 6 new MCP resources with comprehensive deep-dive information

**Time Estimate:** 2-3 days

---

### Phase 5: Advanced Intelligence (Optional Enhancements)

**Goal:** Add sophisticated intelligence features

**Tasks:**
1. **Corpus Learning**
   - Analyze document set for common structures
   - Build project-specific vocabulary
   - Identify evidence location patterns

2. **Adaptive Methodology**
   - Auto-detect methodology from documents
   - Load appropriate checklist dynamically
   - Support multiple methodologies

3. **Smart Extraction Strategy**
   - Pre-map documents to requirements
   - Recommend optimal extraction order
   - Identify evidence gaps early

**Code Locations:**
- `src/registry_review_mcp/intelligence/corpus_learning.py` - New file
- `src/registry_review_mcp/intelligence/methodology_detection.py` - New file
- `src/registry_review_mcp/intelligence/extraction_planning.py` - New file

**Tests:**
- `tests/test_corpus_learning.py`
- `tests/test_methodology_detection.py`
- `tests/test_extraction_planning.py`

**Deliverable:** Advanced intelligence features for power users

**Time Estimate:** 3-4 days

---

### Total Implementation Timeline

**Minimum Viable Intelligence (Phases 1-3):** 6-8 days
**Full Intelligence (Phases 1-4):** 8-11 days
**Advanced Intelligence (All Phases):** 11-15 days

---

## Alignment with Architecture Principles

### 1. Standalone Completeness ✅

**Principle:** MCP works independently without external dependencies

**Alignment:**
- All intelligence operates on local documents and session data
- No external API calls required
- Metadata extraction uses local pattern matching and content analysis
- Prior review parsing reads PDF content directly

**No Violation:** Intelligence layer is self-contained

---

### 2. Optional Integration ✅

**Principle:** Can enhance with KOI/Ledger but doesn't require them

**Alignment:**
- Auto-detected project ID can be validated against KOI if available
- Methodology detection works locally but could query Ledger for latest versions
- All features work without external MCPs

**Enhancement Opportunity:** When KOI is available, cross-check detected project ID. When Ledger is available, verify methodology version is latest.

---

### 3. Session-Based State ✅

**Principle:** All state persists in local JSON files

**Alignment:**
- Document classifications with confidence stored in `documents.json`
- Metadata (project ID, methodology) stored in `project_metadata.json`
- Evidence with confidence scores stored in `evidence.json`
- Prior review analysis stored in `prior_reviews.json` (new)

**No Violation:** All intelligence persists to session files

---

### 4. Fail-Explicit ✅

**Principle:** Escalate to human review when uncertain, never guess

**Alignment:**
- Confidence scoring makes uncertainty explicit
- Medium confidence (0.5-0.8) → "verify recommended"
- Low confidence (<0.5) → "human review required"
- Contradictions → "human review required"
- Unknown document types → "manual classification needed"

**Strong Alignment:** Intelligence layer enhances fail-explicit principle by quantifying uncertainty

---

### 5. Evidence Traceability ✅

**Principle:** Every finding cites source document, page, section

**Alignment:**
- Confidence scores include citation quality factor
- Cross-validation checks citations across documents
- Prior review references include original citation locations
- All evidence includes detailed source attribution

**Enhancement:** Confidence scoring reinforces traceability by scoring citation quality

---

### 6. Workflow-Oriented ✅

**Principle:** Prompts guide through sequential stages, not isolated tools

**Alignment:**
- Level 1 (Smart Highlights) enhances workflow prompts with contextual intelligence
- Level 2 (Queryable Resources) supports deep dives without disrupting workflow
- Context-aware next steps guide users through stages
- Extraction readiness analysis helps users decide when to proceed

**Strong Alignment:** Intelligence makes workflow guidance more adaptive and contextual

---

## Security & Safety Considerations

### 1. Fail-Explicit Remains Primary Safety Mechanism

**Commitment:** Intelligence enhances efficiency but never overrides human judgment on uncertain cases

**Implementation:**
- Auto-accept only high-confidence findings (≥0.8)
- Flag medium-confidence for verification (0.5-0.8)
- Escalate low-confidence to human review (<0.5)
- All contradictions require human resolution

**Safety Net:** No evidence is accepted without explicit confidence justification

---

### 2. Transparency in Confidence Scoring

**Commitment:** All scoring factors are visible and auditable

**Implementation:**
- Confidence scores include 4 factor breakdown
- Scoring methodology documented
- Reasoning provided for all scores
- Thresholds explicit and configurable

**Auditability:** Reviewers can validate scoring logic

---

### 3. Cross-Validation Prevents False Positives

**Commitment:** Critical facts verified across multiple documents when possible

**Implementation:**
- High-confidence requirements checked in 2+ documents when available
- Contradictions flagged immediately
- Single-source evidence marked as such
- Cross-validation status visible in Level 2 resources

**Safety Net:** Multi-document confirmation reduces error risk

---

### 4. Prior Review Reference, Not Replacement

**Commitment:** Prior reviews inform but don't determine current decisions

**Implementation:**
- Prior evidence shown as reference, not automatic acceptance
- Differences from prior review flagged (e.g., REQ-015 different approach)
- Prior review alignment is one factor (25%) in confidence score
- Current evidence still required for all requirements

**Safety Net:** No requirement auto-satisfied based solely on prior approval

---

### 5. Metadata Inference with Confidence Thresholds

**Commitment:** Auto-detected metadata clearly marked with confidence levels

**Implementation:**
- Project ID detection requires ≥0.9 confidence or human confirmation
- Methodology detection requires exact version match
- Crediting period extraction requires clear date range match
- All inferred metadata shown with detection sources

**Safety Net:** High bar for auto-accepting critical metadata

---

## Backward Compatibility

### No Breaking Changes

**Guarantee:** All existing functionality continues to work exactly as before

**Implementation:**
- Intelligence layer is additive (adds fields, doesn't remove)
- Existing tool schemas unchanged (confidence is optional field)
- Existing prompts enhanced (Level 1 adds information, doesn't break format)
- Existing tests continue to pass (new tests added for intelligence)

**Migration Path:** Zero-effort upgrade - intelligence activates automatically

---

### Gradual Adoption

**Philosophy:** Users can leverage intelligence incrementally

**Adoption Levels:**
1. **Passive:** Get smart highlights automatically, ignore Level 2 resources
2. **Active:** Query Level 2 resources for deep dives when needed
3. **Power:** Use extraction plan, prior review references, confidence scoring for optimized workflow

**User Choice:** Intelligence doesn't force workflow changes

---

## Success Metrics

### Efficiency Metrics

**Goal:** Reduce human review time while maintaining accuracy

**Measurements:**
- Time to complete review (target: 30-50% reduction)
- Number of human verification steps required (target: <25% of requirements)
- Auto-accepted evidence (target: >75% of requirements at high confidence)

---

### Accuracy Metrics

**Goal:** Intelligence inferences are reliable

**Measurements:**
- Metadata detection accuracy (target: >95% for project ID, methodology)
- Document classification accuracy (target: >90% high confidence)
- Evidence confidence calibration (target: high-confidence findings accepted >95% of time)
- Contradiction detection recall (target: >90% of actual contradictions detected)

---

### User Experience Metrics

**Goal:** Intelligence enhances workflow without overwhelming

**Measurements:**
- User comprehension of smart highlights (qualitative feedback)
- Level 2 resource query frequency (indicates value)
- Workflow completion rate (target: >95% complete reviews)
- Uncertainty escalation appropriateness (target: <5% false escalations)

---

## Conclusion

The Intelligence Enhancement Strategy transforms the Registry Review MCP from a reactive tool into a proactive, context-aware assistant that:

1. **Infers Context** — Automatically detects project ID, methodology, crediting periods
2. **Recognizes Patterns** — Classifies documents with confidence, identifies prior reviews
3. **Communicates Intelligently** — Surfaces smart highlights, makes deep context queryable
4. **Scores Confidence** — Transparent confidence scoring for all findings
5. **Cross-Validates** — Detects contradictions, validates evidence across documents
6. **Guides Workflow** — Context-aware next steps, extraction readiness analysis
7. **Leverages History** — References prior review interpretations and precedents
8. **Fails Explicitly** — Escalates uncertainty appropriately, never guesses

The recommended **"Smart Highlights + Queryable Resources"** architecture balances intelligence with usability:
- **Level 1 (Auto):** Essential intelligence surfaced automatically
- **Level 2 (On-Demand):** Comprehensive deep dives via MCP resources

This approach aligns perfectly with existing architecture principles:
- ✅ Standalone completeness (no external dependencies)
- ✅ Session-based state (all intelligence persists locally)
- ✅ Fail-explicit (uncertainty escalated, never hidden)
- ✅ Evidence traceability (confidence scoring enhances citations)
- ✅ Workflow-oriented (prompts enhanced, not disrupted)

The implementation roadmap provides a clear path:
- **Phase 1-3 (6-8 days):** Minimum viable intelligence
- **Phase 4 (8-11 days):** Full queryable resources
- **Phase 5 (11-15 days):** Advanced intelligence features

The result is a registry review system that doesn't just process documents — it understands them, learns from them, and intelligently guides users through the review process with transparency, confidence, and precision.

---

**Next Steps:**

1. Review and approve this strategy
2. Clarify "marker skill" integration question
3. Prioritize implementation phases
4. Begin Phase 1 (Foundation) implementation

---

**Document Status:** ✅ Complete
**Date:** 2025-11-17
**Author:** Claude (Sonnet 4.5)
**Review Status:** Awaiting User Approval
