# Muscle + connective layer: MuscularSystem100 (bellies) + SkeletalSystem100 (.o*/.e* attachment points)
import trimesh, json, re, io, os, sys, collections, numpy as np, difflib
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zatrans

SRC  = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"
PROJ = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie"
BUILD= r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\build"
OBJD = BUILD + r"\obj"
os.makedirs(OBJD, exist_ok=True)

def to_atlas(V):                       # Z-Anatomy metres, Y-up -> atlas mm, Z-up, +Y=back
    V=np.asarray(V,dtype=np.float64); o=np.empty_like(V)
    o[:,0]=V[:,0]*1000.0; o[:,1]=-V[:,2]*1000.0; o[:,2]=V[:,1]*1000.0
    return o

# ---------- PL dictionaries ----------
_sl = json.load(open(f"{PROJ}\\slownik_anatomiczny_umed_pl_en.json", encoding="utf-8"))
EN2PL={}
for e in _sl:
    for en in e["en"].split(";"):
        EN2PL.setdefault(en.lower().strip(), e["pl"])
_om = json.load(open(f"{PROJ}\\all_muscles_labeled.json", encoding="utf-8"))
for e in _om:
    EN2PL.setdefault(e["en"].lower().strip(), e["pl"])
def _norm(s):
    s=s.lower()
    s=re.sub(r'\(.*?\)','',s)
    s=re.sub(r'\b(of|the|a|for|part|belly|muscle|muscles|musculus|m\.)\b',' ',s)
    return re.sub(r'\s+',' ',s).strip()
NORM2PL={}
for k,v in EN2PL.items(): NORM2PL.setdefault(_norm(k),v)
NK=list(NORM2PL.keys())

MUSC_OVR={
 "muscle":"mięsień","deltoid muscle":"Mięsień naramienny","biceps brachii":"Mięsień dwugłowy ramienia",
 "triceps brachii":"Mięsień trójgłowy ramienia","brachialis muscle":"Mięsień ramienny",
 "brachioradialis muscle":"Mięsień ramienno-promieniowy","pectoralis major muscle":"Mięsień piersiowy większy",
 "pectoralis minor muscle":"Mięsień piersiowy mniejszy","trapezius muscle":"Mięsień czworoboczny",
 "latissimus dorsi muscle":"Mięsień najszerszy grzbietu","rectus abdominis muscle":"Mięsień prosty brzucha",
 "external abdominal oblique muscle":"Mięsień skośny zewnętrzny brzucha",
 "internal abdominal oblique muscle":"Mięsień skośny wewnętrzny brzucha",
 "gluteus maximus muscle":"Mięsień pośladkowy wielki","gluteus medius muscle":"Mięsień pośladkowy średni",
 "gluteus minimus muscle":"Mięsień pośladkowy mały","sartorius muscle":"Mięsień krawiecki",
 "gracilis muscle":"Mięsień smukły","soleus muscle":"Mięsień płaszczkowaty",
 "gastrocnemius muscle":"Mięsień brzuchaty łydki","tibialis anterior muscle":"Mięsień piszczelowy przedni",
 "quadriceps femoris muscle":"Mięsień czworogłowy uda","rectus femoris muscle":"Mięsień prosty uda",
 "vastus lateralis muscle":"Mięsień obszerny boczny","vastus medialis muscle":"Mięsień obszerny przyśrodkowy",
 "vastus intermedius muscle":"Mięsień obszerny pośredni","adductor magnus":"Mięsień przywodziciel wielki",
 "adductor longus":"Mięsień przywodziciel długi","adductor brevis":"Mięsień przywodziciel krótki",
 "iliopsoas muscle":"Mięsień biodrowo-lędźwiowy","psoas major muscle":"Mięsień lędźwiowy większy",
 "sternocleidomastoid muscle":"Mięsień mostkowo-obojczykowo-sutkowy","masseter muscle":"Mięsień żwacz",
 "temporalis muscle":"Mięsień skroniowy","diaphragm":"Przepona","coracobrachialis muscle":"Mięsień kruczo-ramienny",
 "anconeus muscle":"Mięsień łokciowy","supinator muscle":"Mięsień odwracacz","pronator teres muscle":"Mięsień nawrotny obły",
}
CONN_OVR={
 "fascia":"powięź","bursa":"kaletka","tendon":" ścięgno","aponeurosis":"rozcięgno",
 "septum":"przegroda","tendon sheath":"pochewka ścięgna","retinaculum":"troczek",
 "calcaneal tendon":"Ścięgno piętowe (Achillesa)","thoracolumbar fascia":"Powięź piersiowo-lędźwiowa",
}
SIDE_PL={"l":"(lewy)","r":"(prawy)","mid":""}
def translate(en, conn=False):
    n=en.lower().strip().strip("()").strip()
    D = CONN_OVR if conn else MUSC_OVR
    if n in D: return D[n],"ovr"
    if n in EN2PL: return EN2PL[n],"exact"
    nn=_norm(n)
    if nn in NORM2PL: return NORM2PL[nn],"norm"
    # "X part/head/belly of Y" -> translate Y, prepend PL adj
    m=re.match(r'^(.*?) (?:part|head|belly) of (.+)$', n)
    if m:
        base_pl,how = translate(m.group(2),conn)
        if how!="none":
            seg=m.group(1)
            SEGPL={"clavicular":"część obojczykowa","sternal":"część mostkowa","sternocostal":"część mostkowo-żebrowa",
                   "abdominal":"część brzuszna","acromial":"część barkowa","spinal":"część grzbietowa",
                   "long":"głowa długa","short":"głowa krótka","lateral":"głowa boczna","medial":"głowa przyśrodkowa",
                   "oblique":"część skośna","transverse":"część poprzeczna","ascending":"część wstępująca",
                   "descending":"część zstępująca","anterior":"brzusiec przedni","posterior":"brzusiec tylny",
                   "humeral":"głowa ramienna","ulnar":"głowa łokciowa","radial":"głowa promieniowa",
                   "deep":"część głęboka","superficial":"część powierzchowna","superior":"część górna",
                   "inferior":"część dolna","costal":"część żebrowa","lumbar":"część lędźwiowa"}
            seg_pl = SEGPL.get(seg)
            if seg_pl is None:
                return zatrans.translate(en)          # unknown segment -> let shared translator try
            return f"{base_pl} — {seg_pl}","part"
    c=difflib.get_close_matches(nn,NK,n=1,cutoff=0.9)
    if c: return NORM2PL[c[0]],"fuzzy"
    return zatrans.translate(en)

