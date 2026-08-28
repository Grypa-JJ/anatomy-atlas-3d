# `_packaging/` — atlas 3D jako aplikacja Windows i Android

Grunt pod spakowanie **atlasu anatomicznego 3D** (`atlas.html` + `_atlas_v2/` + `_organ_compare/`)
w:

- **Windows** — `.exe` + instalator NSIS (Tauri v2), z updaterem
- **Android** — APK do sideloadu (Capacitor), z aktualizacjami OTA warstwy web

Baza pytań („Kocia Baza Wiedzy", `index.html`, Supabase) **nie wchodzi** — pakujemy tylko atlas.

Stan: **rusztowanie gotowe i przetestowane** (bundle się składa, oba widoki 3D ładują się
lokalnie bez internetu). Do sklejenia całości brakuje kroków oznaczonych `TODO (glue)` niżej —
robimy je, gdy inne sesje skończą pracę nad treścią atlasu.

---

## Architektura dystrybucji

```
źródła + assety w repo ──► assemble.mjs ──► _packaging/web/  (płaski bundle ~108 MB)
                                                  │  wszystkie GLB/CT/NIH W ŚRODKU
                        ┌─────────────────────────┴─────────────────┐
                        ▼                                           ▼
              _packaging/tauri/  (Windows)                _packaging/capacitor/  (Android)
                  → NSIS .exe  (assety w instalce)             → APK  (assety w APK)
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

## Ścieżka: Windows

Szczegóły → [`tauri/README.md`](tauri/README.md). Skrót:

```bash
cd _packaging/tauri
npm install
npm run icon          # z app-icon.png (PODMIEŃ na 1024×1024)
npm run build         # → src-tauri/target/release/bundle/nsis/*_x64-setup.exe (+ .sig)
```

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

Zrobione: ✅ scaffolding Tauri + Capacitor · ✅ `assemble.mjs` (przetestowany w przeglądarce) ·
✅ `updater.js` + baner (przetestowany) · ✅ ikona atlasu (192/512/1024 + `.ico`/`.icns`) ·
✅ `pack-assets.mjs`/`fetch-assets.mjs` · ✅ CI `atlas-release.yml`

Zostało (wymaga kont/kluczy/toolchainów, nie kodu):

- [ ] **Odświeżyć bundle** — `node _packaging/assemble.mjs` po ostatnich zmianach innych sesji
- [ ] **Assety dla CI** (pomiń, jeśli budujesz lokalnie) — `node _packaging/pack-assets.mjs`,
      `gh release create atlas-assets _packaging/atlas-assets.tar.gz`, URL → sekret `ATLAS_ASSETS_URL`
- [ ] **`latest.json`** (do aktualizacji) — wgrać pierwszy plik (wzór: `shared/latest.json.example`)
      na GitHub raw lub R2, wpisać jego URL w `shared/app-version.json` **i**
      `tauri/src-tauri/tauri.conf.json` (`plugins.updater.endpoints`). Bez tego apka po prostu
      nie pokazuje banera aktualizacji (updater.js sam się wycisza) — reszta działa.
- [ ] **Klucz updatera Tauri** — `cd _packaging/tauri && npm run tauri signer generate`;
      klucz publiczny → `tauri.conf.json` `pubkey`; prywatny + hasło → sekrety CI
- [ ] **Keystore Android** — `keytool -genkey ... atlas3d.keystore`; base64 → sekret
      `ANDROID_KEYSTORE_BASE64`, hasła/alias → pozostałe sekrety
- [ ] **Pierwszy build** — `git tag atlas-v0.1.0 && git push origin atlas-v0.1.0`
      (albo lokalnie: `_packaging/tauri` → `npm i && npm run build`; `_packaging/capacitor` →
      `npm i && npx cap add android && npm run apk`)
- [ ] **Tauri: potwierdzić CSP** — przejść wszystkie tryby atlasu (quiz, skalpel, przekrój,
      eksport CSV, zrzut ekranu) w oknie `npm run dev`, dopieścić `csp` jeśli coś blokuje
- [ ] **Android: `speechSynthesis`** — sprawdzić na realnym urządzeniu; jeśli głucho, wpiąć
      `@capacitor-community/text-to-speech` pod przycisk 🔈
- [ ] **updater.js: ścieżka natywna Tauri** — zweryfikować `window.__TAURI__.updater` po
      `withGlobalTauri` w realnym oknie; w razie potrzeby dołożyć `@tauri-apps/plugin-updater` przez esbuild
- [ ] **Odchudzenie** (opcjonalne): CT PNG w `_organ_compare/alt/mpr` → WebP/KTX2; `gltfpack` na `.glb`

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
├── tauri/                    ← powłoka Windows (Tauri v2), z src-tauri/icons/
├── capacitor/                ← powłoka Android (Capacitor)
└── web/                      ← WYNIK assemble.mjs (gitignore)

.github/workflows/atlas-release.yml   ← CI: tag atlas-v* → .exe + .apk do Release
```
