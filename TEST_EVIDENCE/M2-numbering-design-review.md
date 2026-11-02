# F07 imported numbering: independent design review

Verdict: **PASS for the clarified F07 design**.
No F07 implementation was present; this is a scientific/domain design review, not an executed acceptance test.
No requester-approval blocker was identified for implementing a source-defined import subset with the stated limits.

Reviewer: `/root/independent_review`, separate from the implementation agent.
Date: 2026-11-02, Asia/Tokyo.
Baseline: `1a0258754fddce41f517d5c561bfcc557578d9ef` plus ADR-0003 and docs/NUMBERING_CONTRACT.md, including the reviewed follow-up clarifications for anchors, insertion subset, source discrepancy and explicit fixture project classification.
Traceability: P01/P02/P08 → J01/J02/J08 → AC-J01/AC-J02/AC-J08, F07 only.

## Clarifications verified before design PASS

1. The updated contract separates complete CDR3 eligibility from successful import of a partial map. It requires observed anchors 104 and 118 around complete raw-index coverage; truncated/anchor-missing maps remain inspectable but explicitly partial/unavailable for grouping. Missing or unobserved CDR3 must never become an empty-string group.
2. The updated contract explicitly names the supported 111/112 insertion subset and identifies other legitimate IMGT insertions as unsupported, rather than scientifically invalid. It chooses the cited FR/CDR nomenclature source's 118–129 FR4 interval and records the differing 118–128 prose on the V-DOMAIN page.
3. The updated contract adds optional Project.data_class with research/synthetic_fixture states; absent means research without rewriting historical records. Fixture eligibility requires both the explicit project classification and engineering_fixture map status. This clarifies provenance without equating fixture data with measured/verified scientific evidence or changing existing identities.

## Primary-source verification

These public sources were independently opened; no private sequence/experiment data was submitted.

- [IMGT FR/CDR definitions](https://www.imgt.org/IMGTScientificChart/Nomenclature/IMGT-FRCDRdefinition.html) supports FR1 1–26, CDR1 27–38, FR2 39–55, CDR2 56–65, FR3 66–104, rearranged CDR3 105–117, FR4 118–129, and the CDR3 neighboring framework anchors 104/118. It distinguishes rearranged from germline CDR3.
- [IMGT V-DOMAIN/V-LIKE-DOMAIN numbering](https://www.imgt.org/IMGTScientificChart/Numbering/IMGTIGVLsuperfamily.html) directly supplies insertion tables. In sequence order, 111 extensions increase, 112 extensions decrease before ordinary 112. The process of adding positions alternates 112.1, 111.1, 112.2, 111.2; that creation order must not be confused with sequence order. Its FR4 overview prose says 118–128, which differs from the nomenclature page.
- [IMGT additional positions](https://www.imgt.org/IMGTScientificChart/Numbering/IMGTnumberingAC.html) gives legitimate examples beyond the proposed subset, including 60.1 and 84A. Restricting F07 support is acceptable if unsupported input is identified honestly and retained outside successful import, never reinterpreted.
- [Lefranc et al. 2003, primary-paper record](https://pubmed.ncbi.nlm.nih.gov/12477501/) confirms the work's scope and bibliographic identity. The abstract alone is insufficient to validate the exact coordinate ordering or boundary details; those were checked against the linked IMGT tables.

## Design assessment

The map identity includes the named Molecule, chain, domain, scheme/definition and map ID. Repeated numeric positions across chains/domains remain distinct. Raw sequence indexes, IMGT coordinates and future structure-author coordinates remain separate. Coordinates must use integer position plus canonical insertion string, never floating-point values; `.10` cannot collapse into `.1`.

A mapped record must exactly cover its declared raw interval in sequence order and match each named-chain amino acid. Numeric gaps describe unoccupied numbering positions and must not be replaced with invented residues. Reject duplicate raw indexes/coordinates, boolean/non-integer indexes, noncanonical insertion codes, mismatched amino acids and incorrect project/type references atomically.

The source verification status is a supplied attestation. Reviewer/reference/time establish recorded provenance, not automatic proof of biological correctness. W must call it an attestation and expose its source. `engineering_fixture` stays visibly synthetic and never becomes a human-validated scientific golden record through a passing engineering test. Eligibility must inspect the map's explicit verification status; a fixture-like project title alone cannot elevate unverified data into a numbering action.

Multiple eligible maps or heavy-chain domains require an explicit stable map/domain selection. No latest, first or sequence-equal substitution is acceptable. Keep that selection and the resulting coordinate identity across E/W/D/R and restart. Group the complete CDR3 amino-acid sequence in raw residue order with explicit provenance; do not sort string coordinates or infer regions from a raw substring heuristic.

No molecular identity, provenance category, persona, primary journey, external sharing behavior or scientific definition is changed by the intended import. The supported subset implements the existing plan. Changing the definition without primary support, silently extending to germline/constant domains, or treating attestation as application-validated science would require a new review and possibly requester escalation.

## Independently proposed edge cases

1. **Long insertion coordinates:** import sequence order `111`, `111.1` through `111.10`, then `112.10` down to `112.1`, `112`. Preserve `.1` and `.10` as different identities through export/reimport; reject lexical/numeric-float reordering, duplicate coordinates and `.01`.
2. **Boundary and truncation:** verify region labels at 26/27, 38/39, 55/56, 65/66, 104/105 and 117/118, plus the documented FR4 upper bound. A map containing only 105–110 imports as declared partial coverage but cannot form a complete CDR3 group; missing and true empty results are not interchangeable.
3. **Ambiguous scFv/multidomain molecule:** one chain has two declared heavy domains or two eligible map versions. Grouping remains blocked until explicit map/domain selection and does not change silently after adding another version. Same coordinate numbers on a light chain stay separate.
4. **Verification-state boundary:** mapped/unverified, failed, unavailable and engineering_fixture records all remain visibly distinct. A project renamed to a fixture-like title does not make an unverified map eligible. A fixture result never counts toward human-validated golden evidence.
5. **Actual unsupported IMGT coordinates:** 60.1 and 84A reject with an unsupported-subset message, not a false claim that IMGT forbids them. Ordinary positions and 111/112 extensions still work.
6. **Equal sequence, wrong identity:** a map for another identical-sequence molecule/chain/project must not be reassigned or merged. Same domain label and coordinate on separate immutable map IDs remain traceable.

## Passage boundary

The clarified design authorizes F07 implementation and independent replay; integration requires a separate implementation PASS. Full M2 passage still requires its structure/mapping observation work; full J01 requires its 800-candidate assay-aware selection path, J02 requires numbered child variants/reasons, and J08 requires the remaining adapters/structure correspondence and final roundtrip. The human-validated scientific golden fixtures and final release gates remain pending.
