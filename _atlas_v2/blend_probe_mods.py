import bpy, json, io
out = []
mod_counts = {}
sample = []
for o in bpy.data.objects:
    if o.type != "MESH": continue
    mods = [m.type for m in o.modifiers]
    for m in mods:
        mod_counts[m] = mod_counts.get(m, 0) + 1
    is_ij = o.name.endswith(".i") or o.name.endswith(".j")
    if is_ij and mods and len(sample) < 30:
        # base centroid vs where a shrinkwrap target would put it
        me = o.data
        if me.vertices:
            import mathutils
            c = sum((o.matrix_world @ v.co for v in me.vertices), mathutils.Vector()) / len(me.vertices)
            sample.append({"name": o.name, "mods": mods, "base_centroid": [round(x,4) for x in c],
                           "parent": o.parent.name if o.parent else None})
    if is_ij:
        out.append({"name": o.name, "mods": mods})
n_ij = len(out)
n_ij_mods = sum(1 for x in out if x["mods"])
json.dump({"mod_counts": mod_counts, "n_ij": n_ij, "n_ij_with_mods": n_ij_mods, "samples": sample},
          io.open(r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\_mods_probe.json","w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("MOD_PROBE_DONE", mod_counts, "ij:", n_ij, "with mods:", n_ij_mods)
