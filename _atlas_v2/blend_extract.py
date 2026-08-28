# Run headless:
#   blender.exe --background "Startup.blend" --python blend_extract.py
# Dumps a full inventory + collection tree + per-top-collection GLB exports.
import bpy, json, os, io, math

OUT = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\blend_dump"
os.makedirs(OUT, exist_ok=True)
os.makedirs(OUT + r"\glb", exist_ok=True)

def w(fn, obj):
    with io.open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)

# ---------------- collection hierarchy ----------------
def coll_tree(coll, depth=0):
    node = {"name": coll.name, "depth": depth,
            "n_objects_direct": len(coll.objects),
            "children": [coll_tree(c, depth + 1) for c in coll.children]}
    return node
w("collections.json", coll_tree(bpy.context.scene.collection))

# map object -> its collection path(s)
obj_colls = {}
def walk(coll, path):
    p = path + [coll.name]
    for o in coll.objects:
        obj_colls.setdefault(o.name, []).append("/".join(p))
    for c in coll.children:
        walk(c, p)
walk(bpy.context.scene.collection, [])

# ---------------- object inventory ----------------
inv = []
type_counts = {}
for o in bpy.data.objects:
    type_counts[o.type] = type_counts.get(o.type, 0) + 1
    rec = {"name": o.name, "type": o.type,
           "collections": obj_colls.get(o.name, []),
           "parent": o.parent.name if o.parent else None,
           "loc": [round(v, 5) for v in o.location],
           "world_loc": [round(v, 5) for v in o.matrix_world.translation],
           "dims": [round(v, 5) for v in o.dimensions]}
    if o.type == "MESH":
        me = o.data
        rec["nverts"] = len(me.vertices)
        rec["npolys"] = len(me.polygons)
        # world-space bbox
        mw = o.matrix_world
        pts = [mw @ v.co for v in me.vertices] if len(me.vertices) < 100000 else [mw @ o.bound_box[i][:] for i in range(8)] if False else None
        if me.vertices:
            xs = [(mw @ v.co) for v in me.vertices]
            mnx = min(p.x for p in xs); mny = min(p.y for p in xs); mnz = min(p.z for p in xs)
            mxx = max(p.x for p in xs); mxy = max(p.y for p in xs); mxz = max(p.z for p in xs)
            rec["wbbox_min"] = [round(mnx,4), round(mny,4), round(mnz,4)]
            rec["wbbox_max"] = [round(mxx,4), round(mxy,4), round(mxz,4)]
            rec["wcentroid"] = [round((mnx+mxx)/2,4), round((mny+mxy)/2,4), round((mnz+mxz)/2,4)]
    inv.append(rec)
w("inventory.json", inv)
w("summary.json", {
    "blend_version": bpy.app.version_string,
    "n_objects": len(bpy.data.objects),
    "type_counts": type_counts,
    "n_meshes": type_counts.get("MESH", 0),
    "top_collections": [c.name for c in bpy.context.scene.collection.children],
})

print("INVENTORY_DONE", len(inv), "objects,", type_counts)

# ---------------- per top-level collection GLB export ----------------
def objs_in_coll_tree(coll):
    out = list(coll.objects)
    for c in coll.children:
        out += objs_in_coll_tree(c)
    return out

for tc in bpy.context.scene.collection.children:
    meshes = [o for o in objs_in_coll_tree(tc) if o.type == "MESH"]
    if not meshes:
        continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        try: o.select_set(True)
        except Exception: pass
    if bpy.context.view_layer.objects.active is None and meshes:
        bpy.context.view_layer.objects.active = meshes[0]
    safe = "".join(ch if ch.isalnum() else "_" for ch in tc.name).strip("_")
    path = os.path.join(OUT, "glb", f"{safe}.glb")
    try:
        bpy.ops.export_scene.gltf(
            filepath=path, export_format='GLB', use_selection=True,
            export_apply=True, export_yup=True, export_materials='NONE',
        )
        print("GLB_EXPORT", tc.name, "->", safe, len(meshes), "meshes")
    except Exception as e:
        print("GLB_FAIL", tc.name, repr(e))

print("ALL_DONE")
