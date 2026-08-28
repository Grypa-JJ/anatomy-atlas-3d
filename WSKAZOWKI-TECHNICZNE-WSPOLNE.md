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

## 6. Rozszerzone gotchas przy screenshotach ("nie widzę screena")

Jeśli mimo sekcji 1 dalej dostajesz "Browser pane is not displayed" albo screenshot się nie odświeża:

- **Programowe zmiany checkboxów NIE działają przez samo `cb.checked = true`** - to nie odpala listenera `change`, więc warstwa się "zaznaczy" wizualnie ale mesh się NIE załaduje (bo loader wisi na evencie `change`, patrz `setLayerVisible`/`ensureKindLoaded`). Zawsze rób:
  ```js
  cb.checked = true;
  cb.dispatchEvent(new Event('change', {bubbles:true}));
  ```
  Samo `cb.click()` bywa niewiarygodne w automatyzacji (czasem nie odpala się w ogóle, bez błędu) - **wersja z jawnym `dispatchEvent('change')` jest jedyna, która działała za każdym razem**.
- **Kamera/raycaster mogą używać STAREJ macierzy, jeśli panel przez chwilę nie był aktywnie renderowany** (pętla `requestAnimationFrame` w tle bywa wstrzymywana, gdy panel "nie widoczny" z perspektywy narzędzi). Objaw: klikasz w wyraźnie widoczny na screenie obiekt i nic się nie zaznacza, mimo że inne kliknięcia (np. przyciski UI) działają. Rozwiązanie: `tabs_select` bezpośrednio przed KAŻDYM kliknięciem w canvas (nie tylko przed screenshotem), ewentualnie dodaj krótki `wait`.
- **Po `location.reload()` stan warstw/checkboxów może wrócić z zapisanego "ostatniego widoku" (localStorage), ale bez realnego wczytania siatek** - checkbox pokazuje `checked=true`, a mesh nigdy się nie załadował (bo `change` nie odpalił się programowo przy przywracaniu stanu). Zawsze rób jawny "wyłącz i włącz z dispatchEvent" po reloadzie, nie ufaj samemu odczytowi `cb.checked`.
- Do debugowania stanu sceny bez UI: tymczasowy `window.__debug` (patrz sekcja 2) z polami typu `getBones: () => bones, getLoadedKinds: () => loadedKinds` - `bones`/`loadedKinds` bywają REASSIGNOWANE (nie mutowane), więc zwykłe `window.__debug = {bones}` złapie STARĄ referencję na zawsze - używaj getterów (`() => bones`), nie gołych referencji.
- Jeśli koniecznie potrzebujesz świeżego hosta bez ŻADNEGO ryzyka cache przeglądarki użytkownika (np. użytkownik twierdzi "nic się nie zmieniło" mimo Twoich zmian) - dodaj nową konfigurację do `.claude/launch.json` na nieużywanym porcie (np. 8951+) i użyj `preview_start({name: "..."})`. To bardziej przekonujące dla użytkownika niż `?v=N` cache-busting na tym samym porcie.

## 7. Raycaster w three.js ignoruje WIĘCEJ niż tylko `.visible`

Potwierdzone czytaniem źródła `three@0.160.0`:
- **Nie sprawdza `.visible`** - trzeba ręcznie filtrować trafienia po `object.visible` (i po widoczności RODZICA, jeśli obiekt jest w grupie).
- **Nie sprawdza `material.clippingPlanes`** - jeśli masz suwak "Przekrój" (renderer-side fragment clipping), raycaster i tak trafi w geometrię po "obciętej" stronie płaszczyzny. Trzeba ręcznie: `sectionToggle.checked && sectionPlane.distanceToPoint(hit.point) < 0` → odrzuć trafienie. Ten sam błąd dotyczy każdej WŁASNEJ warstwy nakładanej na scenę niezależnie od geometrii (np. etykiety ID pozycjonowane przez `project()` - też muszą same sprawdzać `distanceToPoint`, inaczej pokazują ID rzeczy realnie niewidocznych).
- Wzorzec ogólny: **każdy nowy "tryb widoczności" dodany do sceny (nowa warstwa, przekrój, izolacja) wymaga osobnego, ręcznego filtra w KAŻDYM miejscu, które robi raycasting LUB projekcję 3D→2D** (klik, etykiety ID, cursor-zoom raycaster, pomiar odległości). Łatwo dodać nowy tryb i zapomnieć o jednym z tych miejsc - przy dodawaniu czegokolwiek nowego przejrzyj wszystkie istniejące `raycaster.intersectObjects(...)` i `.project(camera)` w pliku.

## 8. Metodologia szukania błędów pozycji ("dlaczego X wystaje poza Y")

Ten projekt ma DWA znane, systemowe, powtarzające się błędy w danych z importu Z-Anatomy (nie dotyczą natywnych obiektów BodyParts3D "FMA*", te są zawsze OK):
- **~98mm przesunięcia w osi Y** (za daleko do tyłu/za mało do przodu) - dotyczyło pierwotnie ~188 obiektów (naczynia/nerwy/część mózgu), naprawione hurtowo wcześniej, ale **stale znajdowane są kolejne pojedyncze/parami obiekty z tym samym błędem**, które umknęły oryginalnemu sweepowi (np. całe grupy nerwów czaszkowych III/IV/V/VIII/IX).
- **~66mm przesunięcia w osi Z** (za wysoko) - dotyczyło innej podgrupy (organy/tkanka łączna/mózg), też stale znajdowane nowe przypadki (np. cała szczegółowa anatomia gałki ocznej - 20 obiektów - i cała chrząstka małżowiny usznej - 27 obiektów - siedziały na czole/za wysoko, nikt tego nie sprawdzał bo nie były to "oczywiste" struktury).

