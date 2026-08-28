import trimesh, json, re, io, collections, numpy as np

SRC = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"
OUT = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2"

scene = trimesh.load(f"{SRC}\\SkeletalSystem100.glb")

# ---- full suffix grammar ----
RX_ATTACH = re.compile(r'\.(?:[oe]\d*[rl])$')          # .or .ol .er .el .o1r .e2l .e12r ...
RX_POINT  = re.compile(r'\.(i|j)$')                    # annotation point L/R
RX_SIDE   = re.compile(r'\.(r|l)$')                    # whole structure R/L
RX_FRAG   = re.compile(r'\.(r|l)_(\d+)$')              # fragment N of R/L
RX_USCORE = re.compile(r'_(\d+)$')                     # authored mesh piece

def classify_suffix(name):
    if RX_ATTACH.search(name): return "attach", RX_ATTACH.sub('', name)
    if RX_POINT.search(name):
        s = RX_POINT.search(name).group(1)
        return ("point_L" if s=="i" else "point_R"), RX_POINT.sub('', name)
    if RX_FRAG.search(name):
        s = RX_FRAG.search(name).group(1)
        return ("body_L" if s=="l" else "body_R"), RX_FRAG.sub('', name)
    if RX_SIDE.search(name):
        s = RX_SIDE.search(name).group(1)
        return ("body_L" if s=="l" else "body_R"), RX_SIDE.sub('', name)
    return "body_mid", name          # no side suffix

def strip_piece(base):
    return RX_USCORE.sub('', base)

rows=[]
for node in scene.graph.nodes_geometry:
    tf, gname = scene.graph[node]
    g = scene.geometry[gname].copy(); g.apply_transform(tf)
    c = g.centroid * 1000.0
    kind, base = classify_suffix(gname)
    rows.append({"geom":gname,"kind":kind,"base":strip_piece(base),"raw_base":base,
                 "nverts":len(g.vertices),"cx":float(c[0]),"cy":float(c[1]),"cz":float(c[2])})

# any base that EVER appears with an attach suffix == a muscle
muscle_bases = set(r["base"] for r in rows if r["kind"]=="attach")

NONBONE = re.compile(r'ligament|membrane|aponeurosis|retinaculum|fascia|raphe|tendon|'
    r'meniscus|labrum|cartilage|bursa|\bcapsule\b|nerve|artery|vein|'
    r'\bdisc\b|symphysis|\bgland\b', re.I)
TOOTH = re.compile(r'\b(incisor|canine|premolar|molar|wisdom tooth)\b', re.I)
OSSICLE = re.compile(r'\b(malleus|incus|stapes)\b', re.I)
# a base is a SUB-FEATURE (not a whole bone) when it reads "<featureword> of <bone>"
FEATUREWORDS = {"process","tubercle","tuberosity","fossa","notch","groove","sulcus","crest",
    "line","linea","ridge","border","margin","angle","surface","facet","head","neck","body",
    "base","apex","spine","foramen","canal","condyle","epicondyle","malleolus","trochlea",
    "trochanter","protuberance","eminence","impression","hamulus","cornu","ala","arch","lamina",
    "pedicle","wing","horn","part","hiatus","tubercle","fovea","incisure","dens","promontory",
    "sustentaculum","conus","tendon","fibers","layer","attachment","insertion","origin"}
FEATURE_STANDALONE = re.compile(r'^(pterion|bregma|lambda|inion|nasion|gnathion|asterion|'
    r'sinus of \w+|infrasternal angle|sternal angle|costal (arch|margin)|'
    r'linea aspera|pecten pubis)\b', re.I)
KEEP_AS_BONE = {"body of sternum"}
def is_feature(name):
    n = name.strip().lower()
    if n in KEEP_AS_BONE: return False
    if FEATURE_STANDALONE.match(n): return True
    if " of " in n and n.split(" of ")[0].split()[-1] in FEATUREWORDS: return True
    return False

bodies = collections.defaultdict(lambda:{"L":[],"R":[],"mid":[]})
for r in rows:
    if not r["kind"].startswith("body"): continue
    if r["nverts"] < 40: continue
    b = r["base"]
    if b in muscle_bases: continue
    if NONBONE.search(b): continue
    if is_feature(b): continue
    side = r["kind"].split("_")[1]   # L / R / mid
    bodies[b][side].append(r)

# classify each bone base
out=[]
for b, sd in sorted(bodies.items()):
    geoms = sd["L"]+sd["R"]+sd["mid"]
    xs = [i["cx"] for i in geoms]
    if not xs: continue
    # paired if the actual instances span both sides of the midline
    paired = any(x > 12 for x in xs) and any(x < -12 for x in xs)
    midline = (not paired) and max(abs(x) for x in xs) < 35
    cat = "tooth" if TOOTH.search(b) else ("ossicle" if OSSICLE.search(b) else "bone")
    out.append({"base":b,"category":cat,"paired":paired,"midline":midline,
                "n_geoms":len(sd["L"])+len(sd["R"])+len(sd["mid"]),
                "maxv":max(i["nverts"] for i in sd["L"]+sd["R"]+sd["mid"])})

json.dump(out, io.open(f"{OUT}\\classify.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
cats = collections.Counter(o["category"] for o in out)
print("bone bases:", len(out), dict(cats))
print("paired:", sum(o["paired"] for o in out), " midline:", sum(o["midline"] for o in out),
      " neither:", sum(1 for o in out if not o["paired"] and not o["midline"]))
print("total bone OBJECTS (L/R split, teeth+ossicles excluded from 'bone'):",
      sum((2 if o["paired"] else 1) for o in out if o["category"]=="bone"))
print("\n-- 'neither' (ambiguous, need review) --")
for o in out:
    if not o["paired"] and not o["midline"]:
        print(f"  {o['base'][:50]:50} v={o['maxv']}")
print("\n-- all bone bases --")
for o in out:
    if o["category"]=="bone":
        print(f"  {'PAIR' if o['paired'] else ('MID ' if o['midline'] else '??? ')} {o['base']}")
