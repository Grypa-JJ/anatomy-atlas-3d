import trimesh, json, re, io, os, numpy as np, difflib

SRC  = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"
OUT  = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\pilot"
PROJ = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie"
os.makedirs(OUT, exist_ok=True)

# ---------- global transform  Z-Anatomy(m, Y-up) -> atlas(mm, Z-up, +Y=back) ----------
def to_atlas_pts(V):
    out = np.empty_like(V, dtype=np.float64)
    out[:,0] =  V[:,0]*1000.0
    out[:,1] = -V[:,2]*1000.0
    out[:,2] =  V[:,1]*1000.0
    return out

# ---------- PL dictionary ----------
_sl = json.load(open(f"{PROJ}\\slownik_anatomiczny_umed_pl_en.json", encoding="utf-8"))
EN2PL = {}
for e in _sl:
    EN2PL.setdefault(e["en"].lower().strip(), e["pl"])
EN_KEYS = list(EN2PL.keys())

def norm(s):
    s = s.lower().strip()
    s = re.sub(r'\b(of|the|a)\b', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s
NORM2PL = {}
for k, v in EN2PL.items():
    NORM2PL.setdefault(norm(k), v)

PILOT_PL_OVERRIDES = {
    "body of humerus": "Trzon kości ramiennej",
    "head of humerus": "Głowa kości ramiennej",
    "capitulum of humerus": "Główka kości ramiennej",
    "trochlea of humerus": "Bloczek kości ramiennej",
    "anatomical neck of humerus": "Szyjka anatomiczna kości ramiennej",
    "surgical neck of humerus": "Szyjka chirurgiczna kości ramiennej",
    "crest of greater tubercle": "Grzebień guzka większego",
    "crest of lesser tubercle": "Grzebień guzka mniejszego",
    "intertubercular sulcus": "Bruzda międzyguzkowa",
    "radial groove": "Bruzda nerwu promieniowego",
    "anterior border of humerus": "Brzeg przedni kości ramiennej",
    "lateral border of humerus": "Brzeg boczny kości ramiennej",
    "medial border of humerus": "Brzeg przyśrodkowy kości ramiennej",
    "anterolateral surface of humerus": "Powierzchnia przednio-boczna kości ramiennej",
    "anteromedial surface of humerus": "Powierzchnia przednio-przyśrodkowa kości ramiennej",
    "posterior surface of humerus": "Powierzchnia tylna kości ramiennej",
    "glenoid fossa": "Wydrążenie stawowe łopatki",
    "glenoid process of scapula": "Wyrostek stawowy łopatki",
    "scapular notch": "Wcięcie łopatki",
    "spinoglenoid notch": "Wcięcie szyjki łopatki (spinoglenoidalne)",
    "lateral border of scapula": "Brzeg boczny łopatki",
    "medial border of scapula": "Brzeg przyśrodkowy łopatki",
    "superior border of scapula": "Brzeg górny łopatki",
    "posterior surface of scapula": "Powierzchnia tylna łopatki",
}

def translate(en):
    en_l = en.lower().strip()
    if en_l in PILOT_PL_OVERRIDES: return PILOT_PL_OVERRIDES[en_l], "override"
    if en_l in EN2PL:               return EN2PL[en_l], "exact"
    n = norm(en_l)
    if n in NORM2PL:                return NORM2PL[n], "norm"
    # try dropping a trailing "of humerus/scapula/..." qualifier
    GENERIC = {"body","head","neck","border","surface","angle","crest","tuberosity","process","spine","notch","fossa"}
    m = re.match(r'^(.*?) of (humerus|scapula|rib|clavicle|ulna|radius)$', en_l)
    if m and m.group(1) in EN2PL and m.group(1) not in GENERIC:
        return EN2PL[m.group(1)], "qual"
    close = difflib.get_close_matches(n, list(NORM2PL.keys()), n=1, cutoff=0.86)
    if close:                       return NORM2PL[close[0]], "fuzzy"
    return None, "none"

# ---------- load skeleton, apply transform ----------
scene = trimesh.load(f"{SRC}\\SkeletalSystem100.glb")
inst = []
for node in scene.graph.nodes_geometry:
    tf, gname = scene.graph[node]
    g = scene.geometry[gname].copy(); g.apply_transform(tf)
    g.vertices = to_atlas_pts(np.asarray(g.vertices))
    inst.append((gname, g))

def base_of(name):
    return re.sub(r'\.(i|j|r|l|r_\d+|l_\d+|or|ol|er|el|o\d[rl]|e\d[rl])$', '', name)

# ---------- pilot bones (right side) ----------
BONE_SPECS = [
    {"key": "scapula_r", "pl": "Łopatka (prawa)",       "frags": {"Scapula.r","Scapula.r_1","Scapula.r_2","Scapula.r_3"}},
    {"key": "humerus_r", "pl": "Kość ramienna (prawa)", "frags": {"Humerus.r","Humerus.r_1","Humerus.r_2"}},
]
bones_out, boxes = [], {}
for spec in BONE_SPECS:
    parts = [g for gname,g in inst if gname in spec["frags"] and g.centroid[0] < 0]
    merged = trimesh.util.concatenate(parts)
    merged.export(f"{OUT}\\{spec['key']}.obj", include_texture=False)
    lo, hi = merged.bounds
    boxes[spec["key"]] = (lo, hi)
    bones_out.append({"id": spec["key"], "pl": spec["pl"],
                      "bbox_min":[round(float(x),1) for x in lo],
                      "bbox_max":[round(float(x),1) for x in hi],
                      "nverts": int(len(merged.vertices))})
    print(f"{spec['key']}: {len(merged.vertices)} verts / {len(parts)} frags  bbox {np.round(lo,0)}..{np.round(hi,0)}")

# ---------- native landmark points, routed BY NAME ----------
ROUTE = [
    ("humerus_r", re.compile(r'\bhumerus\b|\bhumeral\b|greater tubercle|lesser tubercle|'
        r'intertubercular|bicipital groove|deltoid tuberosity|radial groove|'
        r'(surgical|anatomical) neck|capitulum|trochlea of humerus|olecranon fossa|'
        r'coronoid fossa|radial fossa|(medial|lateral) epicondyle|'
        r'(medial|lateral) sup(ra)?condylar|condyle of humerus', re.I)),
    ("scapula_r", re.compile(r'scapula|scapular|glenoid|acromi|coracoid|'
        r'(supra|infra)spinous fossa|subscapular fossa|spinoglenoid|'
        r'(supra|infra)glenoid|spine of scapula', re.I)),
]
EXCLUDE = re.compile(r'\bulna\b|\bradius\b|\bradial (notch|tuberosity)\b|\bclavicl|'
    r'\brib\b|\bribs\b|trapezoid line|conoid|subclavius|costal|sternal|'
    r'coronoid process of ulna|olecranon\b(?! fossa)|trochlear notch|sublime tubercle|'
    r'supinator crest|neck of radius|articular facet of head of radius|'
    r'pectoral girdle|thoracic aperture', re.I)

lm_out, seen = [], set()
for gname, g in inst:
    m = re.search(r'\.(i|j)$', gname)
    if not m or m.group(1) != "j":          # pilot = right side => '.j'
        continue
    if len(g.vertices) > 400:
        continue
    base = base_of(gname)
    if EXCLUDE.search(base):
        continue
    c = g.centroid
    for key, rx in ROUTE:
        if not rx.search(base):
            continue
        lo, hi = boxes[key]
        pad = (hi - lo) * 0.25 + 20
        if not (np.all(c >= lo-pad) and np.all(c <= hi+pad)):
            continue
        if (key, base) in seen:
            break
        seen.add((key, base))
        pl, how = translate(base)
        lm_out.append({"boneId": key, "en": base,
                       "pl": pl or base, "pl_from": how, "approx": pl is None,
                       "pos": [round(float(x),2) for x in c]})
        break

lm_out.sort(key=lambda x: (x["boneId"], x["en"]))
json.dump(bones_out, io.open(f"{OUT}\\_pilot_bones.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(lm_out,   io.open(f"{OUT}\\bone_landmarks_v2.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

n_tr = sum(1 for l in lm_out if not l["approx"])
print(f"\nlandmarks: {len(lm_out)}  translated: {n_tr}  untranslated: {len(lm_out)-n_tr}")
for l in lm_out:
    flag = l["pl_from"] if not l["approx"] else "!!"
    print(f"  [{l['boneId']:10}] {flag:6} {l['en']:42} -> {l['pl']}")
