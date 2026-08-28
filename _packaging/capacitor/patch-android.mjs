#!/usr/bin/env node
/* Nakłada nasze poprawki na świeżo wygenerowany android/ (Capacitor odtwarza go
 * przy `npx cap add android`). Idempotentny. Wołany z `npm run sync` i w CI.
 *
 *   - android/app/build.gradle:  blok signingConfigs.release (czyta ../keystore.properties
 *     lub zmienne ANDROID_KEYSTORE_*), podpięcie pod buildTypes.release,
 *     wyłączony lint dla release (wywala się na spacji w ścieżce "projekt w budowie")
 *   - android/local.properties:  sdk.dir z $ANDROID_HOME (jeśli nie istnieje)
 */
import { promises as fs } from 'node:fs';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ANDROID = path.join(HERE, 'android');
const GRADLE = path.join(ANDROID, 'app', 'build.gradle');

if (!existsSync(GRADLE)) {
  console.error('patch-android: brak android/ — uruchom najpierw `npx cap add android`');
  process.exit(1);
}

let g = await fs.readFile(GRADLE, 'utf8');
if (g.includes('// [atlas-patch]')) {
  console.log('patch-android: już naniesione — pomijam.');
} else {
  const header = `// [atlas-patch] podpis release + wyłączony lint
def _ksProps = new Properties()
def _ksFile = rootProject.file("keystore.properties")
if (_ksFile.exists()) { _ksProps.load(new FileInputStream(_ksFile)) }
def _ksStore = _ksProps['storeFile'] ?: System.getenv('ANDROID_KEYSTORE_FILE')
def _ksStorePass = _ksProps['storePassword'] ?: System.getenv('ANDROID_KEYSTORE_PASSWORD')
def _ksAlias = _ksProps['keyAlias'] ?: System.getenv('ANDROID_KEY_ALIAS')
def _ksKeyPass = _ksProps['keyPassword'] ?: System.getenv('ANDROID_KEY_PASSWORD')

`;
  g = header + g;

  // lint off + signingConfigs zaraz po "android {"
  g = g.replace(/android\s*\{/, `android {
    lint { checkReleaseBuilds false; abortOnError false }
    signingConfigs {
        release {
            if (_ksStore) {
                storeFile file(_ksStore)
                storePassword _ksStorePass
                keyAlias _ksAlias
                keyPassword _ksKeyPass
            }
        }
    }`);

  // podpięcie signingConfig do release
  g = g.replace(/(buildTypes\s*\{\s*release\s*\{)/, `$1
            if (_ksStore) { signingConfig signingConfigs.release }`);

  await fs.writeFile(GRADLE, g);
  console.log('patch-android: build.gradle zaktualizowany.');
}

// local.properties
const lp = path.join(ANDROID, 'local.properties');
const sdk = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT;
if (!existsSync(lp) && sdk) {
  // forward-slashe — AGP je akceptuje, a unika się piekła escapowania w .properties
  await fs.writeFile(lp, 'sdk.dir=' + sdk.replace(/\\/g, '/') + '\n');
  console.log('patch-android: local.properties utworzony.');
}
