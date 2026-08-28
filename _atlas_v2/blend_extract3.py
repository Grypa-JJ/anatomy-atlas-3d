# Robust geometry dump from full Z-Anatomy .blend — NO depsgraph (it crashes here).
# MESH: base mesh data + matrix_world.   CURVE: to_mesh() in try/except.
#   blender.exe --background "Startup.blend" --python blend_extract3.py
import bpy, json, os, io, traceback

OUT  = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\blend_dump3"
OBJD = OUT + r"\obj"
os.makedirs(OBJD, exist_ok=True)

# ---- object -> collection paths ----
obj_paths = {}
def walk(coll, path):
    p = path + [coll.name]
    for o in coll.objects:
        obj_paths.setdefault(o.name, []).append("/".join(p[1:]))
    for c in coll.children:
        walk(c, p)
walk(bpy.context.scene.collection, [])

SYS = ("1: Skeletal system", "2: Muscular insertions", "3: Joints", "4: Muscular system",
       "5: Cardiovascular system", "6: Lymphoid organs", "7: Nervous system & Sense organs",
       "8: Visceral systems", "9: Regions of human body")
def system_of(paths):
    for p in paths:
        if p.split("/")[0] in SYS:
            return p.split("/")[0]
    return None
def bonus_path(paths):
    b = sorted((p for p in paths if p.startswith("Bonus collection/")), key=len, reverse=True)
    return b[0][len("Bonus collection/"):] if b else None

def write_obj(path, verts, faces):
    with io.open(path, "w", encoding="utf-8") as f:
        f.write("".join(f"v {v[0]:.5f} {v[1]:.5f} {v[2]:.5f}\n" for v in verts))
        f.write("".join("f " + " ".join(str(i+1) for i in tri) + "\n" for tri in faces))

def tri_faces(polys):
    out = []
    for p in polys:
        vs = list(p.vertices)
        for k in range(1, len(vs)-1):
            out.append((vs[0], vs[k], vs[k+1]))
    return out

meta, labels = [], []
idx = skipped = 0

def flush():
    json.dump(meta, io.open(os.path.join(OUT, "objects.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(labels, io.open(os.path.join(OUT, "labels.json"), "w", encoding="utf-8"), ensure_ascii=False)

for o in bpy.data.objects:
    paths = obj_paths.get(o.name, [])
    try:
        if o.type == "FONT":
            wl = o.matrix_world.translation
            labels.append({"name": o.name, "body": (getattr(o.data, "body", "") or "").strip(),
                           "pos": [round(wl.x,5), round(wl.y,5), round(wl.z,5)],
                           "system": system_of(paths), "path": bonus_path(paths)})
            continue
        if o.type == "MESH":
            me = o.data
            if not me.vertices:
                skipped += 1; continue
            mw = o.matrix_world
            verts = [tuple(mw @ v.co) for v in me.vertices]
            faces = tri_faces(me.polygons)
            tmp = False
        elif o.type == "CURVE":
            try:
                me = o.to_mesh()
            except Exception:
                skipped += 1; continue
            if me is None or not me.vertices:
                try: o.to_mesh_clear()
                except Exception: pass
                skipped += 1; continue
            mw = o.matrix_world
            verts = [tuple(mw @ v.co) for v in me.vertices]
            faces = tri_faces(me.polygons)
            tmp = True
        else:
            continue

        xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
        write_obj(os.path.join(OBJD, f"{idx}.obj"), verts, faces)
        meta.append({"idx": idx, "name": o.name, "type": o.type,
                     "nverts": len(verts), "nfaces": len(faces),
                     "system": system_of(paths), "path": bonus_path(paths), "all_paths": paths,
                     "wbbox_min": [round(min(xs),4), round(min(ys),4), round(min(zs),4)],
                     "wbbox_max": [round(max(xs),4), round(max(ys),4), round(max(zs),4)],
                     "wcentroid": [round((min(xs)+max(xs))/2,4), round((min(ys)+max(ys))/2,4), round((min(zs)+max(zs))/2,4)]})
        idx += 1
        if tmp:
            try: o.to_mesh_clear()
            except Exception: pass
        if idx % 300 == 0:
            print("PROGRESS", idx); flush()
    except Exception:
        skipped += 1
        print("ERR", o.name); traceback.print_exc()

flush()
print("DONE", idx, "written,", skipped, "skipped,", len(labels), "labels")
