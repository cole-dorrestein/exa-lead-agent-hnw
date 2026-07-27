---
name: imperial-portfolio-design
description: Design spec for Imperial Business School MSc Strategic Marketing work placement reflective portfolio — Legacy Hotels, 3,000-word self-evaluation covering all five themes
metadata:
  type: project
---

# Imperial Business School — Work Placement Portfolio Design

_Date: 2026-07-27_
_Organisation: Legacy Hotels_
_Submission deadline: 16:00 Friday 28 August 2026_

---

## Deliverable

A **3,000-word individual reflective portfolio** (Pass/Fail). Submitted as a single consolidated PDF via the Hub. Font: Arial 11pt, 1.5 line spacing. Appendices are not counted toward word limit.

---

## Structure

### A. Title Page

- Organisation name: "Legacy Hotels"
- No student name, no CID (anonymity requirement)

---

### B. Self-Evaluation Report (~2,700 words)

Structural approach: **thematic with Kolb backbone**. One section per theme. Each section implicitly follows Kolb's cycle of learning (Experience → Reflective Observation → Abstract Conceptualisation → Active Experimentation / what I'd do differently). Examiner can trace the reflection; reads as prose not a template.

Recommended word allocation per section below.

---

#### Introduction (~120 words)

- 4-week placement at Legacy Hotels, working directly under Gijs (Head of Sales)
- Built an AI-powered lead generation pipeline to identify high-net-worth (HNW) executive prospects in Sub-Saharan Africa for luxury apartment sales in Johannesburg and Cape Town
- Signals five-theme structure; references Kolb as the reflective framework

---

#### Theme 1 — Problem-Solving (~600 words)

**Experience:**
Gijs needed a scalable way to identify C-suite, VP, and Director-level individuals at large Sub-Saharan African corporations and international firms with African offices — as prospects for luxury apartment sales. Manual LinkedIn research was slow, unscalable, and produced no contact data.

**Reflective Observation:**
Analysed the gap between available tools (generic lead-gen tools not calibrated for SSA markets) and what was needed (ICP-scored, structured output with LinkedIn URLs and contact routes). Framed as an information asymmetry problem: Legacy Hotels had product excellence but weak prospect intelligence. Referenced Market Research module methodology: problem definition → data requirements → source evaluation → output validation.

**Abstract Conceptualisation:**
Decomposed the problem into five sub-problems: (1) org discovery, (2) executive identification, (3) contact enrichment, (4) deduplication/scoring, (5) delivery format. Each mapped to a distinct technical component. This decomposition mirrors systematic market research design — defining research objectives before selecting methods.

**Active Experimentation / Critical Insight:**
Built pipeline iteratively (v1 → v4). Key decisions: Grok 4.20 reasoning model for org and people discovery (handles unstructured web + X/Twitter sources); Exa deep search API for structured LinkedIn/people verification; Pydantic typed models for output integrity; ICP role-tier scoring (Tier 1 C-suite → Tier 3 Director). Constraints documented in RULES.md; ICP spec in ICPs.md for transparency and replicability.

Critical insight: initial version found names and titles but lacked contact data — making leads unusable for outreach. This was a pivotal problem reframe: the real output requirement was not "a list of names" but "actionable contact records." Added contact enrichment module as a second pipeline pass. Lesson: defining success criteria precisely before building prevents costly mid-project pivots.

---

#### Theme 2 — Managing Relationships (~500 words)

**Experience:**
Primary relationship: Gijs as client-manager hybrid — domain expert in luxury sales, non-technical. He articulated the need in sales language ("find rich people in Africa who could buy apartments") not engineering language. No formal specification existed at the outset.

**Reflective Observation:**
First deliverable produced names and company affiliations but few usable contact routes. Gijs's feedback revealed the misalignment — he needed a minimum of a LinkedIn URL per lead to initiate any outreach. This showed I had been optimising for quantity over the contact-data quality he actually required.

**Abstract Conceptualisation:**
Applied expectation management principles from Applied Strategic Marketing: converted Gijs's qualitative brief into a precise ICP document (ICPs.md) with minimum data requirements, seniority tiers, geography constraints, and company revenue qualifier. Turned a subjective aspiration into a testable, documented specification. This mirrors B2B briefing best practice — aligning supplier capability to client value definition before execution.