# ---------- classify helpers ----------
RX_SIDE=re.compile(r'\.(r|l)$'); RX_FRAG=re.compile(r'\.(r|l)_(\d+)$'); RX_US=re.compile(r'_(\d+)$')
def parse(name):
    if RX_FRAG.search(name): s=RX_FRAG.search(name).group(1); return RX_FRAG.sub('',name), s
    if RX_SIDE.search(name): s=RX_SIDE.search(name).group(1); return RX_SIDE.sub('',name), s
    return name, ''
def strip_us(b): return RX_US.sub('', b)

CONNECTIVE=re.compile(r'\b(fascia|bursa|aponeurosis|septum|retinacul|sheath|tendon|ligament|'
    r'membrane|raphe|tendinous (ring|arch|intersection)|trochlea of|fibrous (sheath|ring)|'
    r'palmar aponeurosis|plantar aponeurosis|linea alba|inguinal (ligament|falx))\b', re.I)

# ---------- MUSCLE / CONNECTIVE BODIES ----------
sceneM = trimesh.load(f"{SRC}\\MuscularSystem100.glb")
inst=[]
for node in sceneM.graph.nodes_geometry:
    tf,g=sceneM.graph[node]; m=sceneM.geometry[g].copy(); m.apply_transform(tf)
    m.vertices=to_atlas(m.vertices)
    inst.append((g,m))

grp=collections.defaultdict(list)
for gname,m in inst:
    if len(m.vertices)<30: continue
    base,side=parse(gname); base=strip_us(base)
    grp[base].append((m, m.centroid[0]))

objects=[]
for base,items in sorted(grp.items()):
    conn = bool(CONNECTIVE.search(base))
    layer = "connective" if conn else "muscle"
    xs=[cx for _,cx in items]
    paired = any(v>12 for v in xs) and any(v<-12 for v in xs)
    slug=re.sub(r'[^a-z0-9]+','_',base.lower()).strip('_')
    pl,how=translate(base, conn); pl=zatrans.strip_side(pl)
    if paired:
        for side,sign in (("l",1),("r",-1)):
            parts=[m for m,cx in items if (cx>0)==(sign>0)]
            if not parts: continue
            mesh=trimesh.util.concatenate(parts)
            objects.append({"id":f"{slug}_{side}","en":base,"pl":(pl+zatrans.side_label(base,side)).strip(),
                            "side":side,"layer":layer,"kind":layer,"pl_from":how,"mesh":mesh})
    else:
        mesh=trimesh.util.concatenate([m for m,_ in items])
        objects.append({"id":slug,"en":base,"pl":pl,"side":"mid","layer":layer,"kind":layer,"pl_from":how,"mesh":mesh})

