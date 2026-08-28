# Atlas 3D — powłoka Android (Capacitor)

Pakuje `_packaging/web/` w APK do **sideloadu** (poza sklepem). Stan: **działa** —
`atlas-anatomiczny-3d-0.1.0.apk` (~79 MB) buduje się lokalnie, podpisany, renderuje offline.

Android używa własnego WebView opartego na Chromium — **nie ma buga WebGL z WebView2** (patrz
`_packaging/README.md`), więc atlas renderuje się poprawnie.

## Toolchain (jednorazowo)

- **Node 18+**
- **JDK 21** — `winget install EclipseAdoptium.Temurin.21.JDK`
  ⚠️ JDK 23+ psuje AGP 8.7 ("Unsupported class file major version"). JDK 17 też działa.
- **Android SDK** — cmdline-tools + `platform-tools` + `platforms;android-35` + `build-tools;35.0.0`
  (bez Android Studio: rozpakuj `commandlinetools-win-*.zip` do
  `%LOCALAPPDATA%\Android\Sdk\cmdline-tools\latest\`, potem
  `sdkmanager --licenses` i `sdkmanager "platform-tools" "platforms;android-35" "build-tools;35.0.0"`)
- `ANDROID_HOME` = ścieżka do SDK

## Keystore (jednorazowo, POZA repo)

```bash
keytool -genkeypair -v -keystore %USERPROFILE%\.android-keys\atlas3d.keystore \
  -alias atlas3d -keyalg RSA -keysize 2048 -validity 10000 \
  -storepass <hasło> -dname "CN=Grypa-JJ, O=Grypa-JJ, C=PL"
```
(PKCS12 → store i key mają to samo hasło). Zapisz `android/keystore.properties` (gitignore):
```
storeFile=C:/Users/<user>/.android-keys/atlas3d.keystore
storePassword=<hasło>
keyAlias=atlas3d
keyPassword=<hasło>
```

## Build APK

```bash
cd _packaging/capacitor
npm install
npm run add        # cap add android + patch-android.mjs (signing + lint off + local.properties)
# skopiuj keystore.properties do android/  (rm -rf android przy npm run add je czyści)
npm run apk        # = sync + gradlew assembleRelease --no-daemon
```

APK: `android/app/build/outputs/apk/release/app-release.apk`.

`patch-android.mjs` (idempotentny, wołany z `npm run add` i `npm run sync`) nakłada na
świeżo wygenerowany `android/`:
- `signingConfigs.release` czytający `keystore.properties` lub `ANDROID_KEYSTORE_*`
- `lint { checkReleaseBuilds false }` — `lintVitalReportRelease` wywala się na spacji w
  ścieżce projektu ("projekt w budowie")
- `local.properties` z `sdk.dir` (**forward-slashe** — backslashe łamią parser `.properties`)

## Aktualizacje

### A. Warstwa web (GLB, JS, HTML) — OTA, bez reinstalacji

`@capgo/capacitor-updater` (wpięty, `autoUpdate: false`). `updater.js` przy nowej wersji w
`latest.json` woła `CapacitorUpdater.download({url: web.url})` → `set()` → restart do nowej paczki.
Paczkę web (`web-X.Y.Z.zip`) wgraj na R2 / GitHub Release, URL w `latest.json` → `web.url`.

### B. Powłoka natywna (nowy plugin) — nowy APK

`latest.json` → `android.url` na nowy APK. Baner „Zaktualizuj" otworzy link → user instaluje ręcznie.

## Sideload u użytkownika

Pobiera `.apk` → przy otwarciu Android pyta o „Instaluj nieznane aplikacje" dla przeglądarki →
Zainstaluj. Min. Android 6.0 (API 23). Wymaga WebGL2 (Chrome/WebView ≥ 75 — praktycznie każdy
telefon z 2019+).

## Znane pułapki

- **`speechSynthesis`** w Android WebView bywa pusty (brak silnika Google TTS →
  `getVoices()` = []). Jeśli mowa ma działać pewnie: `@capacitor-community/text-to-speech`
  pod przycisk 🔈 (glue-faza).
- 79 MB APK. Gdyby przeszkadzało: chudy APK + pobranie paczki GLB przy 1. starcie tym samym
  mechanizmem co OTA.
- `allowMixedContent: false` — zdalne zasoby (R2) muszą być https (są).
