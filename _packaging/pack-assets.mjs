#!/usr/bin/env node
/* Pakuje ciezkie assety atlasu (GLB, CT, NIH — to, czego brakuje po samym `git clone`,
 * bo sa w .gitignore) w jeden plik  _packaging/atlas-assets.tar.gz.
 *
 *   node _packaging/pack-assets.mjs
 *
 * Do czego to sluzy: build w CI (`git clone` nie ma GLB — sa w .gitignore).
 * Build lokalny tego NIE potrzebuje — masz assety na dysku.
 * NIE ma zwiazku z runtime: gotowy .exe/.apk i tak niesie wszystkie assety w sobie.
 *
 * Gdzie wgrac (wybierz jedno, oba za darmo, bez limitu transferu):
 *   A) GitHub Release:  gh release create atlas-assets _packaging/atlas-assets.tar.gz --notes "assety atlasu"
 *      URL:  https://github.com/Grypa-JJ/medstudy/releases/download/atlas-assets/atlas-assets.tar.gz
 *   B) Cloudflare R2:   atlas/assets/atlas-assets-<hash>.tar.gz
 * Ten URL -> secret CI  ATLAS_ASSETS_URL  (+ opcjonalnie ATLAS_ASSETS_SHA256 z pliku obok).
 */
import { spawnSync } from 'node:child_process';
import { promises as fs } from 'node:fs';
import { createHash } from 'node:crypto';
import { createReadStream } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const OUT = path.join(HERE, 'atlas-assets.tar.gz');

// wzgledne do ROOT — to, czego assemble.mjs potrzebuje a git nie ma
const PATHS = [
  '_atlas_v2/dist',
  '_organ_compare/alt',
  '_organ_compare/visceral.glb',
  '_organ_compare/visceral_manifest.json',
];

for (const p of PATHS) {
  try { await fs.access(path.join(ROOT, p)); }
  catch { console.error('BRAK:', p, '- uruchom najpierw build GLB (patrz atlas-v3-zanatomy-build)'); process.exit(1); }
}

console.log('pakowanie', PATHS.length, 'sciezek ->', path.relative(ROOT, OUT));
const r = spawnSync('tar', ['-czf', OUT, '-C', ROOT, ...PATHS], { stdio: 'inherit' });
if (r.status !== 0) process.exit(r.status || 1);

const hash = createHash('sha256');
await new Promise((res, rej) => createReadStream(OUT).on('data', d => hash.update(d)).on('end', res).on('error', rej));
const sha = hash.digest('hex');
const { size } = await fs.stat(OUT);

await fs.writeFile(path.join(HERE, 'atlas-assets.sha256'), sha + '\n');
console.log(`\n✔ ${path.relative(ROOT, OUT)}  ${(size / 1048576).toFixed(1)} MB`);
console.log(`  sha256 ${sha}`);
console.log(`\n  najprosciej (GitHub Release, bez R2):`);
console.log(`    gh release create atlas-assets _packaging/atlas-assets.tar.gz --notes "assety atlasu (build-time)"`);
console.log(`  potem secret ATLAS_ASSETS_URL =`);
console.log(`    https://github.com/Grypa-JJ/medstudy/releases/download/atlas-assets/atlas-assets.tar.gz`);
