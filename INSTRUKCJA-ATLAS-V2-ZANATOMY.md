# Instrukcja: Atlas v2 oparty w całości na Z-Anatomy (bez BodyParts3D)

**Kontekst dla nowej rozmowy**: to jest samodzielna instrukcja, nie zakładaj że masz dostęp do historii sesji w której powstała. Wszystko co potrzebne jest tutaj albo w plikach, do których się odwołuje.

## Cel

Zbudować **drugą, niezależną wersję atlasu** (nie nadpisywać obecnego `atlas_pilot.html`), w której CAŁA geometria (kości, mięśnie, naczynia, nerwy, narządy, tkanka łączna, mózg) pochodzi z pełnego źródła Z-Anatomy — **nie** z BodyParts3D — i wykorzystuje **gotowe, natywne punkty-adnotacje** ("szpilki") wbudowane w ten model, zamiast liczyć/zgadywać pozycje.

**Powód**: sprawdziliśmy to na łopatce (patrz `_scratch_scapula_viz.html` / opublikowany artefakt z tamtej sesji, jeśli jeszcze istnieje) — model Z-Anatomy ma znacznie bogatszy, gotowy zestaw punktów orientacyjnych niż to co dotychczas ręcznie/algorytmicznie liczono dla BodyParts3D. User ocenił że różnica jakości jest na tyle duża, że lepiej zbudować od nowa na tym źródle niż dalej łatać stare.

## Co ZACHOWUJEMY z obecnego projektu

- **Cały silnik/UI** `atlas_pilot.html` — Three.js scena, kamera, warstwy (Kości/Mięśnie/Naczynia/...), wyszukiwarka, tryb kolokwium, panel notatek, tryb quizu, eksport do Anki, pomiar odległości, skalpel, "Pokaż ID na scenie" (świeżo dodany system rozpychania etykiet — działa dobrze, zostaje). Ten kod NIE jest specyficzny dla BodyParts3D — czyta dane z plików JSON + `.obj`, więc powinien dać się podłączyć pod nowy zestaw danych bez przepisywania od zera.
- `słownik_anatomiczny_umed_pl_en.json` — słownik PL/EN nazw anatomicznych (do tłumaczenia angielskich nazw mesh z Z-Anatomy na polskie).
- `notatki_wykladowe.json` — notatki z wykładów, pogrupowane tematycznie (nie zależą od geometrii, zostają bez zmian).
- `szpilki_map.json` / `szpilki_todo.json` — lista szpilek z kolokwiów, ALE: powiązania (`id`/`boneId`) trzeba będzie przemapować na nowe ID struktur (patrz niżej), bo stare ID (`FMA*`, `ZAC*` itd.) znikają.
- `WSKAZOWKI-TECHNICZNE-WSPOLNE.md` — ogólne gotchy Three.js/BVH/kamery nadal aktualne, ale sekcja 8 (metodologia szukania błędów pozycji) w dużej mierze **przestaje być potrzebna** — jeśli cała geometria pochodzi z jednego spójnego źródła, nie powinno być tego patchworku błędów co przy imporcie częściowym.

## Co WYWALAMY / nie przenosimy

- **Całą zależność od BodyParts3D** (`FMA*` id, pliki `.obj` spod `all_*_labeled.json` obecnego projektu) — nowe id będą z Z-Anatomy.
- **`bone_landmarks.json`** w obecnej postaci — większość pozycji tam to albo auto-wygenerowane znaczniki (środek/koniec/przyczep, policzone z geometrii BodyParts3D) albo ręcznie/algorytmicznie dopasowane punkty. Nowe landmarki mają pochodzić z natywnych adnotacji Z-Anatomy, nie z przeliczania.
- **`MESH_POSITION_CORRECTIONS` / `MESH_SCALE_CORRECTIONS` / `MESH_AFFINE_CORRECTIONS` / `MESH_SHEAR_CORRECTIONS`** w `atlas_pilot.html` (~90 wpisów naprawiających błędy importu BodyParts3D+częściowy Z-Anatomy) — to są łatki na starą, patchworkową geometrię. Nowa, spójna geometria z jednego źródła nie powinna ich potrzebować (do zweryfikowania empirycznie, ale nie kopiować na start).
- Moje własne, ręcznie/geometrycznie wyliczone punkty dodane w poprzedniej sesji (np. "Wzgórek kości krzyżowej", "Trzon mostka" — dodane tam gdzie w BodyParts3D był realny brak) — w Z-Anatomy prawdopodobnie te struktury **już istnieją jako gotowe bryły z adnotacjami**, więc nie trzeba ich dorabiać ręcznie.

