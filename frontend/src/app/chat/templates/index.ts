import { ArtifactTemplate } from "../types";

export const EXECUTIVE_SUMMARY_MD = `# Executive Summary Report Specification

## Document Overview
The Executive Summary Report delivers a high-impact, C-level briefing synthesizing complex information, operational performance, and strategic decisions into a structured, executive-grade document.

---

## Writing Guidelines

### 1. Tone & Voice
- **Register**: Authoritative, analytical, objective, and executive-ready.
- **Perspective**: Third-person formal; avoid informal qualifiers, conversational fluff, and speculative commentary.
- **Diction**: Action-oriented, active voice, precise terminology with zero corporate jargon clichés.

### 2. Construction & Narrative Framework
- **Framework**: Inverted Pyramid. Lead with the core strategic conclusion, primary outcome, and decisive impact before detailing supporting evidence.
- **Paragraph Sizing**: Strictly 2 to 4 sentences per paragraph. Prioritize visual scanning with bulleted vectors and bold lead-in phrases.
- **Progression**:
  1. Executive Context & Core Finding
  2. Critical Quantitative Metrics & Discovered Trends
  3. Strategic Risk & Exposure Evaluation
  4. Decisive Action Plan with Resource Allocations

### 3. Data Heaviness & Empirical Density
- **Quantitative Standard**: High data density. Every major strategic claim must be accompanied by explicit numerical metrics (e.g., percentages, dollar amounts, delta variances, volume changes).
- **Tabular Requirements**: Include at least one structured comparative Markdown table contrasting targets against actuals, or benchmarking key operational vectors.
- **Confidence Rating**: State explicit confidence thresholds and underlying data sample sizes where applicable.

### 4. Length & Word Count Constraints
- **Target Length**: 800 – 1,200 words.
- **Executive Rule**: If an insight does not alter a strategic or budgetary decision, omit it.

---

## Required Section Blueprint

### 1. Executive Overview
- Direct summary of the core objective, underlying premise, and overarching strategic takeaway.
- Key operational delta statement (e.g., revenue change, performance variance, critical milestone achievement).

### 2. Key Findings & Quantitative Metrics
- Bulleted breakdown of verified factual discoveries.
- Structured Markdown comparison table:
  | Strategic Metric | Baseline / Target | Actual Performance | Variance / Delta | Health Status |
  | :--- | :--- | :--- | :--- | :--- |
- Narrative evaluation of primary drivers behind the variance.

### 3. Strategic Risk & Exposure Matrix
- Categorization of identified operational, financial, technical, or regulatory risks.
- Impact vs. Likelihood assessment with proactive mitigation controls.

### 4. Action Plan & Next Steps
- Time-bound, numbered recommendations in priority order.
- Explicit ownership assignments and milestone completion timelines.
`;

export const RESEARCH_SYNTHESIS_MD = `# Research & Deep-Dive Synthesis Specification

## Document Overview
The Research & Deep-Dive Synthesis transforms disparate technical, empirical, or market data sources into an exhaustive, rigorously cited analytical treatise.

---

## Writing Guidelines

### 1. Tone & Voice
- **Register**: Academic, analytical, thoroughly cited, and defensible.
- **Perspective**: Objective third-person investigator; transparently present opposing evidence, counter-arguments, and boundary conditions.
- **Diction**: Factual, evidence-based, scientifically precise, avoiding hyperbolic superlatives.

### 2. Construction & Narrative Framework
- **Framework**: Adapted IMRAD (Abstract, Problem & Scope, Detailed Methodological Findings, Comparative Matrix, Strategic Conclusion).
- **Paragraph Sizing**: 3 to 5 sentences. Use structured sub-headings, clear demarcation of claims, and inline empirical citations [1], [2].
- **Progression**:
  1. Abstract & Problem Demarcation
  2. Scope & Research Methodology
  3. Thematic Findings & Evidence Clusters
  4. Comparative Synthesis & Benchmark Matrix
  5. Open Limitations & Concluding Implications

### 3. Data Heaviness & Empirical Density
- **Quantitative Standard**: Very high data density. Include exact figures, historical baselines, sample sizes, and empirical citations.
- **Tabular Requirements**: Include a detailed comparative matrix contrasting multiple approaches, vendors, paradigms, or market players across consistent criteria.
- **Citations**: Ground all non-obvious assertions in verified citations or extracted document passages.

### 4. Length & Word Count Constraints
- **Target Length**: 1,200 – 2,000 words.
- **Depth Requirement**: Prioritize exhaustive structural coverage over brevity.

---

## Required Section Blueprint

### 1. Abstract & Problem Context
- Comprehensive synthesis of the research challenge, current state of the art, and core hypothesis.
- Summary of verified conclusions.

### 2. Methodology & Evidence Scope
- Scope of ingested datasets, query parameters, literature bounds, and evaluation criteria.
- Known constraints and evidentiary limitations.

### 3. Detailed Findings & Analysis
- Sub-divided into thematic subsections exploring core facets of the subject.
- In-depth causal analysis explaining why empirical observations occurred.

### 4. Comparative Synthesis Matrix
- Multi-dimensional Markdown comparison table:
  | Dimension / Criteria | Subject / Baseline | Alternative A | Alternative B | Net Impact |
  | :--- | :--- | :--- | :--- | :--- |

### 5. Strategic Implications & Research Conclusion
- Synthesized deduction of long-term ramifications, industry shifts, or architectural impacts.
- Defensible roadmap for ongoing exploration or immediate operational deployment.
`;