**Jak testować pojedynczy obiekt**: policz bbox/centroid, porównaj z NIEZALEŻNYM zaufanym punktem odniesienia:
1. Najlepsze: ta sama struktura istnieje osobno w BodyParts3D (`FMA*`) i w dodatku Z-Anatomy/Brainder pod tą samą nazwą (np. hipokamp, ucho, gałka oczna) → policz różnicę centroidów, to jest Twoja dokładna wartość poprawki, zwykle blisko 66 albo 98mm.
2. Dobre: sąsiadująca kość/struktura, o której wiadomo że jest poprawna (np. nerw międzyżebrowy vs żebro, nerw czaszkowy vs kość skroniowa/klinowa/potyliczna - **uważaj który obiekt to "lewy" a który "prawy", sprawdź pole `en` w JSON, nie zgaduj po ID** - w tym projekcie `FMA52738`=prawa kość skroniowa a `FMA52739`=lewa, czyli NIE rosnąco z L/P).
3. Słabe/zawodne: porównanie do CAŁEGO szkieletu/bbox (może dawać fałszywe negatywy, bo inne części ciała nie są w tej samej płaszczyźnie).

**Testy automatyczne które już były używane, każdy ma ślepy punkt**:
- Test "odległość do najbliższej kości w tym samym pasie Z" (bucket co ~50mm) - **NIE działa dla struktur wewnątrz-czaszkowych/głębokich** (jądra, drogi nerwowe), bo te nigdy nie stykają się z kością, więc "przed" i "po" poprawce dystans jest podobnie duży - fałszywy negatyw. Też **myli lewą/prawą stronę** jeśli bucket łapie kość z drugiej strony ciała na tej samej wysokości Z - stąd potrzebne osobne testy per-obiekt z dopasowaniem strony.
- Test "ekstremalny punkt vs obwiednia czaszki" (margines np. 5mm) - **NIE złapie błędu, jeśli obiekt mieści się W ŚRODKU obwiedni** mimo że jest w złym miejscu wewnątrz niej (dokładnie to co przegapiał test dla jąder nerwów czaszkowych).
- Test symetrii lewo/prawo (porównanie L vs R) - **NIE złapie błędu, jeśli OBIE strony są przesunięte tak samo** (najczęstszy przypadek, bo import zwykle psuje calą parę naraz).
- Test "mediana lokalnych sąsiadów w oknie Z" - **masa fałszywych pozytywów na normalnej anatomii korowej** (bieguny płatów, zakręty) która legalnie rozciąga się szeroko w osi przód-tył na tej samej wysokości - nie ufaj mu bez ręcznej weryfikacji każdego wyniku.
- **Wniosek: żaden pojedynczy automatyczny test nie jest wystarczający, a screenshoty użytkownika regularnie łapały błędy, których wszystkie powyższe testy razem wzięte nie złapały.** Najskuteczniejsze było: (a) nowa funkcja "Pokaż ID na scenie" (etykiety ID bezpośrednio przy strukturach w 3D, patrz sekcja 9) + user robi zrzut ekranu i wskazuje które ID wyglądają źle, (b) traktowanie KAŻDEGO zgłoszenia usera jako prawdziwego tropu do zweryfikowania liczbowo, nie odrzucanie na podstawie "wygląda OK z automatycznych testów".

## 8a. Katalog bugów przemieszczenia znalezionych w tej sesji + hipoteza PRZYCZYNY

Po sesji intensywnego polowania na błędy pozycji (dziesiątki naczyń/nerwów, wyszukiwane przez usera ze zrzutów ekranu + masowe zapytania JS po całym zbiorze), rysuje się wzorzec, który warto zapisać zanim zniknie z pamięci roboczej.

### Jak to wyglądało "z zewnątrz" (objaw wizualny)

Na zrzutach ekranu całego ciała: gęste, poplątane "kłębki" naczyń wystające POZA sylwetkę ciała w konkretnych, powtarzalnych okolicach — czubek głowy (czerwony "kolec" nad czaszką), okolica skroniowo-potyliczna (duże pętle wylatujące z boku głowy), dół tylny czaszki (tętnice krążenia tylnego mózgu daleko za tylną krawędzią czaszki), okolica barku/pachy (naczynia zbierające się w pętle z dala od ramienia), okolica krezki/esicy. Pojedynczo, każdy taki obiekt wyglądał jak "przesunięta kopia" prawidłowo umiejscowionej sąsiedniej struktury.

### Dwa dominujące, DYSKRETNE (nie losowe) offsety

Prawie wszystkie znalezione dziś błędy dały się sprowadzić do jednej z dwóch konkretnych wartości, powtarzających się na dziesiątkach niepowiązanych struktur w różnych częściach ciała:

