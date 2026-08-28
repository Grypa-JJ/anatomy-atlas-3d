#!/usr/bin/env node
/* Zapewnia obecnosc ciezkich assetow atlasu (GLB/CT/NIH) przed assemble.mjs.
 *
 * WAZNE: to jest krok BUILD-TIME, nie runtime. Gotowy .exe/.apk ma wszystkie assety
 * w srodku i dziala w 100% offline — nic nie pobiera po instalacji.
 *
 * Kolejnosc szukania:
 *   1. assety juz na dysku (build lokalny — Ty je masz)          -> NIC nie robi
 *   2. lokalny pakiet _packaging/atlas-assets.tar.gz (z pack-assets.mjs) -> rozpakowuje
 *   3. $ATLAS_ASSETS_URL (CI: GitHub Release albo R2)             -> pobiera + rozpakowuje
 *   4. brak wszystkiego                                           -> blad z instrukcja
 *
 * Opcjonalnie $ATLAS_ASSETS_SHA256 do weryfikacji pobranego pliku.
 */
import { spawnSync } from 'node:child_process';
import { promises as fs } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');

const SENTINELS = [
  '_atlas_v2/dist/bones.glb',
  '_organ_compare/visceral.glb',
  '_organ_compare/alt/visceral_ct.glb',
];

async function present(p) { try { await fs.access(path.join(ROOT, p)); return true; } catch { return false; } }

async function unpack(file, cleanup) {
  console.log('  rozpakowuje', path.relative(ROOT, file), '->', path.relative(ROOT, ROOT) || '.');
  const r = spawnSync('tar', ['-xzf', file, '-C', ROOT], { stdio: 'inherit' });
  if (cleanup) await fs.rm(file, { force: true });
  if (r.status !== 0) process.exit(r.status || 1);
}

// 1. juz sa
if ((await Promise.all(SENTINELS.map(present))).every(Boolean)) {
  console.log('fetch-assets: assety obecne — pomijam (build lokalny).');
  process.exit(0);
}

// 2. lokalny pakiet z pack-assets.mjs
const localPack = path.join(HERE, 'atlas-assets.tar.gz');
if (await present(path.relative(ROOT, localPack))) {
  console.log('fetch-assets: rozpakowuje lokalny atlas-assets.tar.gz');
  await unpack(localPack, false);
} else {
  // 3. pobierz
  const url = process.env.ATLAS_ASSETS_URL;
  if (!url) {
    console.error([
      'fetch-assets: brak ciezkich assetow (GLB/CT/NIH).',
      '',
      '  Build LOKALNY: powinienes miec je na dysku (_atlas_v2/dist/, _organ_compare/alt/ ...).',
      '                 Jesli nie — odtworz je z .blend (patrz atlas-v3-zanatomy-build) albo',
      '                 rozpakuj wlasny  _packaging/atlas-assets.tar.gz  (node pack-assets.mjs).',
      '  Build w CI:     ustaw ATLAS_ASSETS_URL na paczke .tar.gz w GitHub Release lub R2.',
    ].join('\n'));
    process.exit(1);
  }
  const tmp = path.join(HERE, '.atlas-assets.download.tar.gz');
  console.log('fetch-assets: pobieram', url);
  const res = await fetch(url);
  if (!res.ok) { console.error('  HTTP', res.status); process.exit(1); }
  const buf = Buffer.from(await res.arrayBuffer());
  await fs.writeFile(tmp, buf);
  if (process.env.ATLAS_ASSETS_SHA256) {
    const got = createHash('sha256').update(buf).digest('hex');
    if (got !== process.env.ATLAS_ASSETS_SHA256) {
      console.error('  sha256 nie zgadza sie!\n  oczekiwano', process.env.ATLAS_ASSETS_SHA256, '\n  jest      ', got);
      process.exit(1);
    }
  }
  await unpack(tmp, true);
}

if (!(await Promise.all(SENTINELS.map(present))).every(Boolean)) {
  console.error('  po rozpakowaniu nadal brak plikow-wartownikow — zly pakiet?');
  process.exit(1);
}
console.log('fetch-assets: OK');
