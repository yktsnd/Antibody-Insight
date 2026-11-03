# Third-party components

Application source is Apache-2.0 as in LICENSE. The following components retain their own licenses and notices; no upstream source has been relicensed.

## Gemmi0.7.5

Installed unmodified as an external Python package, pinned in requirements.txt. License: MPL-2.0 (the project also offers an LGPL option, which this project does not select).

- Source: https://github.com/project-gemmi/gemmi/tree/v0.7.5
- Distribution: https://pypi.org/project/gemmi/0.7.5/
- License copy: web/vendor/Gemmi-MPL-2.0.txt
- Copyright: Global Phasing Ltd and upstream contributors, as in the distribution.

The covered parser is separate from application files. Its source and license remain available at the linked versioned source and distribution. No modified Gemmi code is included.

## 3Dmol.js2.5.5

Unmodified production browser bundle vendored from the pinned npm3dmol2.5.5 package, whose SHA-512 package integrity was verified before extraction. Version, source and individual file SHA-256 values are in web/vendor/manifest.json.

- Source: https://github.com/3dmol/3Dmol.js/tree/2.5.5
- Main license: BSD-3-Clause.
- Complete upstream and bundled-component notices: web/vendor/3Dmol-LICENSE.txt.
- The upstream bundle includes GLmol (MIT or LGPL3; this project selects the MIT option), Three.js (MIT), and jQuery (MIT); all supplied notices are retained.

The asset is served locally. No CDN, remote structure download or upstream network API is invoked by this application.

## Public PDB experimental test data

The unmodified `fixtures/public/1MLC.cif` coordinate file is PDB archive data, available under CC0 per [RCSB's data policy](https://www.rcsb.org/pages/policies). Depositors/authors, source revision, retrieval URL and exact SHA-256 are recorded in [the fixture notice](fixtures/public/README.md). This is experimental coordinate data used only for offline source/scale validation. The application does not fetch it at runtime. Website images and external integrated annotations are not included.
