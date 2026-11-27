# Third-party components

The desktop application uses pywebview with Microsoft Edge WebView2 on Windows, Biopython for biological file parsing, openpyxl and defusedxml for workbooks, and SQLite via Python for project storage. Python packages are pinned in requirements.txt. Their distributions include their own license information. WebView2 is an operating environment installed separately.

The local 3Dmol.js 3.0.0 and Plotly.js basic 4.3.0 builds are from the npm distributions `3dmol` and `plotly.js-basic-dist-min`. The distributed JavaScript files were extracted unchanged. Their licenses accompany the files in `antibody_insight/ui/vendor/`. The example coordinates, short sequences and example observations are synthetic software fixtures.

Variable-domain numbering uses [Immunum 2.1.0](https://pypi.org/project/immunum/2.1.0/) by ENPICOM, under [the MIT license](https://github.com/ENPICOM/immunum/blob/main/LICENSE). Its original license is included in the Python distribution metadata in the Windows bundle.

Immunum derives its scoring matrices from consensus sequences based on IMGT/GENE-DB V and J germline genes, release 202641-7. IMGT®, the international ImMunoGeneTics information system®, was created by Marie-Paule Lefranc and is maintained by the Institute of Human Genetics, Université de Montpellier and CNRS. IMGT data and metadata are provided under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The consensus and scoring matrices are transformations by the Immunum authors. See [Immunum's source description and citations](https://github.com/ENPICOM/immunum/blob/main/resources/consensus/README.md), [the IMGT conditions](https://www.imgt.org/about/termsofuse.php) and [IMGT/GENE-DB](https://www.imgt.org/genedb/).

Commercial distribution review covering all transitive runtime components is pending.
