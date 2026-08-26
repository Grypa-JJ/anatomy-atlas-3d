# Plan rozwoju: Atlas 3D — funkcje UI + rozwój danych

Ten dokument łączy dwie równoległe ścieżki pracy nad tym samym atlasem:
- **Funkcje/UI** (ta konwersacja) — jak się z atlasem korzysta.
- **Dane** (druga konwersacja) — co jest na atlasie (kości, potem mięśnie/naczynia/nerwy/narządy).

Obie ścieżki mają się w pewnym momencie scalić w jeden produkt.

---

## 1. Stan obecny (punkt wyjścia)

**Plik:** `atlas_pilot.html` (samodzielna strona, three.js, bez frameworka/build-toola)
**Hosting geometrii:** Cloudflare R2, bucket publiczny, zero kosztu transferu
**Dane:** `all_bones_labeled.json` (203 kości, nazwy PL/EN), `bone_landmarks.json` (~1060+ punktów orientacyjnych, rośnie w drugiej konwersacji)

**Co już działa:**
- Wczytywanie i renderowanie całego szkieletu (203 obiekty OBJ, ładowanie równoległe ~8s)
- Obrót/zoom/pan (OrbitControls)
- Klik na kość → podświetlenie + etykieta PL/EN
- Klik na punkt orientacyjny (niebieska kropka) → etykieta, z pierwszeństwem przed całą kością
- Tryb izolacji pojedynczej kości ("Otwórz tę kość") + panel boczny z listą wszystkich jej punktów orientacyjnych, klikalnych
- Automatyczne dopasowanie kamery (poprawna trygonometria, nie mnożnik na oko)
- Zabezpieczenie przed startem w karcie o zerowym rozmiarze

**Czego jeszcze nie ma:** nic z listy niżej (sekcja 2) — to survey WSZYSTKICH funkcji z inspiracji Gemini, żadna jeszcze nie wdrożona poza tym co wyżej.

---

## 2. Pełna lista funkcji z inspiracji (Gemini) — pogrupowana i oceniona

Legenda trudności: 🟢 łatwe (dni), 🟡 średnie (wymaga uwagi/testów), 🔴 trudne/duży nakład, ⚫ poza zasięgiem obecnego stosu (wymaga innej technologii/danych)

### A. Wizualizacja i nawigacja 3D
| Funkcja | Trudność | Uwagi |
|---|---|---|
| Swobodna kamera 360°, zoom, pan | ✅ już jest | OrbitControls |
| **Presety widoku** (przód/tył/bok/góra/dół, reset) | 🟢 | proste pozycje kamery, mamy już `fitCameraToSkeleton()` jako wzorzec |
| **Cross-section (przekrój płaszczyzną)** | 🟡 | three.js ma wbudowane `clippingPlanes` na materiale — realne, wymaga UI do obracania/przesuwania płaszczyzny |
| **Sterowanie warstwami** (ukryj/izoluj/przezroczystość per układ) | 🟡 | mamy `boneObjById` — łatwo dodać toggle widoczności; przezroczystość = zmiana `material.opacity` + `transparent:true` |
| Suwak "warstwowości" (skóra→kości) jak w mockupie | ⚫ | wymaga danych o skórze/mięśniach jako osobnych warstwach — czeka na dane z 2. rozmowy |

### B. Interakcja z danymi i treścią
| Funkcja | Trudność | Uwagi |
|---|---|---|
| **Wyszukiwarka z autouzupełnianiem** | 🟢 | przeszukanie `bones` + `allLandmarks` po polu `pl`/`en`, dropdown, klik → `openBone()`/fokus kamery |
| Interaktywne etykiety/piny (już mamy) | ✅ częściowo | mamy klikalne punkty; brakuje zdjęć/audio/wideo w karcie (patrz sekcja C) |
| **Karta struktury** (System/Origo/Insertio/Unerwienie/Klinika) | 🟡 | UI gotowy do zrobienia teraz (statyczny layout), ale pola Origo/Insertio/Unerwienie mają sens dopiero dla MIĘŚNI/NERWÓW — na razie (same kości) pokażemy tylko to co mamy (nazwa PL/EN, ew. "połączenia z:") |
| **Narzędzia pomiarowe** (odległość/kąt/obwód na modelu) | 🟡 | odległość = trywialna (2 kliknięcia, `Vector3.distanceTo`); kąt = 3 kliknięcia + trygonometria; obwód/powierzchnia = trudniejsze, niższy priorytet |
| **Tryb porównawczy (split-screen)** | 🔴 | wymaga 2 niezależnych scen/kamer renderowanych obok siebie — możliwe w three.js (dwa viewporty), ale spory nakład UI |

