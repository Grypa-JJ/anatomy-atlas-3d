#!/usr/bin/env node
/* _atlas_v2/stage_netlify.mjs
 * Wstawia atlas 3D (całe ciało v3 + przeglądarkę narządów) do folderu deployu
 * Netlify `netlify_deploy/`. Duże binaria (*.glb, alt/) NIE trafiają tu —
 * są hostowane na R2 (patrz GLB_BASE / R2_ORGAN_BASE w plikach viewerów).
 *
 *   node _atlas_v2/stage_netlify.mjs
 *
 * Po tym: mirror pozostałych plików roota do netlify_deploy/ jak zwykle i deploy.
 */
import { promises as fs } from 'node:fs';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, 'netlify_deploy');

async function copyTree(src, dst, skip = () => false) {
  const st = await fs.stat(src);
  if (st.isDirectory()) {
    if (skip(src)) return;
    await fs.mkdir(dst, { recursive: true });
    for (const e of await fs.readdir(src)) await copyTree(path.join(src, e), path.join(dst, e), skip);
  } else {
    if (skip(src)) return;
    await fs.mkdir(path.dirname(dst), { recursive: true });
    await fs.copyFile(src, dst);
  }
}
const rel = (p) => path.relative(ROOT, p);
async function size(dir) {
  let b = 0, n = 0;
  for (const e of await fs.readdir(dir, { withFileTypes: true })) {
    const fp = path.join(dir, e.name);
    if (e.isDirectory()) { const r = await size(fp); b += r.b; n += r.n; }
    else { b += (await fs.stat(fp)).size; n++; }
  }
  return { b, n };
}

if (!existsSync(OUT)) { console.error('! brak netlify_deploy/ — najpierw odtwórz mirror roota'); process.exit(1); }

// 1. ekran startowy
await fs.copyFile(path.join(ROOT, 'atlas.html'), path.join(OUT, 'atlas.html'));
console.log('  ✔ atlas.html');

// 2. atlas v3 — html + katalogi *_v2.json + vendor/ ; BEZ obj/ i BEZ *.glb
const bfSkip = (p) => {
  const b = path.basename(p);
  return b === 'obj' || p.endsWith('.glb') || b.startsWith('_') && b.endsWith('.log');
};
await copyTree(path.join(ROOT, '_atlas_v2', 'build_full'), path.join(OUT, '_atlas_v2', 'build_full'), bfSkip);
console.log('  ✔ _atlas_v2/build_full/  (bez obj/, bez glb)');

// 3. dist — tylko katalogi JSON + manifest (GLB są na R2)
await fs.mkdir(path.join(OUT, '_atlas_v2', 'dist'), { recursive: true });
for (const f of await fs.readdir(path.join(ROOT, '_atlas_v2', 'dist'))) {
  if (f.endsWith('.glb')) continue;
  await fs.copyFile(path.join(ROOT, '_atlas_v2', 'dist', f), path.join(OUT, '_atlas_v2', 'dist', f));
}
console.log('  ✔ _atlas_v2/dist/  (tylko JSON)');

// 4. przeglądarka narządów — html + manifesty + vendor ; BEZ *.glb, BEZ alt/
const ocSkip = (p) => {
  const b = path.basename(p);
  return b === 'alt' || p.endsWith('.glb') || b === '_preview.png';
};
await copyTree(path.join(ROOT, '_organ_compare'), path.join(OUT, '_organ_compare'), ocSkip);
// vendor three dla organ-compare (jak w assemble.mjs — kopia z build_full/vendor)
await copyTree(path.join(OUT, '_atlas_v2', 'build_full', 'vendor'), path.join(OUT, '_organ_compare', 'vendor'));
const roomEnv = path.join(ROOT, '_packaging', 'vendor-extra', 'RoomEnvironment.js');
if (existsSync(roomEnv)) {
  await fs.mkdir(path.join(OUT, '_organ_compare', 'vendor', 'addons', 'environments'), { recursive: true });
  await fs.copyFile(roomEnv, path.join(OUT, '_organ_compare', 'vendor', 'addons', 'environments', 'RoomEnvironment.js'));
}
// patch importmap organ-compare: CDN unpkg -> lokalny ./vendor/
const ocIndex = path.join(OUT, '_organ_compare', 'index.html');
let ocHtml = await fs.readFile(ocIndex, 'utf8');
ocHtml = ocHtml
  .replace(/"three":\s*"https:\/\/unpkg\.com[^"]*"/, '"three": "./vendor/three.module.js"')
  .replace(/"three\/addons\/":\s*"https:\/\/unpkg\.com[^"]*"/, '"three/addons/": "./vendor/addons/"');
await fs.writeFile(ocIndex, ocHtml);
console.log('  ✔ _organ_compare/  (bez glb/alt, vendor lokalny, importmap→vendor)');

// 5. index.html z roota (zawiera kafelek Atlas 3D w anatomii)
await fs.copyFile(path.join(ROOT, 'index.html'), path.join(OUT, 'index.html'));
console.log('  ✔ index.html  (mirror roota z kafelkiem atlasu)');

// 6. nagłówki: .glb hostowane na R2, ale draco .wasm serwuje Netlify
const headers = `# atlas 3D — typy MIME dla vendored three.js / draco
/_atlas_v2/build_full/vendor/*
  Cache-Control: public, max-age=31536000, immutable
/_organ_compare/vendor/*
  Cache-Control: public, max-age=31536000, immutable
/*.wasm
  Content-Type: application/wasm
`;
const hp = path.join(OUT, '_headers');
let existing = existsSync(hp) ? await fs.readFile(hp, 'utf8') : '';
if (!existing.includes('atlas 3D')) await fs.writeFile(hp, existing + (existing ? '\n' : '') + headers);
console.log('  ✔ _headers');

const s = await size(path.join(OUT, '_atlas_v2'));
const o = await size(path.join(OUT, '_organ_compare'));
console.log(`\n  netlify_deploy/_atlas_v2      ${(s.b / 1048576).toFixed(1)} MB / ${s.n} plików`);
console.log(`  netlify_deploy/_organ_compare ${(o.b / 1048576).toFixed(1)} MB / ${o.n} plików`);
console.log('\n  gotowe — deploy netlify_deploy/  (GLB lecą z R2, patrz r2_upload_atlas.sh)\n');
