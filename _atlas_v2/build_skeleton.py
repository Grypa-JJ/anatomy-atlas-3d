# Full skeleton extraction: Z-Anatomy SkeletalSystem100 -> atlas v2 data
import trimesh, json, re, io, os, sys, collections, numpy as np, difflib
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zatrans

SRC  = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"
PROJ = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie"
BUILD= r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\build"
OBJD = BUILD + r"\obj"
os.makedirs(OBJD, exist_ok=True)

def to_atlas(V):
    V = np.asarray(V, dtype=np.float64)
    out = np.empty_like(V)
    out[:,0] =  V[:,0]*1000.0
    out[:,1] = -V[:,2]*1000.0
    out[:,2] =  V[:,1]*1000.0
    return out

# ---------- dictionary ----------
_sl = json.load(open(f"{PROJ}\\slownik_anatomiczny_umed_pl_en.json", encoding="utf-8"))
EN2PL = {}
for e in _sl: EN2PL.setdefault(e["en"].lower().strip(), e["pl"])
def _norm(s):
    s = re.sub(r'\b(of|the|a|for)\b',' ', s.lower()); return re.sub(r'\s+',' ',s).strip()
NORM2PL = {}
for k,v in EN2PL.items(): NORM2PL.setdefault(_norm(k), v)
NORM_KEYS = list(NORM2PL.keys())
ORD = {"first":"I","second":"II","third":"III","fourth":"IV","fifth":"V","sixth":"VI",
       "seventh":"VII","eighth":"VIII","ninth":"IX","tenth":"X","eleventh":"XI","twelfth":"XII"}
