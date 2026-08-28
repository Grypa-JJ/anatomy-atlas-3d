# Modifier-evaluated FONT label positions (HOOK-corrected) -> blend_dump6/labels_eval.json
import bpy, json, io, os, traceback
OUT = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\blend_dump6\labels_eval.json"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
res = []
fonts = [o for o in bpy.data.objects if o.type == "FONT"]
print("FONTS", len(fonts))
for i, o in enumerate(fonts):
    try:
        dg = bpy.context.evaluated_depsgraph_get()
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        if me and len(me.vertices):
            mw = o.matrix_world
            xs=[];ys=[];zs=[]
            for v in me.vertices:
                w = mw @ v.co; xs.append(w.x);ys.append(w.y);zs.append(w.z)
            res.append({"name": o.name,
                        "pos": [round((min(xs)+max(xs))/2,5), round((min(ys)+max(ys))/2,5), round((min(zs)+max(zs))/2,5)]})
        else:
            wl = o.matrix_world.translation
            res.append({"name": o.name, "pos": [round(wl.x,5), round(wl.y,5), round(wl.z,5)]})
        try: oe.to_mesh_clear()
        except Exception: pass
    except Exception:
        wl = o.matrix_world.translation
        res.append({"name": o.name, "pos": [round(wl.x,5), round(wl.y,5), round(wl.z,5)]})
        print("ERR", o.name)
    if (i+1) % 300 == 0:
        json.dump(res, io.open(OUT,"w",encoding="utf-8"), ensure_ascii=False); print("P", i+1)
json.dump(res, io.open(OUT,"w",encoding="utf-8"), ensure_ascii=False)
print("FONTDONE", len(res))
