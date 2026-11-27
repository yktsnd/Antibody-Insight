# WebView2 構造カメラ保存の独立再走

## 対象と範囲

Q9、R-09、AC-17に関係する構造ビューのカメラ状態だけを、Windows上の実際のpywebview EdgeChromium（WebView2）ウィンドウで再走した。AC-17全体の合格判定ではない。選択候補、レイアウト、ノートを含むプロジェクト復元全体は今回の対象外。

再走用案件は `examples/sequences.csv`、`examples/observations.csv`、`examples/synthetic-peptide.pdb` から作る合成データで、終了時に削除する。Example Bには同じ合成構造を別コンポーネントとして登録し、別の構造IDを割り当てた。既存の `tests/desktop_replay.py` と製品コードは変更していない。

## 操作と照合方法

1. Example A / Peptideの構造キャンバス上でマウス左ボタンを押し、120 × 72 pxを8段階でドラッグして回転した。
2. 同じキャンバス上でホイール `deltaY=-480` を送り、ズームした。
3. Example B / Peptideへ切り替え、初回表示、異なるマウス回転とホイール `deltaY=360`、A↔Bの切り替えを行った。
4. 座標を持たないExample A / Reporterを選び、Example A / Peptideへ戻った。
5. WebView2プロセスを終了し、同じ一時プロジェクトを新しいプロセスで開いた。

`3Dmol.js getView()` が返す8値を表示中に読み、同一構造へ戻ったときとプロセス再起動後の値を照合した。順序は `modelGroup.x, modelGroup.y, modelGroup.z, rotationGroup.position.z, quaternion.x, quaternion.y, quaternion.z, quaternion.w`。差の許容値は各成分 `1e-6`。プロジェクトのSQLite `meta.view.cameras[structure_id]` に保存された配列も照合した。

## 実測結果

| 成分 | 初期値 A | マウス回転後 A | ホイール後 A | 再起動後 A |
|---|---:|---:|---:|---:|
| modelGroup.x | -3.083750 | -3.083750 | -3.083750 | -3.083750 |
| modelGroup.y | -1.582500 | -1.582500 | -1.582500 | -1.582500 |
| modelGroup.z | 0 | 0 | 0 | 0 |
| rotationGroup.position.z | 121.643591 | 121.643591 | 115.617854 | 115.617854 |
| quaternion.x | 0 | -0.677516 | -0.677516 | -0.677516 |
| quaternion.y | 0 | -0.400815 | -0.400815 | -0.400815 |
| quaternion.z | 0 | 0 | 0 | 0 |
| quaternion.w | 1 | -0.616701 | -0.616701 | -0.616701 |

Aの回転ではクォータニオン4成分が変わり、ホイール操作では `rotationGroup.position.z` が `121.643591` から `115.617854` に変わった。8成分はAへ戻った時、座標なしコンポーネントを経由した後、およびプロセス再起動後にすべて許容値内で一致した。

Example Bの初回表示時点ではBの保存カメラ配列はなかった。初期ビューの8成分は有限値で、構造IDはAと異なっていた。初回ビューでは、現在のビューアの回転向きが引き継がれ、`zoomTo()`で深度が初期値に戻る挙動を実測した。Bを別向きに回転・ズームすると、Bの8値がBの構造IDで保存され、A↔Bを往復しても各構造の値がそれぞれ復元された。

座標のないExample A / Reporterでは画面に `No coordinates registered` と表示された。選択して戻る操作後もカメラ値は変わらなかった。WebView2コンソールのページエラーは0件だった。実行環境はWindows 11 Home build 26200、WebView2 Runtime `158.0.4370.33`（2026-11-27 JST）。

## 再現コマンドと証拠

```powershell
& '.\.venv\Scripts\python.exe' tests\camera_replay.py 'docs/evidence/camera-review'
```

- [再走スクリプト](../../tests/camera_replay.py)
- [8成分と各照合結果（JSON）](camera-review/camera-state.json)
- [Aのマウス回転後](camera-review/camera-rotated.png)
- [Aのホイール操作後](camera-review/camera-zoomed.png)
- [Bの回転・ズーム後](camera-review/camera-candidate-b.png)
- [新しいWebView2プロセスでの再開](camera-review/camera-after-restart.png)

合成PDB読込時にBiopythonから `END` 行に関する `PDBConstructionWarning` が出たが、2回とも表示・操作・保存・再開に影響せず、ページエラーは記録されなかった。