- **`translateY: -98`** (siatka siedziała ~98mm ZA DALEKO Z TYŁU) — dotyczyło głównie naczyń/nerwów tułowia i kończyn: tętnica/żyła udowa (prawa), pachowa, zasłonowa, żyła wrotna, aorta piersiowa i brzuszna (jako DUPLIKATY poprawnej natywnej aorty pod innym ID), tętnice/żyły lędźwiowe, żyła sromowa wewnętrzna, cała odnoga krezkowa (esicze, krętniczo-okrężnicza, wyrostka robaczkowego, okrężnicza środkowa + żyły), tętnica piersiowo-boczna/piersiowo-barkowa, żyła podłopatkowa, powierzchowny układ żylny ramienia (odpromieniowa/cephalica, łokciowa pośrodkowa, pośrodkowa przedramienia — ale NIE odłokciowa/basilica, ta była OK), tętnice krążenia tylnego mózgu (podstawna, PICA, AICA, SCA, PCA, rdzeniowa przednia) po dopasowaniu do "Stoku" (Clivus) z dokładnością 1mm.
- **`translateZ: -66`** (siatka siedziała ~66mm ZA WYSOKO) — dotyczyło głównie struktur głowy powiązanych z oponami/mózgiem: gałka oczna, chrząstka małżowiny usznej (znalezione wcześniej), a w tej sesji: zatoka strzałkowa górna/dolna, tętnica okołospoidłowa/spoidłowo-brzeżna/bruzdy środkowej i przedśrodkowej, tętnica skroniowa powierzchowna, potyliczna, żyły skroniowe powierzchowne, tętnica ciemieniowa tylna/kątowa/czołowo-podstawna boczna, zatoki oponowe dołu tylnego (esowata/prosta/potyliczna/skaliste), gałąź skroniowa przednia MCA. **Ciekawe**: kilka z tych obiektów (skroniowa powierzchowna, potyliczna, żyły skroniowe) miało NIEZALEŻNY drugi błąd `translateY: -66` (ta sama wartość liczbowa, ale w INNEJ osi) — sugeruje że to nie przypadek tylko systemowa cecha konkretnej podgrupy importu.

### Wyjątek: błąd NIE-sztywny (shear, nie translacja)

Żyła nieparzysta (+ krótka + krótka dodatkowa) nie dała się naprawić żadnym stałym przesunięciem — błąd rósł WZDŁUŻ naczynia (od ~10mm przy przeponie do ~40mm przy Th4-5, potwierdzone atlasem "zatacza łuk"). Naprawione przez interpolację liniową przesunięcia Y wzdłuż lokalnej osi Z obiektu (nowy mechanizm `MESH_SHEAR_CORRECTIONS`, patrz kod). To jedyny znaleziony dotąd przypadek tego typu.

### Hipoteza przyczyny (nie potwierdzona formalnie, ale spójna z dowodami)

1. Import Z-Anatomy do sceny BodyParts3D wymagał jakiegoś przeliczenia współrzędnych między DWOMA różnymi, niezależnie zmodelowanymi szkieletami (różna poza referencyjna, różne proporcje, różny punkt zerowy układu współrzędnych). Widać to wprost w tej sesji: żeby dopasować punkty łopatki z Z-Anatomy do naszej łopatki (BodyParts3D), potrzebne było pełne dopasowanie afiniczne metodą najmniejszych kwadratów (nie prosta translacja) — i nawet wtedy średni błąd wyszedł ~22mm. To sugeruje, że oba szkielety różnią się nie tylko przesunięciem, ale też subtelnie POZĄ/PROPORCJAMI.
2. Import najwyraźniej był robiony w KILKU falach/skryptach (różne partie ciała, różne momenty), z których część używała jednego uproszczonego przesunięcia (np. dopasowanie do jednego punktu referencyjnego zamiast pełnego dopasowania), co dla obiektów BLISKO tego punktu dawało dobry wynik, a dla obiektów DALEKO od niego zostawiało systematyczną resztę — stąd dwie różne, powtarzalne wartości (98mm i 66mm) zamiast jednego uniwersalnego bugu.
3. Wcześniejszy "hurtowy" sweep (patrz sekcja 8 wyżej, ~188 obiektów) najwyraźniej naprawił WIĘKSZOŚĆ dotkniętych obiektów tą samą wartością, ale **nie wszystkie** — stąd wciąż znajdowane "pojedyncze/parami" straggler-y które nie zostały złapane przez oryginalne kryterium wyboru (może dodane do sceny w innym momencie / inny zakres ID / inna nazwa pliku źródłowego niż to na czym operował oryginalny sweep).
4. Żyła nieparzysta (błąd nie-sztywny) prawdopodobnie pochodzi z fragmentu Z-Anatomy o INNEJ krzywiźnie kręgosłupa (kifoza piersiowa) niż nasz szkielet BodyParts3D — naczynie które w źródle ściśle podąża za krzywizną kręgosłupa, po nałożeniu na szkielet o innej krzywiźnie, akumuluje błąd rosnący wzdłuż swojej długości zamiast stałego przesunięcia.

**Wniosek praktyczny dla kolejnych sesji łatających TEN atlas (v1)**: jeśli natrafisz na strukturę wyglądającą na "wystającą"/"oderwaną", sprawdź NAJPIERW czy pasuje do `-98 Y` albo `-66 Z` (i jego kuzyna `-66 Y` dla podgrupy skroniowo-potylicznej) zanim zaczniesz liczyć od zera — to dwa najbardziej prawdopodobne trafienia. Jeśli żadne nie pasuje i błąd rośnie/maleje wzdłuż długości obiektu zamiast być stały — to prawdopodobnie kolejny przypadek "shear", użyj `MESH_SHEAR_CORRECTIONS`.

