# Generic Z-Anatomy layer extractor (vessels / organs / nerves / brain / lymph).
# Usage: python build_layer.py <glb> <layerspec>
# layerspec routes each body mesh to a `kind` via name regex; points route to nearest body of same kind.
import trimesh, json, re, io, os, sys, collections, numpy as np, difflib
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zatrans

SRC=r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"
PROJ=r"C:\Users\Jakub\Desktop\Prod\projekt w budowie"
BUILD=r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\build"
OBJD=BUILD+r"\obj"; os.makedirs(OBJD,exist_ok=True)

def to_atlas(V):
    V=np.asarray(V,dtype=np.float64); o=np.empty_like(V)
    o[:,0]=V[:,0]*1000.0; o[:,1]=-V[:,2]*1000.0; o[:,2]=V[:,1]*1000.0
    return o

# ---- dictionary ----
_sl=json.load(open(f"{PROJ}\\slownik_anatomiczny_umed_pl_en.json",encoding="utf-8"))
EN2PL={}
for e in _sl:
    for en in e["en"].split(";"): EN2PL.setdefault(en.lower().strip(),e["pl"])
for extra in ("all_vessels_labeled.json","all_organs_labeled.json","all_nerves_labeled.json",
              "all_brain_labeled.json","all_lymph_labeled.json"):
    p=f"{PROJ}\\{extra}"
    if os.path.exists(p):
        for e in json.load(open(p,encoding="utf-8")):
            if e.get("en"): EN2PL.setdefault(e["en"].lower().strip(),e["pl"])
def _norm(s):
    s=re.sub(r'\(.*?\)','',s.lower())
    s=re.sub(r"[’'`]",'',s)
    s=re.sub(r'\b(of|the|a|for|part|branch|branches)\b',' ',s)
    return re.sub(r'\s+',' ',s).strip()
NORM2PL={}
for k,v in EN2PL.items(): NORM2PL.setdefault(_norm(k),v)
NK=list(NORM2PL.keys())
def translate(en):
    n=en.lower().strip().strip("()").strip()
    n=re.sub(r'^(right|left)\s+','',n)
    if n in EN2PL: return EN2PL[n],"exact"
    nn=_norm(n)
    if nn in NORM2PL: return NORM2PL[nn],"norm"
    return zatrans.translate(en)

RX_POINT=re.compile(r'\.(i|j)$'); RX_SIDE=re.compile(r'\.(r|l)$')
RX_FRAG=re.compile(r'\.(r|l)_(\d+)$'); RX_US=re.compile(r'_(\d+)$')
def cls(name):
    if RX_POINT.search(name): return ("ptL" if RX_POINT.search(name).group(1)=="i" else "ptR"), RX_POINT.sub('',name)
    if RX_FRAG.search(name):  s=RX_FRAG.search(name).group(1); return ("bodyL" if s=="l" else "bodyR"), RX_FRAG.sub('',name)
    if RX_SIDE.search(name):  s=RX_SIDE.search(name).group(1); return ("bodyL" if s=="l" else "bodyR"), RX_SIDE.sub('',name)
    return "bodyM", name
def strip_us(b): return RX_US.sub('',b)

GLB=sys.argv[1]
SPEC=sys.argv[2]           # e.g. "vessel" or "nerve:brain" — kind, or kind with brain-split
scene=trimesh.load(f"{SRC}\\{GLB}")
inst=[]
for node in scene.graph.nodes_geometry:
    tf,g=scene.graph[node]; m=scene.geometry[g].copy(); m.apply_transform(tf)
    m.vertices=to_atlas(m.vertices)
    k,base=cls(g); base=strip_us(base)
    inst.append({"g":g,"k":k,"base":base,"m":m,"cx":float(m.centroid[0])})

# ---- kind routing for bodies ----
BRAIN=re.compile(r'\b(brain|cerebr|cerebell|telencephal|diencephal|mesencephal|metencephal|'
    r'myelencephal|pons|medulla oblongata|midbrain|thalamus|hypothalam|epithalam|'
    r'corpus callosum|fornix|internal capsule|basal (ganglia|nuclei)|caudate|putamen|'
    r'globus pallidus|substantia nigra|red nucleus|amygdala|hippocampus|gyrus|sulcus of (brain|cerebr)|'
    r'lobe|ventricle|choroid plexus|pineal|pituitary|infundibulum|olfactory bulb|optic (chiasm|tract)|'
    r'lamina terminalis|septum pellucidum|insula|operculum|limbic|cingulate|precuneus|cuneus|'
    r'white matter|grey matter|gray matter|cortex|arbor vitae|vermis|tonsil of cerebellum|'
    r'spinal cord|central canal|conus medullaris|cauda equina|filum terminale)\b',re.I)
EYE=re.compile(r'\b(eyeball|iris|pupil|retina|cornea|sclera|choroid of eye|ciliary|lens|'
    r'vitreous|aqueous|lacrimal|conjunctiva|eyelid|palpebra|tarsus|orbital fat|'
    r'extraocular|rectus muscle of eye|oblique muscle of eye|levator palpebrae|'
    r'anterior chamber|posterior chamber|fovea|macula|optic disc|ora serrata|'
    r'zonule|canal of schlemm|dilator pupillae|sphincter pupillae)\b',re.I)
