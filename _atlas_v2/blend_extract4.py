# Minimal, crash-safe geometry dump. MESH only, base data, no depsgraph, no RNA string reads
# beyond o.name.  blender.exe --background "Startup.blend" --python blend_extract4.py
import bpy, json, os, io, traceback

OUT  = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\blend_dump3"
OBJD = OUT + r"\obj"
os.makedirs(OBJD, exist_ok=True)

obj_paths = {}
def walk(coll, path):
    p = path + [coll.name]
    for o in coll.objects:
        obj_paths.setdefault(o.name, []).append("/".join(p[1:]))
    for c in coll.children:
        walk(c, p)
walk(bpy.context.scene.collection, [])
SYS = ("1: Skeletal system","2: Muscular insertions","3: Joints","4: Muscular system",
       "5: Cardiovascular system","6: Lymphoid organs","7: Nervous system & Sense organs",
       "8: Visceral systems","9: Regions of human body")
def system_of(ps):
    for p in ps:
        if p.split("/")[0] in SYS: return p.split("/")[0]
    return None
def bonus_path(ps):
    b = sorted((p for p in ps if p.startswith("Bonus collection/")), key=len, reverse=True)
    return b[0][17:] if b else None

meta = []
idx = skipped = 0
mesh_objs = [o for o in bpy.data.objects if o.type == "MESH"]
print("MESH_COUNT", len(mesh_objs))

for o in mesh_objs:
    try:
        me = o.data
        nv = len(me.vertices)
        if nv == 0:
            skipped += 1; continue
        mw = o.matrix_world
        lines = []
        for v in me.vertices:
            w = mw @ v.co
            lines.append(f"v {w.x:.5f} {w.y:.5f} {w.z:.5f}\n")
        for p in me.polygons:
            vs = list(p.vertices)
            for k in range(1, len(vs)-1):
                lines.append(f"f {vs[0]+1} {vs[k]+1} {vs[k+1]+1}\n")
        with io.open(os.path.join(OBJD, f"{idx}.obj"), "w", encoding="utf-8") as f:
            f.write("".join(lines))
        ps = obj_paths.get(o.name, [])
        # world bbox from first pass (cheap recompute)
        xs=[];ys=[];zs=[]
        for v in me.vertices:
            w = mw @ v.co; xs.append(w.x); ys.append(w.y); zs.append(w.z)
        meta.append({"idx": idx, "name": o.name, "nverts": nv,
                     "system": system_of(ps), "path": bonus_path(ps), "all_paths": ps,
                     "wbbox_min":[round(min(xs),4),round(min(ys),4),round(min(zs),4)],
                     "wbbox_max":[round(max(xs),4),round(max(ys),4),round(max(zs),4)],
                     "wcentroid":[round((min(xs)+max(xs))/2,4),round((min(ys)+max(ys))/2,4),round((min(zs)+max(zs))/2,4)]})
        idx += 1
        if idx % 200 == 0:
            print("PROGRESS", idx)
            json.dump(meta, io.open(os.path.join(OUT,"objects.json"),"w",encoding="utf-8"), ensure_ascii=False)
    except Exception:
        skipped += 1
        try: print("ERR_IDX", idx, o.name)
        except Exception: print("ERR_IDX", idx, "?")
        traceback.print_exc()

json.dump(meta, io.open(os.path.join(OUT,"objects.json"),"w",encoding="utf-8"), ensure_ascii=False)
print("DONE", idx, "written", skipped, "skipped")
