# Atlas 3D — powłoka Android (Capacitor)

Pakuje `_packaging/web/` w APK do **sideloadu** (poza sklepem) + aktualizacje OTA
warstwy web przez `@capgo/capacitor-updater` (self-host na R2, bez płatnej chmury Capgo).

## Wymagania jednorazowe (maszyna do buildu)

- **Node 18+**, **JDK 17**
- **Android Studio** + Android SDK (API 34+), albo samo `cmdline-tools` + `platform-tools`
- Zmienna `ANDROID_HOME` / `ANDROID_SDK_ROOT`

## Pierwsze uruchomienie

```bash
cd _packaging/capacitor
npm install
node ../assemble.mjs          # zbuduj bundle web/
npx cap add android           # tworzy android/ (jest w .gitignore)
npx cap sync android          # kopiuje web/ + pluginy do android/
npx cap open android          # otwiera w Android Studio
```

## Build APK

```bash
npm run sync                  # assemble + cap sync
cd android
gradlew.bat assembleDebug     # android/app/build/outputs/apk/debug/app-debug.apk
# albo podpisany release:
gradlew.bat assembleRelease
```

### Podpis release (raz)

```bash
keytool -genkey -v -keystore atlas3d.keystore -alias atlas3d -keyalg RSA -keysize 2048 -validity 10000
```

`android/key.properties` (NIE commituj):
```
storeFile=../../atlas3d.keystore
storePassword=...
keyAlias=atlas3d
keyPassword=...
```
i w `android/app/build.gradle` dodaj `signingConfigs` czytające `key.properties`
(standardowy snippet Capacitora/Androida).

## Sideload u użytkownika

1. Wrzuć `app-release.apk` do **GitHub Releases** (tag `atlas-vX.Y.Z`).
2. User: pobiera APK → przy otwarciu Android pyta o zgodę „Instaluj nieznane aplikacje"
   dla przeglądarki/menedżera plików → instaluje.

## Aktualizacje

Dwa poziomy:

### A. Warstwa web (GLB, JS, HTML, szpilki) — OTA, bez reinstalacji

1. `npm run sync` na nowej wersji, spakuj **zawartość `android/app/src/main/assets/public/`**
   (to jest to, co robi `cap sync`) do ZIP-a — albo prościej: spakuj `../web/` do
   `web-X.Y.Z.zip` w formacie oczekiwanym przez Capgo (płaski zip roota).
2. Wgraj ZIP na R2: `atlas/updates/web-X.Y.Z.zip`.
3. W `latest.json` na R2 ustaw `web.url` na ten ZIP + `version`.
4. Klient: `updater.js` wykrywa nową `version`, woła
   `CapacitorUpdater.download({url})` → `set(bundle)` → restart do nowej paczki.

> Uwaga: `@capgo/capacitor-updater` OTA-uje TYLKO assety web. Kod natywny (pluginy) — tylko nowy APK.

### B. Powłoka natywna (nowy plugin, bump Capacitora) — nowy APK

`latest.json` → `android.url` na nowy APK w GitHub Releases. `updater.js` pokaże baner,
„Zaktualizuj" otworzy link → user instaluje APK ręcznie (jak przy pierwszej instalacji).

## Znane pułapki

- **`speechSynthesis`** w Android System WebView bywa pusty (brak silnika Google TTS →
  `getVoices()` = []). Jeśli mowa ma działać pewnie na Androidzie: dodaj
  `@capacitor-community/text-to-speech` i podepnij pod przycisk 🔈 w atlasie (glue-faza).
- WebGL2 działa w nowoczesnym WebView (Chrome ≥ 75). Stare tablety (WebView < 75) — brak.
- 108 MB assetów w APK jest OK dla sideloadu. Gdyby przeszkadzało: chudy APK + pobranie
  paczki GLB przy pierwszym starcie tym samym mechanizmem co OTA.
- `allowMixedContent: false` — wszystkie zdalne zasoby (R2) muszą być https (są).
