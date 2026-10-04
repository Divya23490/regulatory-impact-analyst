### user
Review this draft DORA impact assessment. One round only; the Editor then consolidates.

--- DRAFT ---
# DORA — Impact Assessment

## Executive summary
The Digital Operational Resilience Act (DORA) introduces rigorous, binding requirements across information and communication technology (ICT) risk management, incident reporting, operational resilience testing, third-party risk management, and cyber threat information sharing. An evaluation of our current governance framework reveals significant gaps across core internal policies. Addressing these gaps will require formalizing digital operational resilience strategies, establishing multi-stage regulatory incident reporting workflows, expanding testing programmes beyond external penetration tests, instituting comprehensive ICT third-party registers and contract clauses, and building a governance framework for cyber threat-sharing communities.

## Affected policies
- [policy::POL-001] (ICT Risk Management Framework)
- [policy::POL-011] (Board Training & Competence Policy)
- [policy::POL-003] (Incident Management Standard)
- [policy::POL-004] (Business Continuity & Disaster Recovery)
- [policy::POL-007] (Penetration Testing Standard)
- [policy::POL-005] (Third-Party & Outsourcing Policy)
- [policy::POL-010] (Vendor Contract Clause Library)
- [policy::POL-012] (Threat Intelligence & Information Sharing)

## Gap analysis
- **ICT Risk Management Framework**: POL-001 lacks formalization of the digital operational resilience strategy and annual board review requirements [dora::art6::p8]. POL-011 lacks specialized ICT resilience training modules for the management body [dora::art6::p4].
- **ICT-Related Incident Reporting**: POL-003 lacks regulatory incident workflows, timelines, and multi-stage reporting templates [dora::art17::p3, dora::art19::p1.1, dora::art19::p4]. POL-004 lacks client disclosure procedures and threat notification workflows [dora::art19::p2, dora::art19::p3].
- **Digital Operational Resilience Testing**: POL-007 is restricted to annual external pen tests of internet-facing systems, omitting vulnerability scans, open-source analyses, physical security reviews, and risk-based testing methodologies mandated by DORA Art. 25(1) [dora::art24::p1, dora::art24::p3, dora::art25::p1].
- **ICT Third-Party Risk Management**: POL-005 lacks the required ICT third-party register distinguishing critical functions [dora::art28::p3]. POL-010 lacks mandatory DORA contract clauses regarding audit rights, TLPT cooperation, sub-outsourcing controls, and exit transition periods [dora::art30::p3.1].
- **Cyber Threat Information Sharing**: POL-012 covers commercial feed consumption but lacks a governance framework, rules of conduct, GDPR/confidentiality safeguards, and regulatory notification procedures for participating in trusted threat-sharing communities [dora::art45::p1, dora::art45::p3].

## Recommended actions
1. Update [policy::POL-001] and [policy::POL-011] to incorporate a formal digital operational resilience strategy, annual board review requirements, independent control functions, three lines of defence governance, and specialized ICT resilience training modules for the management body. (Owner: Chief Risk Officer; Priority: H)
2. Revise [policy::POL-003] and [policy::POL-004] to integrate incident management processes with early warning indicators, multi-stage regulatory reporting templates and deadlines, client disclosure procedures, and threat notification workflows. (Owner: Chief Information Security Officer; Priority: H)
3. Update [policy::POL-007] to mandate a comprehensive testing programme covering vulnerability assessments, scans, network security reviews, open-source analyses, physical security reviews, and penetration testing using a risk-based approach. (Owner: Head of Information Security; Priority: M)
4. Amend [policy::POL-005] and [policy::POL-010] to establish an ICT third-party register distinguishing critical functions, annual regulatory reporting, and mandatory vendor contract clauses addressing service levels, notice periods, security measures, TLPT participation, audit rights, and exit strategies. (Owner: Head of Procurement / Vendor Management; Priority: H)
5. Update [policy::POL-012] to institute a formal governance framework, rules of conduct, GDPR and confidentiality safeguards, and regulatory notification procedures for participating in trusted threat-sharing communities. (Owner: Head of Threat Intelligence; Priority: M)

## Open questions
- What specific timeline and template formats will the competent authorities mandate for initial, intermediate, and final major incident reports?
- Which specific external trusted communities will the bank join for cyber threat information sharing, and how will regulatory notification of this participation be operationalized?
- What is the agreed-upon remediation schedule for updating existing legacy vendor contracts that currently lack mandatory DORA clauses in [policy::POL-010]?

