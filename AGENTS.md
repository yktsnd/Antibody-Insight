# Antibody Insight 開発規則

添付の要求原本は所有者のローカル環境で管理する。

起動時に 開発指示、仕様 v1.1、聞き取り原文、[ゴール](GOAL.md)、[開発記録](DEVELOPMENT.md) を読む。最新の明示指示、本人の発言（後の訂正を優先）、確定仕様、技術候補の順で判断する。

Antibodies、Sequences、Structures、Plots を中心に、同じ対象を往復して研究者が判断できることを優先する。基本版の受領・観察・検証・出力を維持する。Design、Advanced Analytics、AI Integration は同じ製品の拡張。フェーズによる要求削減をしない。英語で製品を提供し、日本語で管理・報告する。

変更前に Q/R/AC/V、操作、入出力、対象、正常例と境界例を記す。科学計算・描画は既存ライブラリを優先し、対象・座標・単位・欠測・出典を独立の値と照合する。研究資料は端末内に保つ。確定要求、科学的意味、ライセンス区分の変更、外部共有、破壊的操作は依頼者に確認する。各変更で実行・GUI確認・修正を繰り返し、証拠と残課題を開発記録に残す。再開時は最新の実測から再走し、製品全体の合格には各受入条件の実測を要する。

Windows の Python 3.12 用仮想環境に `requirements-dev.txt` を入れる。起動は `.\start.ps1`、回帰試験は `.\.venv\Scripts\python.exe -m pytest -q`、配布物は `.\build.ps1`。実画面の再走は `tests/desktop_replay.py` と操作別の再走スクリプトに出力先と `--executable dist/AntibodyInsight/AntibodyInsight.exe` を渡す。

`antibody_insight/desktop.py` がローカルファイル操作、`project.py` がSQLite保存と集計、`imports.py`・`alignment.py`・`structures.py` が科学データの処理、`ui/` が4ペインの表示を担当する。`examples/` に英語の入力例、`tests/` に照合手順、`docs/evidence/` に実測を置く。
