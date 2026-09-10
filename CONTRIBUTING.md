# Contributing

Thanks for looking. This is a solo project built for a Polish medical curriculum, opened
so others can learn from it and improve it.

## Good contributions

- **Rendering bugs** — include browser, OS, GPU (especially hybrid-GPU laptops), and a
  screenshot. State whether it happens before or after the model loads.
- **Nomenclature corrections** — wrong or missing Polish/Latin names. Point at the
  structure ID (shown in the info card) and cite a source.
- **Landmark data** — additional or corrected exam pin-points ("szpilki"), with the bone
  ID and an anatomical description.
- **Packaging** — Windows/Android build fixes, the CI workflow.

## Notes

- Code comments and internal docs are in **Polish**. That's fine — outward-facing docs
  (README, this file, ATTRIBUTION) are English.
- The Three.js engine in `_atlas_v2/build_full/atlas_pilot_v3.html` is one large file by
  design (ships as a single offline HTML). The UI shell and the engine are separated
  inside it; keep control element IDs stable.
- Heavy assets (GLB, CT, `.blend`) are gitignored. Don't commit them.
- The 3D geometry is CC BY-SA — see [ATTRIBUTION.md](ATTRIBUTION.md). Don't add geometry
  from incompatible sources.

## Dev loop

```bash
python -m http.server 9028
# http://localhost:9028/_atlas_v2/build_full/atlas_pilot_v3.html
```

Open a PR against `main` with a clear description and reproduction steps.