MANUAL = {
  "hip bone":"Kość miedniczna","clavicle":"Obojczyk","scapula":"Łopatka","humerus":"Kość ramienna",
  "radius":"Kość promieniowa","ulna":"Kość łokciowa","femur":"Kość udowa","patella":"Rzepka",
  "tibia":"Kość piszczelowa","fibula":"Kość strzałkowa","talus":"Kość skokowa","calcaneus":"Kość piętowa",
  "navicular bone":"Kość łódkowata","cuboid bone":"Kość sześcienna","sacrum":"Kość krzyżowa",
  "coccyx":"Kość guziczna","frontal bone":"Kość czołowa","parietal bone":"Kość ciemieniowa",
  "occipital bone":"Kość potyliczna","temporal bone":"Kość skroniowa","sphenoid bone":"Kość klinowa",
  "ethmoid bone":"Kość sitowa","nasal bone":"Kość nosowa","lacrimal bone":"Kość łzowa",
  "zygomatic bone":"Kość jarzmowa","palatine bone":"Kość podniebienna","vomer":"Lemiesz",
  "maxilla":"Szczęka","mandible":"Żuchwa","hyoid bone":"Kość gnykowa","vertebra":"Krąg",
  "atlas (c1)":"Kręg szczytowy (C1)","axis (c2)":"Kręg obrotowy (C2)",
  "manubrium of sternum":"Rękojeść mostka","body of sternum":"Trzon mostka","xiphoid process":"Wyrostek mieczykowaty",
  "scaphoid bone":"Kość łódeczkowata","lunate bone":"Kość księżycowata","triquetrum bone":"Kość trójgraniasta",
  "pisiform bone":"Kość grochowata","trapezium bone":"Kość czworoboczna większa",
  "trapezoid bone":"Kość czworoboczna mniejsza","capitate bone":"Kość główkowata","hamate bone":"Kość haczykowata",
  "medial cuneiform bone":"Kość klinowata przyśrodkowa","intermediate cuneiform bone":"Kość klinowata pośrednia",
  "lateral cuneiform bone":"Kość klinowata boczna","inferior nasal concha bone":"Małżowina nosowa dolna",
  "malleus":"Młoteczek","incus":"Kowadełko","stapes":"Strzemiączko","sesamoid bones of foot":"Kości trzeszczkowate stopy",
}
TOOTH_PL = {"incisor":"Siekacz","canine":"Kieł","premolar":"Ząb przedtrzonowy","molar":"Ząb trzonowy"}
def translate(en):
    n = en.lower().strip()
    if n in MANUAL: return MANUAL[n], "manual"
    # vertebrae: "Vertebra C3" -> "Krąg szyjny III"
    m = re.match(r'^vertebra ([ctl])(\d+)$', n)
    if m:
        reg={"c":"szyjny","t":"piersiowy","l":"lędźwiowy"}[m.group(1)]
        rom={1:"I",2:"II",3:"III",4:"IV",5:"V",6:"VI",7:"VII",8:"VIII",9:"IX",10:"X",11:"XI",12:"XII"}[int(m.group(2))]
        return f"Krąg {reg} {rom}", "vertebra"
    # teeth: "Upper first molar tooth", "Lower canine", "Upper lateral incisor"
    m = re.match(r'^(upper|lower) (?:(first|second|third) )?(medial |lateral )?(incisor|canine|premolar|molar)(?: tooth)?$', n)
    if m:
        jaw = "górny" if m.group(1)=="upper" else "dolny"
        base = TOOTH_PL[m.group(4)]
        adj = jaw
        if m.group(3): adj = ("przyśrodkowy " if "medial" in m.group(3) else "boczny ")+jaw
        num = {"first":"pierwszy ","second":"drugi ","third":"trzeci ",None:""}[m.group(2)]
        # decline: Siekacz boczny górny / Ząb trzonowy pierwszy górny
        if m.group(4) in ("incisor","canine"):
            return f"{base} {adj}".strip(), "tooth"
        return f"{base} {num}{jaw}".strip(), "tooth"
    m = re.match(r'^(anterior|middle|posterior) cells of ethmoid bone$', n)
    if m:
        p={"anterior":"przednie","middle":"środkowe","posterior":"tylne"}[m.group(1)]
        return f"Komórki sitowe {p}", "ethmoid"
    m = re.match(r'^(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth) (rib|metacarpal bone|metatarsal bone)$', n)
    if m:
        base = {"rib":"Żebro","metacarpal bone":"Kość śródręcza","metatarsal bone":"Kość śródstopia"}[m.group(2)]
        return f"{base} {ORD[m.group(1)]}", "ordinal"
    m = re.match(r'^(proximal|middle|distal) phalanx of (first|second|third|fourth|fifth) finger of (hand|foot)$', n)
    if m:
        pos={"proximal":"bliższy","middle":"środkowy","distal":"dalszy"}[m.group(1)]
        loc={"hand":"ręki","foot":"stopy"}[m.group(3)]
        return f"Paliczek {pos} {ORD[m.group(2)]} palca {loc}", "phalanx"
    return zatrans.translate(en)

# ---------- load + classify (mirror of classify.py) ----------
RX_ATTACH=re.compile(r'\.(?:[oe]\d*[rl])$'); RX_POINT=re.compile(r'\.(i|j)$')
RX_SIDE=re.compile(r'\.(r|l)$'); RX_FRAG=re.compile(r'\.(r|l)_(\d+)$'); RX_US=re.compile(r'_(\d+)$')
def clsfy(name):
    if RX_ATTACH.search(name): return "attach", RX_ATTACH.sub('',name)
    if RX_POINT.search(name):  return ("pt_L" if RX_POINT.search(name).group(1)=="i" else "pt_R"), RX_POINT.sub('',name)
    if RX_FRAG.search(name):   return ("bodyL" if RX_FRAG.search(name).group(1)=="l" else "bodyR"), RX_FRAG.sub('',name)
    if RX_SIDE.search(name):   return ("bodyL" if RX_SIDE.search(name).group(1)=="l" else "bodyR"), RX_SIDE.sub('',name)
    return "bodyM", name
def strip_piece(b): return RX_US.sub('', b)