# ---------- MUSCLE ATTACHMENT POINTS from SkeletalSystem .o*/.e* ----------
sceneS = trimesh.load(f"{SRC}\\SkeletalSystem100.glb")
RX_ATT=re.compile(r'\.(?P<t>[oe])(?P<n>\d*)(?P<s>[rl])$')
musc_objs=[o for o in objects if o["layer"]=="muscle"]
# per-side name index
def midx(side):
    d={}
    for o in musc_objs:
        if o["side"] not in (side,"mid"): continue
        d.setdefault(o["en"].lower(),o)
        d.setdefault(_norm(o["en"]),o)
    return d
MIDX={"l":midx("l"),"r":midx("r")}
# fallback KDTree of muscle vertices per side
def mtree(side):
    vs=[];ow=[];objs=[]
    for o in musc_objs:
        if o["side"] not in (side,"mid"): continue
        j=len(objs); objs.append(o)
        v=np.asarray(o["mesh"].vertices); vs.append(v); ow.append(np.full(len(v),j))
    return cKDTree(np.vstack(vs)), np.concatenate(ow), objs
TR={s:mtree(s) for s in ("l","r")}

attach=[]; aseen=set()
for node in sceneS.graph.nodes_geometry:
    tf,g=sceneS.graph[node]
    mm=RX_ATT.search(g)
    if not mm: continue
    mesh=sceneS.geometry[g].copy(); mesh.apply_transform(tf); mesh.vertices=to_atlas(mesh.vertices)
    base=RX_ATT.sub('',g)
    side="l" if mm.group("s")=="l" else "r"
    kind="origin" if mm.group("t")=="o" else "insertion"
    head=mm.group("n") or ""
    c=np.asarray(mesh.centroid)
    o = MIDX[side].get(base.lower()) or MIDX[side].get(_norm(base))
    route="name"
    if o is None:
        tree,ow,objs=TR[side]; d,ix=tree.query(c); o=objs[ow[ix]]; route="spatial"
    key=(o["id"],base,kind,head)
    if key in aseen: continue
    aseen.add(key)
    pl,how=translate(base)
    kpl = "Przyczep początkowy" if kind=="origin" else "Przyczep końcowy"
    if head: kpl += f" (głowa {head})"
    attach.append({"muscleId":o["id"],"en":f"{kind} of {base}","kind":kind,
                   "pl":f"{kpl}: {pl}","pos":[round(float(v),2) for v in c],
                   "route":route,"approx":how=="none"})

# ---------- write ----------
def dump(p,d): json.dump(d,io.open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
for o in objects:
    o["mesh"].export(f"{OBJD}\\{o['id']}.obj", include_texture=False)
musc_meta=[{k:o[k] for k in("id","pl","en","side","kind","pl_from")} for o in objects if o["layer"]=="muscle"]
conn_meta=[{k:o[k] for k in("id","pl","en","side","kind","pl_from")} for o in objects if o["layer"]=="connective"]
dump(f"{BUILD}\\all_muscles_labeled_v2.json", musc_meta)
dump(f"{BUILD}\\all_connective_labeled_v2.json", conn_meta)
dump(f"{BUILD}\\muscle_landmarks_v2.json", [{k:a[k] for k in("muscleId","en","kind","pl","pos","route","approx")} for a in attach])

print(f"muscle objects: {len(musc_meta)}   connective objects: {len(conn_meta)}")
print(f"attachment points: {len(attach)}  (origin {sum(a['kind']=='origin' for a in attach)}, insertion {sum(a['kind']=='insertion' for a in attach)})")
print(f"  routed by name: {sum(a['route']=='name' for a in attach)}  spatial: {sum(a['route']=='spatial' for a in attach)}")
print(f"muscle PL: {collections.Counter(o['pl_from'] for o in objects if o['layer']=='muscle')}")
print(f"untranslated muscles: {[o['en'] for o in objects if o['layer']=='muscle' and o['pl_from']=='none'][:25]}")
