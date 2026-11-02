# M1データ契約

関連：P01/P06/P07/P08、J01/J06/J07/J08、AC-J01/AC-J06/AC-J07/AC-J08。
他の利用者のための最終モデルはDEVELOPMENT_PLAN第7章から削除しない。

## 共通契約

awx/1はprojectとentitiesを含むJSONオブジェクトとする。
projectにはid、title、goal、created_atがある。
data_classは任意でresearch/synthetic_fixtureを指定でき、省略した既存データはresearchとして扱う。
プロジェクト名だけでは試験例としての番号付け処理を有効にしない。
entityにはid、type、project_id、created_atと型固有属性がある。
内部IDは型プレフィックスとUUID（例mol_…）とし、外部ラベルとは別に保存する。
projectと全entityのID衝突を上書きしない。
別プロジェクトの参照を拒否する。
作成日時と測定日時はタイムゾーン付きISO 8601とする。
同じ配列を持つ分子は別IDのまま保存し、重複候補として表示する。
単一鎖の同一性を分子全体の同一性と解釈しない。

全型で未知フィールドをパス付きで拒否する。
nullと0を区別する。
空文字、NaN、Infinity、boolを測定値として受け入れない。
ブラウザとのJSON交換で整数が丸められないよう、値および条件の整数は±(2^53−1)以内に制限する。
浮動小数点数は有限のIEEE 754倍精度数とし、整数値に相当する数にも同じ範囲を適用する。
これを超える数は黙って変換せず、明示的な入力エラーを返す。
JSON中の非ゼロ数値が浮動小数点数の範囲外で0へアンダーフローする場合も拒否する。
データ交換は元IDを維持し、新しい空DBへの取込で全内容を照合する。
既存projectへのentity追加は同一projectオブジェクトに限る。
project内容の不一致、内部ID衝突、同じproject内の外部ID衝突は全取込を拒否する。

| 型 | 属性 | 重要な制約 |
|---|---|---|
| molecule | name, external_id, format, chains, source | chainsは順序付き非空配列。各鎖にid/role/sequence。formatはunspecifiedまたは明示入力。roleから鎖ペアを推測しない |
| construct | name, molecule_id, cds, vector, signal_peptide | cds/vector/signal_peptideはnull可。同一配列でも別ID。CDSの翻訳一致は現段階では未検証 |
| material | name, construct_id, lot | lot必須。実測の直接対象 |
| evidence | subject_id, kind, metric, source, timestamp, conditions, value, unit | kind=measured/computed/literature/annotation。measuredの対象はMaterial。source.nameとversionキーは必須で、実際に版が不明ならversion=null。value=nullならunit=null可。数値なら単位必須（無次元は1）。conditionsはオブジェクトまたはnull |
| decision | candidate_ids, criteria, evidence_snapshot, reason, timestamp, revision, supersedes, status | M1はstatus=draft、criteria=[]、revision=1、supersedes=nullのみ。スナップショットは対象候補に関係する既存Evidenceの完全コピー。候補/根拠IDの重複禁止。確定判定は未実装 |

初期のmolecule.chainsは配列観察の最小モデルである。
追加のF06では、BindingUnit、明示されたcomponent_graph、構成変更のLineageを[追加契約](COMPONENT_CONTRACT.md)に従って保存、検証する。
旧データを推測で補完せず、保存済みの内容は書き換えない。
ResidueMapはF07の[番号付け契約](NUMBERING_CONTRACT.md)に従って取り込む。
対話的な組立操作、Hypothesis、番号付き変異は後続のM3に残す。
未実装型の入力は未対応として拒否する。
構造ファイルはM2で対応するため、M1では未対応形式としてDB変更前に拒否する。
F08では[構造契約](STRUCTURE_CONTRACT.md)に従い、StructureとStructureMapを追加する。
computed Evidenceの直接対象にStructureを認め、元の構造から宣言されたMoleculeへたどれるようにする。
measured Evidenceの直接対象は引き続きMaterialに限り、構造や分子へ実測として付け替えない。

## FASTAとCSV

FASTAの1レコードを、format=unspecified、role=unknownの1鎖を持つ分子として取り込む。
ヘッダー全文を外部IDとして扱う。
異なるレコードのVH/VLペアやIgG形式を推測しない。
空ヘッダー、重複ヘッダー、欠損配列、許可集合外の文字を行単位で報告する。
正常分だけを取込む場合も、プレビューで除外内容を確認して保存する。
CSV列はexternal_id,name,sequence,chain_role,formatとする。
最初の3列を必須とし、後ろの2列は省略時にunknown/unspecifiedとする。
未対応列があれば黙って落とさず拒否する。
測定CSVの取込はM4に残し、配列CSVと混同しない。

入力プレビューは保存しない。
保存前にサーバーで再検証し、transaction内で参照先と衝突を確認する。
受け取ったファイルの内容や配列をサーバーログへ書かない。

## UI原型

- E：左にインポートとQC、中央に検索可能な候補表、右に選択集合。保存前プレビューを表示する。
- W：候補と鎖の配列を表示。2件の同じ配列位置を比較し、番号付けと構造未登録を別に示す。整列なしの位置比較であることを表示する。
- D：M2/M3に必要な番号付け/系譜/構成の未実装状態を表示。偽の設計結果を作らない。
- R：選択候補に関連するEvidenceを種類別ラベルで表示。Material→Construct→Moleculeをたどり、理由と根拠のスナップショットを下書きとして保存する。

共通ナビゲーションに4画面と選択件数を表示する。
選択ID、対象鎖、配列位置、フィルター、画面はプロジェクト別にブラウザのローカル状態へ保存する。
配列と測定値はlocalStorageへ複製しない。
選択集合の保存済み下書きはDBに保持する。
画面は英語、開発文書は日本語とする。
