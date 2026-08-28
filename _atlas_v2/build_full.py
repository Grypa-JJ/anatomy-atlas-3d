# Build Atlas v3 data from the FULL Z-Anatomy .blend dump (blend_dump3/ + blend_dump/inventory.json).
import json, re, io, os, collections, numpy as np, sys, subprocess, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zatrans
from scipy.spatial import cKDTree

D3   = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\blend_dump8"  # hi-poly (Subsurf baked in Blender)
INV  = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\blend_dump\inventory.json"
BUILD= r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\build_full"
OBJD = BUILD + r"\obj"
os.makedirs(OBJD, exist_ok=True)

objs = json.load(open(f"{D3}\\objects.json", encoding="utf-8"))
for o in objs:
    if "idx" not in o and "gi" in o: o["idx"] = o["gi"]   # dump6 uses 'gi'
inv  = {x["name"]: x for x in json.load(open(INV, encoding="utf-8"))}
FONT_POS = {}   # modifier-evaluated FONT label positions (blend_dump6b)
_fp = f"{D3}\\labels_eval.json"
if os.path.exists(_fp):
    FONT_POS = {x["name"]: x["pos"] for x in json.load(open(_fp, encoding="utf-8"))}
for o in objs:
    o["parent"] = (inv.get(o["name"], {}) or {}).get("parent")

# ---------- suffix grammar ----------
RX_ATTACH = re.compile(r'\.(?:[oe]\d*[rl])$')
RX_POINT  = re.compile(r'\.(i|j)$')
RX_SIDE   = re.compile(r'\.(r|l)$')
RX_FRAG   = re.compile(r'\.(r|l)_(\d+)$')
RX_US     = re.compile(r'_(\d+)$')
RX_G      = re.compile(r'\.g$')
def role(name):
    if RX_ATTACH.search(name): return "attach", RX_ATTACH.sub('', name)
    if RX_POINT.search(name):
        s = RX_POINT.search(name).group(1)
        return ("ptL" if s == "i" else "ptR"), RX_POINT.sub('', name)
    if RX_FRAG.search(name):
        s = RX_FRAG.search(name).group(1)
        return ("bodyL" if s == "l" else "bodyR"), RX_FRAG.sub('', name)
    if RX_SIDE.search(name):
        s = RX_SIDE.search(name).group(1)
        return ("bodyL" if s == "l" else "bodyR"), RX_SIDE.sub('', name)
    if RX_G.search(name): return "skip", RX_G.sub('', name)
    return "bodyM", name
def strip_us(b): return RX_US.sub('', b)

# ---------- layer classification ----------
TOOTH = re.compile(r'\b(incisor|canine|premolar|molar|wisdom tooth|deciduous tooth)\b', re.I)
CARTILAGE = re.compile(r'\bcartilage\b|\bmeniscus\b|\blabrum\b|intervertebral disc|\bdisc of\b', re.I)
def layer_of(o):
    s = o["system"]; p = (o["path"] or "")
    name = o["name"]
    if s == "1: Skeletal system":
        if TOOTH.search(name): return "tooth"
        if CARTILAGE.search(name): return "connective"
        return "bone"
    if s == "4: Muscular system": return "muscle"
    if s == "2: Muscular insertions": return "muscle"     # attach points live here
    if s == "3: Joints": return "connective"
    if s == "6: Lymphoid organs": return "lymph"
    if s == "8: Visceral systems": return "organ"
    if s == "5: Cardiovascular system":
        return "organ" if re.search(r'ventricle|atrium|valve|leaflet|papillary|cusp|myocard|pericard|septum|chordae|trabecula', name, re.I) else "vessel"
    if s == "7: Nervous system & Sense organs":
        if "/Central nervous system" in p: return "brain"
        if "/Peripheral nervous system" in p: return "nerve"
        if "/Sense organs" in p: return "organ"
        # fallback by name
        if re.search(r'nerve|plexus|ganglion|ramus', name, re.I): return "nerve"
        if re.search(r'eye|ear|cochlea|retina|iris|tympan|auricle|lacrimal', name, re.I): return "organ"
        return "brain"
    if s == "9: Regions of human body": return "region"
    # None system: guess from bonus path
    if "Nervous system/Central" in p: return "brain"
    if "Nervous system/Peripheral" in p: return "nerve"
    if "Muscular" in p: return "muscle"
    if "Skeletal" in p: return "bone"
    if "Cardiovascular" in p: return "vessel"
    if "Visceral" in p: return "organ"
    return "other"

