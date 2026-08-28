import bpy
o = bpy.data.objects.get("Hip bone.l")
print("base verts:", len(o.data.vertices), "mods:", [(m.type, getattr(m,'levels',None), m.show_viewport) for m in o.modifiers])

# method 1: plain evaluated_depsgraph_get
dg = bpy.context.evaluated_depsgraph_get()
me1 = o.evaluated_get(dg).to_mesh()
print("m1 (evaluated_depsgraph_get):", len(me1.vertices))
o.evaluated_get(dg).to_mesh_clear()

# method 2: force view layer update first
bpy.context.view_layer.update()
dg2 = bpy.context.evaluated_depsgraph_get()
me2 = o.evaluated_get(dg2).to_mesh()
print("m2 (after view_layer.update):", len(me2.vertices))
o.evaluated_get(dg2).to_mesh_clear()

# method 3: preserve_all_data_layers / depsgraph param
me3 = o.evaluated_get(dg2).to_mesh(preserve_all_data_layers=True, depsgraph=dg2)
print("m3 (to_mesh with depsgraph):", len(me3.vertices))
o.evaluated_get(dg2).to_mesh_clear()

# method 4: iterate depsgraph.object_instances
for inst in dg2.object_instances:
    if inst.object.name == "Hip bone.l" or (inst.object.original and inst.object.original.name == "Hip bone.l"):
        print("m4 (object_instances):", len(inst.object.data.vertices))
        break

# method 5: apply modifier via bpy.ops in a temp context
try:
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    dup = o.copy(); dup.data = o.data.copy(); bpy.context.collection.objects.link(dup)
    bpy.context.view_layer.objects.active = dup
    for m in dup.modifiers:
        try: bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception as e: print("apply fail", m.name, e)
    print("m5 (modifier_apply on copy):", len(dup.data.vertices))
except Exception as e:
    print("m5 error", e)
