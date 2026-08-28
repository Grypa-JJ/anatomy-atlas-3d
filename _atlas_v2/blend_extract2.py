# Direct geometry dump from the full Z-Anatomy .blend (no glTF exporter — it mis-handled selection).
#   blender.exe --background "Startup.blend" --python blend_extract2.py
# Writes:  blend_dump2/obj/<idx>.obj  (world-space, modifiers applied; meshes + curves)
#          blend_dump2/objects.json   (per-object metadata incl. system + hierarchy path)
#          blend_dump2/labels.json    (FONT annotation anchors: name + world pos)
import bpy, json, os, io

OUT = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\blend_dump2"
OBJD = OUT + r"\obj"
os.makedirs(OBJD, exist_ok=True)

depsgraph = bpy.context.evaluated_depsgraph_get()

# ---- object -> collection paths ----
obj_paths = {}
def walk(coll, path):
    p = path + [coll.name]
    for o in coll.objects:
        obj_paths.setdefault(o.name, []).append("/".join(p[1:]))  # drop "Scene Collection"
    for c in coll.children:
        walk(c, p)
walk(bpy.context.scene.collection, [])

SYS_PREFIX = ("1: Skeletal system", "2: Muscular insertions", "3: Joints", "4: Muscular system",
              "5: Cardiovascular system", "6: Lymphoid organs", "7: Nervous system & Sense organs",
              "8: Visceral systems", "9: Regions of human body")
def system_of(paths):
    for p in paths:
        head = p.split("/")[0]
        if head in SYS_PREFIX:
            return head
    return None
def bonus_path(paths):
    b = [p for p in paths if p.startswith("Bonus collection/")]
    b.sort(key=len, reverse=True)          # deepest = most specific
    return b[0][len("Bonus collection/"):] if b else None

def write_obj(path, verts, faces):
    with io.open(path, "w", encoding="utf-8") as f:
        for v in verts:
            f.write(f"v {v[0]:.5f} {v[1]:.5f} {v[2]:.5f}\n")
        for tri in faces:
            f.write("f " + " ".join(str(i + 1) for i in tri) + "\n")

meta = []
labels = []
idx = 0
skipped = 0
for o in bpy.data.objects:
    paths = obj_paths.get(o.name, [])
    if o.type == "FONT":
        wl = o.matrix_world.translation
        labels.append({"name": o.name, "body": (o.data.body or "").strip(),
                       "pos": [round(wl.x, 5), round(wl.y, 5), round(wl.z, 5)],
                       "system": system_of(paths), "path": bonus_path(paths)})
        continue
    if o.type not in ("MESH", "CURVE"):
        continue
    try:
        oe = o.evaluated_get(depsgraph)
        me = oe.to_mesh()
    except Exception as e:
        skipped += 1
        continue
    if me is None or len(me.vertices) == 0:
        try: oe.to_mesh_clear()
        except Exception: pass
        skipped += 1
        continue
    mw = o.matrix_world
    verts = [(mw @ v.co)[:] for v in me.vertices]
    faces = []
    for poly in me.polygons:
        vs = list(poly.vertices)
        for k in range(1, len(vs) - 1):          # fan triangulation
            faces.append((vs[0], vs[k], vs[k + 1]))
    xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
    write_obj(os.path.join(OBJD, f"{idx}.obj"), verts, faces)
    meta.append({
        "idx": idx, "name": o.name, "type": o.type,
        "nverts": len(verts), "nfaces": len(faces),
        "system": system_of(paths), "path": bonus_path(paths), "all_paths": paths,
        "wbbox_min": [round(min(xs), 4), round(min(ys), 4), round(min(zs), 4)],
        "wbbox_max": [round(max(xs), 4), round(max(ys), 4), round(max(zs), 4)],
        "wcentroid": [round((min(xs)+max(xs))/2, 4), round((min(ys)+max(ys))/2, 4), round((min(zs)+max(zs))/2, 4)],
    })
    idx += 1
    try: oe.to_mesh_clear()
    except Exception: pass
    if idx % 500 == 0:
        print("PROGRESS", idx)

json.dump(meta, io.open(os.path.join(OUT, "objects.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(labels, io.open(os.path.join(OUT, "labels.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE", idx, "objects written,", skipped, "skipped,", len(labels), "labels")