--- SOURCE TEXT of the provisions the draft cites ---
[policy::POL-001] POL-001
Owner: CISO. Last reviewed: 2023-02-15.
Defines identification/assessment/treatment of ICT risks; annual board review not yet formalised.

[policy::POL-011] POL-011
Owner: Company Secretary. Last reviewed: 2023-10-01.
Induction and annual training plan; no ICT/operational-resilience module.

[policy::POL-003] POL-003
Owner: Head of IT Operations. Last reviewed: 2023-11-20.
Internal incident severity scale (P1-P4); no regulator notification workflow or deadlines.

[policy::POL-004] POL-004
Owner: COO Office. Last reviewed: 2024-01-10.
RTO/RPO per service; annual DR test; scenario library limited to data-centre loss.

[policy::POL-007] POL-007
Owner: CISO. Last reviewed: 2023-07-18.
Annual external pen test of internet-facing systems; no threat-led (TLPT) programme.

[policy::POL-005] POL-005
Owner: Procurement. Last reviewed: 2022-09-05.
Vendor onboarding due diligence; no register distinguishing critical/important functions.

[policy::POL-010] POL-010
Owner: Legal. Last reviewed: 2023-05-09.
Standard clauses; lacks audit/access rights and sub-outsourcing terms for ICT.

[policy::POL-012] POL-012
Owner: SOC Lead. Last reviewed: 2024-05-14.
Consumes commercial feeds; no framework for sharing within trusted communities.

[dora::art6::p8] DORA Art. 6(8)
8. The ICT risk management framework shall include a digital operational resilience strategy setting out how the framework shall be implemented. To that end, the digital operational resilience strategy shall include methods to address ICT risk and attain specific ICT objectives, by:
(a) explaining how the ICT risk management framework supports the financial entity’s business strategy and objectives;
(b) establishing the risk tolerance level for ICT risk, in accordance with the risk appetite of the financial entity, and analysing the impact tolerance for ICT disruptions;
(c) setting out clear information security objectives, including key performance indicators and key risk metrics;
(d) explaining the ICT reference architecture and any changes needed to reach specific business objectives;
(e) outlining the different mechanisms put in place to detect ICT-related incidents, prevent their impact and provide protection from it;
(f) evidencing the current digital operational resilience situation on the basis of the number of major ICT-related incidents reported and the effectiveness of preventive measures;
(g) implementing digital operational resilience testing, in accordance with Chapter IV of this Regulation;
(h) outlining a communication strategy in the event of ICT-related incidents the disclosure of which is required in accordance with Article 14.

[dora::art6::p4] DORA Art. 6(4)
4. Financial entities, other than microenterprises, shall assign the responsibility for managing and overseeing ICT risk to a control function and ensure an appropriate level of independence of such control function in order to avoid conflicts of interest. Financial entities shall ensure appropriate segregation and independence of ICT risk management functions, control functions, and internal audit functions, according to the three lines of defence model, or an internal risk management and control model.

[dora::art17::p3] DORA Art. 17(3)
3. The ICT-related incident management process referred to in paragraph 1 shall:
(a) put in place early warning indicators;
(b) establish procedures to identify, track, log, categorise and classify ICT-related incidents according to their priority and severity and according to the criticality of the services impacted, in accordance with the criteria set out in Article 18(1);
(c) assign roles and responsibilities that need to be activated for different ICT-related incident types and scenarios;
(d) set out plans for communication to staff, external stakeholders and media in accordance with Article 14 and for notification to clients, for internal escalation procedures, including ICT-related customer complaints, as well as for the provision of information to financial entities that act as counterparts, as appropriate;
(e) ensure that at least major ICT-related incidents are reported to relevant senior management and inform the management body of at least major ICT-related incidents, explaining the impact, response and additional controls to be established as a result of such ICT-related incidents;
(f) establish ICT-related incident response procedures to mitigate impacts and ensure that services become operational and secure in a timely manner.

