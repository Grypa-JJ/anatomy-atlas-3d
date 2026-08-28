# Curve geometry (vessels/nerves as beveled tubes). Appends to blend_dump3.
import bpy, json, os, io, traceback
OUT  = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\blend_dump3"
OBJD = OUT + r"\obj"

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

meta = json.load(io.open(os.path.join(OUT,"objects.json"),encoding="utf-8"))
idx = max(m["idx"] for m in meta) + 1
start = idx
skipped = 0
curves = [o for o in bpy.data.objects if o.type == "CURVE"]
print("CURVE_COUNT", len(curves))
for o in curves:
    try:
        me = o.to_mesh()
        if me is None or len(me.vertices) == 0:
            try: o.to_mesh_clear()
            except Exception: pass
            skipped += 1; continue
        mw = o.matrix_world
        lines = []
        xs=[];ys=[];zs=[]
        for v in me.vertices:
            w = mw @ v.co; xs.append(w.x);ys.append(w.y);zs.append(w.z)
            lines.append(f"v {w.x:.5f} {w.y:.5f} {w.z:.5f}\n")
        for p in me.polygons:
            vs=list(p.vertices)
            for k in range(1,len(vs)-1):
                lines.append(f"f {vs[0]+1} {vs[k]+1} {vs[k+1]+1}\n")
        nv=len(me.vertices)
        with io.open(os.path.join(OBJD,f"{idx}.obj"),"w",encoding="utf-8") as f:
            f.write("".join(lines))
        ps=obj_paths.get(o.name,[])
        meta.append({"idx":idx,"name":o.name,"nverts":nv,"is_curve":True,
                     "system":system_of(ps),"path":bonus_path(ps),"all_paths":ps,
                     "wbbox_min":[round(min(xs),4),round(min(ys),4),round(min(zs),4)],
                     "wbbox_max":[round(max(xs),4),round(max(ys),4),round(max(zs),4)],
                     "wcentroid":[round((min(xs)+max(xs))/2,4),round((min(ys)+max(ys))/2,4),round((min(zs)+max(zs))/2,4)]})
        idx+=1
        try: o.to_mesh_clear()
        except Exception: pass
        if idx % 200 == 0:
            print("PROGRESS", idx)
            json.dump(meta, io.open(os.path.join(OUT,"objects.json"),"w",encoding="utf-8"), ensure_ascii=False)
    except Exception:
        skipped += 1; print("ERR", o.name); traceback.print_exc()
json.dump(meta, io.open(os.path.join(OUT,"objects.json"),"w",encoding="utf-8"), ensure_ascii=False)
print("DONE curves", idx-start, "written", skipped, "skipped, total", idx)