export const TECHNICAL_SPECIFICATION_MD = `# Technical Specification & Architecture Audit Specification

## Document Overview
The Technical Specification & Architecture Audit provides software engineers, system architects, and technical leaders with an authoritative blueprint detailing system topology, API contracts, security postures, and execution milestones.

---

## Writing Guidelines

### 1. Tone & Voice
- **Register**: Rigorous, technical, unambiguous, and engineering-grade.
- **Perspective**: System architect and engineering auditor. Avoid hand-wavy generalizations; state exact protocols, schemas, algorithms, and complexity classes.
- **Diction**: Clean technical terminology, RFC-compliant imperative conventions (MUST, SHOULD, MAY).

### 2. Construction & Narrative Framework
- **Framework**: Architectural Systems Decomposition (System Boundaries -> Component Interfaces -> Data Flows -> Security & Compliance -> Phased Rollout).
- **Code & Schemas**: Enclose all data models in syntax-highlighted code fences (typescript, python, json, sql).
- **Progression**:
  1. System Goals, Non-Goals & Latency SLAs
  2. Component Architecture & State Flow
  3. Data Schemas & API Contract Specifications
  4. Security, Authentication & Fault Tolerance
  5. Implementation Phasing & Acceptance Criteria

### 3. Data Heaviness & Empirical Density
- **Technical Standard**: Concrete schemas, throughput benchmarks (requests/sec), p95/p99 latency targets, failover time-to-recovery (MTTR), and token usage budgets.
- **Tabular Requirements**: Include at least one API endpoint or schema contract table.

### 4. Length & Word Count Constraints
- **Target Length**: 1,000 – 1,800 words.
- **Completeness**: Provide fully formed JSON schemas or TypeScript interfaces rather than partial snippets with ellipses.

---

## Required Section Blueprint

### 1. System Overview & Objectives
- Problem statement, primary architectural objectives, explicit Non-Goals, and target SLA thresholds.

### 2. Architectural Breakdown & Topology
- Microservices, event queues, background workers, and persistent stores.
- ASCII or Mermaid system flow diagram illustrating component interactions.

### 3. Data Schemas & API Contracts
- Typed payload interfaces (TypeScript/Pydantic) and endpoint definitions:
  | Method | Endpoint | Auth Level | Request Body Type | Response Schema | Expected p95 |
  | :--- | :--- | :--- | :--- | :--- | :--- |

### 4. Security, Resilience & Failure Modes
- Access control, encryption at rest/transit, rate limiting, and circuit breaker configurations.
- Recovery procedures under database partition, API timeout, or worker exhaustion.

### 5. Implementation Phasing & Milestones
- Ordered engineering phases with completion deliverables and exit gates.
`;

