#!/usr/bin/env bash
# Upload assetów atlasu 3D na Cloudflare R2 (bucket "gielda-obrazki", prefiks atlas/).
# Sekrety WYŁĄCZNIE ze zmiennych środowiskowych — nic nie jest zapisywane w repo.
#
#   export CF_ACCOUNT_ID=...          # ID konta Cloudflare
#   export CF_AUTH_EMAIL=...          # e-mail konta
#   export CF_GLOBAL_API_KEY=...      # Global API Key  (albo użyj tokena scoped R2 — patrz niżej)
#   bash _atlas_v2/r2_upload_atlas.sh            # batch 1: atlas + narządy bez MPR (~62 plików)
#   bash _atlas_v2/r2_upload_atlas.sh mpr        # batch 2: przekroje CT/MPR (~1720 plików)
#   bash _atlas_v2/r2_upload_atlas.sh all        # wszystko
#
# Zamiast Global API Key można użyć tokena R2 S3 (bezpieczniejsze):
#   export CF_R2_S3=1 CF_R2_ACCESS_KEY_ID=... CF_R2_SECRET_ACCESS_KEY=...
#   (wtedy skrypt użyje `aws s3` jeśli dostępne, endpoint R2)
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/r2_upload/atlas"
BUCKET="${CF_R2_BUCKET:-gielda-obrazki}"
PUBLIC="https://pub-75514e92552347ccbcdab6bfacd153fd.r2.dev/atlas"
MODE="${1:-batch1}"

: "${CF_ACCOUNT_ID:?ustaw CF_ACCOUNT_ID}"
: "${CF_AUTH_EMAIL:?ustaw CF_AUTH_EMAIL}"
: "${CF_GLOBAL_API_KEY:?ustaw CF_GLOBAL_API_KEY}"

API="https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/r2/buckets/$BUCKET/objects"

ctype() { case "$1" in
  *.glb) echo "model/gltf-binary";; *.json) echo "application/json";;
  *.png) echo "image/png";; *.jpg|*.jpeg) echo "image/jpeg";; *) echo "application/octet-stream";; esac; }

put() {  # $1 = ścieżka lokalna względem $SRC  (np. v3/bones.glb)
  local rel="$1" f="$SRC/$1"
  [ -f "$f" ] || { echo "  ! brak $rel"; return 1; }
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' -X PUT "$API/atlas/$rel" \
    -H "X-Auth-Email: $CF_AUTH_EMAIL" -H "X-Auth-Key: $CF_GLOBAL_API_KEY" \
    -H "Content-Type: $(ctype "$rel")" --data-binary "@$f")
  case "$code" in 200|201) echo "  ok  atlas/$rel";; *) echo "  FAIL $code atlas/$rel"; return 1;; esac
}

list_batch1() {
  ( cd "$SRC" && \
    ls v3/*.glb && \
    echo narzady/visceral.glb && \
    ( cd narzady && ls *.glb *.json alt/*.glb alt/*.json alt/nih/* 2>/dev/null | sed 's#^#narzady/#' ) )
}
list_mpr() { ( cd "$SRC/narzady" && find alt/mpr -type f | sed 's#^#narzady/#' ); }

case "$MODE" in
  batch1) mapfile -t FILES < <(list_batch1);;
  mpr)    mapfile -t FILES < <(list_mpr);;
  all)    mapfile -t FILES < <(list_batch1; list_mpr);;
  *) echo "użycie: $0 [batch1|mpr|all]"; exit 2;;
esac

echo "▶ upload ${#FILES[@]} plików do R2 ($BUCKET, prefiks atlas/)  tryb=$MODE"
ok=0; fail=0
for rel in "${FILES[@]}"; do
  [ -z "$rel" ] && continue
  if put "$rel"; then ok=$((ok+1)); else fail=$((fail+1)); fi
done
echo "─────────────────────────────"
echo "gotowe: $ok OK, $fail błędów"
echo "weryfikacja: curl -sI $PUBLIC/v3/bones.glb | head -1"
[ "$fail" -eq 0 ]