[dora::art19::p1.1] DORA Art. 19(1)
1. Financial entities shall report major ICT-related incidents to the relevant competent authority as referred to in Article 46 in accordance with paragraph 4 of this Article.
Where a financial entity is subject to supervision by more than one national competent authority referred to in Article 46, Member States shall designate a single competent authority as the relevant competent authority responsible for carrying out the functions and duties provided for in this Article.
Credit institutions classified as significant, in accordance with Article 6(4) of Regulation (EU) No 1024/2013, shall report major ICT-related incidents to the relevant national competent authority designated in accordance with Article 4 of Directive 2013/36/EU, which shall immediately transmit that report to the ECB.
For the purpose of the first subparagraph, financial entities shall produce, after collecting and analysing all relevant information, the initial notification and reports referred to in paragraph 4 of this Article using the templates referred to in Article 20 and submit them to the competent authority. In the event that a technical impossibility prevents the submission of the initial notification using the template, financial entities shall notify the competent authority about it via alternative means.
The initial notification and reports referred to in paragraph 4 shall include all information necessary for the competent authority to determine the significance of the major ICT-related incident and assess possible cross-border impacts.

[dora::art19::p4] DORA Art. 19(4)
4. Financial entities shall, within the time limits to be laid down in accordance with Article 20, first paragraph, point (a), point (ii), submit the following to the relevant competent authority:
(a) an initial notification;
(b) an intermediate report after the initial notification referred to in point (a), as soon as the status of the original incident has changed significantly or the handling of the major ICT-related incident has changed based on new information available, followed, as appropriate, by updated notifications every time a relevant status update is available, as well as upon a specific request of the competent authority;
(c) a final report, when the root cause analysis has been completed, regardless of whether mitigation measures have already been implemented, and when the actual impact figures are available to replace estimates.

[dora::art19::p2] DORA Art. 19(2)
2. Financial entities may, on a voluntary basis, notify significant cyber threats to the relevant competent authority when they deem the threat to be of relevance to the financial system, service users or clients. The relevant competent authority may provide such information to other relevant authorities referred to in paragraph 6.
Credit institutions classified as significant, in accordance with Article 6(4) of Regulation (EU) No 1024/2013, may, on a voluntary basis, notify significant cyber threats to relevant national competent authority, designated in accordance with Article 4 of Directive 2013/36/EU, which shall immediately transmit the notification to the ECB.
Member States may determine that those financial entities that on a voluntary basis notify in accordance with the first subparagraph may also transmit that notification to the CSIRTs designated or established in accordance with Directive (EU) 2022/2555.

[dora::art19::p3] DORA Art. 19(3)
3. Where a major ICT-related incident occurs and has an impact on the financial interests of clients, financial entities shall, without undue delay as soon as they become aware of it, inform their clients about the major ICT-related incident and about the measures that have been taken to mitigate the adverse effects of such incident.
In the case of a significant cyber threat, financial entities shall, where applicable, inform their clients that are potentially affected of any appropriate protection measures which the latter may consider taking.

[dora::art24::p1] DORA Art. 24(1)
1. For the purpose of assessing preparedness for handling ICT-related incidents, of identifying weaknesses, deficiencies and gaps in digital operational resilience, and of promptly implementing corrective measures, financial entities, other than microenterprises, shall, taking into account the criteria set out in Article 4(2), establish, maintain and review a sound and comprehensive digital operational resilience testing programme as an integral part of the ICT risk-management framework referred to in Article 6.

[dora::art24::p3] DORA Art. 24(3)
3. When conducting the digital operational resilience testing programme referred to in paragraph 1 of this Article, financial entities, other than microenterprises, shall follow a risk-based approach taking into account the criteria set out in Article 4(2) duly considering the evolving landscape of ICT risk, any specific risks to which the financial entity concerned is or might be exposed, the criticality of information assets and of services provided, as well as any other factor the financial entity deems appropriate.

[dora::art25::p1] DORA Art. 25(1)
1. The digital operational resilience testing programme referred to in Article 24 shall provide, in accordance with the criteria set out in Article 4(2), for the execution of appropriate tests, such as vulnerability assessments and scans, open source analyses, network security assessments, gap analyses, physical security reviews, questionnaires and scanning software solutions, source code reviews where feasible, scenario-based tests, compatibility testing, performance testing, end-to-end testing and penetration testing.