# ---------- assemble ----------
def to_atlas(P):  # blender metres, Z-up -> atlas mm, Z-up (identity rotation)
    return (np.asarray(P, float) * 1000.0)

def load_obj(idx):
    V=[]; F=[]
    with open(f"{D3}\\obj\\{idx}.obj", encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("v "):
                _,x,y,z = ln.split(); V.append((float(x),float(y),float(z)))
            elif ln.startswith("f "):
                a = [int(t.split("/")[0])-1 for t in ln.split()[1:]]
                for k in range(1,len(a)-1): F.append((a[0],a[k],a[k+1]))
    return np.array(V), np.array(F)

def write_obj(path, V, F):
    with io.open(path,"w",encoding="utf-8") as f:
        f.write("".join(f"v {x:.4f} {y:.4f} {z:.4f}\n" for x,y,z in V))
        if len(F): f.write("".join(f"f {a+1} {b+1} {c+1}\n" for a,b,c in F))

JUNK = re.compile(r'-(curve|profile|mesh|shape)(\.[a-z](_\d+)?)?$|^(meridians?|equator|axis) of |'
    r'\bhelper\b|\bempty\b|^ico|^plane\b|^cube\b|^cylinder\b|bezier|^nurbs|^\?|^\s*$', re.I)
objs = [o for o in objs if not JUNK.search(o["name"])]
for o in objs:
    o["role"], o["base"] = role(o["name"])
    o["base"] = strip_us(o["base"])
    o["layer"] = layer_of(o)

muscle_bases = set(o["base"] for o in objs if o["role"] == "attach")

# ---- bodies ----
bodies = collections.defaultdict(list)   # (layer, base) -> [obj]
for o in objs:
    if not o["role"].startswith("body"): continue
    if o["layer"] in ("region", "other"): continue
    if o["base"] in muscle_bases and o["layer"] != "muscle":  # attachment footprints elsewhere
        pass
    bodies[(o["layer"], o["base"])].append(o)

catalog = []   # {id, en, pl, side, kind, pl_from}
id_by_key = {}
for (layer, base), items in sorted(bodies.items()):
    xs = [it["wcentroid"][0] for it in items]
    paired = any(x > 0.012 for x in xs) and any(x < -0.012 for x in xs)
    slug = re.sub(r'[^a-z0-9]+', '_', base.lower()).strip('_')
    if not slug or len(base.strip()) < 2: continue
    pl, how = zatrans.translate(base); pl = zatrans.strip_side(pl)
    def emit(oid, side, parts):
        Vs=[]; Fs=[]; off=0
        for it in parts:
            V,F = load_obj(it["idx"]);
            if len(V)==0: continue
            Vs.append(to_atlas(V))
            if len(F): Fs.append(F+off)
            off += len(V)
        if not Vs: return
        V = np.vstack(Vs); F = np.vstack(Fs) if Fs else np.zeros((0,3),int)
        # Z-Anatomy ships many bones/joints as low-poly cages meant to be Subsurf'd
        # (modifier is display-disabled in the .blend). Smooth them here so they don't
        # look faceted next to the already-hi-poly meshes.
        # (Subsurf is now baked in Blender at extraction time — see blend_extract8.py)
        write_obj(f"{OBJD}\\{oid}.obj", V, F)
        catalog.append({"id":oid,"en":base,"pl":(pl+zatrans.side_label(base,side)).strip(),
                        "side":side,"kind":layer,"pl_from":how})
        id_by_key[(layer, base, side)] = oid
    if paired:
        for side,sign in (("l",1),("r",-1)):
            parts=[it for it in items if (it["wcentroid"][0]>0)==(sign>0)]
            if parts: emit(f"{slug}_{side}", side, parts)
    else:
        emit(slug, "mid", items)

print(f"catalog bodies: {len(catalog)}   by kind: {collections.Counter(c['kind'] for c in catalog)}")

# ---- landmarks: .i/.j feature meshes + FONT .t/.s labels ----
route_objs = [c for c in catalog if c["kind"] in ("bone","tooth","ossicle","muscle","connective","organ","brain","nerve","vessel","lymph")]
def side_trees():
    T={}
    for side_key,pred in (("l", lambda o:o["side"] in ("l","mid")), ("r", lambda o:o["side"] in ("r","mid"))):
        vs=[];ow=[];lst=[]
        for c in route_objs:
            if not pred(c): continue
            V,_=load_obj_cat(c["id"]);
            if len(V)==0: continue
            j=len(lst); lst.append(c); vs.append(V); ow.append(np.full(len(V),j))
        T[side_key]=(cKDTree(np.vstack(vs)), np.concatenate(ow), lst)
    return T
def load_obj_cat(oid):
    V=[];F=[]
    with open(f"{OBJD}\\{oid}.obj",encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("v "): _,x,y,z=ln.split(); V.append((float(x),float(y),float(z)))
    return np.array(V), None
TREES = side_trees()

_INV_PARENT = {n: (r.get("parent")) for n, r in inv.items()}
def resolve_parent(name):
    seen = set(); cur = _INV_PARENT.get(name)
    while cur and cur not in seen:
        seen.add(cur)
        if not re.search(r'\.(t|s|i|j)$', cur):
            return cur
        cur = _INV_PARENT.get(cur)
    return cur
_BASE_TO_IDS = collections.defaultdict(list)
for (lay, b, sk), oid in id_by_key.items():
    _BASE_TO_IDS[strip_us(b).lower()].append((lay, sk, oid))

def route_landmark(name, pos_atlas, side_hint):
    struct = resolve_parent(name)
    if struct:
        pb = strip_us(re.sub(r'\.(l|r|i|j|s|t)$', '', struct)).lower()
        cands = _BASE_TO_IDS.get(pb, [])
        if cands:
            for lay, sk, oid in cands:
                if sk == side_hint: return oid, "parent"
            return cands[0][2], "parent"
    sk = side_hint if side_hint in ("l", "r") else "l"
    tr, ow, lst = TREES[sk]
    d, ix = tr.query(pos_atlas)
    return lst[ow[ix]]["id"], "spatial"

# collective / organizational label names — NOT real point features
COLLECTIVE = re.compile(
    r'\b(muscles|bones|nerves|organs|arteries|veins|ligaments|joints|glands|'
    r'system|systems|tree|structures|apparatus|region|regions|cavity|cavities|'
    r'skeleton|viscera|cartilages|ossicles|sinuses|meninges|plexuses|ganglia|'
    r'extrinsic|intrinsic|group of|parts of|division of|branches of)\b'
    r'|^(midbrain|pons|medulla oblongata|brainstem|brain|cerebrum|cerebellum|'
    r'diencephalon|telencephalon|forebrain|hindbrain|spinal cord|'
    r'central nervous system|peripheral nervous system|autonomic nervous system|'
    r'facial (bones|muscles|skeleton)|axial skeleton|appendicular skeleton|'
    r'thoracic (cage|wall)|abdominal wall|pelvic (floor|girdle)|pectoral girdle|'
    r'upper limb|lower limb|free (part|limb)|trunk|head|neck|thorax|abdomen)$',
    re.I)

landmarks=[]
lm_by_key={}
_lm_trees_dirty=True
def norm_lm(s): return re.sub(r'[^a-z0-9]+',' ',s.lower()).strip()
def add_lm(oid, base, pos, src):
    if COLLECTIVE.search(base.strip("() ")): return
    pl,pf = zatrans.translate(base); pl=zatrans.strip_side(pl)
    rec={"boneId":oid,"en":base,"pl":pl,"approx":pf=="none",
         "pos":[round(float(v),2) for v in pos],"src":src}
    # dedupe on (owner, PL name) — different EN spellings of one point collapse
    for kk in ((oid, norm_lm(base)), (oid, norm_lm(pl))):
        if kk in lm_by_key:
            if src=="feature" and lm_by_key[kk]["src"]=="label":
                lm_by_key[kk].update(pos=rec["pos"], src="feature")
            return
    # dedupe on proximity: same owner, another point < 6mm away
    pa = np.array(rec["pos"])
    for ex in lm_by_key.values():
        if ex["boneId"]==oid and np.linalg.norm(np.array(ex["pos"])-pa) < 6:
            return
    lm_by_key[(oid, norm_lm(base))]=rec; landmarks.append(rec)

# 2a. .i/.j feature meshes (real geometry -> use centroid)
for o in objs:
    if o["role"] not in ("ptL","ptR"): continue
    if o["nverts"] > 6000: continue
    side = "l" if o["role"]=="ptL" else "r"
    pos = to_atlas(o["wcentroid"])
    oid, _ = route_landmark(o["name"], pos, side)
    add_lm(oid, o["base"], pos, "feature")
# 2b. FONT .t/.s labels (for named points that have no .i/.j mesh)
for name,r in inv.items():
    if r["type"]!="FONT": continue
    base = re.sub(r'\.(t|s)$','',name)
    raw = FONT_POS.get(name) or r["world_loc"]
    pos = to_atlas(raw)
    side = "l" if pos[0] > 12 else ("r" if pos[0] < -12 else "mid")
    add_lm(route_landmark(name, pos, side)[0], base, pos, "label")

print(f"landmarks: {len(landmarks)} (feature {sum(1 for l in landmarks if l['src']=='feature')}, label {sum(1 for l in landmarks if l['src']=='label')})")

# ---- snap landmarks onto their owner structure's surface (points must sit ON the bone) ----
_cat_by_id = {c["id"]: c for c in catalog}
_surf_cache = {}
def _surf(oid):
    if oid not in _surf_cache:
        try:
            v = np.array([[float(t) for t in l.split()[1:]] for l in open(f"{OBJD}\\{oid}.obj") if l.startswith("v ")])
            _surf_cache[oid] = cKDTree(v[::2]) if len(v) else None
        except Exception:
            _surf_cache[oid] = None
    return _surf_cache[oid]
snapped = 0
for l in landmarks:
    tr = _surf(l["boneId"])
    if tr is None: continue
    p = np.array(l["pos"], float)
    d, ix = tr.query(p)
    if d > 6.0:                       # only nudge points that float
        # move 70% of the way to the surface (keeps a hair of offset so the dot reads as ON, not INSIDE)
        target = tr.data[ix]
        newp = p + (target - p) * 0.82
        l["pos"] = [round(float(x), 2) for x in newp]
        snapped += 1
print(f"landmarks snapped to surface: {snapped}/{len(landmarks)}")

# ---- write per-kind catalogues + combined landmarks ----
def dump(p,d): json.dump(d, io.open(p,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
KMAP={"bone":"bones","tooth":"teeth","muscle":"muscles","connective":"connective","vessel":"vessels",
      "nerve":"nerves","brain":"brain","organ":"organs","lymph":"lymph","region":"regions"}
for kind,fk in KMAP.items():
    rows=[{k:c[k] for k in ("id","pl","en","side","kind","pl_from")} for c in catalog if c["kind"]==kind]
    if rows: dump(f"{BUILD}\\all_{fk}_labeled_v2.json", rows)
dump(f"{BUILD}\\bone_landmarks_v2.json",
     [{k:l[k] for k in ("boneId","en","pl","pos","approx","src")} for l in landmarks])

tot=len(catalog); un=sum(1 for c in catalog if c["pl_from"]=="none")
lun=sum(1 for l in landmarks if l["approx"])
print(f"TOTAL objects {tot} ({un} EN)   landmarks {len(landmarks)} ({lun} EN)")
