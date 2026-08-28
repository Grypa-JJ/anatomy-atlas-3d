# Atlas 3D — powłoka Windows (Tauri v2)

Pakuje `_packaging/web/` (bundle z `assemble.mjs`) w aplikację `.exe` z instalatorem NSIS
i wbudowanym updaterem.

## Wymagania jednorazowe (maszyna do buildu)

- **Rust** — https://rustup.rs (`rustup default stable`)
- **Node 18+** (masz 22)
- **WebView2** — jest w Windows 10/11 domyślnie; w razie czego „Evergreen Bootstrapper" od MS
- Visual Studio Build Tools (C++), instalowane zwykle razem z rustup na Windows

## Pierwsze uruchomienie

```bash
cd _packaging/tauri
npm install
npm run icon          # generuje src-tauri/icons/* z app-icon.png  (PODMIEŃ app-icon.png na 1024×1024!)
npm run dev           # okno dev z hot-reloadem; odpala ../../assemble.mjs przed startem
```

## Build produkcyjny

```bash
npm run build
```

Wynik: `src-tauri/target/release/bundle/nsis/Atlas anatomiczny 3D_<wersja>_x64-setup.exe`
oraz `*.exe.sig` (podpis do updatera — patrz niżej).

`beforeBuildCommand` w `tauri.conf.json` sam odpala `assemble.mjs`, więc bundle jest
zawsze świeży. Wymaga obecności źródeł atlasu (GLB w `_atlas_v2/dist/`, `_organ_compare/alt/` itd.).

### Portable zamiast instalatora

W `tauri.conf.json` → `bundle.targets` dodaj `"app"` (folder z `.exe` bez instalatora),
albo zostaw NSIS z `installMode: "currentUser"` — instaluje bez uprawnień administratora.

## Updater — konfiguracja (raz)

1. Wygeneruj parę kluczy:
   ```bash
   npm run tauri signer generate -- -w %USERPROFILE%\.tauri\atlas3d.key
   ```
   - **klucz prywatny** (`atlas3d.key` + hasło) — TRZYMAJ POZA REPO (menedżer haseł / sejf CI)
   - **klucz publiczny** — wklej do `tauri.conf.json` → `plugins.updater.pubkey`
2. W `plugins.updater.endpoints` wpisz URL do `latest.json` na R2
   (np. `https://<bucket>.r2.dev/atlas/updates/latest.json`).
3. Ustaw te same zmienne przy każdym `npm run build`, żeby powstał `.sig`:
   ```bash
   set TAURI_SIGNING_PRIVATE_KEY=<zawartość atlas3d.key>
   set TAURI_SIGNING_PRIVATE_KEY_PASSWORD=<hasło>
   npm run build
   ```

## Wydanie nowej wersji

1. Podnieś `version` w: `src-tauri/tauri.conf.json`, `../shared/app-version.json`, `package.json`.
2. `npm run build`.
3. Wgraj `*_x64-setup.exe` do **GitHub Releases** (tag `atlas-vX.Y.Z`).
4. Zaktualizuj `latest.json` na R2:
   - `version`, `notes`, `pub_date`
   - `platforms.windows-x86_64.url` → link do `.exe` z GitHub Releases
   - `platforms.windows-x86_64.signature` → zawartość `*_x64-setup.exe.sig`
5. Klienci: przy starcie natywny updater Tauri wykryje nowość → `updater.js` pokaże baner
   „Dostępna aktualizacja" (patrz `../shared/updater.js`).

## Podpis kodu (SmartScreen)

Bez certyfikatu Authenticode Windows pokaże „Nieznany wydawca" przy pierwszym uruchomieniu
(user: „Więcej informacji" → „Uruchom mimo to"). Certyfikat OV ~400–600 zł/rok usuwa ostrzeżenie.
Updater Tauri działa niezależnie od tego — używa własnego podpisu Ed25519.

## Znane pułapki

- **CSP** w `tauri.conf.json` musi mieć `worker-src blob:` i `script-src 'wasm-unsafe-eval'` —
  bez tego dekoder Draco (`.glb`) i workery Three.js nie wystartują. Już ustawione.
- `withGlobalTauri: true` daje `window.__TAURI__` w `updater.js` (ścieżka natywnej instalacji).
- Mowa (`speechSynthesis`) działa w WebView2 out-of-the-box.