export const FINANCIAL_ANALYSIS_MD = `# Financial & Quantitative Data Analysis Specification

## Document Overview
The Financial & Quantitative Data Analysis delivers rigorous fiscal reporting, investment metrics, valuation comparisons, unit economics, and probabilistic sensitivity forecasts.

---

## Writing Guidelines

### 1. Tone & Voice
- **Register**: Financially rigorous, disciplined, analytical, and mathematically sound.
- **Perspective**: Senior Financial Analyst / Quantitative Strategist. Explicitly note GAAP vs. non-GAAP calculations, assumptions, and currency denominators.
- **Diction**: Fiscally exact, utilizing standard market metrics (ARR, EBITDA, CAGR, ROAS, Free Cash Flow, Debt-to-Equity).

### 2. Construction & Narrative Framework
- **Framework**: Quantitative Financial Breakdown (Headline Performance -> Unit Economics -> Comparative Multiples -> Scenario Forecast -> Capital Recommendations).
- **Format**: Pair every analytical paragraph with supporting tabular numbers.
- **Progression**:
  1. Top-Line & Bottom-Line Financial Highlights
  2. Operating Margins, Cost Structure & Unit Economics
  3. Structured Multi-Period Comparison Table
  4. Sensitivity Analysis (Bull, Base, Bear Scenarios)
  5. Capital Allocation & Strategic Recommendations

### 3. Data Heaviness & Empirical Density
- **Quantitative Standard**: Extremely high data density. Include currency amounts (in millions/billions), margin percentages, basis points (bps), and YoY/QoQ variance indicators.
- **Tabular Requirements**: Include at least one multi-period or comparative competitor table.

### 4. Length & Word Count Constraints
- **Target Length**: 900 – 1,500 words.
- **Precision**: Round currencies cleanly (e.g., $12.4M, $84.20/share) and state percentage movements to one decimal place (+14.2%).

---

## Required Section Blueprint

### 1. Financial & Operational Highlights
- Summary of top-line revenue, gross profit, net margin, and operating cash flows.
- Commentary on overall fiscal health and macro headwinds/tailwinds.

### 2. Quantitative KPI Breakdown & Margins
- Detailed breakdown of customer acquisition cost (CAC), LTV:CAC ratios, churn rates, and operating expenses.
- Breakdown of fixed vs. variable cost structures.

### 3. Tabular Financial Performance Comparison
- Multi-period or cross-asset Markdown table:
  | Metric / Ticker | Prior Period (Q3) | Current Period (Q4) | Target / Guidance | YoY Delta (%) | Trend Indicator |
  | :--- | :--- | :--- | :--- | :--- | :--- |

### 4. Scenario Projections & Sensitivity Model
- Forward-looking performance projections across 3 distinct macroeconomic environments:
  - Bull Case: Revenue growth, margin expansion, key catalysts.
  - Base Case: Expected trajectory under normalized conditions.
  - Bear Case: Downside protections, burn rate limits, stress tests.

### 5. Strategic Capital Allocation & Recommendations
- Specific actionable advice regarding capital reinvestment, dividends/buybacks, debt reduction, or operational efficiency initiatives.
`;

export const COMPLIANCE_REVIEW_MD = `# Compliance & Policy Review Specification

## Document Overview
The Compliance & Policy Review provides a structured evaluation of organizational controls, regulatory frameworks, policy adherence, security baselines, and legal/contractual requirements.

---

## Writing Guidelines

### 1. Tone & Voice
- **Register**: Audit-grade, objective, authoritative, and defensible.
- **Perspective**: Independent compliance auditor / regulatory analyst. Avoid subjective assertions; reference specific regulation articles, statutory standards, or policy clauses.
- **Diction**: Strict regulatory terminology (e.g., SOC 2 Type II, ISO 27001, GDPR, HIPAA, FedRAMP, zero trust, access controls).

### 2. Construction & Narrative Framework
- **Framework**: Audit & Gap Assessment (Regulatory Baseline -> Control Verification -> Identified Non-Conformances -> Risk Exposure Severity -> Remediation Plan).
- **Format**: Utilize structured pass/fail control matrices and prioritized gap assessments.
- **Progression**:
  1. Audit Scope & Governing Regulatory Frameworks
  2. Control Verification & Evidence Examination
  3. Non-Compliance Findings & Gap Severity Matrix
  4. Governance, Accountability & Remediation Roadmap

### 3. Data Heaviness & Empirical Density
- **Compliance Standard**: Specific control identifiers (e.g., AC-2, CC6.1), sampling frequencies, audit trail log counts, and violation risk ratings (Critical, High, Medium, Low).
- **Tabular Requirements**: Include a comprehensive Audit Adherence Checklist table.

### 4. Length & Word Count Constraints
- **Target Length**: 800 – 1,400 words.
- **Evidence Requirement**: Ground each finding in specific log entries, system policies, or documented operational practices.

---

## Required Section Blueprint

### 1. Scope & Regulatory Baseline
- Demarcation of covered entities, cloud accounts, software versions, and regulatory standards evaluated.
- Audit period and designated compliance officer details.

### 2. Audit Checklist & Adherence Matrix
- Comprehensive evaluation table:
  | Control ID | Control Description | Policy Requirement | Verification Status | Severity Rating |
  | :--- | :--- | :--- | :--- | :--- |

### 3. Identified Gaps & Deficiencies
- Narrative breakdown of all non-conforming controls, potential exploit surfaces, and legal exposures.
- Detailed root cause analysis for each critical deficiency.

### 4. Remediation & Governance Roadmap
- Prioritized remediation steps with assigned compliance owners and SLA resolution dates.
- Ongoing monitoring and recurring internal audit schedule.
`;