**Dla atlasu v2 (patrz `INSTRUKCJA-ATLAS-V2-ZANATOMY.md`)**: to jest właśnie argument ZA budową v2 w całości na jednym źródle (Z-Anatomy) zamiast dalszego łatania patchworku dwóch źródeł — jeśli hipoteza 1 jest prawdziwa, cała ta klasa błędów po prostu nie powinna wystąpić, gdy nie ma już dwóch niezależnie modelowanych szkieletów do pogodzenia.

## 9. Nowe funkcje UI dodane w tej sesji (żeby druga strona nie duplikowała)

- **`#show-id-labels`** (checkbox "🏷️ Pokaż ID na scenie") + `updateIdLabels()` w pętli `animate()` - rysuje pływające etykiety z ID nad każdą aktualnie widoczną (top-level) strukturą, pozycja liczona raz i cache'owana (`idLabelPositionCache`, world-space `Box3().setFromObject`), bo liczenie co klatkę dla setek obiektów byłoby wolne. **Szanuje `.visible` ORAZ płaszczyznę przekroju** (patrz sekcja 7) - jeśli dodajesz kolejny tryb widoczności, pamiętaj dopisać go tu też.
- **Skalpel** (`#scalpel-toggle`, `#scalpel-undo`, `#scalpel-restore-all`) - tryb w którym klik chowa strukturę (`obj.visible = false`) i odkłada na stos `cutStack`, cofanie zdejmuje ze stosu. Nie wchodzi w drogę normalnemu trybowi zaznaczania (early return w handlerze klika, analogicznie do `measureMode`/`quizMode`).
- Panel informacyjny (`#lbl-id`) i panel boczny izolacji (`#sb-id`) teraz pokazują `ID: <id>` pod nazwą angielską - przydatne przy zgłaszaniu błędów bez potrzeby kopiowania czegokolwiek ręcznie.
- `polygonOffset` (-1.5/-1.5) na materiale KOŚCI - naprawia z-fighting między kością a stykającą się z nią tkanką miękką (np. płat czołowy tuż pod blaszką oczodołu) przy bardzo bliskim kontakcie dwóch poprawnych geometrycznie powierzchni. Kość zawsze "wygrywa" remis głębi. **Nie ustawiaj tej wartości za wysoko (próbowane -4/-4) - powoduje migotanie MIĘDZY samymi kośćmi** (sąsiadujące kości/szwy zaczynają walczyć ze sobą), -1.5 do -2 jest bezpieczne.

## 10. Upload na R2 (Cloudflare) - wzorzec

```bash
# Sekrety trzymamy POZA repo (GitHub push protection blokuje klucz w historii).
# Ustaw w lokalnym środowisku przed uploadem (np. w .env / eksport w shellu):
#   CF_ACCOUNT_ID, CF_R2_BUCKET, CF_AUTH_EMAIL, CF_GLOBAL_API_KEY
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/r2/buckets/$CF_R2_BUCKET/objects/atlas/<podfolder>/<ID>.obj" \
  -H "X-Auth-Email: $CF_AUTH_EMAIL" -H "X-Auth-Key: $CF_GLOBAL_API_KEY" --data-binary "@r2_upload/atlas/<podfolder>/<ID>.obj" > /dev/null
```
- Podfoldery = kind: `szkielet`,`miesnie`,`naczynia`,`narzady`,`zeby`,`lacznotkankowe`,`mozg`,`nerwy`,`chlonne`.
- Dla >20 plików: **rób upload w tle** (`run_in_background: true`), sekwencyjny `curl` dla ~250 plików realnie potrafi przekroczyć 2 minuty i ubić Ci turę. Weryfikuj po fakcie przez bezpośredni `curl` GET pod `https://pub-75514e92552347ccbcdab6bfacd153fd.r2.dev/atlas/<podfolder>/<ID>.obj` (public URL), NIE ufaj samemu "polecenie się zakończyło" bez błędu - czasem trzeba wysłać drugą turą (patrz przypadek gdzie tylko pierwsze 30/96 zdążyło wysłać się przed timeoutem).
- Usuwanie starego duplikatu: `curl -X DELETE` z tym samym URL-em zamiast `PUT`.

## 11. Wzorzec czyszczenia duplikatów struktur

Gdy ta sama struktura anatomiczna istnieje pod dwoma ID (stary import Z-Anatomy + nowszy, dokładniejszy import z innego źródła, np. Brainder):
1. Sprawdź który ma punkty orientacyjne (`bone_landmarks.json`, filtruj po `boneId`).
2. Jeśli NOWY obiekt nie ma punktów, a STARY ma - przekieruj punkty starego na nowy (`lm.boneId = nowyId`, przelicz `lm.pos` z geometrii nowego obiektu - centroid albo punkt ekstremalny, zależnie co reprezentował oryginalny punkt).
3. Jeśli NOWY już ma własne punkty (np. auto-wygenerowany "Środek struktury") - punkty starego są zbędne, po prostu je usuń.
4. Usuń stary obiekt z katalogu JSON (`all_*_labeled.json`), z lokalnego mirrora (`r2_upload/atlas/.../ID.obj`) i z R2 (DELETE).

