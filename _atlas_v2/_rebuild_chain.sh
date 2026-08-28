#!/usr/bin/env bash
# po build_full.py: pack_glb -> remap szpilek -> stage netlify. Odpalane ręcznie.
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
echo "== pack_glb =="
/c/Python311/python pack_glb.py 2>&1 | grep -E 'MB|TOTAL|FAILED|dist/:'
echo "== remap szpilek =="
/c/Python311/python remap_szpilki_full.py 2>&1 | tail -4
echo "== stage netlify =="
node stage_netlify.mjs 2>&1 | tail -6
echo "== gotowe =="
