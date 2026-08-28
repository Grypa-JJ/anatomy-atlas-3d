# Atlas 3D — powłoka Windows (Electron)

Pakuje `_packaging/web/` w `.exe` (instalator NSIS). Electron = własny Chromium, więc atlas
renderuje się **identycznie jak w przeglądarce** (w przeciwieństwie do Tauri/WebView2, który na
hybrydowym GPU dawał szew przez środek okna i wyblakłe modele).

## Wymagania

- **Node 18+** — i tyle. Bez Rusta, bez MSVC.

## Build

```bash
cd _packaging/electron
npm install
npm run build
```

Wynik w `dist/`:
- `Atlas anatomiczny 3D Setup <wersja>.exe` — instalator (~145 MB, Chromium + assety w środku)
- `latest.yml` + `*.blockmap` — feed dla `electron-updater` (wgrać do GitHub Release razem z .exe)

`npm run start` — odpala apkę bez pakowania (dev).

### Jednorazowy problem: winCodeSign

electron-builder pobiera `winCodeSign.7z`, w którym są mac-owe symlinki (`*.dylib`). Windows bez
trybu deweloperskiego nie może ich utworzyć → 7za wywala się z exit 2 i build pada. Obejścia:

1. **Ręczne rozpakowanie cache** (bez zmiany ustawień systemu):
   ```bash
   CACHE="$LOCALAPPDATA/electron-builder/Cache/winCodeSign"
   SZ="node_modules/7zip-bin/win/x64/7za.exe"
   mkdir -p "$CACHE/winCodeSign-2.6.0"
   "$SZ" x "$CACHE"/*.7z -o"$CACHE/winCodeSign-2.6.0" -y '-xr!*.dylib'
   ```
   potem `npm run build` znajdzie cache i pominie pobieranie.
2. Albo: Ustawienia → Prywatność i zabezpieczenia → Dla deweloperów → **Tryb dewelopera: wł.**

## Jak to działa

- `main.js` — tworzy `BrowserWindow`, startuje `static-server.js` na `127.0.0.1:<losowy port>`
  serwujący `web/` (atlas potrzebuje originu http, nie `file://`), ładuje `http://127.0.0.1:PORT/`.
- Assety GLB: w źródle atlasu warunek `_isLocal` (hostname `127.0.0.1` → prawda) ładuje je z
  `../dist/` w bundlu, nie z R2. Apka działa w 100% offline.
- `web/` trafia do instalki jako `extraResources` → `resources/web/`.

## Aktualizacje

`electron-updater`, feed = **GitHub Releases** (`package.json` → `build.publish`).

- przy starcie apka sprawdza najnowsze wydanie; jeśli nowsze → natywny dialog
  „Dostępna aktualizacja” → pobiera → „Zainstaluj i uruchom ponownie”.
- brak wydań = cichy `[updater] No published versions` w konsoli, nic się nie dzieje.
- CI musi wgrać do Release: `*.exe`, `latest.yml`, `*.blockmap`.

> W bundlu jest też `updater.js` (wspólny baner) — w Electronie schodzi na drugi plan
> (pokazałby się tylko gdyby ustawić `shared/app-version.json > update_manifest_url`).
> Docelowo zostaw jeden mechanizm; `electron-updater` jest natywniejszy.

## Podpis kodu

Bez certyfikatu Authenticode SmartScreen pokaże „Nieznany wydawca” przy 1. uruchomieniu
(„Więcej informacji” → „Uruchom mimo to”). `electron-updater` działa niezależnie (podpis SHA-512
z `latest.yml`).