### C. Narzędzia pracy i personalizacji
| Funkcja | Trudność | Uwagi |
|---|---|---|
| Rysowanie po powierzchni modelu | 🔴 | wymaga raycastingu + geometrii "decali" (three.js `DecalGeometry`) — realne, ale niszowe, niski priorytet na start |
| **Zapis zakładek / bookmarki** | 🟢 | `localStorage`, zapis pozycji kamery + zaznaczonej struktury |
| **Eksport zrzutu ekranu bez UI** | 🟢 | ukryj panel HTML na czas `renderer.domElement.toDataURL()`, pokaż z powrotem |
| **Tryb quizu** ("zgadnij strukturę") | 🟡 | logicznie prosty (ukryj etykiety, poproś o kliknięcie, sprawdź `userData`), ale warto dobrze przemyśleć UX (progres, wynik, powtórki błędnych — **mamy już wzorzec z reszty apki**, tryb Leitner/kolejka błędnych) |
| Eksport fiszek do Anki | 🟢 | mamy już cały pipeline CSV→Supabase z reszty projektu, można analogicznie wyeksportować punkty orientacyjne jako fiszki |

### D. Technologia i dostępność
| Funkcja | Trudność | Uwagi |
|---|---|---|
| Multiplatformowość (przeglądarka, WebGL) | ✅ już jest | działa wszędzie gdzie WebGL |
| Sterowanie dotykowe | 🟢 | OrbitControls ma to wbudowane, trzeba tylko przetestować na mobile |
| Skróty klawiszowe | 🟢 | proste event listenery |
| **Wielojęzyczność interfejsu i nazewnictwa** (PL/łacina/EN) | 🟡 | mamy już PL/EN w danych; **łacina wymaga dołożenia trzeciej kolumny nazw** (np. z TA2.csv, który już mamy pobrany — patrz notatka o atlasie 3D) |
| Wymowa audio (odsłuch łaciny) | 🔴 | wymaga plików audio (TTS albo nagrania) — realne przez Web Speech API (`speechSynthesis`, ograniczona jakość dla łaciny) jako tanie MVP, docelowo nagrania |
| AR/VR | ⚫ | WebXR API istnieje i three.js go wspiera, ale to osobny, duży temat (kontrolery, śledzenie, UX dotykowy w 3D) — zdecydowanie faza końcowa, nie teraz |

---

## 3. Priorytetowa kolejność wdrożenia (proponowana)

**Faza 1 — fundament nawigacji: ✅ GOTOWE**
1. ✅ Wyszukiwarka z autouzupełnianiem (kości + punkty, PL/EN, klik → otwiera i podświetla)
2. ✅ Presety widoku (przód/tył/prawo/lewo/góra/dół/reset)
3. ✅ Suwak przezroczystości (globalny, na cały szkielet)
4. ⏸️ Odświeżony panel informacyjny wg mockupu — **odłożone**, sensowne dopiero gdy dojdą pola typu Origo/Insertio z 2. rozmowy (na razie panel ma tylko nazwę PL/EN, to wystarcza)

**Faza 2 — praca z modelem: ✅ GOTOWE**
5. ✅ Przekrój płaszczyzną (X/Y/Z + suwak, `material.clippingPlanes`)
6. ✅ Narzędzie pomiaru odległości (2 kliknięcia → dystans w mm + linia, przycisk czyszczenia)
7. ⏸️ Toggle widoczności układów — **czeka na dane z 2. rozmowy** (na razie tylko "szkielet")

