# Compliance & Policy Review Specification

## Document Overview
The Compliance & Policy Review provides a structured evaluation of organizational controls, regulatory frameworks, policy adherence, security baselines, and legal/contractual requirements.

---

## Writing Guidelines

### 1. Tone & Voice
- **Register**: Audit-grade, objective, authoritative, and defensible.
- **Perspective**: Independent compliance auditor / regulatory analyst. Avoid subjective assertions; reference specific regulation articles, statutory standards, or policy clauses.
- **Diction**: Strict regulatory terminology (e.g., SOC 2 Type II, ISO 27001, GDPR, HIPAA, FedRAMP, zero trust, access controls).

### 2. Construction & Narrative Framework
- **Framework**: Audit & Gap Assessment (Regulatory Baseline $\to$ Control Verification $\to$ Identified Non-Conformances $\to$ Risk Exposure Severity $\to$ Remediation Plan).
- **Format**: Utilize structured pass/fail control matrices and prioritized gap assessments.
- **Progression**:
  1. Audit Scope & Governing Regulatory Frameworks
  2. Control Verification & Evidence Examination
  3. Non-Compliance Findings & Gap Severity Matrix
  4. Governance, Accountability & Remediation Roadmap

### 3. Data Heaviness & Empirical Density
- **Compliance Standard**: Specific control identifiers (e.g., `AC-2`, `CC6.1`), sampling frequencies, audit trail log counts, and violation risk ratings (`Critical`, `High`, `Medium`, `Low`).
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
- Prioritized remediation steps with assigned compliance owners and SLA resolution dates (e.g., Critical: 7 days, High: 30 days, Medium: 90 days).
- Ongoing monitoring and recurring internal audit schedule.