[dora::art28::p3] DORA Art. 28(3)
3. As part of their ICT risk management framework, financial entities shall maintain and update at entity level, and at sub-consolidated and consolidated levels, a register of information in relation to all contractual arrangements on the use of ICT services provided by ICT third-party service providers.
The contractual arrangements referred to in the first subparagraph shall be appropriately documented, distinguishing between those that cover ICT services supporting critical or important functions and those that do not.
Financial entities shall report at least yearly to the competent authorities on the number of new arrangements on the use of ICT services, the categories of ICT third-party service providers, the type of contractual arrangements and the ICT services and functions which are being provided.
Financial entities shall make available to the competent authority, upon its request, the full register of information or, as requested, specified sections thereof, along with any information deemed necessary to enable the effective supervision of the financial entity.
Financial entities shall inform the competent authority in a timely manner about any planned contractual arrangement on the use of ICT services supporting critical or important functions as well as when a function has become critical or important.

[dora::art30::p3.1] DORA Art. 30(3)
3. The contractual arrangements on the use of ICT services supporting critical or important functions shall include, in addition to the elements referred to in paragraph 2, at least the following:
(a) full service level descriptions, including updates and revisions thereof with precise quantitative and qualitative performance targets within the agreed service levels to allow effective monitoring by the financial entity of ICT services and enable appropriate corrective actions to be taken, without undue delay, when agreed service levels are not met;
(b) notice periods and reporting obligations of the ICT third-party service provider to the financial entity, including notification of any development that might have a material impact on the ICT third-party service provider’s ability to effectively provide the ICT services supporting critical or important functions in line with agreed service levels;
(c) requirements for the ICT third-party service provider to implement and test business contingency plans and to have in place ICT security measures, tools and policies that provide an appropriate level of security for the provision of services by the financial entity in line with its regulatory framework;
(d) the obligation of the ICT third-party service provider to participate and fully cooperate in the financial entity’s TLPT as referred to in Articles 26 and 27;
(e) the right to monitor, on an ongoing basis, the ICT third-party service provider’s performance, which entails the following:
  (i) unrestricted rights of access, inspection and audit by the financial entity, or an appointed third party, and by the competent authority, and the right to take copies of relevant documentation on-site if they are critical to the operations of the ICT third-party service provider, the effective exercise of which is not impeded or limited by other contractual arrangements or implementation policies;

[dora::art45::p1] DORA Art. 45(1)
1. Financial entities may exchange amongst themselves cyber threat information and intelligence, including indicators of compromise, tactics, techniques, and procedures, cyber security alerts and configuration tools, to the extent that such information and intelligence sharing:
(a) aims to enhance the digital operational resilience of financial entities, in particular through raising awareness in relation to cyber threats, limiting or impeding the cyber threats’ ability to spread, supporting defence capabilities, threat detection techniques, mitigation strategies or response and recovery stages;
(b) takes places within trusted communities of financial entities;
(c) is implemented through information-sharing arrangements that protect the potentially sensitive nature of the information shared, and that are governed by rules of conduct in full respect of business confidentiality, protection of personal data in accordance with Regulation (EU) 2016/679 and guidelines on competition policy.

[dora::art45::p3] DORA Art. 45(3)
3. Financial entities shall notify competent authorities of their participation in the information-sharing arrangements referred to in paragraph 1, upon validation of their membership, or, as applicable, of the cessation of their membership, once it takes effect.

### ComplianceOfficer
1. **Omission**: Under ICT Third-Party Risk Management, the draft and recommended action 4 omit the requirement for financial entities to report **at least yearly** to competent authorities regarding new ICT third-party arrangements, categories of providers, types of contracts, and services provided [dora::art28::p3].
2. **Omission**: Under Cyber Threat Information Sharing, recommended action 5 omits the requirement to notify competent authorities upon **cessation of membership** in information-sharing arrangements, in addition to upon validation of membership [dora::art45::p3].
3. **Omission**: Under ICT-Related Incident Reporting, the draft and recommended action 2 omit the obligation for financial entities to transmit threat notifications or voluntary significant cyber threat notifications to **CSIRTs** designated or established under Directive (EU) 2022/2555, where Member States determine such transmission is permitted [dora::art19::p2].

