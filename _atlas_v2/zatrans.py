# Shared EN->PL translator for Atlas v2 (Z-Anatomy names -> UMed dictionary).
# Used by build_skeleton / build_muscles / build_layer.
import json, re, os, difflib, functools

PROJ = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie"

# ---------------------------------------------------------------- dictionary ---
def _load_dict():
    d = {}
    def _pl_clean(pl):
        pl = pl.strip()
        # drop side markers baked into some dictionary / v1-catalogue values
        pl = re.sub(r'\s*\((lewy|lewa|lewe|prawy|prawa|prawe|[LP]|left|right)\)\s*$', '', pl, flags=re.I)
        # "Żyła serca wielka, żyła sercowa wielka" -> first synonym only
        if ',' in pl:
            first = pl.split(',')[0].strip()
            if len(first) >= 6:
                pl = first
        return pl.strip()
    # known errors in the raw UMed dictionary (PDF extraction slips) — win over everything
    CORRECTIONS = {
        "radial artery": "Tętnica promieniowa",
        "radial vein": "Żyła promieniowa",
        "radial nerve": "Nerw promieniowy",
        "lateral femoral cutaneous nerve": "Nerw skórny boczny uda",
        "lateral cutaneous nerve of thigh": "Nerw skórny boczny uda",
        "posterior femoral cutaneous nerve": "Nerw skórny tylny uda",
        "anterior cutaneous branches of femoral nerve": "Gałęzie skórne przednie nerwu udowego",
        "great auricular nerve": "Nerw uszny wielki",
        "frontal nerve": "Nerw czołowy",
        "supraorbital nerve": "Nerw nadoczodołowy",
        "supratrochlear nerve": "Nerw nadbloczkowy",
        "posterior communicating artery": "Tętnica łącząca tylna",
        "anterior communicating artery": "Tętnica łącząca przednia",
        "corona radiata": "Wieniec promienisty",
        "claustrum": "Przedmurze",
        "extreme capsule": "Torebka ostatnia",
        "external capsule": "Torebka zewnętrzna",
        "locus coeruleus": "Miejsce sinawe",
        "dentate gyrus": "Zakręt zębaty",
        "olfactory tract": "Pasmo węchowe",
        "olfactory bulb": "Opuszka węchowa",
        "interthalamic adhesion": "Zrost międzywzgórzowy",
        "hypothalamic sulcus": "Bruzda podwzgórzowa",
        "facial colliculus": "Wzgórek twarzowy",
        "middle cerebellar peduncle": "Konar środkowy móżdżku",
        "superior cerebellar peduncle": "Konar górny móżdżku",
        "inferior cerebellar peduncle": "Konar dolny móżdżku",
        "basilar sulcus": "Bruzda podstawna mostu",
        "primary fissure": "Szczelina pierwsza",
        "superior medullary velum": "Zasłona rdzeniowa górna",
        "inferior medullary velum": "Zasłona rdzeniowa dolna",
        "denticulate ligament": "Więzadło ząbkowane",
        "head of caudate nucleus": "Głowa jądra ogoniastego",
        "tail of caudate nucleus": "Ogon jądra ogoniastego",
        "body of caudate nucleus": "Trzon jądra ogoniastego",
        "occipital forceps": "Kleszcze potyliczne","forceps major": "Kleszcze potyliczne",
        "frontal forceps": "Kleszcze czołowe","forceps minor": "Kleszcze czołowe",
        "striatum": "Prążkowie","uncus": "Hak (zakrętu przyhipokampowego)",
        "genu of corpus callosum": "Kolano ciała modzelowatego",
        "rostrum of corpus callosum": "Dziób ciała modzelowatego",
        "splenium of corpus callosum": "Płat ciała modzelowatego",
        "body of corpus callosum": "Trzon ciała modzelowatego",
        "trunk of corpus callosum": "Trzon ciała modzelowatego",
        "column of fornix": "Słup sklepienia","body of fornix": "Trzon sklepienia",
        "crus of fornix": "Odnoga sklepienia","crura of fornix": "Odnogi sklepienia",
        # --- audyt 2026-08-28: błędne dopasowania fuzzy / złe wpisy słownika ---
        "dorsal calcaneocuboid ligament": "Więzadło piętowo-sześcienne grzbietowe",
        "plantar calcaneocuboid ligament": "Więzadło piętowo-sześcienne podeszwowe",
        "posterior tibiotalar ligament": "Więzadło piszczelowo-skokowe tylne",
        "anterior tibiotalar ligament": "Więzadło piszczelowo-skokowe przednie",
        "tibiocalcaneal ligament": "Więzadło piszczelowo-piętowe",
        "tibionavicular ligament": "Więzadło piszczelowo-łódkowe",
        "medial femoral intermuscular septum": "Przegroda międzymięśniowa przyśrodkowa uda",
        "lateral femoral intermuscular septum": "Przegroda międzymięśniowa boczna uda",
        "inferior papillary muscle of left ventricle": "Mięsień brodawkowaty tylny (komora lewa)",
        "inferior papillary muscle of right ventricle": "Mięsień brodawkowaty tylny (komora prawa)",
        "superior papillary muscle of left ventricle": "Mięsień brodawkowaty przedni (komora lewa)",
        "superior papillary muscle of right ventricle": "Mięsień brodawkowaty przedni (komora prawa)",
        "anterior inferior pancreaticoduodenal artery": "Tętnica trzustkowo-dwunastnicza dolna przednia",
        "posterior inferior pancreaticoduodenal artery": "Tętnica trzustkowo-dwunastnicza dolna tylna",
        "anterior superior pancreaticoduodenal artery": "Tętnica trzustkowo-dwunastnicza górna przednia",
        "posterior superior pancreaticoduodenal artery": "Tętnica trzustkowo-dwunastnicza górna tylna",
        "middle lobar bronchus": "Oskrzele płatowe środkowe (prawe)",
        "right gastro-omental nodes": "Węzły żołądkowo-sieciowe prawe",
        "left gastro-omental nodes": "Węzły żołądkowo-sieciowe lewe",
        "posterior layer of thoracolumbar fascia": "Blaszka tylna powięzi piersiowo-lędźwiowej",
        "anterior layer of thoracolumbar fascia": "Blaszka przednia powięzi piersiowo-lędźwiowej",
        "middle layer of thoracolumbar fascia": "Blaszka środkowa powięzi piersiowo-lędźwiowej",
        "external abdominal oblique muscle": "Mięsień skośny zewnętrzny brzucha",
        "internal abdominal oblique muscle": "Mięsień skośny wewnętrzny brzucha",
        "superficial head of pronator teres": "Głowa powierzchowna mięśnia nawrotnego obłego",
        "deep head of pronator teres": "Głowa głęboka mięśnia nawrotnego obłego",
        "humero-ulnar head of pronator teres": "Głowa ramienno-łokciowa mięśnia nawrotnego obłego",
        "superior extensor retinaculum of ankle": "Troczek górny prostowników goleni",
        "inferior extensor retinaculum of ankle": "Troczek dolny prostowników stopy",
        "mucosa of stomach": "Błona śluzowa żołądka",
        "triradiate cartilage": "Chrząstka Y panewki (chrząstka trójpromienna)",
        "nasal septal cartilage": "Chrząstka przegrody nosa",
        "lateral process of nasal septal cartilage": "Wyrostek boczny chrząstki przegrody nosa",
        "stylohyoid ligament": "Więzadło rylcowo-gnykowe",
        "median thyrohyoid ligament": "Więzadło tarczowo-gnykowe pośrodkowe",
        "lateral thyrohyoid ligament": "Więzadło tarczowo-gnykowe boczne",
        "lateral temporomandibular ligament": "Więzadło skroniowo-żuchwowe boczne",
        "pterygospinous ligament": "Więzadło skrzydłowo-kolcowe",
        "pterygospinal ligament": "Więzadło skrzydłowo-kolcowe",
        "intercornual ligament": "Więzadło międzyrożne (rogów krzyżowych)",
        "sacrococcygeal symphysis": "Spojenie krzyżowo-guziczne",
        "costotransverse ligament": "Więzadło żebrowo-poprzeczne",
        "superior costotransverse ligament": "Więzadło żebrowo-poprzeczne górne",
        "lateral costotransverse ligament": "Więzadło żebrowo-poprzeczne boczne",
        "intersesamoid ligament": "Więzadło międzytrzeszczkowe",
        "frenula capsulae": "Wędzidełka torebki stawowej",
        "popliteofibular ligament": "Więzadło podkolanowo-strzałkowe",
        "meniscopatellar ligament": "Więzadło łąkotkowo-rzepkowe",
        "transverse tibiofibular ligament": "Więzadło poprzeczne (piszczelowo-strzałkowe dolne głębokie)",
        "superior glenohumeral ligament": "Więzadło obrąbkowo-ramienne górne",
        "middle glenohumeral ligament": "Więzadło obrąbkowo-ramienne środkowe",
        "inferior glenohumeral ligament": "Więzadło obrąbkowo-ramienne dolne",
        "anterior meniscotibial ligament (medial meniscus)": "Więzadło łąkotkowo-piszczelowe przednie (łąkotki przyśrodkowej)",
        "anterior meniscotibial ligament (lateral meniscus)": "Więzadło łąkotkowo-piszczelowe przednie (łąkotki bocznej)",
        "posterior meniscotibial ligament (medial meniscus)": "Więzadło łąkotkowo-piszczelowe tylne (łąkotki przyśrodkowej)",
        "posterior meniscotibial ligament (lateral meniscus)": "Więzadło łąkotkowo-piszczelowe tylne (łąkotki bocznej)",
        "scapular spinal part of deltoid muscle": "Część grzebieniowa mięśnia naramiennego",
        "clavicular part of deltoid muscle": "Część obojczykowa mięśnia naramiennego",
        "acromial part of deltoid muscle": "Część barkowa mięśnia naramiennego",
        "sciatic bursa of gluteus maximus muscle": "Kaletka kulszowa mięśnia pośladkowego wielkiego",
        "external part of thyro-arytenoid muscle": "Część zewnętrzna mięśnia tarczowo-nalewkowego",
        "thyro-epiglottic part of thyro-arytenoid muscle": "Część tarczowo-nagłośniowa mięśnia tarczowo-nalewkowego",
        "common tendon sheath of fibularis muscles": "Pochewka wspólna ścięgien mięśni strzałkowych",
        "plantar tendon sheath of fibularis longus muscle": "Pochewka podeszwowa ścięgna mięśnia strzałkowego długiego",
        "dorsal digital arteries of foot": "Tętnice grzbietowe palców stopy",
        "dorsal digital veins of foot": "Żyły grzbietowe palców stopy",
        "dorsal digital arteries of hand": "Tętnice grzbietowe palców ręki",
        "dorsal digital veins of hand": "Żyły grzbietowe palców ręki",
        "palmar digital veins": "Żyły dłoniowe palców",
        "plantar digital veins": "Żyły podeszwowe palców",
        "intercuneiform interosseous ligaments": "Więzadła międzyklinowe międzykostne",
        "superficial transverse metacarpal ligament": "Więzadło śródręczne poprzeczne powierzchowne",
        "superficial transverse metatarsal ligament": "Więzadło śródstopne poprzeczne powierzchowne",
        "sesamoid bones of foot": "Kości trzeszczkowate stopy",
        "sesamoid bones of hand": "Kości trzeszczkowate ręki",
    }
    d.update(CORRECTIONS)
    # v1 atlas catalogues FIRST — human-curated over many sessions, higher trust
    # than the raw PDF-extracted dictionary (which has transcription errors).
    for extra in ("all_muscles_labeled.json","all_vessels_labeled.json","all_nerves_labeled.json",
                  "all_organs_labeled.json","all_brain_labeled.json","all_lymph_labeled.json",
                  "all_connective_labeled.json","all_bones_labeled.json"):
        p = f"{PROJ}\\{extra}"
        if os.path.exists(p):
            for e in json.load(open(p, encoding="utf-8")):
                if e.get("en") and e.get("pl"):
                    d.setdefault(e["en"].lower().strip(), _pl_clean(e["pl"]))
    # UMed dictionary as fallback
    sl = json.load(open(f"{PROJ}\\slownik_anatomiczny_umed_pl_en.json", encoding="utf-8"))
    for e in sl:
        pl = _pl_clean(e["pl"])
        for en in re.split(r'[;]', e["en"]):
            en = en.strip()
            if en:
                d.setdefault(en.lower(), pl)
    return d

EN2PL = _load_dict()

