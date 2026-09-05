### user
Review this draft DORA impact assessment. One round only; the Editor then consolidates.

--- DRAFT ---
# DORA — Impact Assessment

## Executive summary
The Digital Operational Resilience Act (DORA) imposes rigorous obligations on the bank regarding ICT risk management, incident reporting, digital operational resilience testing, third-party risk management, and information sharing. Based on the consolidated research findings (`findings.md`), the bank's current regulatory posture contains significant compliance gaps across twelve core policies (POL-001 through POL-012). Addressing these gaps requires immediate, coordinated intervention across Information Security, Risk Management, Third-Party Vendor Management, and Operations to avoid regulatory sanction and ensure operational continuity.

## Affected policies
*   **POL-001** (ICT Risk Management Framework)
*   **POL-002** (Major ICT Incident Management & Reporting)
*   **POL-003** (Digital Operational Resilience Testing)
*   **POL-004** (ICT Third-Party Risk Management / Outsourcing)
*   **POL-005** (Information & Intelligence Sharing on Cyber Threats)
*   **POL-006** (Business Continuity & Disaster Recovery)
*   **POL-007** (Asset & Configuration Management)
*   **POL-008** (Access Control & Identity Management)
*   **POL-009** (Data Protection & Cryptography)
*   **POL-010** (Physical & Environmental Security)
*   **POL-011** (Project & Change Management)
*   **POL-012** (Training & Awareness)

## Gap analysis
*   **ICT Risk Management & Governance (POL-001, POL-007, POL-008, POL-009, POL-010, POL-011):** The bank lacks an integrated ICT risk framework that explicitly covers all DORA mandates. Asset inventories (POL-007) do not comprehensively map critical ICT assets supporting vital functions. Access controls (POL-008) and cryptographic standards (POL-009) fail to meet DORA's heightened encryption-at-rest and strict least-privilege baseline requirements. Physical security (POL-010) and change management (POL-011) procedures lack formal alignment with ICT resilience standards.
*   **Incident Management (POL-002, POL-006):** Current major incident workflows do not support DORA's strict preliminary, intermediate, and final reporting timelines to competent authorities. Business continuity plans (POL-006) lack mandatory ICT-focused disaster recovery testing scenarios and fail to account for severe systemic disruptions.
*   **Resilience Testing (POL-003):** The bank's testing regime relies on standard vulnerability scans and penetration tests, falling short of DORA requirements for advanced Threat-Led Penetration Testing (TLPT) for critical functions.
*   **Third-Party Risk Management (POL-004):** Existing vendor management policies do not incorporate mandatory DORA contractual clauses regarding audit rights, termination assistance, performance monitoring, and concentration risk analysis for ICT third-party service providers (ICT TPPs).
*   **Information Sharing (POL-005):** The bank has no formal policy or framework governing participation in cyber threat intelligence information-sharing arrangements with trusted financial sector peers.
*   **Training & Awareness (POL-012):** Current staff training programs do not include DORA-specific operational resilience and digital hygiene modules tailored to role-based risks.

## Recommended actions
1. **[Owner: Chief Information Security Officer]** Overhaul POL-001, POL-007, POL-008, POL-009, POL-010, and POL-011 to establish a unified ICT risk management framework, complete asset inventory, and elevated technical security controls matching DORA baselines. *(Priority: High)*
2. **[Owner: Head of Operational Risk]** Update POL-002 and POL-006 to institute accelerated major ICT incident classification, escalation, and regulatory reporting workflows, alongside enhanced ICT disaster recovery testing. *(Priority: High)*
3. **[Owner: Head of Vendor Management]** Revise POL-004 to introduce rigorous ICT third-party risk management lifecycles, mandating standardized DORA contractual provisions and concentration risk tracking. *(Priority: High)*
4. **[Owner: Head of Information Security]** Establish a Threat-Led Penetration Testing (TLPT) program under POL-003 targeting critical ICT systems. *(Priority: Medium)*
5. **[Owner: Head of Threat Intelligence]** Draft and implement POL-005 to formalize protocols for participating in cyber threat intelligence sharing arrangements. *(Priority: Medium)*
6. **[Owner: Head of Human Resources / Learning & Development]** Update POL-012 to mandate annual DORA-specific digital resilience and cyber hygiene training across all staff levels. *(Priority: Medium)*

## Open questions
*   Which specific external entities have been designated by national competent authorities as critical ICT third-party service providers (ICT TPPs) for our institution?
*   What is the exact jurisdictional timeline and template format required by our primary regulator for intermediate and final major ICT incident reports under DORA?
*   Are existing threat-intelligence sharing arrangements legally compliant with data privacy frameworks (e.g., GDPR) while participating in DORA-aligned information-sharing pacts?

### ComplianceOfficer
1. **Missing Regulation Articles:** The draft completely omits specific DORA article references (e.g., Articles 5-16 for ICT Risk Management, Articles 17-23 for Incident Reporting, Articles 24-27 for Testing, and Articles 28-44 for Third-Party Risk). 
2. **Missing Obligation (Register of Information):** The impact assessment fails to mandate the creation and maintenance of the comprehensive Register of Information required under Article 28(3) for all contractual arrangements on the use of ICT services.
3. **Wrong/Missing Deadlines:** The draft omits the statutory application date of DORA (January 17, 2025) and regulatory enforcement timelines, leaving all remediation actions tied only to vague priorities rather than hard legal deadlines.

