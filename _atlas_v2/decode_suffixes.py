import trimesh, json, re, collections, io, numpy as np

SRC = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"
OUT = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2"

def load_world(path):
    scene = trimesh.load(path)
    rows = []
    for node in scene.graph.nodes_geometry:
        tf, gname = scene.graph[node]
        g = scene.geometry[gname]
        c = g.copy(); c.apply_transform(tf)
        rows.append({
            "node": node, "geom": gname,
            "centroid": c.centroid.tolist(),
            "bounds_min": c.bounds[0].tolist(), "bounds_max": c.bounds[1].tolist(),
            "nverts": len(c.vertices), "nfaces": len(c.faces),
            "diag": float(np.linalg.norm(c.bounds[1]-c.bounds[0])),
        })
    return scene, rows

sk_scene, sk = load_world(f"{SRC}\\SkeletalSystem100.glb")

SUF = re.compile(r'^(?P<base>.*?)\.(?P<suf>(?:i|j|r|l|r_\d+|l_\d+|or|ol|er|el|o\dr|o\dl|e\dr|e\dl))$')
def split(name):
    m = SUF.match(name)
    if m: return m.group('base'), m.group('suf')
    if re.search(r'_\d+$', name):
        return re.sub(r'_\d+$','',name), '<_N>'
    return name, '<none>'

by_suf = collections.Counter()
for r in sk:
    b, s = split(r['geom'])
    r['base'], r['suf'] = b, s
    by_suf[s] += 1

# 1. Femur: all nodes
femur = [r for r in sk if r['base']=='Femur' or r['geom'].startswith('Femur')]
# 2. origin/insertion suffix examples with a known muscle-related bone feature
attach = [r for r in sk if r['suf'] in ('or','ol','er','el') or re.match(r'[eo]\d[rl]', r['suf'] or '')]
attach_names = collections.Counter(r['base'] for r in attach)
# 3. duplicate/collection meshes: same centroid & nverts as another, or huge diag (whole-region)
big = sorted(sk, key=lambda r:-r['diag'])[:25]
# 4. i/j pair mirror check across many pairs
groups = collections.defaultdict(dict)
for r in sk:
    if r['suf'] in ('i','j'):
        groups[r['base']][r['suf']] = np.array(r['centroid'])
mirror_stats = []
for b,d in groups.items():
    if 'i' in d and 'j' in d:
        i,j = d['i'], d['j']
        mirror_stats.append({
            "base": b,
            "i_x": round(float(i[0]),4), "j_x": round(float(j[0]),4),
            "dx_sum": round(float(i[0]+j[0]),5),   # ~0 if mirror
            "dy": round(float(i[1]-j[1]),5), "dz": round(float(i[2]-j[2]),5),
            "i_is_positive_x": bool(i[0] > 0),
        })
n_mirror = sum(1 for m in mirror_stats if abs(m['dx_sum'])<0.01 and abs(m['dy'])<0.01 and abs(m['dz'])<0.01)
n_i_pos = sum(1 for m in mirror_stats if m['i_is_positive_x'])

# 5. r/l explicit whole-structure pairs: which x sign is .l
rl = collections.defaultdict(dict)
for r in sk:
    m = re.match(r'^(.*)\.(r|l)$', r['geom'])
    if m: rl[m.group(1)][m.group(2)] = np.array(r['centroid'])
rl_check = [{"base": b, "l_x": round(float(d['l'][0]),4), "r_x": round(float(d['r'][0]),4)}
            for b,d in rl.items() if 'l' in d and 'r' in d]

out = {
  "suffix_counts": by_suf.most_common(),
  "femur_nodes": [{"geom": r['geom'], "centroid": [round(x,3) for x in r['centroid']], "nverts": r['nverts'], "diag": round(r['diag'],3)} for r in femur],
  "attach_suffix_total": len(attach),
  "attach_base_samples": attach_names.most_common(20),
  "attach_examples": [{"geom": r['geom'], "centroid":[round(x,3) for x in r['centroid']], "nverts": r['nverts']} for r in attach[:20]],
  "biggest_meshes": [{"geom": r['geom'], "diag": round(r['diag'],3), "nverts": r['nverts']} for r in big],
  "ij_pairs_total": len(mirror_stats),
  "ij_pairs_clean_mirror": n_mirror,
  "ij_pairs_i_positive_x": n_i_pos,
  "ij_mirror_samples": mirror_stats[:15],
  "rl_explicit_pairs": rl_check,
}
with io.open(f"{OUT}\\decode_suffixes.json","w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=1)
print("suffixes:", by_suf.most_common())
print(f"i/j pairs: {len(mirror_stats)}  clean-mirror: {n_mirror}  i-on-+X: {n_i_pos}")
print("r/l explicit pairs (l_x should be >0):", rl_check[:5])
print("femur nodes:", [r['geom'] for r in femur])