## Źródła do pobrania

1. **`github.com/LluisV/Z-Anatomy-Sample`** (już częściowo eksplorowane) — repo Unity, CC BY-SA, folder `Assets/Models/1.0 Models/`:
   - `SkeletalSystem100.fbx` (41 MB) — **już pobrany i skonwertowany** w poprzedniej sesji, patrz `SkeletalSystem100.glb` w scratchpadzie (ale scratchpad jest per-sesja, może trzeba pobrać ponownie).
   - `MuscularSystem100.fbx` (37 MB)
   - `CardioVascular41.fbx` (65 MB) — serce rozłożone + całe naczynia
   - `NervousSystem100.fbx` (54 MB)
   - `VisceralSystem100.fbx` (18 MB, **312 brył**)
   - `LymphoidOrgans100.fbx` (2 MB)
   - `Joints100.fbx` (10 MB)
   - `Regions of human body100.fbx` (4 MB)
   - `Reference lines, planes and movements 1.fbx` (0.4 MB)
   - URL wzorzec: `raw.githubusercontent.com/LluisV/Z-Anatomy-Sample/main/Assets/Models/1.0%20Models/<NAZWA>.fbx`
2. **WAŻNE — sprawdzić kompletność**: powyższe to tylko **PRÓBKA** ("Sample"). Wiadomo już, że w naszych obecnych danych BRAKUJE m.in. **całego żeńskiego układu rozrodczego** (macica, jajniki, jajowody, pochwa) i kilku struktur języka — trzeba sprawdzić, czy `VisceralSystem100.fbx` z próbki je zawiera. Jeśli nie: pełniejsza wersja podobno jest w `Z-Anatomy/The-blend` → `Z-Anatomy.zip`, ale to plik `.blend` (Blender), **którego nie mamy zainstalowanego** — do rozpoznania osobno, może dać się otworzyć/skonwertować inaczej (np. przez `bpy` jako moduł Pythona bez pełnego Blendera, do sprawdzenia).
3. Zanim zaczniesz masowo pobierać — **zapytaj usera o zgodę na każdy plik** (rozmiar + źródło), zgodnie z zasadami sesji (pobieranie plików wymaga jawnej zgody w czacie).

## Pipeline konwersji (sprawdzony w praktyce na łopatce)

1. **Pobierz FBX** (`curl -L -o plik.fbx "<url>"`).
2. **Konwertuj do GLB**: `npm i fbx2gltf` (paczka npm zawiera binarkę), potem:
   ```
   FBX2glTF.exe -i wejście.fbx -o wyjście --binary
   ```
   **Uwaga**: żadnych dodatkowych flag (np. `--keep-attribute`) — psują konwersję. Binarka ląduje pod `node_modules/fbx2gltf/bin/Windows_NT/FBX2glTF.exe` — **ale w tej sesji `npm install` wylądował w nieoczekiwanym katalogu** (najwyraźniej working directory Bash-a w tym środowisku bywa niestabilny między wywołaniami) — po instalacji ZAWSZE zweryfikuj `find` gdzie faktycznie jest binarka, nie zakładaj ścieżki.
3. **Wczytaj przez `trimesh`** (Python, już zainstalowany — `pip show trimesh` żeby potwierdzić):
   ```python
   import trimesh
   scene = trimesh.load('plik.glb')
   names = list(scene.geometry.keys())  # wszystkie nazwane obiekty
   ```
4. **KRYTYCZNE — zastosuj transform grafu sceny**, inaczej skala/pozycja będą losowo błędne (przykład z poprzedniej sesji: wątroba wyszła ~1000× za mała):
   ```python
   def get_world_mesh(name):
       for node in scene.graph.nodes_geometry:
           tf, geom_name = scene.graph[node]
           if geom_name == name:
               m = scene.geometry[geom_name].copy()
               m.apply_transform(tf)
               return m
   ```