NONBONE=re.compile(r'ligament|membrane|aponeurosis|retinaculum|fascia|raphe|tendon|meniscus|labrum|cartilage|bursa|\bcapsule\b|nerve|artery|vein|\bdisc\b|symphysis|\bgland\b',re.I)
TOOTH=re.compile(r'\b(incisor|canine|premolar|molar|wisdom tooth)\b',re.I)
OSSICLE=re.compile(r'\b(malleus|incus|stapes)\b',re.I)
FW={"process","tubercle","tuberosity","fossa","notch","groove","sulcus","crest","line","linea","ridge","border","margin","angle","surface","facet","head","neck","body","base","apex","spine","foramen","canal","condyle","epicondyle","malleolus","trochlea","trochanter","protuberance","eminence","impression","hamulus","cornu","ala","arch","lamina","pedicle","wing","horn","part","hiatus","fovea","incisure","dens","promontory","sustentaculum","conus"}
FSTAND=re.compile(r'^(pterion|bregma|lambda|inion|nasion|gnathion|asterion|sinus of \w+|infrasternal angle|sternal angle|costal (arch|margin)|linea aspera|pecten pubis)\b',re.I)
def is_feat(name):
    n=name.strip().lower()
    if n=="body of sternum": return False
    if FSTAND.match(n): return True
    if " of " in n and n.split(" of ")[0].split()[-1] in FW: return True
    return False

scene = trimesh.load(f"{SRC}\\SkeletalSystem100.glb")
G=[]  # geometry instances with atlas-space mesh
for node in scene.graph.nodes_geometry:
    tf,gname = scene.graph[node]
    g = scene.geometry[gname].copy(); g.apply_transform(tf)
    g.vertices = to_atlas(g.vertices)
    k,base = clsfy(gname); base = strip_piece(base)
    G.append({"geom":gname,"kind":k,"base":base,"mesh":g,"cx":float(g.centroid[0])})

muscle_bases = set(x["base"] for x in G if x["kind"]=="attach")

def cat_of(b):
    if TOOTH.search(b): return "tooth"
    if OSSICLE.search(b): return "ossicle"
    return "bone"

# ---------- assemble bone objects ----------
groups = collections.defaultdict(list)   # base -> list of body geom dicts
for x in G:
    if not x["kind"].startswith("body"): continue
    if len(x["mesh"].vertices) < 40: continue
    b = x["base"]
    if b in muscle_bases or NONBONE.search(b) or is_feat(b): continue
    groups[b].append(x)

objects = []   # {id, en, pl, side, category, mesh}
for b, items in sorted(groups.items()):
    xs = [it["cx"] for it in items]
    paired = any(v>12 for v in xs) and any(v<-12 for v in xs)
    cat = cat_of(b)
    slug = re.sub(r'[^a-z0-9]+','_', b.lower()).strip('_')
    if paired:
        for side,sign,en_sfx in (("l",1,"left"),("r",-1,"right")):
            parts=[it["mesh"] for it in items if (it["cx"]>0)==(sign>0)]
            if not parts: continue
            mesh=trimesh.util.concatenate(parts)
            pl,how=translate(b); pl=zatrans.strip_side(pl)
            objects.append({"id":f"{slug}_{side}","en":f"{en_sfx} {b}",
                            "pl":(pl + zatrans.side_label(b, side)).strip(),
                            "side":side,"category":cat,"kind":("tooth" if cat=="tooth" else "bone"),"mesh":mesh,"pl_from":how})
    else:
        mesh=trimesh.util.concatenate([it["mesh"] for it in items])
        pl,how=translate(b); pl=zatrans.strip_side(pl)
        objects.append({"id":slug,"en":b,"pl":pl,"side":"mid","category":cat,"kind":("tooth" if cat=="tooth" else "bone"),"mesh":mesh,"pl_from":how})

# ---------- per-side KDTrees over bone/ossicle vertices for landmark routing ----------
route_objs=[o for o in objects if o["category"] in ("bone","ossicle")]
def build_tree(pred):
    vs=[]; own=[]
    for i,o in enumerate(route_objs):
        if not pred(o): continue
        v=np.asarray(o["mesh"].vertices); vs.append(v); own.append(np.full(len(v),i))
    return cKDTree(np.vstack(vs)), np.concatenate(own)
