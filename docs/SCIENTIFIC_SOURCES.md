# 参照標準と採用範囲

公開一次資料を2026-11-02に参照した。
配列や実験値を外部検索へ送っていない。

- IMGT番号付け：https://www.imgt.org/IMGTindex/numbering.php
  - IMGT番号は配列の単純な通し番号とは別に扱う。現段階でIMGT付番アルゴリズムを実装せず、未登録をmapping unavailableと表示する。
- W3C PROV：https://www.w3.org/TR/prov-overview/
  - 対象、生成処理、作成元をたどれる来歴を設計の参考にする。awx/1をPROV準拠の交換形式とは称さない。
- AIRR：https://docs.airr-community.org/en/latest/datarep/overview.html
  - バージョン付きスキーマという交換原則を参考にする。現段階のawx/1はAIRR仕様そのものではなく、AIRRアダプターは未実装。
- OWASP ASVS：https://asvs.owasp.org/
  - 参照時の安定版は5.0.0。ローカルAPIの入力検証、オリジン照合、出力エスケープ、秘密を含まないログの試験を設計する。全項目適合とは称さない。

FASTA取込では受け入れ文字集合を明示する。
許可するのは20標準アミノ酸とB/Z/J/X/U/Oであり、後者は曖昧または非標準として警告する。
これは製品の入力契約であり、抗体として妥当という科学的判定ではない。
CDR、鎖型、分子形式、活性、物性を配列だけから推測しない。
