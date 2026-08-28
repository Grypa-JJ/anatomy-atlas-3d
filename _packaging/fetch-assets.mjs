#!/usr/bin/env node
/* Pobiera i rozpakowuje ciezkie assety atlasu przed assemble.mjs.
 * Uzywane w CI (gdzie po `git clone` brakuje GLB/CT/NIH). Lokalnie zwykle NIC nie robi —
 * jesli assety juz sa, konczy sie od razu.
 *
 *   ATLAS_ASSETS_URL=https://<bucket>.r2.dev/atlas/assets/atlas-assets-XXXX.tar.gz  node _packaging/fetch-assets.mjs
 *
 * Opcjonalnie ATLAS_ASSETS_SHA256 do weryfikacji.
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

if ((await Promise.all(SENTINELS.map(present))).every(Boolean)) {
  console.log('fetch-assets: assety obecne — pomijam.');
  process.exit(0);
}

const url = process.env.ATLAS_ASSETS_URL;
if (!url) {
  console.error('fetch-assets: brak assetow i brak ATLAS_ASSETS_URL. Ustaw zmienna albo skopiuj assety recznie.');
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

console.log('  rozpakowuje ->', ROOT);
const r = spawnSync('tar', ['-xzf', tmp, '-C', ROOT], { stdio: 'inherit' });
await fs.rm(tmp, { force: true });
if (r.status !== 0) process.exit(r.status || 1);

if (!(await Promise.all(SENTINELS.map(present))).every(Boolean)) {
  console.error('  po rozpakowaniu nadal brak plikow-wartownikow — zly pakiet?');
  process.exit(1);
}
console.log('fetch-assets: OK');
