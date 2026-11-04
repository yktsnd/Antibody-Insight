# Initial J08 harness diagnosis

These preliminary test failures were investigated before the passing root J08 replay; they are not omitted product defects.

1. The first main journey attempted Decision finalization without entering the required explicit criterion weight/preference. The application rejected the request and did not save a Decision. The test was corrected to perform those real user inputs, without changing product behavior or weakening validation.
2. The next duplicate-ID negative constructed its bundle through JavaScript JSON parse/stringify, which normalized exact stored source numeric types/signs before reaching the intended ID collision. Source-consistency validation correctly rejected that altered input. The test now mutates the exported file using Python while preserving numeric representations, uploads it through the actual file control, then attempts Save and verifies the actual atomic ID collision and unchanged project.

The current M5-J08-initial-root-results.json records all three prescribed groups PASS, including actual restart/full export/fresh-store exact typed comparison. M5-J08-failure.png is a retained diagnostic from preliminary harness work, not a current acceptance artifact. The independent browser reviewer separately preserves its own fixture/option-state harness diagnoses and final results. Final frozen integration remains a separate gate.

The later escaped-Unicode rejection-response bug was independently reproduced as an actual product defect, not classified as a harness issue. Its original failure and independently verified correction are documented in M5-predictions-surrogate-independent-finding.md and M5-predictions-surrogate-fixed-independent-review.md.
