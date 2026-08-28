import bpy, collections
lvl = collections.Counter()
viewport_on = collections.Counter()
solidify = collections.Counter()
sample = []
for o in bpy.data.objects:
    if o.type != "MESH": continue
    for m in o.modifiers:
        if m.type == "SUBSURF":
            lvl[m.levels] += 1
            viewport_on[m.show_viewport] += 1
            if len(sample) < 10:
                sample.append((o.name, m.levels, m.show_viewport, len(o.data.vertices)))
        if m.type == "SOLIDIFY":
            solidify[round(m.thickness, 4)] += 1
print("SUBSURF levels:", dict(lvl))
print("SUBSURF show_viewport:", dict(viewport_on))
print("SOLIDIFY thickness dist (top):", solidify.most_common(6))
print("samples (name, level, show_viewport, base_verts):")
for s in sample: print("  ", s)