EAR=re.compile(r'\b(cochlea|vestibule|semicircular|utricle|saccule|endolymph|perilymph|'
    r'organ of corti|spiral|tympanic membrane|auditory ossicle|eustachian|pharyngotympanic|'
    r'external acoustic meatus|auricle of ear|helix|antihelix|tragus|concha of auricle)\b',re.I)

CNS=re.compile(r'\b(nucleus|nuclei|tract|fasciculus|lemniscus|colliculus|colliculi|'
    r'peduncle|commissure|gyrus|gyri|sulcus|sulci|lobule|vermis|culmen|declive|folium|'
    r'tuber of vermis|uvula of vermis|pyramid of (medulla|vermis)|nodule of vermis|'
    r'flocculus|lingula of cerebellum|cerebell|cerebr|encephal|telencephal|diencephal|'
    r'mesencephal|metencephal|myelencephal|brain|hemisphere|thalam|hypothalam|epithalam|'
    r'subthalam|habenula|geniculate|amygdal|hippocamp|fornix|septum pellucidum|'
    r'corpus callosum|internal capsule|corona radiata|putamen|caudate|pallidus|lentiform|'
    r'claustrum|substantia nigra|red nucleus|reticular formation|\bolive\b|\bpons\b|'
    r'medulla oblongata|midbrain|tectum|tegmentum|ventricle|choroid plexus|'
    r'aqueduct of midbrain|central canal|arbor vitae|falx cerebri|tentorium|dura mater|'
    r'arachnoid|pia mater|leptomening|spinal cord|grey matter|gray matter|white matter|'
    r'(anterior|posterior|lateral) horn of spinal|cauda equina|conus medullaris|'
    r'filum terminale|stria (medullaris|terminalis)|area postrema|\bobex\b|'
    r'optic (chiasm|tract|radiation)|olfactory (bulb|tract|trigone)|insula|operculum|'
    r'cuneus|precuneus|calcar avis|mammillary body|pineal|infundibulum|'
    r'lamina terminalis|indusium griseum|paraterminal gyrus|limen of insula|'
    r'base of peduncle|cerebral peduncle|quadrangular lobule|biventral lobule|'
    r'semilunar lobule|gracile lobule|simple lobule|central lobule|tonsil of cerebellum|'
    r'ala of central lobule|nervi nervorum|spinal reticular|central mesencephalic)\b',re.I)
PNS=re.compile(r'\b(nerve|nerves|plexus|ganglion|ganglia|ramus communicans|rami communicantes|'
    r'(anterior|posterior) root of spinal nerve|(anterior|posterior) rootlets|'
    r'(superior|middle|inferior) trunk of brachial|(lateral|medial|posterior) cord of brachial|'
    r'(anterior|posterior) division of (superior|middle|inferior) trunk|dermatome|'
    r'chorda tympani|spinal nerve|dorsal root|ventral root)\b',re.I)
def is_brain(n):
    if CNS.search(n): return True
    if PNS.search(n): return False
    return True   # unlabelled CNS structure in the nervous-system file

# heart chambers / valves / myocardium / conduction — NOT vessels; -> organ layer
HEART=re.compile(r'\b(ventricle|atrium|atrio-?ventricular|auricle of (right|left)|'
    r'(coronary|semilunar|septal|anterior|posterior|inferior) leaflet|leaflet of|'
    r'non-?coronary (leaflet|cusp|sinus)|(right|left|posterior|anterior|septal) (coronary )?cusp|'
    r'papillary muscle|chordae tendineae|trabecula|trabeculae carneae|moderator band|'
    r'inter(ventricular|atrial) septum|crista terminalis|fossa ovalis|pectinate muscle|'
    r'myocardium|endocardium|epicardium|pericard|conus arteriosus|infundibulum of heart|'
    r'sinus of coronary|coronary sinus|(anterior|posterior|middle) cardiac vein|'
    r'valve of (coronary sinus|inferior vena cava)|aortic (valve|vestibule)|mitral valve|'
    r'tricuspid valve|pulmonary valve|apex of heart|base of heart|(right|left) fibrous (ring|trigone))\b',re.I)

def kind_of(base):
    n=base.lower()
    if SPEC.startswith("nerve"):
        if EYE.search(n) or EAR.search(n): return "organ"   # sensory detail -> organ layer
        return "brain" if is_brain(n) else "nerve"
    if SPEC=="vessel":
        return "organ" if HEART.search(n) else "vessel"
    if SPEC=="organ":
        if EYE.search(n) or EAR.search(n): return "organ"
        return "organ"
    if SPEC=="lymph": return "lymph"
    if SPEC=="connective": return "connective"
    return SPEC