def _clean(s):
    s = s.strip()
    # whole string wrapped in parens -> unwrap (Z-Anatomy marks variant/optional names this way)
    if s.startswith("(") and s.endswith(")") and s.count("(") == 1:
        s = s[1:-1].strip()
    s = re.sub(r"[\u2019'`]", "", s)              # apostrophes
    s = re.sub(r'\s*\*+\s*$', '', s)              # trailing *
    s = re.sub(r'\s*\([^()]*\)\s*$', '', s)       # trailing (qualifier)
    s = re.sub(r'\s*//.*$', '', s)                # // notes
    s = re.sub(r'\s*\(([MF])\)\s*', ' ', s)       # (M)/(F) gender-of-structure markers
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def _norm(s):
    s = _clean(s).lower()
    s = re.sub(r'\b(m1|m2|m3|m4)[- ]?segment\b', '', s)
    s = re.sub(r'\b(right|left)\s+', '', s)
    s = re.sub(r'\b(the|a|an|muscle|muscles|musculus)\b', ' ', s)
    s = re.sub(r'\bm\.\s', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip(" -.")
    return s

_NORM2PL = {}
for _k, _v in EN2PL.items():
    _NORM2PL.setdefault(_norm(_k), _v)
    # word-order variant  "A of B" -> "B A"
    _m = re.match(r'^(.*?) of (.+)$', _norm(_k))
    if _m:
        _NORM2PL.setdefault(f"{_m.group(2)} {_m.group(1)}", _v)
_NK = list(_NORM2PL.keys())

# ------------------------------------------------------------- synonym rules ---
SYN = [
    (r'\bfibularis\b', 'peroneus'),
    (r'\bperoneus\b', 'fibularis'),
    (r'\bdeep (artery|vein) of (the )?thigh\b', r'deep femoral \1'),
    (r'\bdeep femoral (artery|vein)\b', r'deep \1 of thigh'),
    (r'\bgreat saphenous\b', 'long saphenous'),
    (r'\bsmall saphenous\b', 'short saphenous'),
    (r'\bfibula\b', 'peroneal bone'),
]

# ------------------------------------------------------ compositional pieces ---
POS = {  # positional / directional adjectives  (masc / fem / neut approximations)
    "anterior":("przedni","przednia","przednie"), "posterior":("tylny","tylna","tylne"),
    "superior":("górny","górna","górne"), "inferior":("dolny","dolna","dolne"),
    "medial":("przyśrodkowy","przyśrodkowa","przyśrodkowe"),
    "lateral":("boczny","boczna","boczne"),
    "internal":("wewnętrzny","wewnętrzna","wewnętrzne"),
    "external":("zewnętrzny","zewnętrzna","zewnętrzne"),
    "deep":("głęboki","głęboka","głębokie"), "superficial":("powierzchowny","powierzchowna","powierzchowne"),
    "common":("wspólny","wspólna","wspólne"), "proper":("właściwy","właściwa","właściwe"),
    "middle":("środkowy","środkowa","środkowe"), "central":("środkowy","środkowa","środkowe"),
    "transverse":("poprzeczny","poprzeczna","poprzeczne"),
    "oblique":("skośny","skośna","skośne"), "straight":("prosty","prosta","proste"),
    "great":("wielki","wielka","wielkie"), "greater":("większy","większa","większe"),
    "small":("mały","mała","małe"), "lesser":("mniejszy","mniejsza","mniejsze"),
    "long":("długi","długa","długie"), "short":("krótki","krótka","krótkie"),
    "left":("lewy","lewa","lewe"), "right":("prawy","prawa","prawe"),
    "dorsal":("grzbietowy","grzbietowa","grzbietowe"), "ventral":("brzuszny","brzuszna","brzuszne"),
    "palmar":("dłoniowy","dłoniowa","dłoniowe"), "plantar":("podeszwowy","podeszwowa","podeszwowe"),
    "cranial":("czaszkowy","czaszkowa","czaszkowe"), "caudal":("ogonowy","ogonowa","ogonowe"),
    "anterolateral":("przednio-boczny","przednio-boczna","przednio-boczne"),
    "anteromedial":("przednio-przyśrodkowy","przednio-przyśrodkowa","przednio-przyśrodkowe"),
    "posteromedial":("tylno-przyśrodkowy","tylno-przyśrodkowa","tylno-przyśrodkowe"),
    "posterolateral":("tylno-boczny","tylno-boczna","tylno-boczne"),
    "posteroventral":("tylno-brzuszny","tylno-brzuszna","tylno-brzuszne"),
    "articular":("stawowy","stawowa","stawowe"), "basal":("podstawny","podstawna","podstawne"),
    "apical":("szczytowy","szczytowa","szczytowe"), "lingular":("języczkowy","języczkowa","języczkowe"),
    "apicoposterior":("szczytowo-tylny","szczytowo-tylna","szczytowo-tylne"),
    "sagittal":("strzałkowy","strzałkowa","strzałkowe"), "coronal":("czołowy","czołowa","czołowe"),
}
# head noun -> (PL, gender index 0=m,1=f,2=n)
HEAD = {
    "sulcus":("Bruzda",1), "gyrus":("Zakręt",0), "lobule":("Płacik",0), "lobe":("Płat",0),
    "tract":("Droga",1), "fasciculus":("Pęczek",0), "lemniscus":("Wstęga",1),
    "nucleus":("Jądro",2), "nuclei":("Jądra",2), "commissure":("Spoidło",2),
    "peduncle":("Konar",0), "colliculus":("Wzgórek",0),
    "surface":("Powierzchnia",1), "border":("Brzeg",0), "margin":("Brzeg",0),
    "angle":("Kąt",0), "crest":("Grzebień",0), "line":("Kresa",1), "ridge":("Grzebień",0),
    "tuberosity":("Guzowatość",1), "tubercle":("Guzek",0), "process":("Wyrostek",0),
    "fossa":("Dół",0), "notch":("Wcięcie",2), "groove":("Bruzda",1), "spine":("Kolec",0),
    "head":("Głowa",1), "neck":("Szyjka",1), "body":("Trzon",0), "base":("Podstawa",1),
    "apex":("Szczyt",0), "facet":("Powierzchnia stawowa",1), "horn":("Róg",0),
    "branch":("Gałąź",1), "branches":("Gałęzie",1), "trunk":("Pień",0),
    "arch":("Łuk",0), "wall":("Ściana",1), "circumference":("Obwód",0), "extremity":("Koniec",0),
    "part":("Część",1), "pole":("Biegun",0), "rami":("Gałęzie",1), "root":("Korzeń",0),
    "lamina":("Blaszka",1), "ala":("Skrzydło",2), "impression":("Wycisk",0), "fissure":("Szczelina",1),
    "funiculus":("Sznur",0), "column":("Słup",0),
    "bursa":("Kaletka",1), "fascia":("Powięź",1), "aponeurosis":("Rozcięgno",2),
    "septum":("Przegroda",1), "sheath":("Pochewka",1), "ligament":("Więzadło",2),
    "membrane":("Błona",1), "vein":("Żyła",1), "artery":("Tętnica",1), "nerve":("Nerw",0),
    "plexus":("Splot",0), "ganglion":("Zwój",0), "duct":("Przewód",0), "canal":("Kanał",0),
    "foramen":("Otwór",0), "sinus":("Zatoka",1), "cavity":("Jama",1),
}
GEN_OF = {   # genitive of common bone / structure names for "<feature> of <X>"
    "humerus":"kości ramiennej","scapula":"łopatki","femur":"kości udowej",
    "tibia":"kości piszczelowej","fibula":"kości strzałkowej","radius":"kości promieniowej",
    "ulna":"kości łokciowej","clavicle":"obojczyka","mandible":"żuchwy","maxilla":"szczęki",
    "sternum":"mostka","sacrum":"kości krzyżowej","coccyx":"kości guzicznej",
    "hip bone":"kości miednicznej","ilium":"talerza biodrowego","ischium":"kości kulszowej",
    "pubis":"kości łonowej","patella":"rzepki","calcaneus":"kości piętowej","talus":"kości skokowej",
    "occipital bone":"kości potylicznej","temporal bone":"kości skroniowej",
    "frontal bone":"kości czołowej","parietal bone":"kości ciemieniowej",
    "sphenoid bone":"kości klinowej","ethmoid bone":"kości sitowej","rib":"żebra",
    "spinal cord":"rdzenia kręgowego","brain":"mózgu","cerebellum":"móżdżku","vermis":"robaka",
    "midbrain":"śródmózgowia","pons":"mostu","medulla oblongata":"rdzenia przedłużonego",
    "thalamus":"wzgórza","hypothalamus":"podwzgórza","cerebrum":"kresomózgowia",
    "heart":"serca","liver":"wątroby","spleen":"śledziony","stomach":"żołądka",
    "kidney":"nerki","lung":"płuca","pancreas":"trzustki","thymus":"grasicy",
    "midbrain tegmentum":"nakrywki śródmózgowia","pontine tegmentum":"nakrywki mostu",
    "greater wing":"skrzydła większego","lesser wing":"skrzydła mniejszego",
    "atlas":"kręgu szczytowego","axis":"kręgu obrotowego","dens axis":"zęba kręgu obrotowego",
    "dens of axis":"zęba kręgu obrotowego",
    "phalanx of hand":"paliczka ręki","phalanx of foot":"paliczka stopy",
    "hand":"ręki","foot":"stopy","great toe":"palucha","thumb":"kciuka",
    "metatarsal bone":"kości śródstopia","metacarpal bone":"kości śródręcza",
    "cricoid cartilage":"chrząstki pierścieniowatej","thyroid cartilage":"chrząstki tarczowatej",
    "arytenoid cartilage":"chrząstki nalewkowatej","epiglottis":"nagłośni",
    "stomach":"żołądka","suprarenal gland":"nadnercza","gallbladder":"pęcherzyka żółciowego",
    "urinary bladder":"pęcherza moczowego","uterus":"macicy","prostate":"gruczołu krokowego",
    "medulla oblongata":"rdzenia przedłużonego","fourth ventricle":"komory czwartej",
    "occipital bone":"kości potylicznej","head of fibula":"głowy kości strzałkowej",
    "head of radius":"głowy kości promieniowej","head of ulna":"głowy kości łokciowej",
    "head of rib":"głowy żebra","tubercle of rib":"guzka żebra","trapezium bone":"kości czworobocznej większej",
    "scaphoid bone":"kości łódeczkowatej","navicular bone":"kości łódkowatej","cuboid bone":"kości sześciennej",
    "third metacarpal bone":"kości śródręcza III",
}
MUSCLE_GEN = {   # a few common muscle genitives for bursa / tendon-sheath composition
    "biceps femoris muscle":"mięśnia dwugłowego uda","gastrocnemius muscle":"mięśnia brzuchatego łydki",
    "triceps brachii muscle":"mięśnia trójgłowego ramienia","gluteus maximus muscle":"mięśnia pośladkowego wielkiego",
    "obturator internus":"mięśnia zasłaniacza wewnętrznego","iliacus muscle":"mięśnia biodrowego",
    "infraspinatus muscle":"mięśnia podgrzebieniowego","sartorius muscle":"mięśnia krawieckiego",
    "teres major muscle":"mięśnia obłego większego","tibialis anterior":"mięśnia piszczelowego przedniego",
    "trapezius muscle":"mięśnia czworobocznego","piriformis muscle":"mięśnia gruszkowatego",
    "extensor carpi ulnaris":"prostownika łokciowego nadgarstka","extensor digiti minimi manus":"prostownika palca małego ręki",
    "extensor digitorum longus":"prostownika długiego palców","extensor digitorum":"prostownika palców",
    "fibularis longus muscle":"mięśnia strzałkowego długiego","fibularis muscles":"mięśni strzałkowych",
    "infraspinatus":"mięśnia podgrzebieniowego","teres major":"mięśnia obłego większego",
    "subscapularis":"mięśnia podłopatkowego","subscapularis muscle":"mięśnia podłopatkowego",
    "coracobrachialis":"mięśnia kruczo-ramiennego","coracobrachialis muscle":"mięśnia kruczo-ramiennego",
    "latissimus dorsi":"mięśnia najszerszego grzbietu","latissimus dorsi muscle":"mięśnia najszerszego grzbietu",
    "semimembranosus":"mięśnia półbłoniastego","semimembranosus muscle":"mięśnia półbłoniastego",
}
VERMIS = {
    "culmen":"Szczyt (robak)","declive":"Stok (robak)","folium of vermis":"Blaszka robaka",
    "tuber of vermis":"Guzek robaka","pyramis of vermis":"Piramida robaka",
    "uvula of vermis":"Języczek robaka","nodule of vermis":"Grudka robaka",
    "lingula of cerebellum":"Języczek móżdżku","central lobule":"Płacik środkowy",
    "flocculus":"Kłaczek","biventral lobule":"Płacik dwubrzuścowy",
    "anterior quadrangular lobule":"Płacik czworoboczny przedni",
    "posterior quadrangular lobule":"Płacik czworoboczny tylny",
    "superior semilunar lobule":"Płacik półksiężycowaty górny",
    "inferior semilunar lobule":"Płacik półksiężycowaty dolny",
    "gracile lobule":"Płacik smukły","simple lobule":"Płacik prosty","olive":"Oliwka",
}
OVR = {
    "diaphragm":"Przepona","brain":"Mózg","cerebrum":"Kresomózgowie","cerebellum":"Móżdżek",
    "spinal cord":"Rdzeń kręgowy","auditory tube":"Trąbka słuchowa","central canal":"Kanał środkowy",
    "temporal plane":"Płaszczyzna skroniowa","straight gyrus":"Zakręt prosty",
    "nucleus proprius":"Jądro właściwe","septal nuclei":"Jądra przegrody",
    "spinal dura":"Opona twarda rdzenia kręgowego","spinal dura mater":"Opona twarda rdzenia kręgowego",
    "hippocampal commissure":"Spoidło hipokampa","anterior commissure":"Spoidło przednie",
    "posterior commissure":"Spoidło tylne","fascia lata":"Powięź szeroka",
    "crural fascia":"Powięź goleni","popliteal fascia":"Powięź podkolanowa",
    "epicranial aponeurosis":"Rozcięgno naczaszne","diaphragmatic fascia":"Powięź przeponowa",
    "piriformis fascia":"Powięź mięśnia gruszkowatego","anserine bursa":"Kaletka gęsia",
    "subacromial bursa":"Kaletka podbarkowa","subdeltoid bursa":"Kaletka podnaramienna",
    "suprapatellar bursa":"Kaletka nadrzepkowa","semimembranosus bursa":"Kaletka mięśnia półbłoniastego",
    "reticular formation":"Twór siatkowaty","red nucleus":"Jądro czerwienne",
    "substantia nigra":"Istota czarna","subthalamic nucleus":"Jądro niskowzgórzowe",
    "caudate nucleus":"Jądro ogoniaste","lentiform nucleus":"Jądro soczewkowate",
    "internal capsule":"Torebka wewnętrzna","corpus callosum":"Ciało modzelowate",
    "fornix":"Sklepienie","septum pellucidum":"Przegroda przezroczysta",
    "optic chiasm":"Skrzyżowanie wzrokowe","habenula":"Uzdeczka",
    "lateral geniculate body":"Ciało kolankowate boczne","medial geniculate body":"Ciało kolankowate przyśrodkowe",
    "amygdaloid body":"Ciało migdałowate","hypothalamus":"Podwzgórze","thalamus":"Wzgórze",
    "pineal gland":"Szyszynka","pituitary gland":"Przysadka","infundibulum":"Lejek",
    "midbrain":"Śródmózgowie","pons":"Most","medulla oblongata":"Rdzeń przedłużony",
    "tectum":"Pokrywa","tegmentum":"Nakrywka","cerebral peduncle":"Konar mózgu",
    "superior colliculus":"Wzgórek górny","inferior colliculus":"Wzgórek dolny",
    "cauda equina":"Ogon koński","conus medullaris":"Stożek rdzeniowy","filum terminale":"Nić końcowa",
    "falx cerebri":"Sierp mózgu","tentorium cerebelli":"Namiot móżdżku","dura mater":"Opona twarda",
    "arachnoid mater":"Pajęczynówka","pia mater":"Opona miękka",
    "fibularis longus muscle":"Mięsień strzałkowy długi","fibularis brevis muscle":"Mięsień strzałkowy krótki",
    "fibularis tertius muscle":"Mięsień strzałkowy trzeci","peroneus longus muscle":"Mięsień strzałkowy długi",
    "peroneus brevis muscle":"Mięsień strzałkowy krótki","peroneus tertius muscle":"Mięsień strzałkowy trzeci",
    "bucinator":"Mięsień policzkowy","buccinator":"Mięsień policzkowy",
    "corrugator supercilii":"Mięsień marszczący brwi","depressor anguli oris":"Mięsień obniżacz kąta ust",
    "depressor septi nasi":"Mięsień obniżacz przegrody nosa","depressor labii inferioris":"Mięsień obniżacz wargi dolnej",
    "levator anguli oris":"Mięsień dźwigacz kąta ust","levator labii superioris":"Mięsień dźwigacz wargi górnej",
    "coccygeus muscle":"Mięsień guziczny","dorsal interossei muscles of hand":"Mięśnie międzykostne grzbietowe ręki",
    "dorsal interossei muscles of foot":"Mięśnie międzykostne grzbietowe stopy",
    "palmar interossei muscles":"Mięśnie międzykostne dłoniowe","extensor digitorum":"Mięsień prostownik palców",
    "extensor digiti minimi":"Mięsień prostownik palca małego",
    "tongue":"Język","gingiva":"Dziąsło","uvula of palate":"Języczek podniebienny",
    "suprarenal gland":"Nadnercze","adenohypophysis":"Część gruczołowa przysadki",
    "neurohypophysis":"Część nerwowa przysadki","palatine tonsil":"Migdałek podniebienny",
    "pharyngeal tonsil":"Migdałek gardłowy","lingual tonsil":"Migdałek językowy",
    "mucosa of nasal cavity":"Błona śluzowa jamy nosowej","intermediate bronchus":"Oskrzele pośrednie",
    "anterior chamber of eyeball":"Komora przednia gałki ocznej",
    "posterior chamber of eyeball":"Komora tylna gałki ocznej",
    "anterior segment of eyeball":"Odcinek przedni gałki ocznej",
    "posterior segment of eyeball":"Odcinek tylny gałki ocznej",
    "vitreous body":"Ciało szkliste","aqueous humour":"Ciecz wodnista","crystalline lens":"Soczewka",
    "bicipitoradial bursa":"Kaletka dwugłowo-promieniowa","coracobrachial bursa":"Kaletka kruczo-ramienna",
    "iliopectineal bursa":"Kaletka biodrowo-łonowa","common flexor tendon sheath":"Pochewka wspólna zginaczy",
    "deep infrapatellar bursa":"Kaletka podrzepkowa głęboka",
    "subcutaneous infrapatellar bursa":"Kaletka podrzepkowa podskórna",
    "subcutaneous prepatellar bursa":"Kaletka przedrzepkowa podskórna",
    "subfascial prepatellar bursa":"Kaletka przedrzepkowa podpowięziowa",
    "subtendinous prepatellar bursa":"Kaletka przedrzepkowa podścięgnowa",
    "subcutaneous trochanteric bursa":"Kaletka krętarzowa podskórna",
    "subcutaneous calcaneal bursa":"Kaletka piętowa podskórna",
    "subtendinous calcaneal bursa":"Kaletka piętowa podścięgnowa",
    "cruciform part of fibrous sheath of digit of hand":"Część krzyżowa pochewki włóknistej palca ręki",
    "epicranial aponeurosis":"Czepiec ścięgnisty","palmar aponeurosis":"Rozcięgno dłoniowe",
    "plantar aponeurosis":"Rozcięgno podeszwowe","thoracolumbar fascia":"Powięź piersiowo-lędźwiowa",
    "auditory tube":"Trąbka słuchowa","central canal":"Kanał środkowy rdzenia kręgowego",
    "spinal dura":"Opona twarda rdzenia kręgowego","septal nuclei":"Jądra przegrody",
    "nucleus proprius":"Jądro właściwe","intermediolateral nucleus":"Jądro pośrednio-boczne",
    "intermediomedial nucleus":"Jądro pośrednio-przyśrodkowe","temporal plane":"Płaszczyzna skroniowa",
    "posterolateral tract":"Droga tylno-boczna (Lissauera)","spinotectal tract":"Droga rdzeniowo-pokrywowa",
    "olive":"Oliwka","hippocampal commissure":"Spoidło hipokampa","straight gyrus":"Zakręt prosty",
    "gyrus rectus":"Zakręt prosty","anterior fasciculus proprius":"Pęczek własny przedni",
    "lateral fasciculus proprius":"Pęczek własny boczny","posterior fasciculus proprius":"Pęczek własny tylny",
    "lateral corticospinal tract":"Droga korowo-rdzeniowa boczna",
    "anterior corticospinal tract":"Droga korowo-rdzeniowa przednia",
    "anterior spinothalamic tract":"Droga rdzeniowo-wzgórzowa przednia",
    "lateral spinothalamic tract":"Droga rdzeniowo-wzgórzowa boczna",
    "anterior spinocerebellar tract":"Droga rdzeniowo-móżdżkowa przednia",
    "posterior spinocerebellar tract":"Droga rdzeniowo-móżdżkowa tylna",
}

# --- adjective bank for lymph-node / bronchus / generic region composition ---
ADJ = {
  "axillary":"pachowe","jugular":"szyjne wewnętrzne","cervical":"szyjne","inguinal":"pachwinowe",
  "iliac":"biodrowe","sacral":"krzyżowe","tracheobronchial":"tchawiczo-oskrzelowe",
  "pancreatic":"trzustkowe","pancreaticoduodenal":"trzustkowo-dwunastnicze","colic":"okrężnicze",
  "paracolic":"przyokrężnicze","sigmoid":"esicze","gastric":"żołądkowe","parotid":"przyuszne",
  "intraglandular":"śródgruczołowe","mastoid":"sutkowe","occipital":"potyliczne",
  "submandibular":"podżuchwowe","submental":"podbródkowe","supraclavicular":"nadobojczykowe",
  "mesenteric":"krezkowe","obturator":"zasłonowe","brachiocephalic":"ramienno-głowowe",
  "paratracheal":"okołotchawicze","pretracheal":"przedtchawicze","retropharyngeal":"zagardłowe",
  "pericardial":"osierdziowe","prepericardial":"przedosierdziowe","popliteal":"podkolanowe",
  "apical":"szczytowe","central":"środkowe","anterior":"przednie","posterior":"tylne",
  "superior":"górne","inferior":"dolne","deep":"głębokie","superficial":"powierzchowne",
  "lateral":"boczne","medial":"przyśrodkowe","intermediate":"pośrednie","common":"wspólne",
  "external":"zewnętrzne","internal":"wewnętrzne","median":"pośrodkowe","proximal":"bliższe",
  "distal":"dalsze","subaortic":"podaortalne","retro-aortic":"zaaortalne","retroaortic":"zaaortalne",
  "retrocaval":"zażylne (za żyłą główną)","retropyloric":"zaodźwiernikowe","subpyloric":"pododźwiernikowe",
  "suprapyloric":"nadodźwiernikowe","juxta-oesophageal":"przyprzełykowe","juxtaoesophageal":"przyprzełykowe",
  "intrapulmonary":"śródpłucne","infra-auricular":"poduszne","infraauricular":"poduszne",
  "pre-auricular":"przeduszne","preauricular":"przeduszne","nasolabial":"nosowo-wargowe",
  "buccinator":"policzkowe","mandibular":"żuchwowe","thyroid":"tarczowe","lacunar":"zatokowe (rozstępu)",
  "fibular":"strzałkowe","tibial":"piszczelowe","superolateral":"górno-boczne","superomedial":"górno-przyśrodkowe",
  "jugulodigastric":"żyłowo-dwubrzuścowy","subscapular":"podłopatkowe","pectoral":"piersiowe",
  "lumbar":"lędźwiowe","aortic":"aortalne","hilar":"wnękowe","bronchopulmonary":"oskrzelowo-płucne",
  "lingular":"języczkowe","apicoposterior":"szczytowo-tylne","anteromedial":"przednio-przyśrodkowe",
  "basal":"podstawne","middle":"środkowe","pyloric":"odźwiernikowe","thoracic":"klatki piersiowej","abdominal":"brzucha","pelvic":"miednicy",
}
NODE_ADJ_ORDER = ["superficial","deep","superolateral","superomedial","apical","central","anterior",
  "posterior","superior","inferior","lateral","medial","intermediate","common","proximal","distal",
  "external","internal","median"]

_POSITIONAL = {"superficial","deep","apical","central","anterior","posterior","superior","inferior",
               "lateral","medial","intermediate","common","proximal","distal","external","internal",
               "median","superolateral","superomedial"}
def _lymph(n):
    n = n.strip("() ")
    m = re.match(r'^(.+?)\s+(?:lymph\s+)?(node|nodes)$', n)
    if not m: return None
    head = "Węzeł chłonny" if m.group(2) == "node" else "Węzły chłonne"
    words = m.group(1).lower().split()
    region, pos, unk = [], [], []
    for w in words:
        key = w if w in ADJ else None            # keep hyphenated keys intact
        if key is None:
            unk.append(w); continue
        (pos if w in _POSITIONAL else region).append(ADJ[key])
    if unk: return None
    return f"{head} {' '.join(region + pos)}".strip()

def _bronchus(n):
    m = re.match(r'^(.+?) segmental bronchus of (right|left) lung(?:\s*\(([^)]+)\))?$', n)
    if not m: return None
    adjw = m.group(1).replace("-", " ").split()
    pls = [ADJ.get(w, w) for w in adjw]
    lung = "prawego" if m.group(2) == "right" else "lewego"
    tag = f" ({m.group(3).upper()})" if m.group(3) else ""
    return f"Oskrzele segmentowe {' '.join(pls)} płuca {lung}{tag}".strip()

def _liver_seg(n):
    m = re.match(r'^(.+) segment of liver \(([ivx]+)\)$', n, re.I)
    if m: return f"Segment wątroby [{m.group(2).upper()}]"
    return None

def _lung_seg(n):
    m = re.match(r'^(.+?) segment of (right|left) lung(?:\s*\(([^)]+)\))?$', n, re.I)
    if not m: return None
    adjw = m.group(1).replace("-", " ").split()
    pls = [POS[w][0] if w in POS else w for w in adjw]   # masculine, agrees with "Segment"
    lung = "prawego" if m.group(2).lower() == "right" else "lewego"
    tag = f" ({m.group(3).upper()})" if m.group(3) else ""
    return f"Segment {' '.join(pls)} płuca {lung}{tag}".strip()

# region-suffix muscles: "<base> <colli|thoracis|lumborum|cervicis|capitis> muscle"
_MREGION = {"colli":"szyi","cervicis":"szyi","thoracis":"klatki piersiowej","lumborum":"lędźwi",
            "capitis":"głowy","abdominis":"brzucha"}
_MBASE = {
    "iliocostalis":"Mięsień biodrowo-żebrowy","longissimus":"Mięsień najdłuższy",
    "spinalis":"Mięsień kolcowy","semispinalis":"Mięsień półkolcowy","multifidus":"Mięsień wielodzielny",
    "splenius":"Mięsień płatowaty","longus":"Mięsień długi","rectus":"Mięsień prosty",
    "obliquus":"Mięsień skośny","interspinales":"Mięśnie międzykolcowe",
    "intertransversarii":"Mięśnie międzypoprzeczne","rotatores":"Mięśnie skręcające",
    "levatores":"Mięśnie dźwigacze żeber",
}
def _muscle(n):
    m = re.match(r'^(iliocostalis|longissimus|spinalis|semispinalis|multifidus|splenius|longus|'
                 r'interspinales|obliquus) (colli|cervicis|thoracis|lumborum|capitis)( muscles?)?$', n)
    if m and m.group(1) in _MBASE:
        return f"{_MBASE[m.group(1)]} {_MREGION[m.group(2)]}"
    m = re.match(r'^(obliquus|rectus) (superior|inferior|anterior|posterior|lateral)?\s*'
                 r'(major|minor)?\s*capitis( muscle)?$', n)
    if m:
        base = "Mięsień skośny głowy" if m.group(1) == "obliquus" else "Mięsień prosty głowy"
        parts = [POS[m.group(2)][0] if m.group(2) in POS else "",
                 {"major":"większy","minor":"mniejszy",None:""}[m.group(3)]]
        return re.sub(r'\s+', ' ', f"{base} {' '.join(p for p in parts if p)}").strip()
    m = re.match(r'^(superior|middle|inferior) pharyngeal constrictor( muscle)?$', n)
    if m:
        return f"Mięsień zwieracz gardła {POS[m.group(1)][0]}"
    m = re.match(r'^(superior|inferior) gemellus( muscle)?$', n)
    if m: return f"Mięsień bliźniaczy {POS[m.group(1)][0]}"
    m = re.match(r'^scalenus (anterior|medius|posterior)( muscle)?$', n)
    if m:
        return {"anterior":"Mięsień pochyły przedni","medius":"Mięsień pochyły środkowy",
                "posterior":"Mięsień pochyły tylny"}[m.group(1)]
    m = re.match(r'^lumbrical muscles of (hand|foot)$', n)
    if m: return f"Mięśnie glistowate {'ręki' if m.group(1)=='hand' else 'stopy'}"
    m = re.match(r'^flexor digiti minimi of (hand|foot)$', n) or \
        re.match(r'^flexor digiti minimi (brevis )?(of )?(hand|foot)$', n)
    if m: return f"Mięsień zginacz krótki palca małego {'ręki' if 'hand' in n else 'stopy'}"
    return None
_MUSC_GEN_FULL = {   # "<X> muscle" -> genitive "mięśnia <...>" for "nerve to / bursa of"
    "mylohyoid":"żuchwowo-gnykowego","piriformis":"gruszkowatego","quadratus femoris":"czworobocznego uda",
    "obturator internus":"zasłaniacza wewnętrznego","obturator externus":"zasłaniacza zewnętrznego",
    "gluteus medius":"pośladkowego średniego","gluteus minimus":"pośladkowego małego",
    "gluteus maximus":"pośladkowego wielkiego","tibialis posterior":"piszczelowego tylnego",
    "tibialis anterior":"piszczelowego przedniego","digastric":"dwubrzuścowego",
    "superior oblique":"skośnego górnego (oka)","extensor pollicis longus":"prostownika długiego kciuka",
    "flexor pollicis longus":"zginacza długiego kciuka","flexor carpi radialis":"zginacza promieniowego nadgarstka",
    "extensor digitorum longus":"prostownika długiego palców","extensor digitorum":"prostownika palców",
}
def _nerve_vessel(n):
    _TG = {"superior":"górnego","middle":"środkowego","inferior":"dolnego"}
    m = re.match(r'^(anterior|posterior) division of (superior|middle|inferior) trunk of brachial plexus$', n)
    if m: return f"Podział {POS[m.group(1)][0]} pnia {_TG[m.group(2)]} splotu ramiennego"
    m = re.match(r'^(anterior|posterior) division of (mandibular nerve|internal iliac artery|retromandibular vein)$', n)
    if m:
        base = {"mandibular nerve":"nerwu żuchwowego","internal iliac artery":"tętnicy biodrowej wewnętrznej",
                "retromandibular vein":"żyły zażuchwowej"}[m.group(2)]
        return f"Podział {POS[m.group(1)][0]} {base}"
    m = re.match(r'^(anterior|posterior) root of spinal nerve$', n)
    if m: return f"Korzeń {POS[m.group(1)][0]} nerwu rdzeniowego"
    m = re.match(r'^(motor|sensory) root of trigeminal nerve$', n)
    if m: return f"Korzeń {'ruchowy' if m.group(1)=='motor' else 'czuciowy'} nerwu trójdzielnego"
    m = re.match(r'^(anterior|posterior) interosseous nerve of forearm$', n)
    if m: return f"Nerw międzykostny {POS[m.group(1)][0]} przedramienia"
    m = re.match(r'^(superior|inferior) subscapular nerve$', n)
    if m: return f"Nerw podłopatkowy {POS[m.group(1)][0]}"
    m = re.match(r'^nerve to (.+?)(?: muscle)?$', n)
    if m and m.group(1) in _MUSC_GEN_FULL: return f"Nerw do mięśnia {_MUSC_GEN_FULL[m.group(1)]}"
    m = re.match(r'^(posterior|lateral|medial) cord of brachial plexus$', n)
    if m: return f"Pęczek {POS[m.group(1)][0]} splotu ramiennego"
    if n == "roots of brachial plexus": return "Korzenie splotu ramiennego"
    if n == "sympathetic nerves": return "Nerwy współczulne"
    if n == "ganglia of sympathetic trunk": return "Zwoje pnia współczulnego"
    if n == "posterior femoral cutaneous nerve": return "Nerw skórny tylny uda"
    # "trochanteric bursa of gluteus X muscle"
    m = re.match(r'^trochanteric bursa of (.+?)(?: muscle)?$', n)
    if m and m.group(1) in _MUSC_GEN_FULL: return f"Kaletka krętarzowa mięśnia {_MUSC_GEN_FULL[m.group(1)]}"
    m = re.match(r'^tendon sheath of (.+?)(?: muscle)?$', n)
    if m and m.group(1) in _MUSC_GEN_FULL: return f"Pochewka ścięgna {_MUSC_GEN_FULL[m.group(1)]}"
    m = re.match(r'^tendon of (.+?)(?: muscle)?$', n)
    if m and m.group(1) in _MUSC_GEN_FULL: return f"Ścięgno mięśnia {_MUSC_GEN_FULL[m.group(1)]}"
    return None

_FACIAL_OVR = {
    "frontalis muscle":"Mięsień czołowy","occipitalis muscle":"Mięsień potyliczny",
    "temporoparietalis muscle":"Mięsień skroniowo-ciemieniowy","procerus muscle":"Mięsień podłużny nosa",
    "nasalis muscle":"Mięsień nosowy","mentalis muscle":"Mięsień bródkowy","risorius muscle":"Mięsień śmiechowy",
    "zygomaticus major muscle":"Mięsień jarzmowy większy","zygomaticus minor muscle":"Mięsień jarzmowy mniejszy",
    "genioglossus muscle":"Mięsień bródkowo-językowy","hyoglossus muscle":"Mięsień gnykowo-językowy",
    "styloglossus muscle":"Mięsień rylcowo-językowy","palatoglossus muscle":"Mięsień podniebienno-językowy",
    "levator nasolabialis":"Mięsień dźwigacz wargi górnej i skrzydła nosa",
    "semitendinosus muscle":"Mięsień półścięgnisty","semimembranosus muscle":"Mięsień półbłoniasty",
    "pubococcygeus muscle":"Mięsień łonowo-guziczny","iliococcygeus muscle":"Mięsień biodrowo-guziczny",
    "extensor retinaculum of wrist":"Troczek prostowników nadgarstka",
    "flexor retinaculum of ankle":"Troczek zginaczy (kostka)","adductor minimus":"Mięsień przywodziciel najmniejszy",
    "deep brachial artery":"Tętnica głęboka ramienia","proper hepatic artery":"Tętnica wątrobowa właściwa",
    "common facial vein":"Żyła twarzowa wspólna","inferior epigastric vein":"Żyła nabrzuszna dolna",
    "anterior interventricular artery":"Gałąź międzykomorowa przednia","arcuate artery":"Tętnica łukowata",
    "superficial external pudendal artery":"Tętnica sromowa zewnętrzna powierzchowna",
    "posterior superior alveolar artery":"Tętnica zębodołowa górna tylna",
    "parieto-occipital artery":"Tętnica ciemieniowo-potyliczna","dorsal carpal anastomosis":"Sieć grzbietowa nadgarstka",
    "basilar venous plexus":"Splot żylny podstawny","bifurcation of pulmonary trunk":"Rozwidlenie pnia płucnego",
    "perforating femoral arteries":"Tętnice przeszywające uda","lateral plantar veins":"Żyły podeszwowe boczne",
    "medial plantar veins":"Żyły podeszwowe przyśrodkowe","intercapitular veins of foot":"Żyły międzygłówkowe stopy",
    "intertubercular tendon sheath":"Pochewka ścięgna międzyguzkowa","fascia lata":"Powięź szeroka",
    "superficial investing cervical fascia":"Blaszka powierzchowna powięzi szyi",
    "intermediate tendon of digastric muscle":"Ścięgno pośrednie mięśnia dwubrzuścowego",
    "trochlea of superior oblique muscle":"Bloczek mięśnia skośnego górnego (oka)",
    "middle layer of thoracolumbar fascia":"Blaszka środkowa powięzi piersiowo-lędźwiowej",
    "anterior interosseous nerve of forearm":"Nerw międzykostny przedni przedramienia",
    "posterior interosseous nerve of forearm":"Nerw międzykostny tylny przedramienia",
}

TRACT_RE = re.compile(r'^(anterior|posterior|lateral|medial|superior|inferior)?\s*'
    r'(cortico|spino|reticulo|rubro|tecto|vestibulo|olivo)?(spinal|thalamic|cerebellar|'
    r'tectal|bulbar|rubral|nuclear|reticular)?\s*(tract|fasciculus)$')

def _adj(word, gender):
    t = POS.get(word)
    return t[gender] if t else word

# --- second-wave manual dictionary (standard PL for long-tail Z-Anatomy names) ---
OVR2 = {
 # pelvis / hip bone
 "iliac crest":"Grzebień biodrowy","iliac tubercle":"Guzek biodrowy","iliac fossa":"Dół biodrowy",
 "iliopubic eminence":"Wyniosłość biodrowo-łonowa","pubic tubercle":"Guzek łonowy",
 "pubic crest":"Grzebień łonowy","pecten pubis":"Grzebień kości łonowej","pecten of pubis":"Grzebień kości łonowej",
 "ischiopubic ramus":"Gałąź kulszowo-łonowa","ramus of ischium":"Gałąź kości kulszowej",
 "ischial spine":"Kolec kulszowy","ischial tuberosity":"Guz kulszowy","obturator crest":"Grzebień zasłonowy",
 "obturator groove":"Bruzda zasłonowa","supra-acetabular groove":"Bruzda nadpanewkowa",
 "acetabular margin":"Brzeg panewki","acetabular notch":"Wcięcie panewki","acetabular fossa":"Dół panewki",
 "posterior gluteal line":"Kresa pośladkowa tylna","anterior gluteal line":"Kresa pośladkowa przednia",
 "inferior gluteal line":"Kresa pośladkowa dolna","inner lip of iliac crest":"Warga wewnętrzna grzebienia biodrowego",
 "outer lip of iliac crest":"Warga zewnętrzna grzebienia biodrowego","intermediate zone":"Kresa pośrednia (grzebienia biodrowego)",
 # femur / knee
 "lesser trochanter":"Krętarz mniejszy","greater trochanter":"Krętarz większy","third trochanter":"Krętarz trzeci",
 "trochanteric fossa":"Dół krętarzowy","intertrochanteric line":"Kresa międzykrętarzowa",
 "intertrochanteric crest":"Grzebień międzykrętarzowy","quadrate tubercle":"Guzek czworoboczny",
 "gluteal tuberosity":"Guzowatość pośladkowa","pectineal line of femur":"Kresa grzebieniowa kości udowej",
 "intercondylar area":"Pole międzykłykciowe","intercondylar fossa":"Dół międzykłykciowy",
 "intercondylar line":"Kresa międzykłykciowa","popliteal surface":"Powierzchnia podkolanowa",
 "adductor tubercle":"Guzek przywodzicieli","patellar surface":"Powierzchnia rzepkowa",
 "lateral condyle of femur":"Kłykieć boczny kości udowej","medial condyle of femur":"Kłykieć przyśrodkowy kości udowej",
 "lateral epicondyle of femur":"Nadkłykieć boczny kości udowej","medial epicondyle of femur":"Nadkłykieć przyśrodkowy kości udowej",
 "lateral lip of linea aspera":"Warga boczna kresy chropawej","medial lip of linea aspera":"Warga przyśrodkowa kresy chropawej",
 "lateral lip of linea apera":"Warga boczna kresy chropawej","medial lip of linea apera":"Warga przyśrodkowa kresy chropawej",
 # tibia / fibula / foot
 "lateral condyle of tibia":"Kłykieć boczny kości piszczelowej","medial condyle of tibia":"Kłykieć przyśrodkowy kości piszczelowej",
 "tibial plateau":"Powierzchnia górna kości piszczelowej","superior articular surfaces of tibia":"Powierzchnie stawowe górne kości piszczelowej",
 "posterior malleolus":"Kostka tylna","calcaneal tubercle":"Guzek piętowy","calcaneal tuberosity":"Guz piętowy",
 "talar sulcus":"Bruzda kości skokowej","calcaneal sulcus":"Bruzda kości piętowej",
 "sustentaculum tali":"Podpórka kości skokowej","navicular articular surface":"Powierzchnia stawowa łódkowata",
 "facet for plantar calcaneonavicular ligament":"Powierzchnia dla więzadła piętowo-łódkowego podeszwowego",
 "tuberosity of navicular bone":"Guzowatość kości łódkowatej","tuberosity of cuboid bone":"Guzowatość kości sześciennej",
 "tuberosity of distal phalanx of foot":"Guzowatość paliczka dalszego stopy",
 "tuberosity of distal phalanx of hand":"Guzowatość paliczka dalszego ręki",
 "trochlea of phalanx of foot":"Bloczek paliczka stopy","trochlea of phalanx of hand":"Bloczek paliczka ręki",
 "metacarpal base":"Podstawa kości śródręcza","metatarsal base":"Podstawa kości śródstopia",
 # scapula / clavicle / humerus / forearm
 "glenoid fossa":"Wydrążenie stawowe łopatki","glenoid cavity":"Wydrążenie stawowe łopatki",
 "scapular notch":"Wcięcie łopatki","spinoglenoid notch":"Wcięcie szyjki łopatki",
 "supraglenoid tubercle":"Guzek nadpanewkowy","infraglenoid tubercle":"Guzek podpanewkowy",
 "sternal articular surface":"Powierzchnia stawowa mostkowa","acromial facet":"Powierzchnia stawowa barkowa",
 "capitulum of humerus":"Główka kości ramiennej","trochlea of humerus":"Bloczek kości ramiennej",
 "lateral epicondyle of humerus":"Nadkłykieć boczny kości ramiennej","medial epicondyle of humerus":"Nadkłykieć przyśrodkowy kości ramiennej",
 "radial groove":"Bruzda nerwu promieniowego","deltoid tuberosity":"Guzowatość naramienna",
 "dorsal radial tubercle":"Guzek grzbietowy kości promieniowej","grooves for extensor tendons":"Bruzdy dla ścięgien prostowników",
 "sublime tubercle":"Guzek wyniosły","supinator crest":"Grzebień mięśnia odwracacza",
 "articular circumference of head of radius":"Obwód stawowy głowy kości promieniowej",
 "articular circumference of head of ulna":"Obwód stawowy głowy kości łokciowej",
 "hook of hamate bone":"Haczyk kości haczykowatej","tubercle of trapezium bone":"Guzek kości czworobocznej większej",
 "tubercle of scaphoid bone":"Guzek kości łódeczkowatej",
 # vertebrae
 "superior articular facet of vertebra":"Powierzchnia stawowa górna kręgu","inferior articular facet of vertebra":"Powierzchnia stawowa dolna kręgu",
 "superior articular process of vertebra":"Wyrostek stawowy górny kręgu","inferior articular process of vertebra":"Wyrostek stawowy dolny kręgu",
 "superior vertebral notch":"Wcięcie kręgowe górne","inferior vertebral notch":"Wcięcie kręgowe dolne",
 "pedicle of vertebral arch":"Nasada łuku kręgu","lamina of vertebral arch":"Blaszka łuku kręgu",
 "pars interarticularis of vertebral arch":"Część międzystawowa łuku kręgu",
 "uncinate process of vertebra":"Wyrostek haczykowaty kręgu","uncinate process of first thoracic vertebra":"Wyrostek haczykowaty kręgu piersiowego I",
 "annular epiphysis":"Nasada pierścieniowata","transverse ligament tubercle":"Guzek więzadła poprzecznego",
 "costal part of transverse process":"Część żebrowa wyrostka poprzecznego","lateral part of transverse process":"Część boczna wyrostka poprzecznego",
 "anterior tubercle of transverse process":"Guzek przedni wyrostka poprzecznego","posterior tubercle of transverse process":"Guzek tylny wyrostka poprzecznego",
 "ala of sacrum":"Skrzydło kości krzyżowej","dens axis":"Ząb kręgu obrotowego","dens of axis":"Ząb kręgu obrotowego",
 "anterior arch of atlas":"Łuk przedni kręgu szczytowego","posterior arch of atlas":"Łuk tylny kręgu szczytowego",
 "anterior tubercle of atlas":"Guzek przedni kręgu szczytowego","posterior tubercle of atlas":"Guzek tylny kręgu szczytowego",
 "apex of dens axis":"Szczyt zęba kręgu obrotowego",
 "anterior articular facet of dens axis":"Powierzchnia stawowa przednia zęba kręgu obrotowego",
 "posterior articular facet of dens axis":"Powierzchnia stawowa tylna zęba kręgu obrotowego",
 # ribs / sternum
 "crest of neck of rib":"Grzebień szyjki żebra","crest of head of rib":"Grzebień głowy żebra",
 "articular facet of tubercle of rib":"Powierzchnia stawowa guzka żebra","articular facets of head of rib":"Powierzchnie stawowe głowy żebra",
 "articular facet of head of rib":"Powierzchnia stawowa głowy żebra","tubercle of rib":"Guzek żebra","angle of rib":"Kąt żebra",
 "costal groove":"Bruzda żebra","groove for subclavius muscle":"Bruzda mięśnia podobojczykowego",
 "clavicular notch":"Wcięcie obojczykowe","costal notches":"Wcięcia żebrowe","suprasternal notch":"Wcięcie szyjne mostka",
 # skull
 "frontal eminence":"Guz czołowy","frontal tuber":"Guz czołowy","parietal eminence":"Guz ciemieniowy",
 "foramen caecum of frontal bone":"Otwór ślepy kości czołowej","orbital plate of frontal bone":"Blaszka oczodołowa kości czołowej",
 "orbital part of frontal bone":"Część oczodołowa kości czołowej","septum of frontal sinuses":"Przegroda zatok czołowych",
 "septum of frontal sinuses ":"Przegroda zatok czołowych","internal surface of squamous part of frontal bone":"Powierzchnia wewnętrzna łuski kości czołowej",
 "frontal part of orbital margin":"Część czołowa brzegu oczodołu","supra-orbital notch":"Wcięcie nadoczodołowe",
 "supraorbital notch":"Wcięcie nadoczodołowe","fossa for lacrimal gland":"Dół gruczołu łzowego",
 "occipital plane":"Płaszczyzna potyliczna","supreme nuchal line":"Kresa karkowa najwyższa","supreme nuchal line ":"Kresa karkowa najwyższa",
 "external occipital crest":"Grzebień potyliczny zewnętrzny","internal occipital crest":"Grzebień potyliczny wewnętrzny",
 "vermian fossa":"Dół robaka","cerebellar fossa":"Dół móżdżkowy","cerebral fossa":"Dół mózgowy",
 "lateral pterygoid plate":"Blaszka boczna wyrostka skrzydłowatego","medial pterygoid plate":"Blaszka przyśrodkowa wyrostka skrzydłowatego",
 "pterygoid notch":"Wcięcie skrzydłowe","pterygospinous process":"Wyrostek skrzydłowo-kolcowy",
 "sphenoidal yoke":"Jarzmo klinowe","sphenoid yoke":"Jarzmo klinowe","limbus of sphenoid":"Rąbek klinowy",
 "middle clinoid process":"Wyrostek pochyły środkowy","carotid sulcus":"Bruzda tętnicy szyjnej",
 "chiasmatic sulcus":"Bruzda skrzyżowania wzrokowego","prechiasmatic sulcus":"Bruzda przedskrzyżowaniowa",
 "sulcus of auditory tube":"Bruzda trąbki słuchowej","mastoid notch":"Wcięcie sutkowe",
 "occipital margin of temporal bone":"Brzeg potyliczny kości skroniowej","mastoid border of occipital bone":"Brzeg sutkowy kości potylicznej",
 "mandibular symphysis":"Spojenie żuchwy","mental tubercle":"Guzek bródkowy","genion":"Kolec bródkowy (genion)",
 "superior mental spine":"Kolec bródkowy górny","inferior mental spine":"Kolec bródkowy dolny",
 "mandibular dental arch":"Łuk zębowy żuchwy","maxillary dental arch":"Łuk zębowy szczęki",
 # larynx cartilages
 "superior thyroid notch":"Wcięcie tarczowe górne","inferior thyroid notch":"Wcięcie tarczowe dolne",
 "superior thyroid tubercle":"Guzek tarczowy górny","inferior thyroid tubercle":"Guzek tarczowy dolny",
 "thyroid articular surface":"Powierzchnia stawowa tarczowa","arytenoid articular surface":"Powierzchnia stawowa nalewkowa",
 "arch of cricoid cartilage":"Łuk chrząstki pierścieniowatej","lamina of cricoid cartilage":"Blaszka chrząstki pierścieniowatej",
 "lamina of thyroid cartilage":"Blaszka chrząstki tarczowatej","oblique line of thyroid cartilage":"Kresa skośna chrząstki tarczowatej",
 "superior horn of thyroid cartilage":"Róg górny chrząstki tarczowatej","inferior horn of thyroid cartilage":"Róg dolny chrząstki tarczowatej",
 "vocal process":"Wyrostek głosowy","muscular process":"Wyrostek mięśniowy","apex of arytenoid cartilage":"Szczyt chrząstki nalewkowatej",
 "base of arytenoid cartilage":"Podstawa chrząstki nalewkowatej",
 # ear ossicles
 "anterior limb of stapes":"Odnoga przednia strzemiączka","posterior limb of stapes":"Odnoga tylna strzemiączka",
 "long limb of incus":"Odnoga długa kowadełka","short limb of incus":"Odnoga krótka kowadełka",
 "base of stapes":"Podstawa strzemiączka","head of stapes":"Główka strzemiączka",
 "articular facet for malleus":"Powierzchnia stawowa dla młoteczka","articular facet for stapes":"Powierzchnia stawowa dla strzemiączka",
 "articular facet of head of malleus":"Powierzchnia stawowa głowy młoteczka","lenticular process of incus":"Wyrostek soczewkowaty kowadełka",
 "anterior process of malleus":"Wyrostek przedni młoteczka","lateral process of malleus":"Wyrostek boczny młoteczka",
 "head of malleus":"Głowa młoteczka","neck of malleus":"Szyjka młoteczka","manubrium of malleus":"Rękojeść młoteczka",
 "body of incus":"Trzon kowadełka",
 # teeth surfaces
 "distal surface of tooth":"Powierzchnia dalsza zęba","mesial surface of tooth":"Powierzchnia bliższa zęba",
 "lingual surface of tooth":"Powierzchnia językowa zęba","vestibular surface of tooth":"Powierzchnia przedsionkowa zęba",
 "occlusal surface of tooth":"Powierzchnia żująca zęba","cusp of tooth":"Guzek zęba",
 "crown of tooth":"Korona zęba","root of tooth":"Korzeń zęba","neck of tooth":"Szyjka zęba",
 # pituitary / endocrine
 "hypophysis":"Przysadka","pituitary gland":"Przysadka","adenohypophysis":"Część gruczołowa przysadki",
 "pars distalis of hypophysis":"Część dalsza przysadki","pars intermedia of hypophysis":"Część pośrednia przysadki",
 "pars nervosa of hypophysis":"Część nerwowa przysadki","pars tuberalis of hypophysis":"Część guzowa przysadki",
 "pars tubelaris of hypophysis":"Część guzowa przysadki","infundibular stalk":"Lejek przysadki",
 "infundibulum of hypophysis":"Lejek przysadki","parathyroid gland":"Gruczoł przytarczyczny",
 "isthmus of thyroid gland":"Cieśń gruczołu tarczowego","suprarenal gland":"Nadnercze",
 "hilum of spleen":"Wnęka śledziony","hilum of suprarenal gland":"Wnęka nadnercza","hilum of kidney":"Wnęka nerki",
 "bare area of liver":"Pole nagie wątroby",
 "left lateral division of liver":"Część boczna lewa wątroby","left medial division of liver":"Część przyśrodkowa lewa wątroby",
 "right lateral division of liver":"Część boczna prawa wątroby","right medial division of liver":"Część przyśrodkowa prawa wątroby",
 # brain grey/white
 "grey matter":"Istota szara","white matter":"Istota biała","gray matter":"Istota szara",
 "grey matter of spinal cord":"Istota szara rdzenia kręgowego","white matter of spinal cord":"Istota biała rdzenia kręgowego",
 "grey matter of medulla oblongata":"Istota szara rdzenia przedłużonego",
 "grey matter of pontine tegmentum":"Istota szara nakrywki mostu","grey matter of tegmentum of midbrain":"Istota szara nakrywki śródmózgowia",
 "white matter of diencephalon":"Istota biała międzymózgowia","white matter of telencephalon":"Istota biała kresomózgowia",
 "central structures of spinal cord":"Struktury środkowe rdzenia kręgowego","intermediate zone of spinal cord":"Strefa pośrednia rdzenia kręgowego",
 "anterior funiculus":"Sznur przedni","posterior funiculus":"Sznur tylny","lateral funiculus":"Sznur boczny",
 "anterior median fissure of medulla oblongata":"Szczelina pośrodkowa przednia rdzenia przedłużonego",
 "pyramid of medulla oblongata":"Piramida rdzenia przedłużonego","tectum of midbrain":"Pokrywa śródmózgowia",
 "aqueduct of midbrain":"Wodociąg mózgu","cerebral aqueduct":"Wodociąg mózgu","ependyma":"Wyściółka",
 "dorsal striatum":"Prążkowie grzbietowe","basal forebrain":"Przodomózgowie podstawne",
 "commissural fibres of telencephalon":"Włókna spoidłowe kresomózgowia","projection fibres of telencephalon":"Włókna rzutowe kresomózgowia",
 "walls of lateral ventricle":"Ściany komory bocznej","interlobar sulci":"Bruzdy międzypłatowe",
 "oculomotor complex":"Zespół jąder nerwu okoruchowego","nucleus of accessory nerve":"Jądro nerwu dodatkowego",
 "central mesencephalic structures":"Struktury środkowe śródmózgowia","spinal reticular process":"Wyrostek siatkowaty rdzenia",
 "lateral intermediate substance":"Istota pośrednia boczna",
 "superior medulla oblongata":"Rdzeń przedłużony (część górna)","inferior medulla oblongata":"Rdzeń przedłużony (część dolna)",
 # eye
 "corneoscleral junction":"Rąbek rogówki","anterior pole of eyeball":"Biegun przedni gałki ocznej",
 "posterior pole of eyeball":"Biegun tylny gałki ocznej",
 # heart valve leaflets
 "left coronary leaflet":"Płatek wieńcowy lewy zastawki aorty","right coronary leaflet":"Płatek wieńcowy prawy zastawki aorty",
 "non-coronary leaflet":"Płatek niewieńcowy zastawki aorty","noncoronary leaflet":"Płatek niewieńcowy zastawki aorty",
 "anterior semilunar leaflet of pulmonary valve":"Płatek półksiężycowaty przedni zastawki pnia płucnego",
 "left semilunar leaflet of pulmonary valve":"Płatek półksiężycowaty lewy zastawki pnia płucnego",
 "right semilunar leaflet of pulmonary valve":"Płatek półksiężycowaty prawy zastawki pnia płucnego",
 "inferior leaflet of right atrioventricular valve":"Płatek dolny zastawki przedsionkowo-komorowej prawej",
 "septal leaflet of right atrioventricular valve":"Płatek przegrodowy zastawki przedsionkowo-komorowej prawej",
 "posterior leaflet of left atrioventricular valve":"Płatek tylny zastawki przedsionkowo-komorowej lewej",
 "inferior vein of left ventricle":"Żyła dolna komory lewej","great cardiac vein":"Żyła serca wielka",
 "anterior interventricular artery":"Gałąź międzykomorowa przednia","posterior interventricular artery":"Gałąź międzykomorowa tylna",
 # nerves / vessels extra
 "aqueduct of midbrain ":"Wodociąg mózgu","node of ligamentum arteriosum":"Węzeł chłonny więzadła tętniczego",
 "postcentral arterial branch":"Gałąź tętnicza zaśrodkowa","parieto-occipital artery":"Tętnica ciemieniowo-potyliczna",
 "dorsal digital arteries of hand":"Tętnice grzbietowe palców ręki","dorsal digital veins of hand":"Żyły grzbietowe palców ręki",
 "intrarenal arteries of left kidney":"Tętnice śródnerkowe nerki lewej","intrarenal arteries of right kidney":"Tętnice śródnerkowe nerki prawej",
 "intrarenal veins of left kidney":"Żyły śródnerkowe nerki lewej","intrarenal veins of right kidney":"Żyły śródnerkowe nerki prawej",
 "muscular branches of deep fibular nerve":"Gałęzie mięśniowe nerwu strzałkowego głębokiego",
 "calcaneal branches of fibular artery":"Gałęzie piętowe tętnicy strzałkowej",
 "septal branches of anterior interventricular artery":"Gałęzie przegrodowe gałęzi międzykomorowej przedniej",
 "ascending branch of left colic artery":"Gałąź wstępująca tętnicy okrężniczej lewej",
 "descending branch of left colic artery":"Gałąź zstępująca tętnicy okrężniczej lewej",
 "anterior root of posterior femoral cutaneous nerve":"Korzeń przedni nerwu skórnego tylnego uda",
 "posterior root of posterior femoral cutaneous nerve":"Korzeń tylny nerwu skórnego tylnego uda",
 "anterior rami of lumbar nerves":"Gałęzie brzuszne nerwów lędźwiowych","posterior rami of lumbar nerves":"Gałęzie grzbietowe nerwów lędźwiowych",
 "lumbar nerves":"Nerwy lędźwiowe","cervical nerves":"Nerwy szyjne","roots of nerves":"Korzenie nerwów",
 "branches of lateral cord of brachial plexus":"Gałęzie pęczka bocznego splotu ramiennego",
 "branches of medial cord of brachial plexus":"Gałęzie pęczka przyśrodkowego splotu ramiennego",
 "branches of posterior cord of brachial plexus":"Gałęzie pęczka tylnego splotu ramiennego",
 "branches of anterior part of lumbar plexus":"Gałęzie części przedniej splotu lędźwiowego",
 "branches of posterior part of lumbar plexus":"Gałęzie części tylnej splotu lędźwiowego",
 # connective
 "subcutaneous acromial bursa":"Kaletka barkowa podskórna","subacromial bursa":"Kaletka podbarkowa",
 "subcutaneous bursa of tuberosity of tibia":"Kaletka podskórna guzowatości piszczeli",
 "subfacial prepatellar bursa":"Kaletka przedrzepkowa podpowięziowa","superficial layer of temporal fascia":"Blaszka powierzchowna powięzi skroniowej",
 "superficial investing cervical fascia":"Blaszka powierzchowna powięzi szyi","intertubercular tendon sheath":"Pochewka ścięgna międzyguzkowa",
 "synovial sheaths of digits of hand":"Pochewki maziowe palców ręki","intermuscular gluteal bursae":"Kaletki międzymięśniowe pośladkowe",
 "tendon sheath of extensor digitorum and extensor indicis":"Pochewka ścięgien prostownika palców i prostownika wskaziciela",
 "tendon sheath of extensors carpi radialis":"Pochewka ścięgien prostowników promieniowych nadgarstka",
 "tendon sheath of flexor carpi radialis":"Pochewka ścięgna zginacza promieniowego nadgarstka",
 # collective / systems
 "central nervous system":"Ośrodkowy układ nerwowy","peripheral nervous system":"Obwodowy układ nerwowy",
 "autonomic division of peripheral nervous system":"Część autonomiczna obwodowego układu nerwowego",
 "autonomic nervous system":"Autonomiczny układ nerwowy","facial bones":"Kości twarzoczaszki",
 "extracranial bones of head":"Kości głowy poza czaszką","salivary glands":"Gruczoły ślinowe",
 "endocrine glands":"Gruczoły dokrewne","digestive canal":"Przewód pokarmowy","tracheobronchial tree":"Drzewo tchawiczo-oskrzelowe",
 "mouth":"Jama ustna","nose":"Nos","fauces":"Cieśń gardzieli","pharyngeal lymphoid ring":"Pierścień chłonny gardła",
 "primary lymphoid organs":"Pierwotne narządy limfatyczne","secondary lymphoid organs":"Wtórne narządy limfatyczne",
 "abdominal lymph nodes":"Węzły chłonne brzucha","facial nodes":"Węzły chłonne twarzowe",
 "infrahyoid nodes":"Węzły chłonne podgnykowe","gluteal nodes":"Węzły chłonne pośladkowe",
 "extrahepatic bile ducts":"Zewnątrzwątrobowe drogi żółciowe","genital systems":"Układy płciowe",
 "male genital system":"Męski układ płciowy","female genital system":"Żeński układ płciowy",
 "abdominopelvic cavity":"Jama brzuszno-miedniczna","peritoneal structures":"Struktury otrzewnowe",
 "visceral fasciae of abdominopelvic cavity":"Powięzie trzewne jamy brzuszno-miednicznej",
 "cartilages of ear":"Chrząstki ucha","interlobar sulci ":"Bruzdy międzypłatowe",
 "skeleton of free lower limb":"Szkielet wolnej kończyny dolnej","skeleton of free upper limb":"Szkielet wolnej kończyny górnej",
 "skeleton of lower limbs":"Szkielet kończyn dolnych","skeleton of upper limbs":"Szkielet kończyn górnych",
 "iliac crest ":"Grzebień biodrowy",
 "groove for popliteus muscle":"Bruzda mięśnia podkolanowego",
 "groove for tendon of flexor hallucis longus of talus":"Bruzda ścięgna zginacza długiego palucha (kość skokowa)",
 "groove for tendon of flexor hallucis longus of calcaneus":"Bruzda ścięgna zginacza długiego palucha (kość piętowa)",
 "groove for tendon of fibularis longus muscle of cuboid bone":"Bruzda ścięgna mięśnia strzałkowego długiego (kość sześcienna)",
 "groove for tendon of fibularis longus muscle":"Bruzda ścięgna mięśnia strzałkowego długiego",
 "sulcus for auditory tube":"Bruzda trąbki słuchowej","groove for vertebral artery":"Bruzda tętnicy kręgowej",
 "canal for vertebral artery":"Kanał tętnicy kręgowej","posterior obturator tubercle":"Guzek zasłonowy tylny",
 "anterior obturator tubercle":"Guzek zasłonowy przedni","pancreatic impression of spleen":"Wycisk trzustkowy śledziony",
 "gastric impression of spleen":"Wycisk żołądkowy śledziony","renal impression of spleen":"Wycisk nerkowy śledziony",
 "colic impression of spleen":"Wycisk okrężniczy śledziony","diaphragmatic surface of spleen":"Powierzchnia przeponowa śledziony",
 "anterior extremity of spleen":"Koniec przedni śledziony","posterior extremity of spleen":"Koniec tylny śledziony",
 "superior border of spleen":"Brzeg górny śledziony","inferior border of spleen":"Brzeg dolny śledziony",
 "grooves for extensor tendons":"Bruzdy ścięgien prostowników","supra-acetabular groove":"Bruzda nadpanewkowa",
 "sublime tubercle":"Guzek wyniosły","dorsal radial tubercle":"Guzek grzbietowy kości promieniowej",
 "lat_fis-ant-horizont":"Gałąź pozioma przednia bruzdy bocznej","lat_fis-ant-vertical":"Gałąź wstępująca przednia bruzdy bocznej",
 "lat_fis-post":"Gałąź tylna bruzdy bocznej","sulcus interm_prim-jensen":"Bruzda pośrednia pierwsza (Jensena)",
 "cingulate gyrus and sulcus":"Zakręt i bruzda obręczy","paracentral gyrus and sulcus":"Zakręt i bruzda okołośrodkowa",
 "inferior occipital gyrus and sulcus":"Zakręt i bruzda potyliczna dolna","superior occipital gyri":"Zakręty potyliczne górne",
 "transverse frontopolar gyrus and sulcus":"Zakręt i bruzda czołowo-biegunowa poprzeczna",
 "cingulate gyrus and sulcus (middle anterior part)":"Zakręt i bruzda obręczy (część środkowa przednia)",
 "cingulate gyrus and sulcus (middle posterior part)":"Zakręt i bruzda obręczy (część środkowa tylna)",
 "cingulate gyrus and sulcus (posterior dorsal part)":"Zakręt i bruzda obręczy (część tylna grzbietowa)",
 "levatores longi costarum":"Mięśnie dźwigacze żeber długie","levatores breves costarum":"Mięśnie dźwigacze żeber krótkie",
 "rectus lateralis capitis muscle":"Mięsień prosty boczny głowy","rectus anterior capitis muscle":"Mięsień prosty przedni głowy",
 "dorsal parts of lateral intertransversarii lumborum muscles":"Części grzbietowe mięśni międzypoprzecznych bocznych lędźwi",
 "ventral parts of lateral intertransversarii lumborum muscles":"Części brzuszne mięśni międzypoprzecznych bocznych lędźwi",
 "iliopectineal bursa":"Kaletka biodrowo-łonowa","adductor minimus":"Mięsień przywodziciel najmniejszy",
 "bucinator node":"Węzeł chłonny policzkowy","buccinator node":"Węzeł chłonny policzkowy",
 "common flexor tendon":"Ścięgno wspólne zginaczy","common extensor tendon":"Ścięgno wspólne prostowników",
 "articularis genus muscle":"Mięsień stawowy kolana","articularis genus":"Mięsień stawowy kolana",
 "trochanteric insertion":"Przyczep krętarzowy","ganglia":"Zwoje","ganglion":"Zwój",
 "intervertebral surface":"Powierzchnia międzykręgowa","genion":"Kolec bródkowy (genion)",
 "deep branch of transverse cervical artery":"Gałąź głęboka tętnicy poprzecznej szyi",
 "superficial branch of transverse cervical artery":"Gałąź powierzchowna tętnicy poprzecznej szyi",
 "tendon sheath - abd. pollicis longus - ext. pollicis brevis":"Pochewka ścięgien odwodziciela długiego i prostownika krótkiego kciuka",
 "intermediate deep inguinal node":"Węzeł chłonny pachwinowy głęboki pośredni",
 "proximal deep inguinal node":"Węzeł chłonny pachwinowy głęboki bliższy",
 "anterior tibial node":"Węzeł chłonny piszczelowy przedni","posterior tibial node":"Węzeł chłonny piszczelowy tylny",
 "fibular node":"Węzeł chłonny strzałkowy","parietal abdominal lymph nodes":"Węzły chłonne ścienne brzucha",
 "visceral abdominal lymph nodes":"Węzły chłonne trzewne brzucha","parietal pelvic lymph nodes":"Węzły chłonne ścienne miednicy",
 "visceral pelvic lymph nodes":"Węzły chłonne trzewne miednicy","parietal thoracic lymph nodes":"Węzły chłonne ścienne klatki piersiowej",
}

_JOINT_PL = {
 "acromioclavicular":"barkowo-obojczykowego","sternoclavicular":"mostkowo-obojczykowego",
 "glenohumeral":"ramiennego","shoulder":"ramiennego","elbow":"łokciowego","radiocarpal":"promieniowo-nadgarstkowego",
 "wrist":"promieniowo-nadgarstkowego","hip":"biodrowego","knee":"kolanowego","ankle":"skokowo-goleniowego",
 "talocrural":"skokowo-goleniowego","atlanto-occipital":"szczytowo-potylicznego","atlanto-axial":"szczytowo-obrotowego",
 "temporomandibular":"skroniowo-żuchwowego","sacro-iliac":"krzyżowo-biodrowego","sacroiliac":"krzyżowo-biodrowego",
 "interphalangeal joint of great toe":"międzypaliczkowego palucha","interphalangeal":"międzypaliczkowego",
 "distal interphalangeal":"międzypaliczkowych dalszych","proximal interphalangeal":"międzypaliczkowych bliższych",
 "metacarpophalangeal":"śródręczno-paliczkowego","metatarsophalangeal":"śródstopno-paliczkowego",
 "subtalar":"skokowo-piętowego","talocalcaneonavicular":"skokowo-piętowo-łódkowego",
 "proximal tibiofibular":"piszczelowo-strzałkowego bliższego","superior tibiofibular":"piszczelowo-strzałkowego bliższego",
 "distal tibiofibular":"piszczelowo-strzałkowego dalszego","inferior tibiofibular":"piszczelowo-strzałkowego dalszego",
 "tibiofibular":"piszczelowo-strzałkowego",
 "distal radio-ulnar":"promieniowo-łokciowego dalszego","proximal radio-ulnar":"promieniowo-łokciowego bliższego",
 "radio-ulnar":"promieniowo-łokciowego","radioulnar":"promieniowo-łokciowego",
 "costovertebral":"żebrowo-kręgowego","costotransverse":"żebrowo-poprzecznego","sternocostal":"mostkowo-żebrowego",
 "carpometacarpal":"nadgarstkowo-śródręcznych","intercarpal":"międzynadgarstkowych","intermetatarsal":"międzyśródstopnych",
}
def _jkey(name):
    return _JOINT_PL.get(name) or _JOINT_PL.get(name.replace(" joint", "").strip())

# więzadła śród- i międzynadgarstkowe / promieniowo-łokciowe dalsze
# (Terminologia Anatomica: nazwy złożone od polskich nazw kości nadgarstka)
_CARPAL_LIG = {
 "capitohamate interosseous":"międzykostne główkowato-haczykowate",
 "palmar capitohamate":"dłoniowe główkowato-haczykowate",
 "dorsal capitohamate":"grzbietowe główkowato-haczykowate",
 "lunotriquetral interosseous":"międzykostne księżycowato-trójgraniaste",
 "palmar lunotriquetral":"dłoniowe księżycowato-trójgraniaste",
 "dorsal lunotriquetral":"grzbietowe księżycowato-trójgraniaste",
 "scapholunate interosseous":"międzykostne łódeczkowato-księżycowate",
 "trapeziotrapezoidal interosseous":"międzykostne czworoboczno-czworoboczne",
 "trapezoideocapitate interosseous":"międzykostne czworoboczno-główkowate",
 "palmar trapezoideocapitate":"dłoniowe czworoboczno-główkowate",
 "dorsal scaphotriquetral":"grzbietowe łódeczkowato-trójgraniaste",
 "palmar scaphotriquetral":"dłoniowe łódeczkowato-trójgraniaste",
 "radiocapitate":"promieniowo-główkowate (część więzadła promieniowo-nadgarstkowego dłoniowego)",
 "radioscaphocapitate":"promieniowo-łódeczkowato-główkowate",
 "long radiolunate":"promieniowo-księżycowate długie",
 "short radiolunate":"promieniowo-księżycowate krótkie",
 "scaphocapitate":"łódeczkowato-główkowate",
 "scaphotrapeziotrapezoidal":"łódeczkowato-czworoboczne",
 "triquetrocapitate":"trójgraniasto-główkowate",
 "triquetrohamate":"trójgraniasto-haczykowate",
 "ulnocapitate":"łokciowo-główkowate",
 "ulnolunate":"łokciowo-księżycowate",
 "ulnotriquetral":"łokciowo-trójgraniaste",
 "ulnopisiform":"łokciowo-grochowate",
 "pisotriquetral":"grochowato-trójgraniaste",
 "dorsal radio-ulnar":"grzbietowe promieniowo-łokciowe (stawu promieniowo-łokciowego dalszego)",
 "palmar radio-ulnar":"dłoniowe promieniowo-łokciowe (stawu promieniowo-łokciowego dalszego)",
}
def _joint(n):
    m = re.match(r'^intervertebral disc ([a-z]\d+)[- ]([a-z]?\d+)$', n, re.I)
    if m: return f"Krążek międzykręgowy {m.group(1).upper()}–{m.group(2).upper()}"
    if n == "intervertebral discs": return "Krążki międzykręgowe"
    m = re.match(r'^nucleus pulposus ([a-z]\d+)[- ]([a-z]?\d+)$', n, re.I)
    if m: return f"Jądro miażdżyste {m.group(1).upper()}–{m.group(2).upper()}"
    if n == "nucleus pulposus": return "Jądro miażdżyste"
    m = re.match(r'^(.+?) ligaments?$', n)
    if m and m.group(1) in _CARPAL_LIG:
        return f"Więzadło {_CARPAL_LIG[m.group(1)]}"
    m = re.match(r'^(palmar|plantar|dorsal) (interphalangeal|metacarpophalangeal|metatarsophalangeal) ligaments?$', n)
    if m:
        surf = {"palmar":"dłoniowe","plantar":"podeszwowe","dorsal":"grzbietowe"}[m.group(1)]
        jt = {"interphalangeal":"międzypaliczkowych","metacarpophalangeal":"śródręczno-paliczkowych",
              "metatarsophalangeal":"śródstopno-paliczkowych"}[m.group(2)]
        head = "Więzadło" if n.endswith("ligament") else "Więzadła"
        return f"{head} {surf} stawów {jt}"
    m = re.match(r'^articular disc of (.+?) joint$', n)
    if m:
        k = _jkey(m.group(1)); return f"Krążek stawowy stawu {k or m.group(1)}"
    m = re.match(r'^articular capsules? of (.+?) joints?(?: of (.+))?$', n)
    if m:
        k = _jkey(m.group(1)) or m.group(1)
        head = "Torebka stawowa stawu" if "capsule " in n else "Torebki stawowe stawów"
        loc = "" if not m.group(2) else " " + (GEN_OF.get(m.group(2)) or m.group(2))
        return f"{head} {k}{loc}".strip()
    m = re.match(r'^collateral (.+?) ligaments?(?: of (hand|foot))?$', n)
    if m:
        jt = {"interphalangeal":"międzypaliczkowych","metacarpophalangeal":"śródręczno-paliczkowych",
              "metatarsophalangeal":"śródstopno-paliczkowych"}.get(m.group(1))
        loc = {"hand":" ręki","foot":" stopy"}.get(m.group(2) or "", "")
        if jt:
            head = "Więzadło poboczne" if n.rstrip().endswith("ligament") else "Więzadła poboczne"
            return f"{head} stawów {jt}{loc}"
        k = _jkey(m.group(1)) or m.group(1)
        head = "Więzadło poboczne" if n.rstrip().endswith("ligament") else "Więzadła poboczne"
        return f"{head} stawów {k}{loc}" if "Więzadła" in head else f"{head} stawu {k}{loc}"
    m = re.match(r'^(.+?) (meniscus|labrum)$', n)
    if m:
        head = "Łąkotka" if m.group(2) == "meniscus" else "Obrąbek"
        loc = {"medial":"przyśrodkowa","lateral":"boczna","acetabular":"panewki","glenoid":"stawowy (panewki łopatki)"}.get(m.group(1), m.group(1))
        return f"{head} {loc}".strip()
    m = re.match(r'^(.+) ligament(?: of (.+))?$', n)
    if m:
        lig = m.group(1).replace("-", "-")
        LIGPL = {
          "anterior longitudinal":"podłużne przednie","posterior longitudinal":"podłużne tylne",
          "anterior cruciate":"krzyżowe przednie","posterior cruciate":"krzyżowe tylne",
          "medial collateral":"poboczne piszczelowe","lateral collateral":"poboczne strzałkowe",
          "tibial collateral":"poboczne piszczelowe","fibular collateral":"poboczne strzałkowe",
          "radial collateral":"poboczne promieniowe","ulnar collateral":"poboczne łokciowe",
          "annular":"pierścieniowate","acromioclavicular":"barkowo-obojczykowe","coracoclavicular":"kruczo-obojczykowe",
          "coracoacromial":"kruczo-barkowe","coracohumeral":"kruczo-ramienne","transverse humeral":"poprzeczne ramienia",
          "anterior sternoclavicular":"mostkowo-obojczykowe przednie","posterior sternoclavicular":"mostkowo-obojczykowe tylne",
          "costoclavicular":"żebrowo-obojczykowe","interclavicular":"międzyobojczykowe",
          "anterior talofibular":"skokowo-strzałkowe przednie","posterior talofibular":"skokowo-strzałkowe tylne",
          "calcaneofibular":"piętowo-strzałkowe","anterior tibiofibular":"piszczelowo-strzałkowe przednie",
          "posterior tibiofibular":"piszczelowo-strzałkowe tylne","deltoid":"trójgraniaste (przyśrodkowe)",
          "anterior talocalcaneal":"skokowo-piętowe przednie","interosseous talocalcaneal":"skokowo-piętowe międzykostne",
          "long plantar":"podeszwowe długie","plantar calcaneonavicular":"piętowo-łódkowe podeszwowe",
          "bifurcate":"widełkowate","iliofemoral":"biodrowo-udowe","pubofemoral":"łonowo-udowe",
          "ischiofemoral":"kulszowo-udowe","anterior sacro-iliac":"krzyżowo-biodrowe przednie",
          "posterior sacro-iliac":"krzyżowo-biodrowe tylne","interosseous sacro-iliac":"krzyżowo-biodrowe międzykostne",
          "sacrotuberous":"krzyżowo-guzowe","sacrospinous":"krzyżowo-kolcowe","iliolumbar":"biodrowo-lędźwiowe",
          "supraspinous":"nadkolcowe","interspinous":"międzykolcowe","ligamentum flavum":"żółte","flaval":"żółte",
          "nuchal":"karkowe","patellar":"rzepki","arcuate popliteal":"podkolanowe łukowate",
          "oblique popliteal":"podkolanowe skośne","transverse":"poprzeczne","quadrate":"czworoboczne",
          "anterior ligament of fibular head":"przednie głowy strzałki",
        }
        base = LIGPL.get(lig.lower())
        if base:
            tail = ""
            if m.group(2):
                gm = GEN_OF.get(m.group(2)) or {"radius":"kości promieniowej","uterus":"macicy",
                     "head of femur":"głowy kości udowej","fibular head":"głowy strzałki"}.get(m.group(2))
                if gm: tail = " " + gm
            return f"Więzadło {base}{tail}".strip()
    return None

_ORD = {"first":"I","second":"II","third":"III","fourth":"IV","fifth":"V","sixth":"VI",
        "seventh":"VII","eighth":"VIII","ninth":"IX","tenth":"X","eleventh":"XI","twelfth":"XII"}
_CARPAL = {"scaphoid bone":"Kość łódeczkowata","lunate bone":"Kość księżycowata",
  "triquetrum bone":"Kość trójgraniasta","triquetral bone":"Kość trójgraniasta","pisiform bone":"Kość grochowata",
  "trapezium bone":"Kość czworoboczna większa","trapezoid bone":"Kość czworoboczna mniejsza",
  "capitate bone":"Kość główkowata","hamate bone":"Kość haczykowata","navicular bone":"Kość łódkowata",
  "cuboid bone":"Kość sześcienna","medial cuneiform bone":"Kość klinowata przyśrodkowa",
  "intermediate cuneiform bone":"Kość klinowata pośrednia","lateral cuneiform bone":"Kość klinowata boczna",
  "inferior nasal concha bone":"Małżowina nosowa dolna","talus":"Kość skokowa","calcaneus":"Kość piętowa"}
_TOOTHPL = {"incisor":"Siekacz","canine":"Kieł","premolar":"Ząb przedtrzonowy","molar":"Ząb trzonowy"}
def _skel(n):
    if n in _CARPAL: return _CARPAL[n]
    m = re.match(r'^(proximal|middle|distal) phalanx of (first|second|third|fourth|fifth) finger of (hand|foot)$', n)
    if m:
        pos={"proximal":"bliższy","middle":"środkowy","distal":"dalszy"}[m.group(1)]
        loc={"hand":"ręki","foot":"stopy"}[m.group(3)]
        return f"Paliczek {pos} {_ORD[m.group(2)]} palca {loc}"
    m = re.match(r'^(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth) (rib|metacarpal bone|metatarsal bone)$', n)
    if m:
        base={"rib":"Żebro","metacarpal bone":"Kość śródręcza","metatarsal bone":"Kość śródstopia"}[m.group(2)]
        return f"{base} {_ORD[m.group(1)]}"
    m = re.match(r'^costal cartilage of (first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth) rib$', n)
    if m: return f"Chrząstka żebrowa żebra {_ORD[m.group(1)]}"
    m = re.match(r'^(anterior|middle|posterior) cells of ethmoid bone$', n)
    if m: return "Komórki sitowe " + {"anterior":"przednie","middle":"środkowe","posterior":"tylne"}[m.group(1)]
    m = re.match(r'^(upper|lower) (?:(first|second|third) )?(medial |lateral )?(incisor|canine|premolar|molar)(?: tooth)?$', n)
    if m:
        jaw = "górny" if m.group(1)=="upper" else "dolny"
        base=_TOOTHPL[m.group(4)]
        if m.group(4) in ("incisor","canine"):
            adj = jaw if not m.group(3) else ("przyśrodkowy " if "medial" in m.group(3) else "boczny ")+jaw
            return f"{base} {adj}".strip()
        num={"first":"pierwszy ","second":"drugi ","third":"trzeci ",None:""}[m.group(2)]
        return f"{base} {num}{jaw}".strip()
    m = re.match(r'^vertebra ([ctl])(\d+)$', n)
    if m:
        reg={"c":"szyjny","t":"piersiowy","l":"lędźwiowy"}[m.group(1)]
        rom={1:"I",2:"II",3:"III",4:"IV",5:"V",6:"VI",7:"VII",8:"VIII",9:"IX",10:"X",11:"XI",12:"XII"}[int(m.group(2))]
        return f"Krąg {reg} {rom}"
    return None

def _extra_comp(n):
    r = _skel(n)
    if r: return r
    r = _joint(n)
    if r: return r
    # "Groove for <muscle> muscle"  /  "Groove for tendon of <muscle> (of <bone>)"
    m = re.match(r'^groove for (?:tendon of )?(.+?)(?: muscle)?(?: of (.+))?$', n)
    if m:
        mu = m.group(1)
        gen = _MUSC_GEN_FULL.get(mu) or MUSCLE_GEN.get(mu + " muscle") or MUSCLE_GEN.get(mu)
        if not gen and (mu + " muscle") in EN2PL:
            gen = "mięśnia " + EN2PL[mu + " muscle"].lower().replace("mięsień ", "")
        if gen:
            of = ""
            if m.group(2):
                g2 = GEN_OF.get(m.group(2))
                if g2: of = " " + g2
            base = "Bruzda ścięgna" if "tendon" in n else "Bruzda"
            return f"{base} {gen}{of}".strip()
    # "Articular facet for <X>"
    m = re.match(r'^articular facet for (.+)$', n)
    if m:
        t = EN2PL.get(m.group(1)) or _NORM2PL.get(_norm(m.group(1)))
        if t: return f"Powierzchnia stawowa dla {t[0].lower()+t[1:]}"
    # "<dir> condyle/epicondyle of <bone>"  (generic, gendered)
    m = re.match(r'^(anterior|posterior|medial|lateral|superior|inferior) (condyle|epicondyle) of (.+)$', n)
    if m and m.group(3) in GEN_OF:
        head = "Kłykieć" if m.group(2) == "condyle" else "Nadkłykieć"
        return f"{head} {POS[m.group(1)][0]} {GEN_OF[m.group(3)]}"
    return None

_PART_ADJ = {"superior":"górna","inferior":"dolna","lateral":"boczna","medial":"przyśrodkowa",
             "anterior":"przednia","posterior":"tylna","middle":"środkowa","central":"środkowa",
             "dorsal":"grzbietowa","ventral":"brzuszna","rostral":"dziobowa","caudal":"ogonowa"}

@functools.lru_cache(maxsize=8192)
def translate(en):
    raw = en
    # Z-Anatomy dzieli część bruzd/zakrętów na "(... part)" - bez tego dwa różne
    # meshe dostają identyczną nazwę PL. Przetłumacz rdzeń i dopisz część
    # (chyba że pełna nazwa z częścią ma już własny wpis ręczny).
    mp = re.match(r'^(.*\S)\s*\(([a-z][a-z ]*?)\s*part\*?\)\*?$', en.strip(), re.I)
    if mp:
        _full = re.sub(r'\s+', ' ', en.strip().lower()).replace('*', '').strip()
        if _full in OVR2: return OVR2[_full], "ovr"
        if _full in OVR: return OVR[_full], "ovr"
        if True:
            core_pl, how = translate(mp.group(1).strip())
            if how != "none":
                words = [w for w in mp.group(2).lower().split() if w in _PART_ADJ]
                czesc = " ".join(_PART_ADJ[w] for w in words) or mp.group(2).strip().lower()
                return f"{core_pl} (część {czesc})", how
    en = _clean(en)
    n = _norm(en)
    if not n:
        return raw, "none"
    # 0 manual + special tables
    for tbl in (OVR, VERMIS):
        if n in tbl: return tbl[n], "ovr"
        if en.lower() in tbl: return tbl[en.lower()], "ovr"
    # 1 exact
    if en.lower() in EN2PL: return EN2PL[en.lower()], "exact"
    if n in _NORM2PL: return _NORM2PL[n], "norm"
    # 2 synonyms
    for pat, repl in SYN:
        alt = re.sub(pat, repl, n)
        if alt != n and alt in _NORM2PL:
            return _NORM2PL[alt], "syn"
    # 2b domain composers. rawish = parens & roman tags kept (bronchus/liver need them);
    #                       lc     = trailing (...) dropped (lymph etc. want it gone).
    rawish = re.sub(r'\s+', ' ', raw.lower().replace("'", "")).strip()
    if rawish.startswith("(") and rawish.endswith(")") and rawish.count("(") == 1:
        rawish = rawish[1:-1].strip()
    lc = (re.sub(r'\s*\([^()]*\)\s*$', '', rawish) or rawish).strip().rstrip("*").strip()
    for tbl in (_FACIAL_OVR, OVR2):
        if n in tbl: return tbl[n], "ovr"
        if lc in tbl: return tbl[lc], "ovr"
    for fn in (_lymph, _bronchus, _lung_seg, _liver_seg, _muscle, _nerve_vessel, _extra_comp):
        r = fn(rawish) or fn(lc) or fn(n)
        if r: return r, "comp"
    # 3 "<feature> of <bone/struct>"  compositional
    m = re.match(r'^(.*?) of (.+)$', n)
    if m:
        left, tail = m.group(1).strip(), m.group(2).strip()
        toks = left.split()
        if toks and toks[-1] in HEAD:
            headpl, g = HEAD[toks[-1]]
            adjs = " ".join(_adj(t, g) for t in toks[:-1] if t in POS)
            gen = GEN_OF.get(tail) or MUSCLE_GEN.get(tail)
            if gen is None and tail in EN2PL:
                gen = EN2PL[tail].lower()
            if gen:
                return re.sub(r'\s+', ' ', f"{headpl} {adjs} {gen}").strip(), "comp"
        # bursa/sheath "of <muscle> muscle"
        if left.endswith("bursa") or "tendon sheath" in left or left.endswith("sheath"):
            base = "Kaletka" if "bursa" in left else "Pochewka ścięgna"
            mod = ""
            if "subtendinous" in left: mod = " podścięgnowa"
            elif "subcutaneous" in left: mod = " podskórna"
            gen = MUSCLE_GEN.get(tail) or (EN2PL.get(tail, "").lower())
            if gen:
                return f"{base}{mod} {gen}".strip(), "comp"
    # 4 tract / fasciculus
    if n.endswith("tract") or n.endswith("fasciculus") or n.endswith("fasciculus proprius"):
        parts = n.replace(" proprius", "").split()
        headpl = "Droga" if parts[-1] == "tract" else "Pęczek"
        gender = 1 if headpl == "Droga" else 0
        dirs = " ".join(_adj(p, gender) for p in parts if p in POS)
        core = " ".join(p for p in parts if p not in POS and p not in ("tract", "fasciculus"))
        CORE_PL = {"corticospinal":"korowo-rdzeniowa","spinothalamic":"rdzeniowo-wzgórzowa",
                   "spinocerebellar":"rdzeniowo-móżdżkowa","spinotectal":"rdzeniowo-pokrywowa",
                   "reticulospinal":"siatkowo-rdzeniowa","vestibulospinal":"przedsionkowo-rdzeniowa",
                   "rubrospinal":"czerwienno-rdzeniowa","tectospinal":"pokrywowo-rdzeniowa",
                   "olivospinal":"oliwkowo-rdzeniowa"}
        cpl = CORE_PL.get(core, core)
        if headpl == "Pęczek" and not core:
            return f"Pęczek własny {dirs}".strip(), "comp"
        return re.sub(r'\s+', ' ', f"{headpl} {cpl} {dirs}").strip(), "comp"
    # 5 bare "<dir...> <head>"   e.g. "middle frontal gyrus", "anterior occipital sulcus"
    toks = n.split()
    if toks[-1] in HEAD and all(t in POS or t in ("frontal","occipital","temporal","parietal",
            "central","cingulate","orbital","insular","paracentral","precentral","postcentral",
            "marginal","calcarine","collateral","olfactory","parahippocampal","lingual",
            "occipitotemporal","frontopolar","frontomarginal") for t in toks[:-1]):
        headpl, g = HEAD[toks[-1]]
        # gendered region adjectives: (m, f, n)
        REG = {"frontal":("czołowy","czołowa","czołowe"),"occipital":("potyliczny","potyliczna","potyliczne"),
               "temporal":("skroniowy","skroniowa","skroniowe"),"parietal":("ciemieniowy","ciemieniowa","ciemieniowe"),
               "central":("środkowy","środkowa","środkowe"),"cingulate":("obręczy","obręczy","obręczy"),
               "orbital":("oczodołowy","oczodołowa","oczodołowe"),"insular":("wyspowy","wyspowa","wyspowe"),
               "paracentral":("okołośrodkowy","okołośrodkowa","okołośrodkowe"),
               "precentral":("przedśrodkowy","przedśrodkowa","przedśrodkowe"),
               "postcentral":("zaśrodkowy","zaśrodkowa","zaśrodkowe"),
               "marginal":("brzeżny","brzeżna","brzeżne"),"calcarine":("ostrogowy","ostrogowa","ostrogowe"),
               "collateral":("poboczny","poboczna","poboczne"),"olfactory":("węchowy","węchowa","węchowe"),
               "parahippocampal":("przyhipokampowy","przyhipokampowa","przyhipokampowe"),
               "lingual":("językowaty","językowata","językowate"),
               "occipitotemporal":("potyliczno-skroniowy","potyliczno-skroniowa","potyliczno-skroniowe"),
               "frontopolar":("czołowo-biegunowy","czołowo-biegunowa","czołowo-biegunowe"),
               "frontomarginal":("czołowo-brzeżny","czołowo-brzeżna","czołowo-brzeżne")}
        # region adjective first, then directional (Polish: "Bruzda potyliczna przednia")
        regs = [REG[t][g] for t in toks[:-1] if t in REG]
        dirs = [_adj(t, g) for t in toks[:-1] if t in POS]
        return re.sub(r'\s+',' ', f"{headpl} {' '.join(regs)} {' '.join(dirs)}").strip(), "comp"
    # 6 fuzzy
    c = difflib.get_close_matches(n, _NK, n=1, cutoff=0.9)
    if c:
        return _NORM2PL[c[0]], "fuzzy"
    return raw, "none"


# structures whose LEFT/RIGHT genuinely differ in course/relations (taught as such).
# Everything else: no (lewy)/(prawy) suffix.
SIDE_MATTERS = re.compile(
    r'recurrent laryngeal nerve|'
    r'\bvagus nerve\b|'
    r'subclavian artery|'
    r'(testicular|ovarian) vein|'
    r'superior intercostal vein|'
    r'ascending lumbar vein|'
    r'brachiocephalic (vein|artery)|'
    r'coronary artery',
    re.I)

def strip_side(pl):
    """Remove a trailing (lewy)/(prawy)/(L)/(P)/(left)/(right) marker from a PL name."""
    return re.sub(r'\s*\((lewy|lewa|lewe|prawy|prawa|prawe|[LP]|left|right)\)\s*$', '',
                  (pl or "").strip(), flags=re.I).strip()

def side_label(en, side):
    """Return ' (prawy)'/' (lewy)'-style suffix ONLY when side matters; else ''.
    Gender picked from the PL head noun is handled by caller passing pl."""
    if side == "mid" or not SIDE_MATTERS.search(en):
        return ""
    return " prawy" if side == "r" else " lewy"
