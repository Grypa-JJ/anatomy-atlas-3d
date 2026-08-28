import trimesh, json, re, io, collections, numpy as np

SRC = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"
OUT = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2"

scene = trimesh.load(f"{SRC}\\SkeletalSystem100.glb")

# --- scene graph hierarchy: find parent chain of each geometry node ---
G = scene.graph.transforms
try:
    edges = list(G.edge_data.keys())
except Exception:
    edges = []
parent = {}
for a,b in edges:
    parent[b] = a
def chain(n):
    out=[]; seen=set()
    while n in parent and n not in seen:
        seen.add(n); n=parent[n]; out.append(n)
    return out

geo_nodes = scene.graph.nodes_geometry
roots = collections.Counter()
by_toplevel = collections.defaultdict(list)
SUF = re.compile(r'\.(i|j|r|l|r_\d+|l_\d+|or|ol|er|el|o\d[rl]|e\d[rl])$')
def base_of(n): return SUF.sub('', n)

rows=[]
for node in geo_nodes:
    tf, gname = scene.graph[node]
    ch = chain(node)
    top = ch[-2] if len(ch)>=2 else (ch[-1] if ch else node)
    parent1 = ch[0] if ch else None
    by_toplevel[top].append(gname)
    g = scene.geometry[gname]
    rows.append({"node":node,"geom":gname,"base":base_of(gname),
                 "parent":parent1,"top":top,"nverts":len(g.vertices)})

# classify base names
MUSCLE = re.compile(r'muscle|\b(flexor|extensor|adductor|abductor|biceps|triceps|deltoid|'
    r'gluteus|soleus|gastrocnemius|sartorius|gracilis|pectoralis|trapezius|rhomboid|'
    r'levator|serratus|scalenus|semispinalis|multifidus|iliocostalis|longissimus|spinalis|'
    r'obliqu|transvers|rectus|psoas|iliacus|piriformis|masseter|temporalis|pterygoid|'
    r'digastric|mylohyoid|omohyoid|sternohyoid|thyrohyoid|platysma|supinator|pronator|'
    r'brachialis|brachii|anconeus|lumbric|interossei|opponens|palmaris)\b', re.I)
LIG = re.compile(r'ligament|membrane|apon(eu|)rosis|retinaculum|fascia|raphe|tendon|'
    r'intervertebral disc|meniscus|labrum', re.I)
CART = re.compile(r'cartilage', re.I)

base_info = collections.defaultdict(lambda:{"instances":0,"verts":0,"tops":set()})
for r in rows:
    bi = base_info[r["base"]]
    bi["instances"]+=1; bi["verts"]=max(bi["verts"],r["nverts"]); bi["tops"].add(r["top"])

def kind(b):
    if MUSCLE.search(b): return "muscle"
    if LIG.search(b): return "ligament"
    if CART.search(b): return "cartilage"
    return "bone?"

cls = collections.Counter(kind(b) for b in base_info)

report = {
  "n_geometry_nodes": len(geo_nodes),
  "n_unique_base": len(base_info),
  "class_counts": dict(cls),
  "toplevel_groups": {k: len(v) for k,v in sorted(by_toplevel.items(), key=lambda x:-len(x[1]))},
  "bone_bases_sample": sorted([b for b in base_info if kind(b)=="bone?"])[:120],
  "muscle_bases_sample": sorted([b for b in base_info if kind(b)=="muscle"])[:30],
}
json.dump(report, io.open(f"{OUT}\\inventory.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("nodes:", len(geo_nodes), " unique base:", len(base_info))
print("classes:", dict(cls))
print("top-level groups:", report["toplevel_groups"])
