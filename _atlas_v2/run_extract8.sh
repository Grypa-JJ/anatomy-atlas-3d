#!/usr/bin/env bash
cd "C:/Users/Jakub/Desktop/Prod/projekt w budowie/_atlas_v2"
BL="./blender_app/blender-3.6.23-windows-x64/blender.exe"
BLEND="src/Z-Anatomy/Startup.blend"
TOTAL=5520
BATCH=200
mkdir -p blend_dump8
start=0
while [ $start -lt $TOTAL ]; do
  echo "=== batch start=$start ==="
  "$BL" --background "$BLEND" --python blend_extract8.py -- $start $BATCH > "blend_dump8/log_$start.txt" 2>&1
  # how many objs actually written in this batch's obj dir range?
  meta="blend_dump8/objects_$start.json"
  if grep -q "BATCHDONE $start" "blend_dump8/log_$start.txt"; then
    n=$(grep -oE '"gi": [0-9]+' "$meta" 2>/dev/null | tail -1 | grep -oE '[0-9]+')
    echo "  batch ok, last gi=$n"
    start=$((start+BATCH))
  else
    # crashed — resume just past the last written obj
    lastobj=$(ls blend_dump8/obj/*.obj 2>/dev/null | sed 's/.*\///;s/\.obj//' | sort -n | tail -1)
    crashline=$(grep "CRASHOBJ" "blend_dump8/log_$start.txt" | tail -1)
    echo "  CRASH. last obj file=$lastobj  $crashline"
    if [ -n "$lastobj" ] && [ "$lastobj" -ge "$start" ]; then
      start=$((lastobj+2))   # skip the crashing object
    else
      start=$((start+1))
    fi
  fi
done
echo "ALL_BATCHES_DONE"
# merge
python - <<'EOF'
import json,glob,io
allm=[]
for f in sorted(glob.glob(r'blend_dump8\objects_*.json')):
    try: allm += json.load(open(f,encoding='utf-8'))
    except Exception: pass
seen=set(); out=[]
for m in allm:
    if m['gi'] in seen: continue
    seen.add(m['gi']); out.append(m)
json.dump(out, io.open(r'blend_dump8\objects.json','w',encoding='utf-8'), ensure_ascii=False)
print("MERGED", len(out), "objects")
EOF