tree_L,own_L = build_tree(lambda o:o["side"] in ("l","mid"))
tree_R,own_R = build_tree(lambda o:o["side"] in ("r","mid"))

# ---------- native landmark points ----------
# drop collection/grouping annotation points (plurals & region aggregates)
COLLECTION=re.compile(r'^(bones?|phalanges|metacarpal bones|metatarsal bones|tarsal bones|'
    r'carpal bones|ribs|true ribs|false ribs|floating ribs|costal cartilages|vertebrae|'
    r'sesamoid bones|cervical|thoracic|lumbar|vertebral column|thoracic cage|rib cage|'
    r'bony (pelvis|thorax)|pelvic (girdle|inlet|outlet)|pectoral girdle|skull|cranium|'
    r'facial skeleton|neurocranium|viscerocranium|axial skeleton|appendicular skeleton|'
    r'upper limb|lower limb|free (part|limb)|linea terminalis|pelvic (inlet|outlet)|'
    r'thoracic (inlet|outlet)|superior thoracic aperture|inferior thoracic aperture|'
    r'intercostal space|infrasternal angle|costal (arch|margin)|subpubic angle)\b', re.I)
# ---- name-based routing ---------------------------------------------------
# index route objects by their english bone phrase, per side
def obj_index(side):
    idx={}
    for o in route_objs:
        if o["side"] not in (side,"mid"): continue
        en=o["en"].lower().replace("left ","").replace("right ","").strip()
        for k in {en, re.sub(r'\bbone\b','',en).strip(), re.sub(r'\s*\([^)]*\)','',en).strip()}:
            if k: idx.setdefault(k,o)
    return idx
IDX={"l":obj_index("l"),"r":obj_index("r")}