**Active Experimentation / Critical Insight:**
Scheduled informal demo check-ins after each pipeline version to show outputs and adjust the ICP based on Gijs's responses. ICPs.md became a living document revised collaboratively. Also managed the AI "collaborator" relationship — strict constraints in RULES.md prevented the model from fabricating contact data, which required clear, unambiguous instruction design.

Critical insight: the most valuable skill in this placement was not technical — it was translating a sales professional's intuition into a structured, machine-readable brief. That translation layer is where most AI tool-building projects succeed or fail.

---

#### Theme 3 — Managing Time, Tasks & Ethics (~500 words)

**Experience:**
4-week placement with a working deliverable as the exit condition. Competing priorities: building the core pipeline vs. adding supporting features (CRM, batch processing, URL review UI, documentation).

**Reflective Observation:**
Planned iteratively: core discovery pipeline (weeks 1–2) → contact enrichment (weeks 2–3) → batch pipeline + CRM interface (weeks 3–4) → documentation. This sequencing mirrored agile product development — ship a usable v1, then extend. Made explicit trade-offs: excluded auth-gated LinkedIn scraping (violates Terms of Service and GDPR), excluded purchasing third-party contact databases (budget constraint, data freshness concerns, POPIA compliance risk in South Africa).

**Abstract Conceptualisation:**
Ethical dimension was central to task management, not incidental. RULES.md encoded the key constraint: "never fabricate emails or phone numbers." Data privacy of HNW individuals raises genuine legal and ethical questions under GDPR (EU) and POPIA (South Africa's Protection of Personal Information Act). Choosing only publicly available, voluntarily disclosed data sources was the ethically defensible position — and the legally safe one.

**Active Experimentation / Critical Insight:**
Prioritised quality over volume: built deduplication and ICP scoring rather than raw lead count maximisation. Delivered clean, typed CSV output (proper quoting/escaping via csv.writer) rather than unprocessed dumps, so Gijs could use results directly without cleaning.

Critical insight: the ethical constraint (public sources only) turned out to be a design feature rather than a limitation. It forced better engineering — an Exa verification layer, confidence scoring per candidate — and produced more reliable leads than scraped or purchased lists typically yield. Ethical design and engineering quality aligned, not conflicted.

---

#### Theme 4 — Applying Programme Concepts (~500 words)

**Applied Strategic Marketing — STP and ABM:**
ICP definition is STP in practice. Segmented the SSA executive market by industry (banking, telecoms, mining, FMCG, tech, energy, insurance) and company size (revenue ≥ $20M). Targeted Tiers 1–3 only (C-suite through Director level). Positioning informed the qualification criteria: Legacy Hotels apartments are aspirational luxury — the prospect must have both wealth and executive status to be a credible buyer. Also applied Account-Based Marketing (ABM) principles: the pipeline targets named individuals at specific named organisations rather than generating demographic buckets. This is higher-effort, higher-conversion than mass-market digital advertising — appropriate for a low-volume, high-value product.

**Market Research — ICP as Research Design:**
Developing the ICP document (ICPs.md) followed market research methodology from the Market Research module: define the research question (who is a viable prospect?), specify inclusion/exclusion criteria, select data sources, define output schema, validate against real examples. The ICP is not a marketing assumption but a research instrument — it was iterated based on evidence from early pipeline runs.

**Digital Marketing — RACE and Email Analytics:**
The pipeline addresses the Reach stage of the RACE framework (Reach → Act → Convert → Engage). Conscious decision to scope the tool to top-of-funnel lead identification and execute it well, rather than attempting full outreach automation. Email marketing effectiveness depends on list quality — ICP scoring and contact-confidence ranking directly improve open and conversion rates by ensuring relevance before any message is sent. Customer Lifetime Value (CLV) of a luxury apartment sale justified the investment in a multi-stage enrichment pipeline: a single converted lead generates revenue many multiples greater than the tooling development cost.

**Machine Learning Applications in Marketing — LLM Limitations:**
Used Grok 4.20 reasoning model (xAI) for org resolution and executive discovery — an application of large language model technology to a structured extraction task, as covered in the Machine Learning Applications in Marketing module. Applied critical awareness of model limitations: LLMs can hallucinate contact data (fabricate plausible-sounding emails and phone numbers). RULES.md addressed this directly — the model was explicitly instructed never to emit contact routes unless present verbatim in a cited source. This is a practical instantiation of the module's lesson on AI output validation: treat model outputs as hypotheses requiring verification, not ground truth.

---

#### Theme 5 — Creating and Delivering Value (~480 words)

**Value for Legacy Hotels:**
Delivered a functional, documented, independently-runnable pipeline. Gijs can execute `python -m pipeline run <company-url>` on any target corporation and receive up to 50 ICP-scored executive candidates with LinkedIn URLs, role tiers, confidence scores, and contact routes (email, phone). A batch mode (`corp_batch_pipeline.py`) supports parallel processing of multiple corporations simultaneously. A CRM interface (FastAPI + HTMX + Supabase) allows Gijs to filter leads by role tier, contact quality, and geography, and export directly to outreach workflows.

This replaced what would have been hours of manual LinkedIn research per company — unscalable for a small sales team targeting a large and geographically distributed prospect market.

**Value created for self:**
Gained practical experience in Python async and concurrent programming, Pydantic data modelling, AI API integration (xAI Grok, Exa semantic search), agentic pipeline architecture, and FastAPI web application development and deployment. First exposure to delivering a production AI tool in a real commercial context under a real deadline. Synthesised concepts across all four MSc modules — Market Research, Applied Strategic Marketing, Digital Marketing, Machine Learning Applications in Marketing — in a single deployed system.

**Critical reflection — where value was actually created:**
Value was not only in the code but in the documentation: RULES.md, ICPs.md, and README made the system interpretable and operable by a non-technical user. A powerful tool that only the builder can run creates dependency; documentation transforms it into organisational capability. This is consistent with the Applied Strategic Marketing module's emphasis on internal communication and stakeholder alignment as strategic assets.

**What I would do differently:**
Build the CRM interface earlier — from week one — so all pipeline outputs feed a live, navigable UI rather than raw CSV files. This would have improved Gijs's ability to give feedback on lead quality earlier, compressing the iteration cycle. Also: invest in cost telemetry (API call counts and estimated USD cost per pipeline run) from day one. The `pipeline_metrics.py` module arrived late; presenting a cost-per-lead figure to Gijs from week one would have contextualised the value of the tool in financial terms he could use to justify it internally.

---

#### Conclusion (~100 words)

- Placement delivered a working AI lead generation tool for a genuine commercial need at Legacy Hotels
- Across the five themes, a consistent pattern emerges: precise problem framing → structured iterative execution → ethical constraint as design principle → measurable, documented output
- Biggest transferable learning: technical capability alone does not create business value. The translation layer — ICP documentation, expectation management, clean output format, tool documentation — is where value is actually delivered, and where the MSc programme's emphasis on communication and strategic clarity proved most directly applicable

---

## Appendices (not in word count)

| Appendix | Content | Status |
|---|---|---|
| A | Sample pipeline output / lead list screenshot (redact names/emails as needed) | Available |
| B | ICPs.md — ICP specification document | Available |
| C | RULES.md — pipeline constraints and ethical guidelines | Available |
| D | README extract — technical architecture and usage documentation | Available |
| E | Supervisor endorsement declaration (Gijs signs off evidence as true) | **Pending — request from Gijs** |
| F | Daily timesheet (optional) | Optional |

---

## Spec Self-Review

- [x] No TBD or placeholder sections
- [x] 5 themes covered with evidence mapped to each
- [x] All 4 module names incorporated with specific concept references
- [x] Word allocations sum to ~2,700 + 120 intro + ~100 conclusion = ~2,920 (within 3,000 limit)
- [x] Kolb cycle traceable in each theme section
- [x] Ethical dimension covered in Theme 3 (GDPR + POPIA), Theme 1 (no fabrication), Theme 4 (LLM validation)
- [x] Evidence appendices mapped; one item pending (Gijs endorsement)
- [x] No internal contradictions between themes
- [x] Scope appropriate for single 3,000-word report