### RiskOfficer
As Chief Risk Officer, focusing strictly on operational, ICT, and third-party risk sizing and the proportionality of actions, I raise the following 3 points:

1. **Under-scoping of Third-Party Risk Concentration:** The draft correctly identifies gaps in ICT Third-Party Risk Management (POL-004), but the recommended actions fail to size the systemic risk of *chain* outsourcing and geographical concentration. The remediation must explicitly mandate a mapping of downstream sub-outsourcers of critical ICT TPPs to prevent unmitigated single points of failure.
2. **Disproportionate TLPT Prioritizing:** Assigning Threat-Led Penetration Testing (POL-003) a "Medium" priority under Action 4 is misaligned with operational risk reality. If the bank supports critical or important functions under DORA, TLPT is a mandatory regulatory requirement subject to strict oversight. Sizing this as medium risks regulatory sanction; it must be elevated to "High" priority alongside governance and third-party overhauls.
3. **Lack of Phased Operational Sizing for Incident Reporting:** Action 2 tasks the Head of Operational Risk with updating incident workflows (POL-002, POL-006) to meet strict preliminary, intermediate, and final reporting timelines, but fails to size the operational and resourcing burden on the 24/7 Security Operations Center (SOC) and Incident Response teams. The action is disproportionate unless it includes provisions for immediate headcount, tooling, and run-book automation to handle compressed regulatory windows without inducing secondary operational errors.

### LegalCounsel
As Legal Counsel, focusing exclusively on contractual and enforceability issues, I raise the following 3 points:

1. **Enforceability of Contractual Outsourcing Remediation (POL-004):** Action 3 mandates the revision of POL-004 to introduce standardized DORA contractual provisions. However, the assessment fails to address the enforceability risk of retrofitting existing, legacy ICT contracts. The policy must explicitly prescribe a bilateral contract amendment strategy and define fallback legal mechanisms if critical ICT third-party providers (ICT TPPs) refuse to accept mandatory DORA terms (e.g., unhindered audit rights and termination assistance under Article 30).
2. **Regulatory Notification Duties and Contractual Indemnification:** Action 2 addresses major ICT incident reporting workflows (POL-002), but omits the necessary alignment with vendor contract terms. To ensure the bank can meet strict regulatory notification timelines without breaching liability caps, vendor contracts must be updated to legally bind ICT TPPs to immediate self-reporting obligations and to indemnify the bank for regulatory fines arising from third-party operational failures.
3. **Sub-outsourcing Chain Visibility:** The framework lacks a contractual mandate to restrict or pre-approve downstream sub-outsourcing of critical or important functions. Without binding contractual clauses requiring ICT TPPs to notify the bank of any intended sub-outsourcing—and granting the bank a contractual right to object—the bank's regulatory compliance posture under DORA Article 30 remains legally exposed and unenforceable against the actual service delivery chain.

### DevilsAdvocate
1. **Over-confident Timeline Assumption:** The draft treats all twelve policies as if they can be overhauled concurrently under a generic "immediate, coordinated intervention," dangerously assuming that Risk, Security, Vendor Management, and HR have the bandwidth to rewrite their core governance documents simultaneously without causing operational paralysis or producing superficial, check-the-box policies that will fail regulatory scrutiny.
2. **Unaddressed Risk (Cross-Border Data Sovereignty):** The draft completely misses the compliance trap between DORA's mandatory information-sharing/incident-reporting rules and existing data sovereignty laws (like GDPR and national banking secrecy laws), risking heavy privacy penalties if threat intelligence or incident details containing client data are shared across borders.

### Editor
### REDLINES
1. **Executive summary:** Update the Executive summary to explicitly incorporate statutory DORA article references (Articles 5–44) and the January 17, 2025 enforcement deadline.
2. **Gap analysis:** Update the Gap analysis under POL-004 to mandate the creation of the comprehensive Register of Information required under Article 28(3).
3. **Gap analysis:** Update the Gap analysis to include explicit compliance safeguards addressing the legal tension between DORA information-sharing mandates and cross-border data privacy frameworks (e.g., GDPR and banking secrecy laws).
4. **Recommended actions:** Revise Action 1, Action 2, and Action 3 to incorporate a phased rollout schedule that prevents operational paralysis across the responsible departments.
5. **Recommended actions:** Update Action 2 to size the operational and resourcing burden on the 24/7 Security Operations Center (SOC) and Incident Response teams, including provisions for automated run-books and headcount adjustments.
6. **Recommended actions:** Update Action 2 to explicitly require that vendor contracts legally bind ICT TPPs to immediate incident self-reporting and indemnify the bank against regulatory fines.
7. **Recommended actions:** Elevate Action 4 (Threat-Led Penetration Testing under POL-003) from Medium to High priority to reflect mandatory regulatory oversight.
8. **Recommended actions:** Revise Action 3 to mandate a contractual sub-outsourcing mapping strategy that covers downstream sub-outsourcers, concentration risk, notification of changes, and bank veto rights.
9. **Recommended actions:** Update Action 3 to include a bilateral contract amendment strategy and defined legal fallbacks for legacy ICT contracts where providers resist mandatory DORA terms.
10. **Recommended actions:** Update Action 6 to reflect realistic deployment bandwidth rather than assuming concurrent overhauls of all twelve policies.

REDLINES_COMPLETE