export const MEETING_MINUTES_MD = `# Actionable Meeting & Transcript Minutes Specification

## Document Overview
The Actionable Meeting & Transcript Minutes document transforms verbose call recordings, stakeholder syncs, and transcripts into an executive synthesis centered around decisions adopted and actionable commitments.

---

## Writing Guidelines

### 1. Tone & Voice
- **Register**: Direct, succinct, objective, and action-oriented.
- **Perspective**: Impartial executive recorder. Eliminate conversational banter, filler speech, false starts, and tangential debates.
- **Diction**: Unambiguous, commitment-focused (e.g., "Decided", "Approved", "Committed", "Assigned").

### 2. Construction & Narrative Framework
- **Framework**: Decision-to-Action Pipeline (Context & Attendees -> Strategic Discussion Highlights -> Binding Decisions -> Ownership & Accountability Matrix).
- **Paragraph Sizing**: 1 to 3 sentences. Emphasize bullet points and explicit name tags for consensus tracking.
- **Progression**:
  1. Meeting Context, Objectives & Roster
  2. Core Discussion Threads & Debated Perspectives
  3. Formal Decisions Adopted
  4. Action Items & Deliverables Table

### 3. Data Heaviness & Empirical Density
- **Accountability Standard**: Every action item MUST have:
  - Exact Task Description
  - Directly Responsible Individual (DRI)
  - Concrete Completion Deadline
  - Verification Criterion / Success Deliverable
- **Tabular Requirements**: Include a structured Action Items Matrix.

### 4. Length & Word Count Constraints
- **Target Length**: 500 – 1,000 words.
- **Brevity Rule**: Ensure attendees can digest all outcomes and their individual action items within 60 seconds of reading.

---

## Required Section Blueprint

### 1. Agenda & Meeting Context
- Meeting objective, date/time, presiding leader, and roster of active participants.
- Agenda items covered vs. deferred to subsequent sessions.

### 2. Executive Discussion Points
- Concise synopsis of main agenda topics debated.
- Key perspectives voiced, objections raised, and consensus reached.

### 3. Key Decisions Adopted
- Bulleted list of formal agreements, architectural sign-offs, budgetary approvals, or scope modifications agreed upon by the team.

### 4. Action Items & Ownership Matrix
- Structured execution table:
  | # | Action Item Deliverable | Directly Responsible Individual (DRI) | Target Deadline | Verification Output |
  | :--- | :--- | :--- | :--- | :--- |
`;