5. **Skala**: Z-Anatomy jest w METRACH, atlas (i cały istniejący kod) oczekuje MILIMETRÓW → mnóż współrzędne ×1000.
6. **GLB z trimesh nie ma wektorów normalnych** → w Three.js renderuje się jako czarna sylwetka. Przy wczytywaniu w przeglądarce: `geometry.deleteAttribute('normal'); geometry.computeVertexNormals();` (albo `flatShading: true`).

## Rozpoznanie konwencji nazewnictwa — DO ZROBIENIA NA START, nie zakładaj z góry

W `SkeletalSystem100.fbx` znaleziono (dla łopatki) nazwy typu:
- `Scapula.r`, `Scapula.r_1` — całe bryły kości (różne warianty/części?)
- `Scapular notch.j`, `Scapular notch.i` — dwa warianty tej samej nazwanej adnotacji
- Dla mięśni widziano też sufiksy `.or`, `.ol`, `.o1r`, `.o1l`, `.o2r`, `.o2l`, `.er`, `.el` (prawdopodobnie origin/insertion × prawa/lewa, ale **niepotwierdzone**)

**Hipoteza z poprzedniej sesji** (częściowo zweryfikowana, ale NIE w 100%): `.i`/`.j` = lewa/prawa strona (ustalone przez to że mają przeciwny znak X i identyczne pozostałe współrzędne — sprawdzone na kilku parach dla łopatki, pasowało). Zanim zbudujesz na tym cały pipeline: **zweryfikuj to na kilku strukturach z WYRAŹNĄ asymetrią ciała** (np. serce, wątroba — jeśli są w tym samym pliku/repo) żeby mieć pewność co do znaczenia `.i` vs `.j`, zamiast zakładać.

Zrób pełny spis WSZYSTKICH unikalnych sufiksów w każdym pliku FBX (`grep -oE '\.[a-z0-9_]+$' names.txt | sort | uniq -c`) i rozszyfruj każdy zanim zaczniesz masowo eksportować — inaczej ryzykujesz pomieszanie stron ciała albo typów adnotacji na dużą skalę.

## Układ współrzędnych — TU JEST DOBRA WIADOMOŚĆ

W poprzedniej sesji dopasowanie Z-Anatomy → nasz atlas wymagało dopasowania metodą najmniejszych kwadratów (bo łączyliśmy DWA różne źródła: BodyParts3D + Z-Anatomy) i miało błąd średnio ~22mm na kości ~160mm.

**Przy budowie v2 CAŁA geometria pochodzi z Z-Anatomy** — więc to konkretne źródło problemu znika. Wszystkie pliki FBX z tego samego repo Z-Anatomy-Sample powinny (do zweryfikowania!) dzielić JEDEN spójny, wewnętrznie zgodny układ współrzędnych (to ten sam model człowieka rozłożony na kilka plików wg układów). Czyli zamiast dopasowywać kość-po-kości metodą najmniejszych kwadratów, powinno wystarczyć:

1. Ustalić JEDNO globalne przekształcenie osi (obrót Y-up → nasz Z-up, skala ×1000, ewentualnie przesunięcie początku układu) — **raz, dla całego modelu**, nie osobno per struktura.
2. Zweryfikować to przekształcenie na kilku niezależnych, oczywistych faktach anatomicznych rozsianych po całym ciele (nie tylko jednej kości!) — np.:
   - Szczyt czaszki wyżej niż stopy (oś góra-dół).
   - Kość krzyżowa niżej niż kręgi szyjne.
   - Symetria lewo-prawo (jeśli `.i`/`.j` to faktycznie strony — środki masy powinny być lustrzane względem linii pośrodkowej).
   - Jeśli sięgniesz po `CardioVascular41.fbx`: koniuszek serca powinien wskazywać w lewo (znany fakt anatomiczny, łatwy do sprawdzenia).
3. Dopiero po potwierdzeniu tego JEDNEGO globalnego przekształcenia na kilku niezależnych punktach — zastosuj je do WSZYSTKICH wyeksportowanych brył i punktów naraz.

Jeśli mimo wszystko okaże się, że różne pliki FBX (Skeletal vs Muscular vs CardioVascular...) NIE dzielą wspólnego układu (np. każdy eksportowany osobno z Blendera z inną pozą referencyjną) — wtedy trzeba wrócić do metody per-plik (dopasowanie kilku punktów wspólnych między plikami, tą samą metodą najmniejszych kwadratów co przy łopatce, kod niżej).

