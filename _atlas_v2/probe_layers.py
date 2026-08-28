import trimesh, re, collections, json, io, numpy as np
SRC=r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"

def probe(fn):
    s=trimesh.load(f"{SRC}\\{fn}")
    names=list(s.geometry.keys())
    mn=np.array([1e18]*3); mx=np.array([-1e18]*3)
    cents=[]
    for node in s.graph.nodes_geometry:
        tf,g=s.graph[node]; m=s.geometry[g].copy(); m.apply_transform(tf)
        mn=np.minimum(mn,m.bounds[0]); mx=np.maximum(mx,m.bounds[1]); cents.append(m.centroid)
    ext=mx-mn
    suf=collections.Counter()
    for n in names:
        mm=re.search(r'(\.[A-Za-z0-9_]+)+$',n)
        if mm:
            for t in re.findall(r'\.[A-Za-z0-9_]+',mm.group(0)): suf[t]+=1
        else: suf['<none>']+=1
    # candidate up-axis = axis with largest extent
    up=int(np.argmax(ext))
    print(f"\n=== {fn} ===")
    print(f"  geoms={len(names)}  graph_nodes={len(s.graph.nodes_geometry)}")
    print(f"  raw extent XYZ = {np.round(ext,4)}   (max axis = {'XYZ'[up]})")
    print(f"  raw bounds min={np.round(mn,4)}  max={np.round(mx,4)}")
    print(f"  suffixes: {suf.most_common(15)}")
    print(f"  sample names: {names[:12]}")
    return ext

for fn in ["CardioVascular41.glb","NervousSystem100.glb","VisceralSystem100.glb","LymphoidOrgans100.glb"]:
    probe(fn)
