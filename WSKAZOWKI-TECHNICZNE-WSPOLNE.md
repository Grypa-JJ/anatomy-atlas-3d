# Wskazówki techniczne — wspólne dla obu konwersacji (atlas 3D)

Ten plik czytają/aktualizują OBIE równoległe konwersacje pracujące nad `atlas_pilot.html` (jedna nad danymi/landmarkami, druga nad UI/funkcjami). Cel: nie odkrywać tych samych błędów dwa razy. Dopisuj nowe sztuczki na dole, nie kasuj cudzych wpisów bez potrzeby.

## 1. Podgląd w przeglądarce (Browser pane) — jak nie dostać "Browser pane is not displayed"

- **Nie startuj serwera ręcznie przez Bash/PowerShell** (`python -m http.server 8791`). Taki proces nie jest zarządzany przez narzędzia przeglądarki - jak padnie w tle (np. po restarcie sesji), screenshot zacznie zwracać błąd albo strona załaduje się jako `chrome-error://chromewebdata/`, a Ty tego nie zauważysz bez dodatkowej kontroli.
- **Użyj `preview_start({name: "static-server"})`** - konfiguracja już jest w `.claude/launch.json` (porty 8934 i "static-server-test" na 8940). To narzędzie samo pilnuje procesu.
- **Zawsze `tabs_select({tabId})` PRZED screenshotem**, nawet jeśli tab był już otwarty wcześniej w tej samej sesji - samo `navigate` czasem nie wystarcza, żeby panel się realnie wyrenderował.
- Kolejność, która działa niezawodnie:
  ```
  preview_start({name: "static-server"})
  navigate({tabId, url: "http://localhost:8934/atlas_pilot.html?v=N"})   // ?v=N = cache-busting
  computer({action:"wait", duration:3})
  tabs_select({tabId})
  computer({action:"screenshot"})
  ```
- Jeśli dalej nie działa: sprawdź `document.title`/`location.href` przez `javascript_tool` zanim obwinisz screenshot - `chrome-error://chromewebdata/` znaczy że serwer nie odpowiada (wróć do punktu wyżej), nie że coś jest nie tak z samym narzędziem.

## 2. Testowanie bez UI - konwencja `window.__debug` / `window.__dbg*`

- Obie konwersacje używają tego samego wzorca: tymczasowo dopisz na końcu `init()` (albo na końcu skryptu) linijkę typu `window.__debug = { scene, camera, bones, ... }`, przetestuj przez `javascript_tool`, **usuń przed uznaniem featury za gotową**.
- **Jeśli zastałeś/aś cudzy `window.__debug` z polami, których nie rozpoznajesz (np. `getLoadedKinds`, `boneObjById`) - to nie Twój kod, prawdopodobnie zostawiła go druga konwersacja mid-testu.** Nie kasuj go przy okazji niepowiązanej zmiany - zostaw, albo dopisz swoje pola obok, nie nadpisuj całego obiektu.
- Nazwij swój hook unikalnie jeśli nie chcesz kolidować z drugą stroną w tej samej sesji przeglądarki (np. `window.__dbgDance` zamiast walczyć o `window.__debug`).

## 3. Plik `atlas_pilot.html` jest edytowany RÓWNOLEGLE przez obie konwersacje

- Przed każdym `Edit` rób świeży `Read`/`Grep` fragmentu, który zamierzasz zmienić - numery linii i sąsiedni kod przesuwają się między Twoimi turami, bo druga strona dopisuje kod w międzyczasie (np. w jednej sesji plik urósł z ~880 do ~1800 linii przez dodanie warstw mięśnie/naczynia/narządy).
- Jeśli `Edit` zwróci błąd "file has been modified since read" - to NORMALNE przy tej pracy równoległej, nie oznacza usterki. Po prostu przeczytaj plik ponownie i nanieś zmianę na aktualną wersję.
- Współdzielone pliki danych (`all_bones_labeled.json`, `bone_landmarks.json` itd.) - **nie zakładaj sztywno schematu**, sprawdź aktualną zawartość/pola przed napisaniem kodu, który je czyta (np. pole `kind`/`source`/`approx` mogły dojść po Twoim ostatnim spojrzeniu).
- Trzymaj się zasady "osobne pliki dla osobnych warstw danych" (np. `all_muscles_labeled.json` zamiast dopisywania mięśni do `all_bones_labeled.json`) - to pozwala pracować równolegle bez nadpisywania się nawzajem.

## 4. Serwowanie plików lokalnie

- Porty z `.claude/launch.json`: `static-server` = 8934, `static-server-test` = 8940. Jeśli obie konwersacje siedzą na tym samym porcie jednocześnie, może dojść do konfliktu "port zajęty" - w razie wątpliwości użyj `static-server-test` (8940) jako alternatywy.

## 5. Znane, nietrywialne gotchas w tym projekcie (Three.js/BVH/kamery)

- `camera.up.set(...)` MUSI być wywołane PRZED `new OrbitControls(camera, ...)` - inaczej matematyka sferyczna kontrolek się psuje (kamera "patrzy" w losowe miejsce).
- Siatki BodyParts3D mają niespójne/odwrócone normalne → zawsze `side: THREE.DoubleSide` na materiale, inaczej część siatki jest niewidoczna/nietrafialna promieniem (raycasting).
- Konwencja osi całego modelu: **X = przyśrodkowo-bocznie (prawa strona = ujemne X), Y = przód-tył (przód = ujemne Y), Z = góra-dół**. To ZOSTAŁO KIEDYŚ POMYLONE (X i Y zamienione) w ~35 ręcznie pisanych landmarkach - jeśli coś wygląda symetrycznie "na opak", sprawdź to najpierw.
- Reparenting obiektu Three.js z zachowaniem pozycji w świecie: policz `parentInv * child.matrixWorld`, dopiero potem `parent.add(child)` i `decompose()` wyniku na `position/quaternion/scale` - samo `.add()` NIE zachowuje pozycji w świecie.
- BVH (motion capture, Y-up) vs nasz model (Z-up): surowe kopiowanie rotacji ze szkieletu BVH wygląda "połamane" (ciało jakby się przewróciło) - trzeba przeliczyć każdą deltę rotacji przez sprzężenie `Qc * delta * Qc^-1`, gdzie `Qc` to rotacja +90° wokół osi X (patrz `DANCE_AXIS_FIX` w kodzie trybu tańca, jeśli szukasz gotowego przykładu).

---
*Dopisuj tu nowe odkrycia, żeby druga strona nie traciła czasu na to samo.*
