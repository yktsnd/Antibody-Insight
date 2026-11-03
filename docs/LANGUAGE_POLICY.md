# Language and terminology

Code, identifiers, API errors and core UI labels use English by default.
Human-facing explanations have English and Japanese versions. The application guide has an explicit language selector; README.md and README.ja.md link to each other.
New explanatory content must update both versions. Explain any unsupported operation or scientific limitation consistently in both languages.

Language selection changes explanations only. It must not translate or normalize stored metric names, units, source text, conditions, sequences, identifiers or researcher notes.
Do not use machine translation to assign a scientific meaning. Preserve the English term with a short explanation when a Japanese equivalent would be ambiguous.

| English | Japanese explanation | Usage boundary |
|---|---|---|
| humanization | ヒト化 | An engineering action; do not use as the label of a humanness score. |
| humanness | ヒト抗体らしさ（humanness） | Give the actual method-specific definition and source. Do not imply a universal measure or proven function. No humanness calculation is implemented yet. |
| measured value | 実測値 | Retain the experimental material, construct, conditions and source. |
| computed result | 計算結果 | Retain the method and source; use 予測結果 only when the source actually describes a prediction. |
| missing value | 欠測値 | Distinguish a registered null value, no registered measurement and a true numeric zero. |
| construct | コンストラクト | Keep separate from molecule and experimental material. |
| experimental material | 実験試料 | Preserve its lot and construct identity. |
| provenance | 来歴 | Include source, version, time and direct subject. |
| structural correspondence | 構造と配列の対応付け | Preserve model, chain, residue identifier, insertion code and conformer. |
| shortlist draft | ショートリストの下書き | Do not present as a finalized scientific decision. |

The reviewer checks both meaning and operation: switching explanations must preserve selection and recorded data. New scientific definitions still require primary sources under AGENTS.md; this glossary is an editorial policy, not a substitute for those sources.