**Faza 3 — personalizacja i nauka: ✅ GOTOWE**
8. ✅ Zakładki (localStorage) — zapis nazwy+kamery+ew. izolowanej kości, lista z przejściem/usuwaniem
9. ✅ Eksport zrzutu ekranu (bez UI, PNG, `preserveDrawingBuffer`)
10. ✅ Tryb quizu ("zgadnij strukturę") — losowa kość, klik sprawdzany po NAZWIE (nie ID, bo kości symetryczne np. "Strzałka" mają identyczną nazwę L/P), wynik na bieżąco. Integracja z Leitner — odłożona, patrz pytania niżej.

**Faza 4 — rozszerzenia (dopiero po powyższym):**
11. ⏸️ Łacina jako trzeci język nazewnictwa — **zablokowane**: plik TA2.csv (wcześniej pobrany) nie istnieje już na dysku, trzeba pobrać ponownie zanim to ruszy
12. ✅ Eksport do Anki — przycisk generuje CSV (`Przód;Tył`, separator `;`) ze wszystkich punktów orientacyjnych (Front=PL, Back=EN+kość-kontekst), gotowy do bezpośredniego importu w Anki
13. ✅ Split-screen porównawczy — druga niezależna kamera+OrbitControls na TEJ SAMEJ scenie (bez duplikowania modelu), renderowanie przez `setViewport`/`setScissor`; routing kliknięć/przeciągnięć po stronie ekranu (capture-phase listener na `document`, żeby wyprzedzić wewnętrzny listener OrbitControls); zaznaczanie/etykiety też świadome podziału (raycasting z właściwej kamery)
14. ✅ Audio wymowy — przycisk 🔊 przy etykiecie, Web Speech API (`speechSynthesis`, `lang="pl-PL"`), tanie MVP bez własnych nagrań
15. AR/VR — jeszcze nie zrobione, największy osobny temat

---

## 4. Punkt styku z drugą konwersacją (dane)

Druga rozmowa dokłada punkt-po-punkcie nazwane struktury do `bone_landmarks.json` i docelowo rozszerzy `all_bones_labeled.json`-podobny plik o **mięśnie, naczynia, nerwy, narządy** (BodyParts3D ma ~1523 obiekty łącznie na całe ciało, kości to 203/241 z tego).

**Żeby UI było gotowe na to bez przepisywania od zera**, przy budowie funkcji z Fazy 1-2 trzeba:
- Nie zakładać na sztywno "kość" jako jedynego typu obiektu — pole `system`/`typ` w danych (do dodania przez 2. rozmowę: `"uklad": "kostny"|"miesniowy"|"naczyniowy"|"nerwowy"|"narzady"`) powinno od razu sterować kolorem materiału i widocznością w toggle układów.
- Karta informacyjna structury projektować z polami OPCJONALNYMI (Origo/Insertio/Unerwienie puste/ukryte dla kości, wypełnione dla mięśni) — nie hardcodować że każda struktura ma te same pola.
- Nazwa pliku danych landmarks/bones docelowo ujednolicić (np. `all_structures.json`) żeby nie robić dwóch osobnych schematów przy scalaniu.

**Scalenie obu prac**: gdy 2. rozmowa dorzuci nowy `system`/typ do danych, UI z tej rozmowy (toggle układów, karta info) zacznie z tego korzystać automatycznie, o ile trzymamy się powyższych zasad już teraz.

---

## 5. Otwarte pytania (do ustalenia z użytkownikiem, nie teraz)

- Czy quiz ma być osobnym trybem w tym atlasie, czy ma się integrować z istniejącym systemem powtórek (Leitner) z resztą apki?
- Czy eksport do Anki ma iść przez ten sam pipeline CSV→Supabase co reszta pytań, czy być niezależny?
- Priorytet łaciny: czy to MUSI być zanim inne funkcje, czy może poczekać do Fazy 4 jak zaplanowano?
