# Pack per-layer .obj files -> one .glb per layer (node name = structure id).
# Then gltf-transform draco-compresses them.  Output: dist/
import json, os, glob, io, numpy as np, trimesh, subprocess, collections

SRC   = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\build_full"
OBJD  = SRC + r"\obj"
DIST  = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\dist"
os.makedirs(DIST, exist_ok=True)

KMAP = {"bones":"all_bones_labeled_v2.json", "teeth":"all_teeth_labeled_v2.json",
        "muscles":"all_muscles_labeled_v2.json", "connective":"all_connective_labeled_v2.json",
        "vessels":"all_vessels_labeled_v2.json", "nerves":"all_nerves_labeled_v2.json",
        "brain":"all_brain_labeled_v2.json", "organs":"all_organs_labeled_v2.json",
        "lymph":"all_lymph_labeled_v2.json"}

def load_obj(p):
    V=[]; F=[]
    with open(p, encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("v "):
                _,x,y,z = ln.split(); V.append((float(x),float(y),float(z)))
            elif ln.startswith("f "):
                a=[int(t.split("/")[0])-1 for t in ln.split()[1:]]
                for k in range(1,len(a)-1): F.append((a[0],a[k],a[k+1]))
    return np.array(V,float), np.array(F,int)

manifest = {}
for layer, jf in KMAP.items():
    path = os.path.join(SRC, jf)
    if not os.path.exists(path): continue
    rows = json.load(open(path, encoding="utf-8"))
    scene = trimesh.Scene()
    n = 0
    for r in rows:
        op = os.path.join(OBJD, r["id"] + ".obj")
        if not os.path.exists(op): continue
        V, F = load_obj(op)
        if len(V) == 0 or len(F) == 0: continue
        m = trimesh.Trimesh(vertices=V, faces=F, process=False)
        scene.add_geometry(m, geom_name=r["id"], node_name=r["id"])
        n += 1
    raw = os.path.join(DIST, f"{layer}.raw.glb")
    scene.export(raw)
    manifest[layer] = {"structures": n, "raw_mb": round(os.path.getsize(raw)/1e6, 1)}
    print(f"{layer:11} {n:4} structures  {manifest[layer]['raw_mb']} MB raw")

# ---- draco compress ----
print("\n-- draco compression --")
for layer in KMAP:
    raw = os.path.join(DIST, f"{layer}.raw.glb")
    if not os.path.exists(raw): continue
    out = os.path.join(DIST, f"{layer}.glb")
    r = subprocess.run(["npx","--yes","@gltf-transform/cli","draco", raw, out,
                        "--method","edgebreaker","--quantize-position","14","--quantize-normal","8"],
                       capture_output=True, text=True, shell=True)
    if os.path.exists(out):
        mb = round(os.path.getsize(out)/1e6, 2)
        manifest[layer]["glb_mb"] = mb
        os.remove(raw)
        print(f"  {layer:11} -> {mb} MB")
    else:
        print(f"  {layer} FAILED\n{r.stderr[-400:]}")

# ---- copy the small JSON catalogues + landmarks + szpilki ----
for f in glob.glob(os.path.join(SRC, "all_*_labeled_v2.json")) + \
         [os.path.join(SRC, x) for x in ("bone_landmarks_v2.json","szpilki_map_v2.json","szpilki_todo_v2.json","notatki_wykladowe.json")]:
    if os.path.exists(f):
        import shutil; shutil.copy(f, DIST)

json.dump(manifest, io.open(os.path.join(DIST, "layers_manifest.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
tot = sum(m.get("glb_mb", 0) for m in manifest.values())
print(f"\nTOTAL compressed geometry: {round(tot,1)} MB across {len(manifest)} layers")
print("dist/:", sorted(os.listdir(DIST)))