export const BUILTIN_ARTIFACT_TEMPLATES: ArtifactTemplate[] = [
  {
    id: "executive-summary",
    title: "Executive Summary Report",
    badge: "EXECUTIVE",
    description: "High-level overview, key findings, strategic takeaways, and recommended action matrix",
    sections: ["Executive Overview", "Key Findings & Data Points", "Strategic Risk Matrix", "Recommended Action Plan"],
    defaultFormat: "pdf",
    tone: "Authoritative, analytical, objective, and C-level executive ready",
    construction: "Inverted Pyramid (lead with core conclusion & impact, follow with empirical proof)",
    dataHeaviness: "High density (explicit metrics, delta variances, comparative KPI table)",
    targetLength: "800 – 1,200 words (concise, 2-4 sentences per paragraph)",
    markdownInstructions: EXECUTIVE_SUMMARY_MD,
  },
  {
    id: "research-report",
    title: "Research & Deep-Dive Synthesis",
    badge: "RESEARCH",
    description: "In-depth analysis, methodology, comparative findings, citations, and comprehensive conclusion",
    sections: ["Abstract & Problem Context", "Methodology & Scope", "Detailed Findings & Analysis", "Comparative Evidence", "Strategic Conclusion"],
    defaultFormat: "pdf",
    tone: "Academic, objective, evidence-driven, thoroughly cited",
    construction: "Adapted IMRAD (Abstract, Methodology, Findings, Comparative Matrix, Strategic Conclusion)",
    dataHeaviness: "Very high (benchmarks, statistical significance, comparative criteria matrix)",
    targetLength: "1,200 – 2,000 words (deep analytical coverage)",
    markdownInstructions: RESEARCH_SYNTHESIS_MD,
  },
  {
    id: "tech-spec",
    title: "Technical Specification & Architecture Audit",
    badge: "TECHNICAL",
    description: "System architecture breakdown, data schemas, security posture, and engineering roadmap",
    sections: ["System Overview & Objectives", "Architectural Breakdown", "Security & Compliance Analysis", "Implementation Phasing & Milestones"],
    defaultFormat: "pdf",
    tone: "Rigorous, technical, unambiguous, and engineering-grade",
    construction: "Architectural Systems Decomposition (Boundaries -> Interfaces -> Schemas -> Security -> Phasing)",
    dataHeaviness: "High technical density (typed schemas, API contract tables, latency SLAs)",
    targetLength: "1,000 – 1,800 words (complete payload specs)",
    markdownInstructions: TECHNICAL_SPECIFICATION_MD,
  },
  {
    id: "financial-data",
    title: "Financial & Quantitative Data Analysis",
    badge: "FINANCIAL",
    description: "Quantitative metrics, KPI performance, tabular comparisons, and forward projections",
    sections: ["Financial & Operational Highlights", "Quantitative KPI Breakdown", "Tabular Performance Comparison", "Forward Projections & Forecast"],
    defaultFormat: "pdf",
    tone: "Financially rigorous, disciplined, analytical, and mathematically sound",
    construction: "Quantitative Breakdown (Highlights -> Margins -> Multi-Period Table -> Scenarios -> Capital Advice)",
    dataHeaviness: "Extremely high (currency metrics, margin percentages, bps, multi-period table)",
    targetLength: "900 – 1,500 words (fiscally exact)",
    markdownInstructions: FINANCIAL_ANALYSIS_MD,
  },
  {
    id: "compliance-review",
    title: "Compliance & Policy Review",
    badge: "AUDIT",
    description: "Regulatory evaluation, policy gap analysis, audit checklist, and remediation timeline",
    sections: ["Scope & Regulatory Baseline", "Audit Checklist & Adherence", "Identified Gaps & Discrepancies", "Remediation & Governance Roadmap"],
    defaultFormat: "pdf",
    tone: "Audit-grade, objective, authoritative, and defensible",
    construction: "Audit & Gap Assessment (Baseline -> Control Verification -> Deficiencies -> Remediation Roadmap)",
    dataHeaviness: "High compliance density (control IDs, sampling frequencies, pass/fail matrix)",
    targetLength: "800 – 1,400 words (evidence-grounded)",
    markdownInstructions: COMPLIANCE_REVIEW_MD,
  },
  {
    id: "meeting-minutes",
    title: "Actionable Meeting & Transcript Minutes",
    badge: "MINUTES",
    description: "Executive discussion points, key decisions adopted, and action item matrix with owners/deadlines",
    sections: ["Agenda & Meeting Context", "Executive Discussion Points", "Key Decisions Adopted", "Action Items Matrix (Owner & Deadline)"],
    defaultFormat: "pdf",
    tone: "Direct, succinct, objective, and action-oriented",
    construction: "Decision-to-Action Pipeline (Context -> Discussions -> Binding Decisions -> Ownership Matrix)",
    dataHeaviness: "High accountability density (every action item has DRI, deadline, and deliverable)",
    targetLength: "500 – 1,000 words (digestible in 60 seconds)",
    markdownInstructions: MEETING_MINUTES_MD,
  },
];
