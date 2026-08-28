#!/usr/bin/env node
/* _packaging/assemble.mjs
 * Sklada samodzielny, plaski bundle  _packaging/web/  atlasu 3D z biezacych zrodel repo.
 * Idempotentny — uruchamiaj ponownie po kazdej zmianie w atlasie (inne sesje) przed pakowaniem.
 *
 *   node _packaging/assemble.mjs
 *
 * Zrodla (musza istniec lokalnie — czesc jest w .gitignore / na R2):
 *   atlas.html
 *   _atlas_v2/build_full/   (html + *_v2.json + vendor/ ; katalog obj/ jest pomijany)
 *   _atlas_v2/dist/         (*.glb Draco + *_v2.json + layers_manifest.json)
 *   _organ_compare/         (index.html + *.glb + *.json + alt/)
 *
 * Wynik:  _packaging/web/  (gitignore) — root serwowany przez Tauri / Capacitor / dowolny static server.
 */
import { promises as fs } from 'node:fs';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const OUT = path.join(HERE, 'web');
const SHARED = path.join(HERE, 'shared');
const VENDOR_EXTRA = path.join(HERE, 'vendor-extra');

let hadError = false;
function must(p) {
  if (!existsSync(p)) { console.error('  ! BRAK ZRODLA:', path.relative(ROOT, p)); hadError = true; }
  return p;
}

async function rmrf(p) {
  // Windows: serwer podglądu / indekser potrafi trzymać uchwyt do samego katalogu web/
  // (jego cwd) -> rmdir EBUSY. Czyścimy WNĘTRZE (to zwykle się udaje), a sam katalog
  // usuwamy best-effort z retry.
  let entries = [];
  try { entries = await fs.readdir(p); } catch { return; }
  for (const e of entries) {
    await fs.rm(path.join(p, e), { recursive: true, force: true, maxRetries: 8, retryDelay: 250 });
  }
  for (let i = 0; i < 4; i++) {
    try { await fs.rmdir(p); return; }
    catch { await new Promise(r => setTimeout(r, 400)); }
  }
  // katalog został (zablokowany) — jest teraz pusty, mkdir recursive to zniesie
}

async function copyTree(src, dst, skipName) {
  const st = await fs.stat(src);
  if (st.isDirectory()) {
    if (skipName && path.basename(src) === skipName) return;
    await fs.mkdir(dst, { recursive: true });
    for (const e of await fs.readdir(src)) {
      await copyTree(path.join(src, e), path.join(dst, e), skipName);
    }
  } else {
    await fs.mkdir(path.dirname(dst), { recursive: true });
    await fs.copyFile(src, dst);
  }
}

async function patch(file, fn) {
  await fs.writeFile(file, fn(await fs.readFile(file, 'utf8')));
}

