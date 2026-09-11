<!-- SEO / discoverability: interactive 3D human anatomy atlas, web-based, Three.js / WebGL,
     full body, ~2500 structures, English + Polish anatomical nomenclature, exam preparation,
     offline desktop (Windows) and Android app. -->

# Anatomy Atlas 3D

**An interactive, web-based 3D atlas of human anatomy.** Rotate a full-body model of
~2,500 individually selectable structures across ten anatomical layers (bones, muscles,
fascia, vessels, organs, teeth, connective tissue, brain, nerves, lymphatics), read every
name and the whole interface in **English or Polish** (one tap to switch), explode the
layers apart, take a cross-section, isolate a single structure with all of its named
landmarks, and study for anatomy practicals ("kolokwia") with the built-in pin-point
("szpilki") sets.

Runs in any modern browser (Three.js / WebGL2, Draco-compressed geometry). Also ships as
an **offline desktop app for Windows** (Electron) and an **Android APK** (Capacitor) that
carry the whole model inside — no download, no account, works on a plane.

> Status: working prototype, actively developed. First public code: August 2026.

---

## Features

| | |
|---|---|
| **Full-body model** | ~2,500 structures, 10 toggleable layers, Draco-GLB (~29 MB total) |
| **English / Polish** | one-tap language switch — every structure name and the whole UI change together |
| **Explode view** | one slider fans every tissue layer away from the skeleton |
| **Isolate structure** | open a single bone/muscle full-screen with all of its named landmarks listed |
| **Cross-section** | clipping plane on any axis |
| **Landmarks / "szpilki"** | ~490 exam pin-points mapped to the geometry, grouped by practical (Kolokwium I–IV) |
| **Lecture notes** | per-structure theory notes (attachments, innervation, clinical relevance) |
| **Study tools** | quiz mode, distance measure, scalpel (hide structures), split-screen compare, bookmarks, Anki CSV export |
| **Organ browser** | separate viewer comparing 33 organs across three source datasets (Z-Anatomy / CT / NIH) with MPR slices |
| **Offline apps** | Windows `.exe` (Electron) + Android `.apk` (Capacitor), assets bundled, OTA web-layer updates |

## Anatomical data

The geometry is **not original to this project**. It is adapted from:

- **[BodyParts3D](https://lifesciencedb.jp/bp3d/)** 4.0 / 2.1 — © The Database Center for
  Life Science, licensed **CC BY-SA 2.1 JP**
- **[Z-Anatomy](https://www.z-anatomy.com/)** — a Blender-based whole-body model, licensed **CC BY-SA 4.0**

Polish naming follows the *Słownik mian anatomicznych* (Medical University of Łódź) and
*Terminologia Anatomica*. See **[ATTRIBUTION.md](ATTRIBUTION.md)** for the full breakdown
and the share-alike obligations that apply to the model files and any derivative of them.

This is an educational reference, **not** a diagnostic or surgical tool. It does not
represent every human structure or anatomical variation.

## Repository layout

```
atlas.html              start screen (mode picker)
_atlas_v2/              the atlas
  build_full/           atlas_pilot_v3.html — the viewer (Three.js engine + UI)
  dist/                 Draco-GLB layers (gitignored; see _atlas_v2/README-ish notes)
  *.py                  geometry extraction pipeline (Blender headless → GLB)
_organ_compare/         organ browser (33 organs × 3 datasets, MPR)
_packaging/             desktop + mobile packaging
  electron/             Windows (Electron + electron-updater)
  capacitor/            Android (Capacitor + OTA updater)
  assemble.mjs          builds the self-contained web bundle
.github/workflows/      tag-triggered release build (atlas-v*)
```

Heavy binary assets (GLB layers, CT volumes, the Z-Anatomy `.blend`) are **not** in git —
see `.gitignore`. The extraction pipeline and packaging scripts fetch or regenerate them.

## Run it locally

Any static file server works (the viewer needs `http://`, not `file://`):

```bash
python -m http.server 9028
# open http://localhost:9028/_atlas_v2/build_full/atlas_pilot_v3.html
```

With the GLB layers present in `_atlas_v2/dist/` it runs fully offline; otherwise it falls
back to loading them from a public bucket.

## Build the apps

```bash
# Windows installer (Electron)
cd _packaging/electron && npm ci && npm run build      # -> dist/*.exe

# Android APK (Capacitor) — needs JDK 21 + Android SDK
cd _packaging/capacitor && npm ci
npm run add && npm run apk                             # -> android/app/build/outputs/apk/release/
```

See [`_packaging/README.md`](_packaging/README.md) for toolchain details and the
tag-triggered CI release workflow.

## Contributing

Issues and PRs welcome — bug reports, nomenclature corrections, landmark data. Please
include browser/device details for rendering problems. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Application code: **MIT** (see [LICENSE](LICENSE)).
3D geometry and any files derived from it: **CC BY-SA** (inherited from BodyParts3D /
Z-Anatomy — see [ATTRIBUTION.md](ATTRIBUTION.md)). If you redistribute the model files or
a derivative, you must keep the attribution and the share-alike license.