NONBODY=re.compile(r'^(cardiovascular system|nervous system|circulatory system|arteries|veins|'
    r'lymphatic system|lymph nodes of|visceral system|digestive system|respiratory system|'
    r'urinary system|abdominal cavity|thoracic cavity|pelvic cavity|body cavity|'
    r'systemic circulation|pulmonary circulation|portal (system|circulation)|'
    r'superficial (veins|lymphatics)|deep (veins|lymphatics))\b',re.I)

JUNK=re.compile(r'^[\W_]*$|^\?|^x+$|^untitled|^object\d*$|^mesh\d*$|^n/?a$', re.I)
grp=collections.defaultdict(list)
for it in inst:
    if not it["k"].startswith("body"): continue
    if len(it["m"].vertices)<24: continue
    if NONBODY.match(it["base"]): continue
    if JUNK.match(it["base"].strip()) or len(re.sub(r'[^a-zA-Z]','',it["base"]))<3: continue
    grp[it["base"]].append(it)

objects=[]
for base,items in sorted(grp.items()):
    kind=kind_of(base)
    xs=[i["cx"] for i in items]
    paired=any(v>12 for v in xs) and any(v<-12 for v in xs)
    slug=re.sub(r'[^a-z0-9]+','_',base.lower()).strip('_')
    if not slug or len(base.strip())<2: continue
    pl,how=translate(base); pl=zatrans.strip_side(pl)
    if paired:
        for side,sign in (("l",1),("r",-1)):
            parts=[i["m"] for i in items if (i["cx"]>0)==(sign>0)]
            if not parts: continue
            objects.append({"id":f"{slug}_{side}","en":base,"pl":(pl+zatrans.side_label(base,side)).strip(),
                            "side":side,"kind":kind,"pl_from":how,"mesh":trimesh.util.concatenate(parts)})
    else:
        objects.append({"id":slug,"en":base,"pl":pl,"side":"mid","kind":kind,"pl_from":how,
                        "mesh":trimesh.util.concatenate([i["m"] for i in items])})

# ---- points -> nearest body of matching side ----
bykind=collections.defaultdict(list)
for o in objects: bykind[o["kind"]].append(o)
def tree_for(kind,side):
    objs=[o for o in bykind[kind] if o["side"] in (side,"mid")]
    if not objs: objs=bykind[kind]
    if not objs: return None,None,None
    vs=[];ow=[]
    for j,o in enumerate(objs):
        v=np.asarray(o["mesh"].vertices); vs.append(v); ow.append(np.full(len(v),j))
    return cKDTree(np.vstack(vs)),np.concatenate(ow),objs
TREES={}

points=[]; pseen=set()
for it in inst:
    if it["k"] not in ("ptL","ptR"): continue
    if len(it["m"].vertices)>800: continue
    base=it["base"]
    if NONBODY.match(base): continue
    side="l" if it["k"]=="ptL" else "r"
    kind=kind_of(base)
    key=(kind,side)
    if key not in TREES: TREES[key]=tree_for(kind,side)
    tr,ow,objs=TREES[key]
    if tr is None: continue
    c=np.asarray(it["m"].centroid)
    d,ix=tr.query(c); o=objs[ow[ix]]
    k2=(o["id"],base)
    if k2 in pseen: continue
    pseen.add(k2)
    pl,how=translate(base)
    points.append({"ownerId":o["id"],"kind":kind,"en":base,"pl":pl,"approx":how=="none",
                   "dist_mm":round(float(d),1),"pos":[round(float(v),2) for v in c]})

# ---- write per kind (MERGE into existing files, keyed by id, so a secondary
#      kind emitted by another GLB run does not clobber the primary run) ----
def merge_dump(path, new_items, key):
    old=[]
    if os.path.exists(path):
        try: old=json.load(open(path,encoding="utf-8"))
        except Exception: old=[]
    by={d[key]:d for d in old if key in d}
    for d in new_items: by[d[key]]=d
    json.dump(list(by.values()), io.open(path,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    return len(by)

KMAP={"vessel":"vessels","organ":"organs","nerve":"nerves","brain":"brain","lymph":"lymph","connective":"connective"}
for kind,fk in KMAP.items():
    objs=[o for o in objects if o["kind"]==kind]
    if not objs: continue
    for o in objs: o["mesh"].export(f"{OBJD}\\{o['id']}.obj",include_texture=False)
    tot=merge_dump(f"{BUILD}\\all_{fk}_labeled_v2.json",
                   [{k:o[k] for k in ("id","pl","en","side","kind","pl_from")} for o in objs], "id")
    pts=[p for p in points if p["kind"]==kind]
    ptot=0
    if pts:
        ptot=merge_dump(f"{BUILD}\\{fk}_landmarks_v2.json",
                        [dict({k:p[k] for k in ("ownerId","en","pl","pos","approx","dist_mm")},
                              lmid=f"{p['ownerId']}|{p['en']}") for p in pts], "lmid")
    n_none=sum(o["pl_from"]=="none" for o in objs)
    print(f"  {kind}: +{len(objs)} obj (file now {tot}, {n_none} nowych bez PL), +{len(pts)} pkt (file {ptot}), >15mm: {sum(p['dist_mm']>15 for p in pts)}")
print(f"total objects {len(objects)}, total points {len(points)}")