## 12. Katalog spotkanych bugów RENDEROWANIA (nie danych/pozycji - to sekcja 8)

Lista typów problemów wizualnych napotkanych w tej sesji, żeby przyszła rozmowa rozpoznała objaw i wiedziała gdzie szukać, zamiast diagnozować od zera.

1. **Z-fighting kość↔tkanka miękka przy bardzo bliskim styku** - objaw: różowe/kolorowe "cętki" albo migoczące plamki na powierzchni kości, mimo że geometria obu obiektów jest POPRAWNA (raycast w to miejsce trafia w litą kość, bez dziury). Przyczyna: dwie powierzchnie tak blisko siebie, że precyzja z-bufora GPU nie odróżnia która jest bliżej kamery, więc miesza kolory piksel-po-pikselu. **Test rozstrzygający**: kliknij dokładnie w podejrzany piksel - jeśli raycaster (dokładny test geometryczny) konsekwentnie zwraca kość/spójny obiekt, to NIE jest błąd pozycji, tylko renderu. Naprawione przez `polygonOffset` na materiale kości (sekcja 9) - kość zawsze wygrywa remis głębi.
2. **Migotanie MIĘDZY samymi kośćmi** (efekt uboczny #1) - jeśli `polygonOffsetFactor/Units` ustawisz za wysoko (próbowane -4/-4), sąsiadujące kości/szwy zaczynają walczyć ze sobą zamiast z tkanką miękką. Trzymaj się -1.5 do -2.
3. **Raycaster trafia w niewidoczne obiekty** - dwa niezależne przypadki w tym projekcie: (a) punkty orientacyjne z wyłączonej warstwy dalej klikalne (brak filtra po `.visible`), (b) geometria "odcięta" suwakiem Przekroju dalej klikalna (brak filtra po płaszczyźnie przekroju). Oba naprawione ręcznym filtrem w handlerze klika (sekcja 7) - **za każdym razem gdy dodajesz nowy tryb widoczności, sprawdź czy nie trzeba dopisać trzeciego takiego filtra**.
4. **Własne warstwy 3D→2D (etykiety ID) pokazujące dane rzeczy niewidocznych** - ten sam korzeń co #3 (`.project(camera)` nie wie nic o `.visible` ani o płaszczyźnie przekroju), tylko w kodzie WŁASNYM (nie w bibliotece). Widoczne np. jako etykiety ID daleko poniżej wyraźnej linii ucięcia suwakiem.
5. **"Dimowanie" złej warstwy po kliknięciu przez lukę w pokryciu siatki** - gdy klik przez dziurę w warstwie mięśni trafiał w leżącą pod spodem kość, efekt "przygaś wszystko oprócz zaznaczonego" przygaszał CAŁĄ inną warstwę (mięśnie) zamiast tylko innych kości. Naprawione: `dimOthersExcept` przygasza tylko obiekty TEGO SAMEGO `kind` co zaznaczony.
6. **Stara/zablokowana macierz kamery gdy panel nie jest aktywnie renderowany** - `requestAnimationFrame` bywa wstrzymywane w tle, więc `camera.matrixWorldInverse` używane przez raycaster jest nieaktualne mimo że świeży screenshot wygląda poprawnie. Objaw: klikasz w coś oczywistego na screenie i nic się nie zaznacza. Patrz sekcja 6 (rozwiązanie: `tabs_select` tuż przed każdym klikiem, nie tylko przed screenshotem).
7. **Duplikaty struktur renderujące się "na siebie"** - dwa obiekty (stary import + nowy, dokładniejszy) w tym samym miejscu dają wizualnie gęstszy/dziwnie wyglądający fragment, czasem mylony z błędem pozycji zamiast z duplikatem. Sprawdź czy nie ma dwóch ID pod tą samą polską nazwą (`grep` po `all_*_labeled.json`) zanim zaczniesz szukać przesunięcia.
8. **NIEROZWIĄZANE na koniec tej sesji: "postrzępiony"/"potłuczone szkło" wzór ciemnych trójkątnych plamek na całej powierzchni obiektu przy Przekroju + duże zbliżenie** - zgłoszone przez użytkownika ze zrzutem ekranu (okrągły kształt, wygląda jak popękana skorupa z ciemnymi dziurami rozsianymi po całej widocznej powierzchni, NIE tylko przy linii cięcia). Nie odtworzone jeszcze samodzielnie w tej sesji (próby z izolowaną żuchwą przy różnych wartościach suwaka wyglądały czysto). **Hipotezy do sprawdzenia**: (a) `side: THREE.DoubleSide` (wymagane dla siatek BodyParts3D, patrz sekcja 5) + brak "zaślepki" (cap) na przeciętej krawędzi → widać wnętrze bryły, które przy pewnych kątach miesza się z zewnętrzną ścianą w z-bufferze; (b) interakcja `polygonOffset` (punkt 1 wyżej) z przycinaniem fragmentów w rejonach o dużym gradiencie głębi; (c) błąd specyficzny dla konkretnego obiektu/siatki (samoprzecinająca się geometria). Zacznij od odtworzenia na TYM SAMYM obiekcie co użytkownik (żuchwa, warstwy Kości+Narządy, suwak Przekroju w okolicy wartości, przy której użytkownik to zobaczył), potem wyłącz `polygonOffset` tymczasowo żeby sprawdzić czy to on jest winny.

## 13. Pobieranie NOWYCH modeli 3D (Z-Anatomy, NIH, Zenodo) — gotchas kompilacji atlasu

Kontekst: obecny atlas stoi na BodyParts3D (`FMA*`) + częściowym imporcie Z-Anatomy (`ZA*`). BodyParts3D jest niskiej jakości i wiele struktur to jeden nienazwany blob (np. serce `FMA7274`). Pełne źródło Z-Anatomy pozwala to podmienić — poniżej co zadziałało i na czym się wykłada.

### 13.1. Skąd brać — CAŁE ciało jako nazwane siatki
- **`github.com/LluisV/Z-Anatomy-Sample`** (repo Unity, ~204 MB, CC BY-SA). W `Assets/Models/1.0 Models/` leży **9 plików FBX wg układów**, każdy z setkami nazwanych brył (nazwa łac./ang. = nazwa mesha):
  - `SkeletalSystem100.fbx` (41 MB) · `MuscularSystem100.fbx` (37 MB) · `CardioVascular41.fbx` (65 MB, serce rozłożone + całe naczynia) · `NervousSystem100.fbx` (54 MB) · `VisceralSystem100.fbx` (18 MB, **312 brył** — wszystkie narządy) · `LymphoidOrgans100.fbx` (2 MB) · `Joints100.fbx` (10 MB) · `Regions of human body100.fbx` (4 MB) · `Reference lines, planes and movements 1.fbx` (0.4 MB)
  - pobieranie pojedynczego pliku: `raw.githubusercontent.com/LluisV/Z-Anatomy-Sample/main/Assets/Models/1.0%20Models/<NAZWA>.fbx`
  - pełniejszy (z żeńskimi narządami itd.) jest w `Z-Anatomy/The-blend` → `Z-Anatomy.zip`, ale to `.blend` (patrz 13.3).
- Inne źródła sprawdzone: **NIH 3D** (`3d.nih.gov`) i **Sketchfab CC-BY** = pojedyncza NIENAZWANA bryła (dobre jako "hero model" do jednego widoku, bezużyteczne do klikania struktur). **Zenodo 4590294** (Rodero, CC BY 4.0) = 4-jamowe serca z CT, ale to siatki tetrahedralne do symulacji (24 regiony, w tym 14 technicznych pierścieni).

### 13.2. FBX → GLB → OBJ bez Blendera (Blender NIE jest zainstalowany)
- `npm i fbx2gltf` → binarka `node_modules/fbx2gltf/bin/Windows_NT/FBX2glTF.exe`
- **Działa TYLKO tak:** `FBX2glTF.exe -i in.fbx -o out --binary` (bez rozszerzenia w `-o`, dopisuje `.glb`). Dodatkowe flagi typu `--keep-attribute position normal` → błąd "File does not exist: normal".
- Wielkość: `CardioVascular41.fbx` 65 MB → `.glb` 38 MB; `VisceralSystem100.fbx` 18 MB → 17 MB.

### 13.3. Pułapki przy wyciąganiu siatek z przekonwertowanego GLB (trimesh)
- **MUSISZ zaaplikować transformy grafu sceny.** `scene.geometry[name]` zwraca SUROWĄ geometrię — w obrębie jednego FBX różne meshe mają różną skalę/pozycję zapiekaną w macierzy węzła (np. w `VisceralSystem` Wątroba wyszła ~1000× za mała, Okrężnica wstępująca w skali ~1:1). Poprawnie:
  ```python
  for node in scene.graph.nodes_geometry:
      tf, geom = scene.graph[node]
      if geom == name:
          m = scene.geometry[name].copy(); m.apply_transform(tf)
  ```
- **GLB wyeksportowany z trimesh NIE MA wektorów normalnych** → w three.js `MeshStandardMaterial`/`MeshPhongMaterial` renderuje się jako **czarna sylwetka bez światła**. Fix przy wczytaniu: `o.geometry.deleteAttribute('normal'); o.geometry.computeVertexNormals();` (albo `flatShading:true`). STL nie ma tego problemu, bo tam i tak liczy się `computeVertexNormals()` ręcznie.
- **Jednostki: Z-Anatomy = METRY, atlas/BodyParts3D = MILIMETRY → skaluj ×1000** przy imporcie. `CardioVascular` serce ~0.13 m; `all_organs_labeled.json` oczekuje mm.
- **Sufiks `.j` w nazwach Z-Anatomy** = powierzchnie-kotwice adnotacji (brzegi, powierzchnie, wpuklenia, bieguny, wnęki), NIE bryły narządów. W `VisceralSystem`: 312 meshy = ~134 bryły + ~178 `.j`. `.j` można wykorzystać jako gotowe "szpilki"/landmarki narządów, ale nie renderować jako solid.

### 13.4. Toolchain do siatek (musiał być doinstalowany pip-em w tej sesji)
- Było już: `trimesh` 5.0, `nibabel` 5.4. Doinstalowane: `scikit-image` (przez `pip install --no-deps scikit-image` + osobno `scipy networkx imageio tifffile lazy-loader pillow` — bo zwykły `pip install` wywala się na zablokowanym `Scripts\trimesh.exe`), `matplotlib`. `meshio` się NIE zainstalował. Blendera i `pyglet` brak (trimesh `scene.save_image` nie działa — renderuj podgląd przez three.js w `preview_start`, nie przez trimesh).
- Marching cubes z NIfTI: `skimage.measure.marching_cubes`. VTK unstructured grid (tet) parsuj ręcznie liniami (kolejność sekcji bywa CELL_TYPES→CELLS→CELL_DATA, nie zawsze standardowa) i wyciągaj powierzchnię per-region jako ściany należące do dokładnie jednego tet-a danego regionu.

### 13.5. Kamera / framing przy nowych złożonych modelach
- Celuj kamerą w bbox **samego narządu** (dla serca: 4 jamy LA/LV/RA/RV), nie w bbox całego zestawu — wielkie naczynia (aorta piersiowa/brzuszna, brzuszny IVC) ściągają środek o kilkadziesiąt mm (w teście: 77 mm za nisko, `fill_pct` 4 % → 31 % po poprawce). Przy imporcie do atlasu rozważ wywalenie odcinków naczyń daleko od narządu.

### 13.6. Dwie dodatkowe pułapki wykryte przy narządach
- **three.js `GLTFLoader` SANITYZUJE nazwy węzłów**: spacje → `_`, znaki `. : / [ ]` usuwane. `"Kidney.l"` w GLB → `mesh.name === "Kidneyl"` w three. Jeśli mapujesz manifest→mesh po nazwie, użyj tej samej sanityzacji po obu stronach (`n.replace(/\s/g,'_').replace(/[.:\/\[\]]/g,'')`).
- **Skala między plikami FBX Z-Anatomy JEST NIESPÓJNA.** `CardioVascular41` wyszło w metrach (~0.13), `VisceralSystem100` w ~nanometrach (rozpiętość 9e8). NIE zakładaj ×1000 na sztywno — licz auto-skalę: `scale = docelowa_rozpiętość_mm / aktualna_maks_rozpiętość`.
- **Oś pionowa: FBX2glTF → Y-up, a `trimesh` przy eksporcie GLB TEŻ zapisuje Y-up (spec glTF).** Efekt: jeśli w ekstrakcji obrócisz siatki do Z-up i wyeksportujesz przez trimesh, model wróci Y-up i będzie "do góry nogami / na boku". Rozwiązanie które zadziałało: NIE obracać w ekstrakcji, w viewerze `camera.up.set(0,1,0)`. Weryfikacja kierunku: nagłośnia/gardło ma mieć world-Y > wątroba > stercz/jądra (sprawdź `Box3().setFromObject` PO `scene.updateMatrixWorld(true)` — bez tego wszystkie `matrixWorld` są jednostkowe i rzuty na ekran wychodzą identyczne). Przy imporcie DO atlasu (Z-up) obróć wtedy `rotation_matrix(+pi/2,[1,0,0])`.
- **Zapis JSON na Windows**: `open('plik.json','w')` bez `encoding='utf-8'` pisze w cp1250 → polskie znaki w manifeście trafiają do przeglądarki jako U+FFFD. Zawsze `open(..., 'w', encoding='utf-8')` + `json.dump(..., ensure_ascii=False)`.
- **Cache przy podglądzie**: `?v=N` w URL busta tylko `index.html`. `fetch()`/`loadAsync()` innych plików trzeba bustować osobno (dopisz `?b=N` w kodzie), inaczej przeglądarka trzyma starą wersję manifestu/GLB.

### 13.8. Rejestracja naczyń CardioVascular → CT (przełącznik "unaczynienie" w `_organ_compare`)
- `CardioVascular41` i `VisceralSystem/CT` mają **różny układ** — samo skala+translacja daje MIRROR. Poprawnie: **Kabsch z odbiciem** (`np.linalg.svd(P0.T@Q0)`, `d=sign(det(Vt.T@U.T))`, `R=Vt.T@diag(1,1,d)@U.T`) na centroidach par landmarków. Wyszło: skala ~996, `R≈diag(-1,+1,-1)` (flip X+Z = obrót 180° wokół osi SI).
- Landmarki wektorowe obecne w obu: aorta, ż. główna górna/dolna, ż. wrotna wątroby, tt. nerkowe L/P. Rezydua 6–26 mm dla dużych naczyń (tt. nerkowe gorzej — parowane z centroidem całej nerki). Do schematycznej nakładki wystarcza.
- Nakładka jest w panelu **CT** (nie ZA), bo rejestracja jest do przestrzeni CT s0086; dla innych osobników ukrywana + nota. `vessels.glb` (60 siatek) + `vessels_manifest.json` (`{organ,vessel,kind:artery|vein,key}`), filtr `byOrgan`.

### 13.9. Barwienie HU na MPR
- Nie da się odzyskać HU z wypalonego szarego JPEG — trzeba **drugi zestaw** plastrów renderowany z `.nii.gz` przez LUT klas tkanek (`_mpr_hu.py`, `<pl>_<i>_hu.jpg` obok `<pl>_<i>.jpg`). Viewer: `MPR.color` bool → sufiks `_hu`. Skan z kontrastem: narządy miąższowe 100–200 HU wpadają w pasmo "krew/kontrast" (czerwień) — to poprawne, nie błąd LUT.

### 13.10. Czaszka / mózg do `_organ_compare` z pełnego blendu (build 70–73)
- **Sample vs pełny blend, podstawa czaszki: BEZ RÓŻNICY.** Sprawdzone: te same ~28 znaczników `.j` (2-wierzchołkowe markery, nie prawdziwe otwory w siatce), ta sama siatka kości (ta sama liczba trójkątów). `bone_landmarks_v2.json` w `build/` i `build_full/` ma identyczny zestaw dla czaszki (foramen ovale/rotundum/spinosum, optic/hypoglossal/condylar canal, wyrostki pochyłe, arcuate eminence). Podmiana Sample→full dla czaszki NIC nie da.
- Czego **nie ma w Z-Anatomy w ogóle** (żadnej wersji): kanał t. szyjnej, przewód słuchowy wewn., otwór szyjny jako taki, rozdarty, szczelina oczodołowa górna, grzebień koguci, blaszka sitowa, otwór rylcowo-sutkowy. Nazwy "Carotid canal"/"Crista galli"/"IAM"/"Cribriform plate" **są tylko w drzewie kolekcji blendu jako węzły taksonomiczne — zero geometrii**. → `_organ_compare` stawia te ~8 ręcznie po współrzędnych anatomicznych (`skull_landmarks.json`, `approx:true`).
- **Mózg — pełny blend WARTO** (inaczej niż czaszka): `all_brain_labeled_v2.json` = 260 struktur z parcelacją kory (52 zakręty + 54 bruzdy), Sample `NervousSystem100` miał korę jako 2 bryły. Pułapki przy ekstrakcji do przeglądarki: (a) `all_brain_labeled_v2.json` zawiera zanieczyszczenia z warstwy CNS — oko (cornea/lens/sclera), rdzeń kręgowy, nerwy obwodowe, "Nerve to quadratus femoris" — filtrować regexem; (b) długie **drogi rdzeniowe** (korowo-rdzeniowa, rdzeniowo-móżdżkowa, pęczek klinowaty/smukły) mają `ptp(y) ≈ 490 mm` — schodzą przez cały rdzeń; odrzucać po `np.ptp(vertices[:,1]) > 150`; (c) kompozytor PL sklejał pod-struktury w jedną etykietę ("Część zakręt czołowy dolny" ×3 = opercular/orbital/triangular part IFG) — deduplikować sufiksem z `id`.
- Transform `build_full/obj/*.obj` (atlas_v2, Z-up, +Y=tył) → viewer `_organ_compare` (Y-up, +Z=przód): `(x,y,z) → (x, z, -y)`. Zweryfikowane na centroidach: superior frontal gyrus z=1671 (górny), medulla z=1567 (dolny), occipital pole y=+87 (tył).

### 13.7. Pliki robocze tej sesji
- `_heart_compare/` w repo: `index.html` (podgląd 3 modeli serca obok siebie), `z-anatomy-heart.glb` + `z-anatomy/*.obj` (37 struktur, CC BY-SA), `rodero-heart.glb` + `rodero/*.obj` (CT, CC BY 4.0), `nih_heart.stl` (Public Domain).
- `_organ_compare/` w repo: `index.html` (przeglądarka narządów: lewa lista grup→narządów po polsku, klik = izolacja+kadr, klik w siatkę = **polska nazwa** + ang. jako podtytuł, toggle "segmenty" / "powierzchnie·etykiety" / "izolacja", RoomEnvironment do światła, `camera.up=(0,1,0)`), `visceral.glb` (16 MB, 312 nazwanych siatek, mm, wyśrodkowane, **Y-up po eksporcie trimesh**), `visceral_manifest.json` (per siatka: `organ`,`group`,`label`,`segment`,`pl`,`pl_match`). Źródło: `VisceralSystem100.fbx`, CC BY-SA.
- **Mapowanie EN→PL zrobione: 312/312 (100%).** Metoda w skrypcie: słownik `slownik_anatomiczny_umed_pl_en.json` rozbity po `;` (wieloznaczne `en`), normalizacja (lowercase, `oe/ae→e`, usuń `(...)` `[...]` `.l/.r/.j` `_N`), warianty zapytania (`left/right +`, l.poj/mn, `"A of B"→"B A"` i `"A of B"→"A"`), ~55 ręcznych `OVR`, `difflib` cutoff 0.86, segmenty Couinauda z regexa `(N)`→`Segment wątroby [N]`, `_N` dziedziczy z bazowej nazwy. Laterality: sufiks uzgodniony rodzajowo wg końcówki (`-a`→lewa, `-o/-e/-um`→lewe, reszta→lewy).
- Surowce (FBX, konwerter fbx2gltf): scratchpad `.../scratchpad/hearts/` i `.../scratchpad/node_modules/`.
- **Do zrobienia:** polskie nazwy per-siatka (mechanizm: `slownik_anatomiczny_umed_pl_en.json` + `ta2_latin_lookup.json`), integracja z `atlas_pilot.html` (dodać jako warstwę/podkategorię, wpisy do `all_organs_labeled.json`, usunąć stare `FMA*` narządy-bloby).

---
*Dopisuj tu nowe odkrycia, żeby druga strona nie traciła czasu na to samo.*