function injectCommon(html) {
  if (html.includes('data-atlas-injected')) return html;
  // viewport: atlas_pilot_v3.html go nie ma i nie ma responsywnego CSS (panele na
  // sztywno 240-280px). Wymuszamy layout 980px, a skalowanie do ekranu robi:
  //  - w przegladarce: to i tak domyslne zachowanie mobilnego Chrome
  //  - w APK: MainActivity (setUseWideViewPort + setLoadWithOverviewMode, patch-android.mjs)
  // Strony z wlasnym viewportem (atlas.html, _organ_compare) zostawiamy nietkniete.
  const viewport = /<meta[^>]+name=["']viewport["']/i.test(html)
    ? ''
    : '\n<meta name="viewport" content="width=980">';
  const tag = `${viewport}
<link rel="manifest" href="/manifest.webmanifest" data-atlas-injected>
<meta name="theme-color" content="#1a1a1a">
<script src="/updater.js" defer></script>
<script>
  if ('serviceWorker' in navigator && location.protocol === 'https:' && !window.__TAURI__ && !window.Capacitor) {
    addEventListener('load', function () { navigator.serviceWorker.register('/sw.js').catch(function () {}); });
  }
  // Dotyk: menedzer okien atlasu slucha tylko mouse* -> na telefonie nie da sie
  // przeciagnac panelu za pasek tytulu. Tlumaczymy touch -> mouse tylko dla .winbar
  // (przewijanie tresci panelu i przyciski dzialaja bez zmian).
  (function () {
    var dragging = false;
    function xy(e) { var t = e.touches && e.touches[0] || e.changedTouches && e.changedTouches[0]; return t ? { x: t.clientX, y: t.clientY } : null; }
    function fire(type, p, target) {
      (target || document).dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window, clientX: p ? p.x : 0, clientY: p ? p.y : 0 }));
    }
    document.addEventListener('touchstart', function (e) {
      var bar = e.target.closest && e.target.closest('.winbar');
      if (!bar || (e.target.classList && e.target.classList.contains('wb-x'))) return;
      var p = xy(e); if (!p) return;
      dragging = true;
      fire('mousedown', p, e.target);
    }, { passive: true });
    document.addEventListener('touchmove', function (e) {
      if (!dragging) return;
      var p = xy(e); if (!p) return;
      e.preventDefault();
      fire('mousemove', p);
    }, { passive: false });
    document.addEventListener('touchend', function () {
      if (!dragging) return;
      dragging = false;
      fire('mouseup', null);
    });
  })();
</script>`;
  return html.includes('</head>') ? html.replace('</head>', tag + '\n</head>') : tag + html;
}

async function measure(dir) {
  let files = 0, bytes = 0;
  for (const e of await fs.readdir(dir, { withFileTypes: true })) {
    const fp = path.join(dir, e.name);
    if (e.isDirectory()) { const r = await measure(fp); files += r.files; bytes += r.bytes; }
    else { files++; bytes += (await fs.stat(fp)).size; }
  }
  return { files, bytes };
}

// ─────────────────────────────────────────────────────────────────────────────
const appVersion = JSON.parse(await fs.readFile(path.join(SHARED, 'app-version.json'), 'utf8'));
console.log(`\n▶ assemble atlas  v${appVersion.version} (${appVersion.channel})`);

await rmrf(OUT);
await fs.mkdir(OUT, { recursive: true });

// 1. atlas.html -> web/index.html
//    - usun stopke "Powrot do bazy pytan" (w bundlu nie ma bazy)
//    - usun sekcje "Wersja na komputer i telefon" (w zainstalowanej apce nie ma sensu;
//      w zrodle zostaje dla deployu na strone)
let entry = await fs.readFile(must(path.join(ROOT, 'atlas.html')), 'utf8');
entry = entry.replace(/<footer>[\s\S]*?<\/footer>/i, '');
entry = entry.replace(/<section class="apps">[\s\S]*?<\/section>/i, '');
const entryHtml = injectCommon(entry);
await fs.writeFile(path.join(OUT, 'index.html'), entryHtml);
// viewery linkują "wróć do trybów" jako ../atlas.html — w bundlu też musi istnieć
await fs.writeFile(path.join(OUT, 'atlas.html'), entryHtml);

// 2. _atlas_v2/build_full  (bez obj/)
await copyTree(must(path.join(ROOT, '_atlas_v2', 'build_full')), path.join(OUT, '_atlas_v2', 'build_full'), 'obj');

// 3. _atlas_v2/dist
await copyTree(must(path.join(ROOT, '_atlas_v2', 'dist')), path.join(OUT, '_atlas_v2', 'dist'));

// 4. _organ_compare  (cale, z alt/)
await copyTree(must(path.join(ROOT, '_organ_compare')), path.join(OUT, '_organ_compare'));

if (hadError) {
  console.error('\n✖ przerwano — uzupelnij brakujace zrodla (patrz wyzej).\n');
  process.exit(1);
}

// 5. vendor three dla _organ_compare  (kopia z build_full/vendor + brakujacy RoomEnvironment)
const ocVendor = path.join(OUT, '_organ_compare', 'vendor');
await copyTree(path.join(OUT, '_atlas_v2', 'build_full', 'vendor'), ocVendor);
await fs.mkdir(path.join(ocVendor, 'addons', 'environments'), { recursive: true });
await fs.copyFile(
  must(path.join(VENDOR_EXTRA, 'RoomEnvironment.js')),
  path.join(ocVendor, 'addons', 'environments', 'RoomEnvironment.js')
);

// 6. patch _organ_compare/index.html  (importmap CDN unpkg -> lokalny ./vendor/) + wspolne wstrzykniecia
await patch(path.join(OUT, '_organ_compare', 'index.html'), (html) => {
  // Sciezki ABSOLUTNE (nie ./) — odporne na brak ukosnika konczacego / clean-URL
  // redirecty statycznych serwerow. W Tauri/Capacitor root bundla == '/'.
  html = html
    .replace(/"three":\s*"https:\/\/unpkg\.com[^"]*"/, '"three": "/_organ_compare/vendor/three.module.js"')
    .replace(/"three\/addons\/":\s*"https:\/\/unpkg\.com[^"]*"/, '"three/addons/": "/_organ_compare/vendor/addons/"');
  if (/https:\/\/unpkg\.com|https:\/\/cdn\.|esm\.sh/.test(html)) {
    console.warn('  ! _organ_compare/index.html nadal ma odwolanie do CDN — sprawdz recznie');
  }
  return injectCommon(html);
});

// 7. patch _atlas_v2/build_full/atlas_pilot_v3.html  (wspolne wstrzykniecia)
await patch(path.join(OUT, '_atlas_v2', 'build_full', 'atlas_pilot_v3.html'), injectCommon);

// 8. pliki wspolne w root bundla
for (const f of ['updater.js', 'manifest.webmanifest', 'sw.js']) {
  await fs.copyFile(path.join(SHARED, f), path.join(OUT, f));
}
await fs.writeFile(path.join(OUT, 'app-version.json'), JSON.stringify({
  ...appVersion,
  built_at: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
}, null, 2) + '\n');

// 9. ikony PWA — z shared/icons/ jesli sa, inaczej placeholder z brand-assets (zla rozdzielczosc, ale dziala)
await fs.mkdir(path.join(OUT, 'icons'), { recursive: true });
const iconSrcDir = path.join(SHARED, 'icons');
for (const [name, fallback] of [['icon-192.png', 'favicon-180.png'], ['icon-512.png', 'favicon-180.png']]) {
  const real = path.join(iconSrcDir, name);
  if (existsSync(real)) {
    await fs.copyFile(real, path.join(OUT, 'icons', name));
  } else {
    const fb = path.join(ROOT, 'brand-assets', fallback);
    if (existsSync(fb)) {
      await fs.copyFile(fb, path.join(OUT, 'icons', name));
      console.warn(`  ! icons/${name}: placeholder z brand-assets/${fallback} — podmien na wlasciwy rozmiar`);
    }
  }
}

const { files, bytes } = await measure(OUT);
console.log(`\n✔ bundle gotowy: ${path.relative(ROOT, OUT)}`);
console.log(`  ${files} plikow · ${(bytes / 1048576).toFixed(1)} MB`);
console.log(`  wersja ${appVersion.version} · endpoint aktualizacji: ${appVersion.update_manifest_url}\n`);
