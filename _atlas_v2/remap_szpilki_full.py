# Remap szpilki_map.json (kolokwia I-IV) from BodyParts3D ids -> Atlas v2 ids.
# Matches by Polish name (text / matchedPl) against v2 catalogues + v2 landmarks.
import json, re, io, os, glob, difflib, collections

PROJ  = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie"
BUILD = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\build_full"

sm = json.load(open(f"{PROJ}\\szpilki_map.json", encoding="utf-8"))
st = json.load(open(f"{PROJ}\\szpilki_todo.json", encoding="utf-8"))

# ---- v2 catalogues ----
meshes = []   # {id, pl, kind, side}
for f in glob.glob(f"{BUILD}\\all_*_labeled_v2.json"):
    for o in json.load(open(f, encoding="utf-8")):
        meshes.append(o)
landmarks = json.load(open(f"{BUILD}\\bone_landmarks_v2.json", encoding="utf-8"))

def norm(s):
    s = (s or "").lower().strip()
    s = s.replace("–", " ").replace("—", " ")
    s = re.sub(r'\s*\([^()]*\)\s*', ' ', s)              # drop (trochlea) (prawy) ...
    s = re.sub(r'\b(lewy|lewa|lewe|prawy|prawa|prawe|deep|superficial)\b', '', s)
    s = s.replace("-", " ")
    s = re.sub(r'\s+', ' ', s).strip(" .,")
    return s

SYN = {   # v1 szpilka name -> v2 catalogue name (where phrasing diverged)
    "hak kości haczykowatej": "haczyk kości haczykowatej",
    "wyrostek dziobiasty": "wyrostek dziobiasty kości łokciowej",
    "guzek stożkowaty": "guzek stożkowaty obojczyka",
    "kresa chropawa kości udowej": "kresa chropawa",
    "nerw pośrodkowy": "nerw pośrodkowy",
    "tętnica łącząca tylna": "tętnica łącząca tylna",
    "przysadka mózgowa": "przysadka",
    "konar mózgu": "konar mózgu",
    "wodociąg śródmózgowia": "wodociąg mózgu",
    "splot naczyniówkowy komory bocznej": "splot naczyniówkowy",
    "splot naczyniówkowy komory trzeciej": "splot naczyniówkowy",
    "splot naczyniówkowy komory czwartej": "splot naczyniówkowy",
    "kolano ciała modzelowatego": "ciało modzelowate",
    "dziób ciała modzelowatego": "ciało modzelowate",
    "płat ciała modzelowatego": "ciało modzelowate",
    "pień ciała modzelowatego": "ciało modzelowate",
    "trzon ciała modzelowatego": "ciało modzelowate",
    "bruzda ciała modzelowatego": "ciało modzelowate",
    "promienistość ciała modzelowatego": "ciało modzelowate",
    "trzon sklepienia": "sklepienie",
    "odnoga sklepienia": "sklepienie",
    "słup sklepienia": "sklepienie",
    "spoidło przednie": "spoidło przednie",
    "torebka wewnętrzna": "torebka wewnętrzna",
    "zakręt zębaty": "zakręt zębaty",
    "stopa hipokampa": "hipokamp",
    "opuszka węchowa": "opuszka węchowa",
    "mięsień żwacz część powierzchowna": "mięsień żwacz część powierzchowna",
    "mięsień żwacz część głęboka": "mięsień żwacz część głęboka",
    "kąt żuchwy": "kąt żuchwy",
    "wcięcie żuchwy": "wcięcie żuchwy",
    "otwór żuchwy": "otwór żuchwy",
    "dół żuchwowy": "dół żuchwowy",
}
def keyset(name):
    n = norm(name)
    ks = {n, SYN.get(n, n)}
    ks.add(re.sub(r'\s*kości\s+\w+$', '', n).strip())
    ks.add(re.sub(r'^(kolano|dziób|płat|pień|trzon|bruzda|promienistość|odnoga|słup|głowa|szyjka|podstawa|szczyt|część|brzeg|powierzchnia)\s+', '', n).strip())
    ks.add(" ".join(sorted(n.split())))          # word-order-insensitive key
    return {k for k in ks if k and len(k) > 2}

