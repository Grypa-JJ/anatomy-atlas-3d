# Attribution & licensing

This project bundles application code and adapted anatomical data under **different
licenses**. If you reuse anything from here, read this file.

## Application code — MIT

Everything in this repository that is *code* (the Three.js viewer in
`_atlas_v2/build_full/`, the organ browser in `_organ_compare/`, the packaging in
`_packaging/`, the Python extraction pipeline, build scripts, CI) is released under the
[MIT License](LICENSE).

## 3D geometry — CC BY-SA (share-alike)

The 3D models — the GLB layer files, any mesh exported by the extraction pipeline, and any
render or derivative of them — are **adapted from**:

### BodyParts3D
- Source: BodyParts3D, © The Database Center for Life Science (DBCLS)
- <https://lifesciencedb.jp/bp3d/> · <https://dbarchive.biosciencedbc.jp/en/bodyparts3d/>
- License: **Creative Commons Attribution-ShareAlike 2.1 Japan (CC BY-SA 2.1 JP)**
- Publication: Mitsuhashi N. et al., *BodyParts3D: 3D structure database for anatomical
  concepts.* Nucleic Acids Research 37 (2009): D782–D785.

### Z-Anatomy
- Source: Z-Anatomy — a Blender whole-body anatomical model
- <https://www.z-anatomy.com/> · <https://github.com/LluisV/Z-Anatomy>
- License: **Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0)**
- Z-Anatomy itself builds on BodyParts3D.

**What this means for you:** the model files and their derivatives stay under CC BY-SA.
If you redistribute them (or renders/exports made from them) you must credit the sources
above and license your version under the same terms. The MIT license on the code does
**not** relicense the geometry.

## Anatomical nomenclature

- Polish names: *Słownik mian anatomicznych* (Medical University of Łódź / Uniwersytet
  Medyczny w Łodzi) and *Terminologia Anatomica* (FIPAT).
- This project is **not affiliated with or endorsed by** any anatomical society, FIPAT,
  UMed Łódź, DBCLS, or the Z-Anatomy project. Names are used descriptively for education.

## Third-party libraries

Vendored under `_atlas_v2/build_full/vendor/` and `_organ_compare/vendor/`:

- **three.js** — MIT (© three.js authors)
- **Draco** decoder — Apache-2.0 (© Google)

Node dependencies (`_packaging/*/package.json`) retain their own licenses.
