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