def catkeys(pl):
    n = norm(pl)
    ks = {n, re.sub(r'\s*kości\s+\w+$', '', n).strip(), " ".join(sorted(n.split()))}
    return {k for k in ks if k and len(k) > 2}

mesh_idx = collections.defaultdict(list)
for o in meshes:
    for k in catkeys(o["pl"]):
        mesh_idx[k].append(o)
lm_idx = collections.defaultdict(list)
for l in landmarks:
    for k in catkeys(l["pl"]):
        lm_idx[k].append(l)
MESH_KEYS = list(mesh_idx)
LM_KEYS = list(lm_idx)

def pick_side(cands):
    # prefer right, else first
    for c in cands:
        if c.get("side") == "r": return c
    return cands[0]

def match_mesh(name, kind=None):
    for k in keyset(name):
        if k in mesh_idx:
            cs = mesh_idx[k]
            if kind: cs2 = [c for c in cs if c["kind"] == kind] or cs
            else: cs2 = cs
            return pick_side(cs2), "exact"
    # fuzzy
    n = norm(name)
    close = difflib.get_close_matches(n, MESH_KEYS, n=1, cutoff=0.88)
    if close:
        cs = mesh_idx[close[0]]
        if kind: cs = [c for c in cs if c["kind"] == kind] or cs
        return pick_side(cs), "fuzzy"
    return None, None

def match_lm(name):
    for k in keyset(name):
        if k in lm_idx:
            return lm_idx[k][0], "exact"
    n = norm(name)
    close = difflib.get_close_matches(n, LM_KEYS, n=1, cutoff=0.88)
    if close:
        return lm_idx[close[0]][0], "fuzzy"
    return None, None

out, unmatched = [], []
stats = collections.Counter()
for it in sm:
    names = [it.get("text", ""), it.get("matchedPl", "")]
    rec = {k: it[k] for k in ("kolokwium", "category", "noteCategory", "text") if k in it}
    hit = how = None
    if it["linkType"] == "landmark":
        for nm in names:
            l, how = match_lm(nm)
            if l: hit = l; break
        if hit:
            rec.update(linkType="landmark", boneId=hit["boneId"], matchedPl=hit["pl"])
        else:
            # a v1 landmark may be a v2 mesh (e.g. some processes modelled as bodies)
            for nm in names:
                m, how = match_mesh(nm)
                if m: hit = m; break
            if hit:
                rec.update(linkType="mesh", kind=hit["kind"], id=hit["id"], matchedPl=hit["pl"])
    else:  # mesh
        for nm in names:
            m, how = match_mesh(nm, it.get("kind"))
            if m: hit = m; break
        if hit:
            rec.update(linkType="mesh", kind=hit["kind"], id=hit["id"], matchedPl=hit["pl"])
    if hit:
        stats[f"{it['linkType']}->{rec['linkType']}/{how}"] += 1
        out.append(rec)
    else:
        stats["UNMATCHED"] += 1
        unmatched.append({"kolokwium": it["kolokwium"], "linkType": it["linkType"],
                          "text": it["text"], "matchedPl": it.get("matchedPl", "")})

# todo entries stay as-is (no structure yet); keep for the "not placed" list
json.dump(out, io.open(f"{BUILD}\\szpilki_map_v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
todo_all = st + unmatched
json.dump(todo_all, io.open(f"{BUILD}\\szpilki_todo_v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"szpilki_map: {len(sm)} -> matched {len(out)}, unmatched {len(unmatched)}")
print("stats:", dict(stats))
print(f"szpilki_todo_v2: {len(todo_all)} ({len(st)} original todo + {len(unmatched)} newly unmatched)")
print("\n-- UNMATCHED (need manual target or Joints100.fbx) --")
by_k = collections.Counter()
for u in unmatched:
    by_k[u["kolokwium"]] += 1
    print(f"  [{u['kolokwium']}] {u['linkType']:8} {u['text']}")
print("per kolokwium:", dict(by_k))