### RiskOfficer
1. **Under-scoping of ICT Risk Independence**: Action 1 correctly links POL-001 and POL-011 to board review and training, but under-sizes the structural requirement of DORA Art. 6(4). It fails to mandate the operational independence of the ICT risk control function from ICT service delivery functions (avoiding conflicts of interest), which is a core governance deficiency for operational risk.
2. **Disproportionate Third-Party Contract Scope**: Action 4 broadly mandates that all vendor contract clauses (service levels, notice periods, security measures, TLPT, audit rights) apply universally to ICT third-party arrangements. DORA Art. 30(3) restricts these rigorous, heavy-lift contractual obligations specifically to arrangements supporting *critical or important functions*, making the blanket application disproportionate for non-critical vendors.
3. **Omission of Sub-Outourcing Governance**: The gap analysis under ICT Third-Party Risk Management and Action 4 omit the specific DORA requirement to control and monitor *sub-outsourcing* of critical or important functions (Art. 30(2)(a)), which represents a major operational and third-party concentration risk exposure if left unaddressed in the policy framework.

### LegalCounsel
1. **Universal Contractual Mandates vs. Critical Function Scope:** Recommended Action 4 incorrectly applies heavy-lift vendor contract clauses (such as audit rights and TLPT cooperation) universally across all ICT third-party arrangements. Under DORA Article 30(3), these specific, rigorous contractual obligations are legally mandated only for arrangements supporting *critical or important functions*; a blanket policy will create unnecessary negotiation gridlock with non-critical vendors.
2. **Omission of Sub-Outourcing Controls in Vendor Policies:** The gap analysis and Recommended Action 4 fail to explicitly mandate contractual controls and prior notification requirements for *sub-outsourcing* of critical or important ICT functions. Leaving out sub-outsourcing governance creates an unmitigated third-party concentration and enforcement gap under DORA vendor compliance.
3. **Incomplete Notification Duties for Threat-Sharing Cessation:** Recommended Action 5 appropriately addresses notification to competent authorities upon validation of membership in threat-sharing communities, but omits the mandatory notification duty upon the *cessation of such membership* as required by DORA Article 45(3).

### DevilsAdvocate
1. **Over-confident Timeline Assumptions:** The draft's recommended actions treat policy updates as administrative document fixes that can be cleanly assigned to high-level owners (CRO, CISO) with standard priorities, ignoring the profound friction and operational gridlock that will occur when attempting to retroactively renegotiate existing legacy vendor contracts to meet DORA Art. 30 standards. 
2. **Missed Risk (Personal Liability):** The assessment completely misses the personal accountability risk DORA introduces for the management body; by focusing merely on updating board training policies (POL-011) rather than establishing personal liability frameworks and documented oversight trails for ICT risk sign-offs, executives remain personally exposed to regulatory enforcement actions.

### Editor
# REDLINES

1. Amend Recommended Action 4 to explicitly restrict heavy-lift vendor contract clauses (such as audit rights and TLPT cooperation) to ICT third-party arrangements supporting critical or important functions, avoiding universal application to non-critical vendors [dora::art30::p3.1].
2. Update the gap analysis and Recommended Action 4 under ICT Third-Party Risk Management to include contractual controls, ongoing monitoring, and prior notification requirements for the sub-outsourcing of critical or important ICT functions [dora::art28::p3, dora::art30::p3.1].
3. Update the gap analysis and Recommended Action 4 to explicitly include the requirement for financial entities to report at least yearly to competent authorities on new ICT third-party arrangements, provider categories, contract types, and provided services [dora::art28::p3].
4. Revise Recommended Action 5 and the corresponding gap analysis to include the mandatory notification duty to competent authorities upon the cessation of membership in information-sharing arrangements, in addition to upon validation [dora::art45::p3].
5. Update Recommended Action 2 and the gap analysis under ICT-Related Incident Reporting to incorporate the option for financial entities to transmit voluntary significant cyber threat notifications to designated CSIRTs under Directive (EU) 2022/2555 where permitted by Member States [dora::art19::p2].
6. Update Recommended Action 1 to mandate the clear structural operational independence of the ICT risk control function from ICT service delivery functions to prevent conflicts of interest, rather than only addressing board reviews and training [dora::art6::p4].
7. Expand Recommended Actions 1 and 4 to address executive accountability, establishing formal documented oversight trails and governance frameworks for management body ICT risk sign-offs to mitigate personal regulatory liability risks.
8. Revise the implementation plan associated with Recommended Action 4 to account for the operational friction and remediation timelines required for legacy vendor contract renegotiations rather than treating them as simple document updates.

REDLINES_COMPLETE