# `_packaging/` — atlas 3D jako aplikacja Windows i Android

Grunt pod spakowanie **atlasu anatomicznego 3D** (`atlas.html` + `_atlas_v2/` + `_organ_compare/`)
w:

- **Windows** — `.exe` + instalator NSIS (**Electron**), z updaterem `electron-updater`
- **Android** — APK do sideloadu (Capacitor), z aktualizacjami OTA warstwy web

Baza pytań („Kocia Baza Wiedzy", `index.html`, Supabase) **nie wchodzi** — pakujemy tylko atlas.

Stan: **zbudowane i działa.** Windows `.exe` (Electron, 145 MB) i Android `.apk` (78 MB) powstają
lokalnie; oba renderują atlas poprawnie i offline. Do wydania publicznego brakuje kroków
`Zostało` niżej (konta/klucze, nie kod).

> **Dlaczego Electron a nie Tauri (`_packaging/tauri/`):** Tauri używa systemowego WebView2,
> który na laptopach z hybrydową grafiką (AMD iGPU + NVIDIA dGPU) renderuje WebGL wadliwie —
> pionowy szew przez środek okna, wyblakłe modele. Chrome/Edge/Electron (własny Chromium) tego
> nie mają. `_packaging/tauri/` zostaje w repo jako referencja, ale **nie jest ścieżką wydania.**

---

## Architektura dystrybucji

```
źródła + assety w repo ──► assemble.mjs ──► _packaging/web/  (płaski bundle ~108 MB)
                                                  │  wszystkie GLB/CT/NIH W ŚRODKU
                        ┌─────────────────────────┴─────────────────┐
                        ▼                                           ▼
              _packaging/electron/  (Windows)             _packaging/capacitor/  (Android)
                  → NSIS .exe  (Chromium + assety)             → APK  (assety w APK)
                        │                                           │
                        └──────────── updater.js ───────────────────┘
                                          │  tylko SPRAWDZENIE wersji przy starcie
                         latest.json (kilka KB) — GitHub raw / R2
```

**Runtime = 100% offline.** `.exe`/`.apk` zawiera wszystkie assety. Po instalacji aplikacja
łączy się z siecią **tylko** żeby sprawdzić `latest.json` (kilka KB) — i to można wyłączyć.

**Hosting bez opłat za transfer:**
| Co | Gdzie | Rozmiar / częstość |
|---|---|---|
| instalator `.exe`, `.apk` | GitHub Releases (`Grypa-JJ/medstudy`, tag `atlas-vX.Y.Z`) | ~110 MB, co wydanie |
| `atlas-assets.tar.gz` (**tylko dla buildu w CI**) | GitHub Release `atlas-assets` (lub R2) | ~103 MB, rzadko |
| `latest.json` | GitHub raw lub R2 | kilka KB |
| paczki OTA Android `web-X.Y.Z.zip` (opcjonalne) | R2 lub GitHub Release | ~40–100 MB, co wydanie |

---

## `assemble.mjs` — builder bundla

```bash
node _packaging/assemble.mjs
# albo:  cd _packaging && npm run assemble
```

Co robi (idempotentnie — czyści `web/` i składa od zera):

1. `atlas.html` → `web/index.html` (usuwa stopkę „Powrót do bazy pytań")
2. `_atlas_v2/build_full/` → `web/_atlas_v2/build_full/` (bez `obj/` — 686 MB, niepotrzebne w runtime)
3. `_atlas_v2/dist/` → `web/_atlas_v2/dist/` (9 plików `.glb` Draco + JSON)
4. `_organ_compare/` → `web/_organ_compare/` (z `alt/`: CT, NIH, MPR)
5. **vendoruje three.js dla `_organ_compare`** (oryginał ciągnie z `unpkg` CDN → nie działałby offline):
   kopiuje `vendor/` z `build_full` + dokłada `vendor-extra/RoomEnvironment.js`, przepisuje importmap
   na ścieżki absolutne `/_organ_compare/vendor/...`
6. wstrzykuje do 3 stron HTML: `<script src="/updater.js">`, `<link rel="manifest">`,
   rejestrację service workera (tylko gdy `https:` i poza Tauri/Capacitor)
7. kopiuje do roota: `updater.js`, `manifest.webmanifest`, `sw.js`, `app-version.json` (ze stemplem czasu)
8. ikony z `shared/icons/`

**Assety w instalce, nie z sieci.** Źródło (`atlas_pilot_v3.html`, `_organ_compare/index.html`)
ma warunek `_isLocal` — gdy `window.__TAURI__` lub `window.Capacitor` jest obecne (czyli w `.exe`/`.apk`),
GLB ładują się z `../dist/`, a nie z R2. `assemble.mjs` kopiuje wszystkie GLB/CT/NIH do bundla,
więc `.exe`/`.apk` niesie je w środku i działa offline. **Zweryfikowane:** load atlasu z bundla
= 0 zapytań do `r2.dev`. R2 obsługuje tylko wariant webowy (Netlify), gdzie 28.9 MB GLB nie mieści
się sensownie w deployu.

**Skąd assety przy budowaniu:** są w `.gitignore` (nie ma ich po `git clone`). `fetch-assets.mjs`
szuka po kolei: (1) na dysku → **build lokalny nic nie pobiera**, (2) `_packaging/atlas-assets.tar.gz`,
(3) `$ATLAS_ASSETS_URL` (CI). `beforeBuildCommand` obu powłok woła go przed `assemble.mjs`.

Test bundla bez pakowania:
```bash
cd _packaging && npm run serve      # http://localhost:9040
```

## Ciężkie assety w CI — `pack-assets.mjs` / `fetch-assets.mjs`

**Tylko dla buildu w chmurze.** Build lokalny pomija — masz assety na dysku.

```bash
node _packaging/pack-assets.mjs      # -> atlas-assets.tar.gz (~103 MB) + sha256
```

Wgraj gdziekolwiek za darmo bez limitu transferu — najprościej **GitHub Release** (bez R2):
```bash
gh release create atlas-assets _packaging/atlas-assets.tar.gz --notes "assety atlasu (build-time)"
```
URL (`https://github.com/Grypa-JJ/medstudy/releases/download/atlas-assets/atlas-assets.tar.gz`)
→ sekret CI `ATLAS_ASSETS_URL` (+ opcjonalnie `ATLAS_ASSETS_SHA256`). Ponów po regeneracji GLB.

## CI — `.github/workflows/atlas-release.yml`

Push tagu `atlas-vX.Y.Z` → build `.exe` (windows-latest, `tauri-action`) + `.apk`
(ubuntu-latest, Capacitor) → **draft Release** z oboma plikami. Darmowe (GitHub Actions).

Śpi, dopóki nie ustawisz sekretów (lista na górze pliku workflow): `ATLAS_ASSETS_URL`,
`TAURI_SIGNING_PRIVATE_KEY`(+hasło), `ANDROID_KEYSTORE_BASE64`(+hasła/alias). Bez CI — build lokalny (niżej).

---

## Aktualizacje — jak to działa

`web/app-version.json` (wbudowana wersja) ma pole `update_manifest_url` → wskazuje `latest.json` na R2.

`updater.js` (wstrzyknięty w każdą stronę): 2,5 s po załadowaniu pobiera `latest.json`,
porównuje semver, i jeśli jest nowsza wersja — pokazuje baner **„Dostępna aktualizacja X.Y.Z"**
z przyciskami `Zaktualizuj` / `Później` (dismiss per-wersja w `localStorage`).

`Zaktualizuj` zależnie od środowiska:
| Środowisko | Zachowanie |
|---|---|
| Tauri (Windows) | natywny updater Tauri (pobiera podpisany `.exe`, instaluje, restart); fallback: otwiera link |
| Capacitor (Android) | `CapacitorUpdater.download()` + `set()` — podmiana paczki web, restart; fallback: link do APK |
| przeglądarka / PWA | otwiera link do pobrania |

Format `latest.json`: patrz [`shared/latest.json.example`](shared/latest.json.example)
(zgodny z natywnym updaterem Tauri; klucze `android`/`web` czyta tylko `updater.js`).

---

## Ścieżka: Windows (Electron)

Szczegóły → [`electron/README.md`](electron/README.md). Skrót:

```bash
cd _packaging/electron
npm install
npm run build         # → dist/Atlas anatomiczny 3D Setup <wersja>.exe  (+ latest.yml, .blockmap)
```

Wymaga tylko **Node** (żadnego Rusta/MSVC). Jednorazowo: jeśli `winCodeSign` się nie rozpakuje
(symlinki Mac, Windows bez trybu deweloperskiego), rozpakuj cache ręcznie z pominięciem `*.dylib`
albo włącz Developer Mode — patrz `electron/README.md`.

## Ścieżka: Android

Szczegóły → [`capacitor/README.md`](capacitor/README.md). Skrót:

```bash
cd _packaging/capacitor
npm install
node ../assemble.mjs
npx cap add android
npm run sync
cd android && gradlew.bat assembleRelease
```

---

## TODO (glue) — do zrobienia, gdy treść atlasu jest gotowa

Zrobione: ✅ `assemble.mjs` · ✅ Windows `.exe` (Electron, **zbudowany i przetestowany** —
renderuje czysto, bez szwu) · ✅ Android `.apk` (Capacitor, zbudowany) · ✅ ikona atlasu ·
✅ `pack-assets.mjs`/`fetch-assets.mjs` · ✅ CI `atlas-release.yml` (job Android gotowy)

Zostało:

- [ ] **CI: job Windows na Electron** — obecny `windows:` w `atlas-release.yml` używa `tauri-action`
      (martwe). Zamienić na: `cd _packaging/electron && npm ci && npm run build`, potem upload
      `dist/*.exe`, `dist/latest.yml`, `dist/*.blockmap` do Release. (Nie tknąłem pliku — inna
      sesja ma tam niezacommitowane zmiany do Androida.)
- [ ] **Assety dla CI** (pomiń, jeśli budujesz lokalnie) — `node _packaging/pack-assets.mjs`,
      `gh release create atlas-assets _packaging/atlas-assets.tar.gz`, URL → sekret `ATLAS_ASSETS_URL`
- [ ] **Keystore Android** — `keytool -genkey ... atlas3d.keystore`; base64 → sekret
      `ANDROID_KEYSTORE_BASE64`, hasła/alias → pozostałe sekrety
- [ ] **Pierwszy build publiczny** — `git tag atlas-v0.1.0 && git push origin atlas-v0.1.0`
      (albo lokalnie: `_packaging/electron` → `npm i && npm run build`; `_packaging/capacitor` →
      `npm i && npm run apk`). Wrzucić `.exe`+`latest.yml`+`.blockmap` oraz `.apk` do GitHub Release.
- [ ] **Android: `speechSynthesis`** — sprawdzić na realnym urządzeniu; jeśli głucho, wpiąć
      `@capacitor-community/text-to-speech` pod przycisk 🔈
- [ ] **Przebudować `.exe`/`.apk`** po tym jak druga sesja skończy poprawę renderowania atlasu
      (`assemble.mjs` bierze świeże źródło — wystarczy `npm run build` raz jeszcze).
- [ ] **Odchudzenie** (opcjonalne): CT PNG w `_organ_compare/alt/mpr` → WebP/KTX2; `gltfpack` na `.glb`
- [ ] **`_packaging/tauri/`** — do usunięcia gdy Electron się utrwali (zostaje jako referencja).

## Pliki

```
_packaging/
├── README.md                 ← ten plik
├── CZYTAJ-dysk-roku.txt      ← instrukcja instalacji do wrzucenia na dysk roku
├── assemble.mjs              ← builder bundla
├── fetch-assets.mjs          ← pobiera ciężkie assety z R2 (CI / czysta maszyna)
├── pack-assets.mjs           ← pakuje ciężkie assety → atlas-assets.tar.gz (do wgrania na R2)
├── make_icon.py              ← generuje ikonę atlasu (shared/icons/ + tauri/app-icon.png)
├── package.json
├── shared/
│   ├── updater.js           ← baner „dostępna aktualizacja" (agnostyczny wobec platformy)
│   ├── app-version.json     ← wbudowana wersja + URL manifestu aktualizacji
│   ├── latest.json.example  ← wzór zdalnego manifestu (na R2)
│   ├── manifest.webmanifest
│   ├── sw.js                ← cache offline dla wariantu PWA
│   └── icons/               ← icon-192/512 + app-icon-1024
├── vendor-extra/
│   └── RoomEnvironment.js   ← brakujący addon three (dla _organ_compare)
├── electron/                 ← powłoka Windows (Electron) — ŚCIEŻKA WYDANIA
├── capacitor/                ← powłoka Android (Capacitor)
├── tauri/                    ← martwe (WebView2 renderuje źle na hybrydowym GPU) — referencja
└── web/                      ← WYNIK assemble.mjs (gitignore)

.github/workflows/atlas-release.yml   ← CI: tag atlas-v* → .exe + .apk do Release
```
