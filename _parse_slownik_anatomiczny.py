import pdfplumber
import json
import re

PDF = "403812670-Słownik-polsko-angielski-mian-anatomicznych-dla-studentow-medycyny-pdf.pdf"

SECTION_HEADERS = set()

def clean(s):
    if not s:
        return ""
    s = s.replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

entries = []
skipped_rows = []

with pdfplumber.open(PDF) as pdf:
    for pageno, page in enumerate(pdf.pages):
        if pageno < 2:  # strona 1 (tytul), strona 2 (spis tresci) - pomin
            continue
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                nonempty = [(i, clean(c)) for i, c in enumerate(row) if c and clean(c)]
                if len(nonempty) < 2:
                    if nonempty:
                        skipped_rows.append({"page": pageno + 1, "cells": nonempty})
                    continue
                # Podziel na "lewa"/"prawa" strone po NAJWIEKSZEJ przerwie miedzy
                # kolejnymi niepustymi indeksami kolumn (adaptacyjne, bo liczba
                # kolumn w tabeli rozna sie miedzy stronami).
                gaps = [(nonempty[k + 1][0] - nonempty[k][0], k) for k in range(len(nonempty) - 1)]
                _, split_k = max(gaps)
                pl = " ".join(v for _, v in nonempty[: split_k + 1]).strip()
                en = " ".join(v for _, v in nonempty[split_k + 1 :]).strip()
                if pl == "MIANO POLSKIE" or en == "MIANO ANGIELSKIE":
                    continue
                if pl and en:
                    entries.append({"pl": pl, "en": en, "page": pageno + 1})
                else:
                    skipped_rows.append({"page": pageno + 1, "cells": nonempty})

print(f"Wyekstrahowano {len(entries)} par polski-angielski.")
print(f"Pominietych (jednostronnych/niejasnych) wierszy: {len(skipped_rows)}")
json.dump(entries, open("slownik_anatomiczny_pl_en_raw.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(skipped_rows[:200], open("_slownik_skipped_sample.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Przyklad pominietych (pierwsze 10):")
for r in skipped_rows[:10]:
    print(" ", r)
