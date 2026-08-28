# Geometry dump WITH procedural Subsurf on low-poly meshes (Z-Anatomy has no bone modifiers;
# mesh density is just inconsistent). Batched.  -- <start> <count>
import bpy, json, os, io, sys, traceback

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
START = int(argv[0]) if argv else 0
COUNT = int(argv[1]) if len(argv) > 1 else 100000

OUT  = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\blend_dump8"
OBJD = OUT + r"\obj"
os.makedirs(OBJD, exist_ok=True)

obj_paths = {}
def walk(coll, path):
    p = path + [coll.name]
    for o in coll.objects: obj_paths.setdefault(o.name, []).append("/".join(p[1:]))
    for c in coll.children: walk(c, p)
walk(bpy.context.scene.collection, [])
SYS = ("1: Skeletal system","2: Muscular insertions","3: Joints","4: Muscular system",
       "5: Cardiovascular system","6: Lymphoid organs","7: Nervous system & Sense organs",
       "8: Visceral systems","9: Regions of human body")
def system_of(ps):
    for p in ps:
        if p.split("/")[0] in SYS: return p.split("/")[0]
def bonus_path(ps):
    b = sorted((p for p in ps if p.startswith("Bonus collection/")), key=len, reverse=True)
    return b[0][17:] if b else None

geo = [o for o in bpy.data.objects if o.type in ("MESH", "CURVE")]
geo.sort(key=lambda o: o.name)
batch = geo[START:START+COUNT]
meta = []
print("BATCH", START, "len", len(batch))

# systems whose meshes should be smoothed (bones/joints/cartilage/organs)
SMOOTH_SYS = {"1: Skeletal system", "3: Joints", "8: Visceral systems", "6: Lymphoid organs"}

for i, o in enumerate(batch):
    gi = START + i
    added = None
    try:
        base_v = len(o.data.vertices) if o.type == "MESH" else 0
        sysn = system_of(obj_paths.get(o.name, []))
        want_ss = (o.type == "MESH" and sysn in SMOOTH_SYS and base_v >= 16 and base_v < 2600
                   and not o.name.endswith((".i", ".j")))
        if want_ss:
            added = o.modifiers.new(name="_ss_tmp", type="SUBSURF")
            added.levels = 2 if base_v < 450 else 1
            added.show_viewport = True
        dg = bpy.context.evaluated_depsgraph_get()
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        if me is None or len(me.vertices) == 0:
            try: oe.to_mesh_clear()
            except Exception: pass
            if added: o.modifiers.remove(added)
            continue
        mw = o.matrix_world
        V = [tuple(mw @ v.co) for v in me.vertices]
        F = []
        for p in me.polygons:
            vs = list(p.vertices)
            for k in range(1, len(vs)-1): F.append((vs[0], vs[k], vs[k+1]))
        try: oe.to_mesh_clear()
        except Exception: pass
        if added: o.modifiers.remove(added); added = None
        xs=[v[0] for v in V]; ys=[v[1] for v in V]; zs=[v[2] for v in V]
        with io.open(os.path.join(OBJD, f"{gi}.obj"), "w", encoding="utf-8") as f:
            f.write("".join(f"v {x:.5f} {y:.5f} {z:.5f}\n" for x,y,z in V))
            f.write("".join(f"f {a+1} {b+1} {c+1}\n" for a,b,c in F))
        ps = obj_paths.get(o.name, [])
        meta.append({"gi": gi, "name": o.name, "type": o.type, "nverts": len(V), "base_verts": base_v,
                     "subsurf": bool(want_ss),
                     "system": sysn, "path": bonus_path(ps), "all_paths": ps,
                     "wbbox_min":[round(min(xs),4),round(min(ys),4),round(min(zs),4)],
                     "wbbox_max":[round(max(xs),4),round(max(ys),4),round(max(zs),4)],
                     "wcentroid":[round((min(xs)+max(xs))/2,4),round((min(ys)+max(ys))/2,4),round((min(zs)+max(zs))/2,4)]})
        if (i+1) % 100 == 0:
            print("P", gi); json.dump(meta, io.open(os.path.join(OUT, f"objects_{START}.json"),"w",encoding="utf-8"), ensure_ascii=False)
    except Exception:
        print("CRASHOBJ", gi, o.name); traceback.print_exc()
        if added:
            try: o.modifiers.remove(added)
            except Exception: pass
json.dump(meta, io.open(os.path.join(OUT, f"objects_{START}.json"),"w",encoding="utf-8"), ensure_ascii=False)
print("BATCHDONE", START, len(meta))
