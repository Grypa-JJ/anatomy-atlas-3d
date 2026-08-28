import trimesh, json, re, io, numpy as np

SRC = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"
OUT = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2"

# Candidate global transform: Z-Anatomy (Y-up, metres, X+=subject-left, Z+=anterior)
#   -> atlas (X=med-lat, Y=ant-post, Z=sup-inf, mm ; right side = -X, per old data)
# rotX(+90): (x,y,z) -> (x, -z, y) ; then *1000
def to_atlas(p):
    x, y, z = p
    return np.array([x*1000.0, -z*1000.0, y*1000.0])

scene = trimesh.load(f"{SRC}\\SkeletalSystem100.glb")
rows = []
for node in scene.graph.nodes_geometry:
    tf, gname = scene.graph[node]
    g = scene.geometry[gname].copy(); g.apply_transform(tf)
    c_src = g.centroid
    c_atl = to_atlas(c_src)
    b0 = to_atlas(g.bounds[0]); b1 = to_atlas(g.bounds[1])
    rows.append({"geom": gname, "src": c_src.tolist(), "atlas": c_atl.tolist(),
                 "atlas_zmin": float(min(b0[2],b1[2])), "atlas_zmax": float(max(b0[2],b1[2])),
                 "atlas_ymin": float(min(b0[1],b1[1])), "atlas_ymax": float(max(b0[1],b1[1]))})

def pick(sub):
    return [r for r in rows if sub.lower() in r['geom'].lower()]
def one(sub):
    hs = pick(sub)
    return hs[0] if hs else None

checks = {}
# 1. superior-inferior (atlas Z): skull vs feet
allZ = [r['atlas']['2'] if isinstance(r['atlas'],dict) else r['atlas'][2] for r in rows]
zmax_r = max(rows, key=lambda r:r['atlas'][2]); zmin_r = min(rows, key=lambda r:r['atlas'][2])
checks['topmost_structure'] = (zmax_r['geom'], round(zmax_r['atlas'][2],1))
checks['bottommost_structure'] = (zmin_r['geom'], round(zmin_r['atlas'][2],1))

# 2. sacrum vs cervical (atlas Z)
sac = one("Sacrum.j") or one("Sacrum")
c1  = one("Atlas (C1)")
checks['sacrum_Z'] = round(sac['atlas'][2],1) if sac else None
checks['C1_atlas_Z'] = round(c1['atlas'][2],1) if c1 else None
checks['sacrum_below_C1'] = (sac['atlas'][2] < c1['atlas'][2]) if (sac and c1) else None

# 3. anterior-posterior (atlas Y): sternum vs a spinous process / occiput
stern = one("Manubrium of sternum")
occ   = one("Occipital bone")
front = one("Frontal bone")
checks['sternum_Y'] = round(stern['atlas'][1],1) if stern else None
checks['occiput_Y'] = round(occ['atlas'][1],1) if occ else None
checks['frontal_Y'] = round(front['atlas'][1],1) if front else None
# in src, sternum z>0 (anterior). atlas Y = -1000*z  => sternum Y should be NEGATIVE, occiput POSITIVE
checks['=> atlas +Y is'] = "POSTERIOR (back)" if (stern and occ and stern['atlas'][1] < occ['atlas'][1]) else "ANTERIOR (front)"

# 4. left/right (atlas X): explicit .r vs .l
def cx(sub_r, sub_l):
    r = one(sub_r); l = one(sub_l)
    return (round(r['atlas'][0],1) if r else None, round(l['atlas'][0],1) if l else None)
checks['Pisiform_bone.r / .l  atlasX'] = cx("Pisiform bone.r", "Pisiform bone.l")
# Femur.r instances: both signs (mirror-instanced). report both
fem = [r for r in rows if r['geom']=='Femur.r']
checks['Femur.r instances atlasX'] = sorted(round(r['atlas'][0],1) for r in fem)

# 5. overall bbox in atlas frame
A = np.array([r['atlas'] for r in rows])
checks['atlas_bbox_min'] = [round(v,1) for v in A.min(axis=0)]
checks['atlas_bbox_max'] = [round(v,1) for v in A.max(axis=0)]

with io.open(f"{OUT}\\verify_transform.json","w",encoding="utf-8") as f:
    json.dump(checks, f, ensure_ascii=False, indent=1)
for k,v in checks.items():
    print(k, "=", v)
