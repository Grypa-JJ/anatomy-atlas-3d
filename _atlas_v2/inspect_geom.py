import trimesh, json, re, collections, io, numpy as np

SRC = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"
OUT = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2"

def world_meshes(scene):
    out = {}
    for node in scene.graph.nodes_geometry:
        tf, gname = scene.graph[node]
        g = scene.geometry[gname].copy()
        g.apply_transform(tf)
        out.setdefault(gname, []).append(g)
    merged = {}
    for name, parts in out.items():
        if len(parts) == 1:
            merged[name] = parts[0]
        else:
            merged[name] = trimesh.util.concatenate(parts)
    return merged

def base_and_suffix(name):
    m = re.match(r'^(.*?)((?:\.[A-Za-z0-9_]+)+)$', name)
    if not m:
        return name, ''
    return m.group(1), m.group(2)

sk = trimesh.load(f"{SRC}\\SkeletalSystem100.glb")
wm = world_meshes(sk)

# overall bbox
allpts = np.vstack([m.bounds for m in wm.values()])
lo = allpts.min(axis=0); hi = allpts.max(axis=0)
info = {"overall_bounds_min": lo.tolist(), "overall_bounds_max": hi.tolist(),
        "extent": (hi-lo).tolist()}

# centroids
cent = {name: m.centroid.tolist() for name, m in wm.items()}

# group by base
groups = collections.defaultdict(dict)
for name, m in wm.items():
    b, s = base_and_suffix(name)
    groups[b][s] = m.centroid.tolist()

# find bases having both .i and .j
ij_pairs = []
for b, d in groups.items():
    if '.i' in d and '.j' in d:
        ij_pairs.append({"base": b, "i": d['.i'], "j": d['.j']})

# find bases having both .r and .l
rl_pairs = []
for b, d in groups.items():
    if '.r' in d and '.l' in d:
        rl_pairs.append({"base": b, "r": d['.r'], "l": d['.l']})

# midline structures of interest
keys = list(wm.keys())
def find(sub):
    return [k for k in keys if sub.lower() in k.lower()]

interest = {}
for term in ["sacrum", "sternum", "mandible", "occipit", "vomer", "hyoid", "coccyx", "atlas", "axis", "frontal bone", "ethmoid", "sphenoid"]:
    hits = find(term)
    interest[term] = {h: cent[h] for h in hits[:8]}

report = {
    "info": info,
    "n_ij_pairs": len(ij_pairs),
    "ij_pairs_sample": ij_pairs[:40],
    "n_rl_pairs": len(rl_pairs),
    "rl_pairs_sample": rl_pairs[:40],
    "midline_interest": interest,
    "suffix_bases_only_i": [b for b,d in groups.items() if set(d.keys())=={'.i'}][:30],
    "suffix_bases_only_j": [b for b,d in groups.items() if set(d.keys())=={'.j'}][:30],
    "bases_with_r_1": [b for b,d in groups.items() if '.r_1' in d][:30],
}
with io.open(f"{OUT}\\inspect_skeletal.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("overall extent (raw units):", (hi-lo).tolist())
print("min", lo.tolist(), "max", hi.tolist())
print("ij_pairs:", len(ij_pairs), " rl_pairs:", len(rl_pairs))