# feature word -> owning bone english phrase
FEAT2BONE=[
 (r'glenoid|coracoid|acromi|supraspinous fossa|infraspinous fossa|subscapular fossa|'
  r'spine of scapula|spinoglenoid|(supra|infra)glenoid|scapular notch|neck of scapula|'
  r'(superior|inferior|lateral|medial) (angle|border) of scapula|costal surface of scapula', 'scapula'),
 (r'acetabul|iliac (crest|fossa|tuberosity|spine|tubercle)|(anterior|posterior) (superior|inferior) iliac spine|'
  r'ischial (spine|tuberosity|ramus)|(greater|lesser) sciatic notch|obturator (foramen|groove|crest|tubercle)|'
  r'pubic (tubercle|crest|symphysis|ramus)|pecten pubis|iliopubic eminence|body of ilium|body of ischium|body of pubis|'
  r'(inner|outer) lip of iliac crest|gluteal (line|surface)|arcuate line', 'hip bone'),
 (r'(greater|lesser|third) trochanter|trochanteric (fossa|line|crest)|linea aspera|gluteal tuberosity|'
  r'pectineal line of femur|patellar surface|intercondylar (fossa|line|area)|adductor tubercle|'
  r'(medial|lateral) (condyle|epicondyle|supracondylar) of femur|quadrate tubercle|popliteal surface|'
  r'head of femur|fovea|neck of femur|body of femur|(medial|lateral) lip of linea', 'femur'),
 (r'medial malleolus|malleolar (groove|facet)|tibial (tuberosity|plateau)|soleal line|'
  r'(medial|lateral) condyle of tibia|intercondylar (eminence|tubercle)|anterior border of tibia|'
  r'(medial|lateral|posterior) surface of tibia|body of tibia', 'tibia'),
 (r'lateral malleolus|(head|neck|apex of head|body) of fibula|(anterior|posterior|interosseous) border of fibula|'
  r'(medial|lateral|posterior|posteromedial) surface of fibula|fibular notch', 'fibula'),
 (r'olecranon(?! fossa)|trochlear notch|radial notch|coronoid process of ulna|(head|body|styloid process) of ulna|'
  r'ulnar tuberosity|tuberosity of ulna|supinator crest|sublime tubercle|(anterior|posterior|medial) surface of ulna', 'ulna'),
 (r'radial (tuberosity|notch)|tuberosity of radius|(head|neck|body|styloid process) of radius|'
  r'(anterior|posterior|lateral) surface of radius|dorsal (radial )?tubercle|grooves for extensor tendons|'
  r'ulnar notch|articular circumference of head of radius|supinator crest of radius', 'radius'),
 (r'capitulum|trochlea of humerus|(greater|lesser) tubercle|crest of (greater|lesser) tubercle|'
  r'intertubercular|bicipital groove|deltoid tuberosity|radial groove|(surgical|anatomical) neck|'
  r'(coronoid|radial|olecranon) fossa|(medial|lateral) (epicondyle|supracondylar ridge)|condyle of humerus|'
  r'head of humerus|body of humerus|(anterior|posterior|anterolateral|anteromedial) surface of humerus|'
  r'(anterior|medial|lateral) border of humerus', 'humerus'),
 (r'dens|odontoid|(anterior|posterior) tubercle of atlas|(anterior|posterior) arch of atlas|'
  r'transverse ligament tubercle|apex of dens|articular facet of dens', 'axis'),
 (r'occipital condyle|foramen magnum|pharyngeal tubercle|(external|internal) occipital (crest|protuberance)|'
  r'(superior|inferior|supreme) nuchal line|hypoglossal canal|jugular (process|notch of occipital)', 'occipital bone'),
 (r'sella turcica|(anterior|middle|posterior) clinoid|dorsum sellae|tuberculum sellae|'
  r'(greater|lesser) wing|pterygoid (plate|process|hamulus|fossa)|foramen (ovale|rotundum|spinosum)|'
  r'optic canal|chiasmatic|carotid sulcus', 'sphenoid bone'),
 (r'petrous|mastoid (process|notch|foramen)|styloid process of temporal|tympanic|'
  r'(internal|external) acoustic|arcuate eminence|tegmen tympani|zygomatic process of temporal', 'temporal bone'),
 (r'superciliary arch|glabella|supra-?orbital (notch|margin|foramen)|frontal (crest|eminence|sinus)|'
  r'trochlear (fovea|spine)|zygomatic process of frontal|nasal (part|spine) of frontal', 'frontal bone'),
 (r'ethmoidal (notch|cells|labyrinth)|crista galli|cribriform|perpendicular plate of ethmoid|'
  r'(superior|middle) nasal concha|uncinate process of ethmoid', 'ethmoid bone'),
 (r'sagittal (border|margin)|parietal (eminence|foramen|tuber)|(superior|inferior) temporal line', 'parietal bone'),
]
ORD_RE={"first":1,"second":2,"third":3,"fourth":4,"fifth":5,"sixth":6,"seventh":7,"eighth":8,
        "ninth":9,"tenth":10,"eleventh":11,"twelfth":12}
ROM={1:"i",2:"ii",3:"iii",4:"iv",5:"v",6:"vi",7:"vii",8:"viii",9:"ix",10:"x",11:"xi",12:"xii"}

def route_by_name(base, side):
    n=base.lower()
    idx=IDX[side]
    # explicit "... of <bone phrase>"
    m=re.search(r' of (?:the )?(.+)$', n)
    if m:
        tail=m.group(1).strip()
        mo=re.match(r'(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth) (rib|thoracic vertebra|lumbar vertebra|cervical vertebra|metacarpal|metatarsal)', tail)
        if mo:
            k=ORD_RE[mo.group(1)]; t=mo.group(2)
            if t=="rib": return idx.get(f"{ROM[k]} rib") or idx.get(f"rib {ROM[k]}")
            if "vertebra" in t:
                reg={"thoracic":"t","lumbar":"l","cervical":"c"}[t.split()[0]]
                return idx.get(f"vertebra {reg}{k}")
            if t in("metacarpal","metatarsal"):
                return idx.get(f"{ROM[k]} {t} bone")
        for en,o in idx.items():
            if en and (en==tail or en in tail or tail in en) and len(en)>3:
                return o
    # feature-word map
    for rx,bonephrase in FEAT2BONE:
        if re.search(rx,n):
            return idx.get(bonephrase) or idx.get(re.sub(r'\bbone\b','',bonephrase).strip())
    # direct: name starts with a bone phrase
    for en,o in sorted(idx.items(),key=lambda kv:-len(kv[0])):
        if en and len(en)>4 and n.startswith(en):
            return o
    return None

