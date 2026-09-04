### user
Review this draft DORA impact assessment. One round only; the Editor then consolidates.

--- DRAFT ---
# DORA — Impact Assessment

## Executive summary
This Regulatory Impact Assessment evaluates the bank's internal policy register against the six core themes of the Digital Operational Resilience Act (DORA). The assessment identified significant policy gaps across all operational resilience domains. Most critically, the bank lacks formalized annual board review workflows (POL-001), harmonized incident reporting criteria and regulator SLAs (POL-003), threat-led penetration testing (POL-007), comprehensive third-party information registers and mandatory contract clauses (POL-005, POL-010), CTPP oversight integration, and trusted-community information sharing frameworks with GDPR safeguards (POL-012). Immediate remediation is required to achieve full compliance and avoid regulatory sanctions.

## Affected policies
* **POL-001**: Governance and Board Oversight Policy (missing annual board review workflows)
* **POL-003**: Incident Management and Reporting Policy (missing harmonized incident reporting criteria and regulator SLAs)
* **POL-005**: Third-Party Risk Management Policy (missing comprehensive register of information)
* **POL-007**: Penetration Testing and Vulnerability Management Policy (missing threat-led penetration testing)
* **POL-010**: Outsourcing and Vendor Contracting Policy (missing mandatory contract clauses and CTPP oversight integration)
* **POL-012**: Threat Intelligence and Information Sharing Policy (missing trusted-community information sharing frameworks and GDPR safeguards)

## Gap analysis
The bank's current internal policy register fails to meet the stringent requirements mandated by DORA across the following areas:
* **Governance and Oversight:** POL-001 does not mandate the formal annual review and approval workflows for digital operational resilience strategies required of the management body.
* **ICT Incident Management:** POL-003 lacks the necessary harmonized classification criteria for major ICT-related incidents and fails to align with strict regulatory Service Level Agreements (SLAs) for initial, intermediate, and final notifications.
* **Digital Operational Resilience Testing:** POL-007 does not incorporate Threat-Led Penetration Testing (TLPT) protocols as mandated for significant financial entities under DORA.
* **Third-Party Risk Management (ICT Third-Party Risk):** POL-005 and POL-010 fail to establish a comprehensive register of information covering all contractual arrangements with ICT third-party service providers. Furthermore, vendor contracts omit mandatory DORA clauses (e.g., access and audit rights, exit strategies) and lack integration for Critical ICT Third-Party Providers (CTPPs).
* **Information Sharing:** POL-012 lacks provisions for participating in trusted-community threat intelligence arrangements while simultaneously enforcing strict GDPR and data protection safeguards.

## Recommended actions
1. Update POL-001 to explicitly mandate and operationalize annual board review workflows for the bank's digital operational resilience strategy. (**Owner:** Chief Risk Officer | **Priority:** H)
2. Revise POL-003 to incorporate harmonized incident reporting criteria and strict regulatory SLAs for major ICT incidents. (**Owner:** Head of Information Security | **Priority:** H)
3. Amend POL-005 and POL-010 to establish a comprehensive ICT third-party register of information and enforce mandatory DORA contract clauses across all vendor agreements. (**Owner:** Head of Procurement / Third-Party Risk | **Priority:** H)
4. Update POL-007 to include frameworks and schedules for Threat-Led Penetration Testing (TLPT). (**Owner:** Head of Information Security | **Priority:** M)
5. Integrate CTPP oversight mechanisms into POL-010 to monitor systemic third-party dependencies. (**Owner:** Head of Third-Party Risk | **Priority:** M)
6. Revise POL-012 to establish trusted-community information sharing frameworks embedded with robust GDPR safeguards. (**Owner:** Chief Information Security Officer / Data Protection Officer | **Priority:** L)

## Open questions
* What is the definitive timeline and regulatory expectation for completing the first mandatory Threat-Led Penetration Testing (TLPT) cycle under DORA?
* Which specific supervisory authority will be designated as the primary lead overseer for the bank's identified Critical ICT Third-Party Providers (CTPPs)?
* What standardized templates or taxonomies do European Supervisory Authorities (ESAs) require for the third-party register of information?

### ComplianceOfficer
As Group Compliance Officer, I have reviewed the draft impact assessment against DORA (Regulation (EU) 2022/2554). 

Raise the following 3 points:

1. **Missing Articles of the Regulation:** The assessment completely omits specific citations to DORA Articles (e.g., Articles 5-16 for Governance, Articles 17-23 for Incident Management, Articles 24-27 for Testing, Articles 28-44 for Third-Party Risk, and Article 45 for Information Sharing). These must be mapped explicitly to each policy gap.
2. **Missing Obligations (ICT Risk Management Framework):** The draft fails to address the foundational ICT Risk Management requirements under Chapter II (Articles 5–15), specifically concerning asset identification, protection, prevention, detection, and business continuity/disaster recovery plans.
3. **Wrong/Missing Deadlines:** The assessment lacks any target remediation dates or compliance timelines tied to DORA’s statutory enforcement date (January 17, 2025), leaving the urgency of the recommended actions undefined.

### RiskOfficer
As Chief Risk Officer, focusing strictly on the sizing of operational, ICT, and third-party risk and the proportionality of the proposed actions, I raise the following 3 points:

