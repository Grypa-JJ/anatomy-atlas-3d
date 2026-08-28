import trimesh, json, re, io, collections, numpy as np

SRC = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"
OUT = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2"

scene = trimesh.load(f"{SRC}\\SkeletalSystem100.glb")

BODY_SUF = re.compile(r'^(?P<base>.*?)(?:\.(?P<s>r|l|r_\d+|l_\d+))?$')
def parse(name):
    m = BODY_SUF.match(name)
    return m.group('base'), (m.group('s') or '')

MUSCLE = re.compile(r'muscle|\b(flexor|extensor|adductor|abductor|biceps|triceps|deltoid|'
    r'gluteus|soleus|gastrocnemius|sartorius|gracilis|pectoralis|trapezius|rhomboid|'
    r'levator|serratus|scalen|semispinalis|multifidus|iliocostalis|longissimus|spinalis|'
    r'oblique|transvers|rectus abdominis|psoas|iliacus|piriformis|masseter|temporalis|pterygoid|'
    r'digastric|mylohyoid|omohyoid|sternohyoid|thyrohyoid|platysma|supinator|pronator|'
    r'brachialis|brachii|anconeus|lumbric|interossei|opponens|palmaris|coccygeus|'
    r'levatores|rotatores|intertransvers|interspinales|quadratus|hyoglossus|genioglossus|'
    r'styloglossus|risorius|buccinator|corrugator|procerus|nasalis|mentalis|zygomaticus|'
    r'orbicularis|occipitofrontalis|auricular|stapedius|tensor|constrictor|salpingo|'
    r'palatoglossus|palatopharyngeus|uvulae|cricothyroid|arytenoid muscle|thyroarytenoid|'
    r'vocalis|aryepiglottic|longus (colli|capitis)|rectus capitis|splenius|iliopsoas|'
    r'pectineus|obturator (internus|externus)|gemellus|articularis|plantaris|popliteus|'
    r'tibialis|fibularis|peroneus|abductor|dorsal interossei|plantar interossei)\b', re.I)
NONBONE = re.compile(r'ligament|membrane|apon(eu|)rosis|retinaculum|fascia|raphe|tendon|'
    r'intervertebral (disc|symphysis)|meniscus|labrum|cartilage|bursa|capsule|'
    r'nerve|artery|vein|plexus|ganglion|nucleus pulposus|annulus|'
    r'\bdisc\b|\bgland\b|tooth|teeth|periodontal', re.I)
# feature words that are sub-parts, not whole bones
FEATURE = re.compile(r'^(process|tubercle|tuberosity|fossa|notch|groove|sulcus|crest|line|'
    r'ridge|border|margin|angle|surface|facet|head|neck|body|base|apex|spine|foramen|'
    r'canal|condyle|epicondyle|malleolus|trochlea|trochanter|protuberance|'
    r'eminence|impression|hamulus|cornu|ala|arch|lamina|pedicle|'
    r'articular|superior|inferior|anterior|posterior|medial|lateral|greater|lesser|'
    r'first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\b', re.I)

rows=[]
for node in scene.graph.nodes_geometry:
    tf, gname = scene.graph[node]
    g = scene.geometry[gname].copy(); g.apply_transform(tf)
    base, s = parse(gname)
    c = g.centroid * 1000.0   # metres -> mm
    rows.append({"geom":gname,"base":base,"suf":s,"nverts":len(g.vertices),
                 "cx":float(c[0]),"cy":float(c[1]),"cz":float(c[2])})

# candidate bone bodies: suffix in {'', r, l, r_N, l_N}, verts >= 60,
# not muscle/nonbone, base not a bare feature word
cand = collections.defaultdict(lambda:{"insts":[],"maxv":0})
for r in rows:
    ok_suf = r["suf"]=='' or re.match(r'^(r|l)(_\d+)?$', r["suf"])
    if not ok_suf: continue
    if r["nverts"] < 60: continue
    b = r["base"]
    if MUSCLE.search(b) or NONBONE.search(b): continue
    if FEATURE.match(b): continue
    cand[b]["insts"].append(r)
    cand[b]["maxv"] = max(cand[b]["maxv"], r["nverts"])

# for each candidate: how many distinct sides (by sign of cx across instances)
summary=[]
for b,info in cand.items():
    xs = [i["cx"] for i in info["insts"]]
    has_L = any(x> 5 for x in xs); has_R = any(x< -5 for x in xs); has_mid = any(abs(x)<=25 for x in xs)
    summary.append({"base":b,"n_inst":len(info["insts"]),"maxv":info["maxv"],
                    "L":has_L,"R":has_R,"mid":has_mid,
                    "frag_suffixes":sorted(set(i["suf"] for i in info["insts"]))})
summary.sort(key=lambda x:x["base"])

json.dump(summary, io.open(f"{OUT}\\bone_bodies.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("candidate bone bodies:", len(summary))
print("  paired L+R:", sum(1 for s in summary if s["L"] and s["R"]))
print("  midline-only:", sum(1 for s in summary if s["mid"] and not(s["L"] and s["R"])))
tot_bones = sum((2 if (s["L"] and s["R"]) else 1) for s in summary)
print("  => total named bone objects (L/R split):", tot_bones)
for s in summary[:80]:
    print(f"  {s['base'][:44]:44} inst={s['n_inst']:2} v={s['maxv']:5} {'L' if s['L'] else ' '}{'R' if s['R'] else ' '}{'M' if s['mid'] else ' '}  {s['frag_suffixes']}")