### Gotowy kod dopasowania (gdyby jednak był potrzebny per-plik)

```python
import numpy as np
# pairs: lista (punkt_w_zanatomy_xyz, punkt_docelowy_xyz), min. 4-6 dobrze rozstawionych par
Z = np.array([p[0] for p in pairs])
O = np.array([p[1] for p in pairs])
Z_aug = np.hstack([Z, np.ones((len(Z),1))])
A, *_ = np.linalg.lstsq(Z_aug, O, rcond=None)  # A: (4,3), transform afiniczny
# zastosowanie: world_new = np.array([x,y,z,1]) @ A
```

## Struktura danych docelowych (żeby pasowało pod istniejący silnik JS)

Istniejący `atlas_pilot.html` oczekuje per-warstwę pliku `all_<kind>_labeled.json` (lista `{id, pl, en}`) + jednego pliku `.obj` per obiekt, plus `bone_landmarks.json` (lista `{boneId, pl, en, pos: [x,y,z], approx?}`, `pos` w układzie LOKALNYM względem `group` — sprawdź w kodzie funkcję `init()` jak `group.position` jest liczone, żeby zachować tę samą konwencję). Rekomendacja: nazwij nowe pliki z sufiksem, np. `all_bones_labeled_v2.json`, `bone_landmarks_v2.json`, żeby NIE nadpisać istniejących (druga równoległa sesja z nich korzysta).

**Nazwy PL**: mesh z Z-Anatomy mają nazwy po angielsku/łacinie — przetłumacz przez `słownik_anatomiczny_umed_pl_en.json` (dopasowanie po `en`/nazwie łacińskiej, fuzzy-match jak w `_parse_slownik_anatomiczny.py` z tego projektu, jeśli trzeba wzorca).

## Rekomendowana kolejność pracy

1. Zapytaj usera o zgodę i pobierz `SkeletalSystem100.fbx` (jeśli nie ma go już lokalnie) + jeden dodatkowy plik do testu spójności układu współrzędnych między plikami (np. `MuscularSystem100.fbx`, bo mięśnie łączą się z kośćmi w znanych miejscach — dobry test).
2. Rozszyfruj sufiksy nazw (pełny spis, nie zgadywanie).
3. Ustal i zweryfikuj JEDEN globalny transform (patrz wyżej).
4. Zbuduj mały pilotaż na 1-2 kościach (np. znowu łopatka + kość ramienna, żeby też sprawdzić staw) — wyeksportuj obiekty, wgraj do nowego, osobnego pliku danych, wyświetl w kopii `atlas_pilot.html` wskazującej na nowe pliki, porównaj wizualnie.
5. Dopiero po potwierdzeniu przez usera że pilotaż wygląda dobrze — skaluj na cały szkielet, potem kolejne warstwy (mięśnie, naczynia, nerwy, narządy...).
6. Na koniec: przemapuj `szpilki_map.json` na nowe ID (dopasowanie tekstowe po nazwie PL, ten sam wzorzec co `match_szpilki.js`/`build_szpilki_data.js` z poprzedniej kampanii tego projektu — szukaj w historii commitów/scratchpadzie jeśli trzeba wzorca).

## Pułapki środowiskowe napotkane w praktyce (żeby nie odkrywać drugi raz)

- **Working directory Bash-a bywa niestabilny między wywołaniami w tym środowisku** — używaj ścieżek bezwzględnych wszędzie, nie polegaj na `cd` przenoszącym się między komendami.
- **Polskie znaki + `print()` w Pythonie do bash stdout** → `UnicodeEncodeError` (cp1250). Zawsze pisz wynik do pliku z `encoding='utf-8'` zamiast printować bezpośrednio, jeśli tekst zawiera polskie znaki.
- **Cache przeglądarki** przy serwerze `python -m http.server` — nie wysyła nagłówków cache-control, Chrome potrafi trzymać starą wersję JSON/HTML pod tym samym portem. Używaj nowego portu (`.claude/launch.json`) albo `?v=N` cache-busting przy każdym teście.
- **Checkbox warstw w UI**: samo `.checked = true` / `.click()` bywa niewiarygodne — używaj `cb.checked = true; cb.dispatchEvent(new Event('change', {bubbles:true}))`.