bone_id_set = set(o["en"].lower() for o in objects)
seen=set(); landmarks=[]
routing_stats=collections.Counter()
for x in G:
    if x["kind"] not in ("pt_L","pt_R"): continue
    m=x["mesh"]
    if len(m.vertices)>600: continue
    base=x["base"]
    if base in muscle_bases: continue
    if COLLECTION.match(base): continue
    c=np.asarray(m.centroid)
    side = "l" if x["kind"]=="pt_L" else "r"
    tree,own = (tree_L,own_L) if side=="l" else (tree_R,own_R)
    d_sp,idx_sp = tree.query(c); o_sp = route_objs[own[idx_sp]]
    o_name = route_by_name(base, side)
    if o_name is not None and o_name["id"]!=o_sp["id"]:
        dn = float(np.min(np.linalg.norm(np.asarray(o_name["mesh"].vertices)-c,axis=1)))
        # name wins only if it is also spatially reasonable (joints: point sits
        # between two bones, so name disambiguates; generic names near one-of-many
        # would drag the point onto the wrong sibling -> keep spatial there)
        if dn <= max(25.0, d_sp + 12.0):
            o, d, how_route = o_name, dn, "name"
        else:
            o, d, how_route = o_sp, d_sp, "spatial(name-far)"
    elif o_name is not None:
        o, d, how_route = o_name, d_sp, "name=spatial"
    else:
        o, d, how_route = o_sp, d_sp, "spatial"
    routing_stats[how_route]+=1
    key=(o["id"],base)
    if key in seen: continue
    seen.add(key)
    pl,how=translate(base)
    landmarks.append({"boneId":o["id"],"en":base,"pl":pl,"pl_from":how,"route":how_route,
                      "approx":(how=="none"),"dist_mm":round(float(d),1),
                      "pos":[round(float(v),2) for v in c]})

# ---------- write ----------
for o in objects:
    o["mesh"].export(f"{OBJD}\\{o['id']}.obj", include_texture=False)

def dump(path, data): json.dump(data, io.open(path,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
bones_meta=[{k:o[k] for k in ("id","pl","en","side","category","kind","pl_from")} for o in objects if o["category"]!="tooth"]
teeth_meta=[{k:o[k] for k in ("id","pl","en","side","category","kind","pl_from")} for o in objects if o["category"]=="tooth"]
dump(f"{BUILD}\\all_bones_labeled_v2.json", bones_meta)
dump(f"{BUILD}\\all_teeth_labeled_v2.json", teeth_meta)
dump(f"{BUILD}\\skeleton_landmarks_v2.json", [{k:l[k] for k in ("boneId","en","pl","pos","approx","pl_from","dist_mm","route")} for l in landmarks])

print(f"bone/ossicle objects: {len(route_objs)}   tooth objects: {len(teeth_meta)}   total obj files: {len(objects)}")
print(f"landmarks routed: {len(landmarks)}   untranslated: {sum(l['approx'] for l in landmarks)}")
print(f"routing: {dict(routing_stats)}")
far=[l for l in landmarks if l['dist_mm']>15]
print(f"landmarks >15mm from routed bone: {len(far)}  (sample: {[(l['en'],l['dist_mm'],l['route']) for l in far[:8]]})")
bad=[o['id'] for o in objects if o['pl_from']=='none']
print(f"bones with no PL: {bad}")