1. **Misallocated Accountability for Board Oversight:** Action 1 assigns ownership of POL-001 (Governance and Board Oversight Policy) to the Chief Risk Officer (CRO). Under DORA, ultimate responsibility and accountability for approving and overseeing the digital operational resilience strategy rests squarely with the management body (the Board), not the second-line risk function. The CRO can advise, but cannot "own" the governance workflow of the board itself. 
2. **Disproportionate Prioritization of TLPT:** Action 4 rates Threat-Led Penetration Testing (POL-007) as Medium priority. Given that TLPT is a major, resource-intensive operational requirement under DORA—mandating specialized external testers, threat intelligence providers, and strict regulatory coordination for significant financial entities—classifying it as Medium risks severe under-scoping and delays in execution.
3. **Underestimated Complexity of ICT Third-Party Registers:** Action 3 bundles the creation of a comprehensive ICT third-party register of information and the renegotiation of all vendor contracts into a single high-priority action. From a risk sizing perspective, retrofitting thousands of legacy vendor contracts with mandatory DORA clauses and establishing the prescribed Register of Information (including intra-group arrangements and sub-outsourcing chains) represent a massive operational and third-party risk burden that requires phased, dedicated sub-workstreams rather than a blanket policy update.

### LegalCounsel
As Legal Counsel, focusing exclusively on contractual and enforceability issues, I raise the following 3 points:

1. **Enforceability of Mandatory DORA Clauses (POL-010):** The assessment correctly identifies the absence of mandatory DORA contract clauses in POL-010, but fails to address the legal mechanism for remediation. Simply updating the internal policy is legally inert regarding existing vendor contracts; the bank must establish a formalized contract remediation playbook (e.g., bilateral amendments, incorporation via renewal, or unilateral change-of-law provisions) to legally bind third-party and sub-outsourced service providers to DORA's access, audit, and exit strategy requirements.
2. **Notification Duties and Contractual SLAs (POL-003):** The reliance on internal policy updates for regulatory SLAs and incident reporting overlooks the contractual friction this creates. Vendor contracts must be proactively aligned to reflect these shortened notification duties; otherwise, third parties failing to report ICT incidents upstream within the statutory timeframes will expose the bank to regulatory penalties without an effective contractual indemnity or breach remedy.
3. **Outsourcing and CTPP Oversight Integration:** While POL-010 notes missing CTPP oversight, the assessment must legally distinguish between standard ICT third-party providers and designated Critical ICT Third-Party Providers (CTPPs) under Article 31 of DORA. Standard outsourcing clauses are insufficient for CTPPs; contracts must legally accommodate the oversight, inspection, and penalty powers directly exercisable by the designated Union Oversight Forum and Lead Overseer without breaching confidentiality or creating conflicting legal obligations.

### DevilsAdvocate
1. **Over-confident assumption on policy remediation:** The draft assumes that updating internal policies (POL-001 through POL-012) equates to regulatory compliance, entirely ignoring the operational reality that rewriting a document does not fix fractured workflows, untracked legacy vendor contracts, or untested incident response mechanisms. 
2. **Missing Risk:** The draft completely overlooks the severe liability exposure of board members under DORA's personal accountability mandates, failing to assess whether directors' and officers' (D&O) insurance covers the newly formalized operational resilience duties being forced onto the management body.

### Editor
### REDLINES

1. **Executive summary:** Amend the executive summary to explicitly incorporate specific DORA article citations (Articles 5-45) and foundational Chapter II ICT Risk Management asset identification and business continuity requirements.
2. **Executive summary:** Update the executive summary and document-wide timelines to establish firm target remediation dates tied to DORA’s statutory enforcement date of January 17, 2025.
3. **Affected policies:** Update POL-001 in the affected policies and recommended actions to reassign ownership of board oversight workflows from the Chief Risk Officer to the management body (the Board).
4. **Gap analysis:** Expand the gap analysis and recommended actions to include foundational ICT Risk Management requirements under Chapter II (Articles 5–15) regarding asset identification, protection, prevention, detection, and business continuity/disaster recovery plans.
5. **Recommended actions:** Elevate Action 4 regarding Threat-Led Penetration Testing (POL-007) from Medium to High priority to reflect its resource-intensive regulatory nature.
6. **Recommended actions:** Split Action 3 into phased, dedicated sub-workstreams to separate the massive operational burden of retrofitting legacy vendor contracts from the creation of the ICT third-party register of information.
7. **Recommended actions:** Update Action 3 and POL-010 to mandate a formal contract remediation playbook (such as bilateral amendments or change-of-law provisions) to legally enforce mandatory DORA clauses on existing third-party providers.
8. **Recommended actions:** Revise Action 3 and POL-003 to ensure vendor contracts are aligned with regulatory SLAs and include contractual remedies for upstream incident reporting failures.
9. **Recommended actions:** Expand POL-010 in Action 5 to legally distinguish between standard ICT providers and designated Critical ICT Third-Party Providers (CTPPs) under Article 31, accommodating direct oversight powers of the Lead Overseer.
10. **Open questions:** Add open questions regarding D&O insurance coverage for board members facing personal accountability mandates under DORA, alongside questions on regulatory deadlines for the first TLPT cycle, CTPP lead overseers, and ESA-mandated third-party register taxonomies.

REDLINES_COMPLETE