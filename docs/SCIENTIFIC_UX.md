# 科学UIの比較と採用判断

2026-11-26。公式資料の操作記述を確認した。Jalview は元配列に結び付いた feature を選択・着色する。IGV は全体と塩基単位の位置を同じ座標で移動する。本製品でも候補ID、構成要素ID、元座標を選択に保持する。DNAとタンパク質を同じ位置として扱わない。[Jalview](https://www.jalview.org/help/html/features/seqfeatures.html)・[IGV](https://igv.org/doc/desktop/UserGuide/navigation/)

3Dの回転・拡大・原子選択にはローカル配布の3Dmol.js、数値系列の描画と点の選択にはPlotlyを使う。独自の分子・グラフ描画エンジンを設けない。原子の対応には元ファイル側の鎖・残基番号・挿入コードを用いる。[3Dmol.js](https://3dmol.csb.pitt.edu/doc/GLViewer.html)
