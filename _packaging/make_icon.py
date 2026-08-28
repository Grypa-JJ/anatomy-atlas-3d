#!/usr/bin/env python3
"""Generuje ikone atlasu 3D -> _packaging/shared/icons/app-icon-1024.png (+ 512, 192).
Prosta, czytelna w malych rozmiarach: figura stojaca (jak emoji w atlas.html) na fioletowym gradiencie.
Uruchom raz; potem `npx tauri icon` w _packaging/tauri robi reszte (.ico/.icns/pngs)."""
from PIL import Image, ImageDraw
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "shared", "icons")
os.makedirs(OUT, exist_ok=True)

S = 1024

def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

TOP = (0x7C, 0x6B, 0xF0)     # jasny fiolet (#6c5ce7 rozjasniony)
BOT = (0x2A, 0x25, 0x50)     # ciemny fiolet (jak tlo atlas.html)

img = Image.new("RGB", (S, S), TOP)
d = ImageDraw.Draw(img)
for y in range(S):
    d.line([(0, y), (S, y)], fill=lerp(TOP, BOT, y / S))

# miekki blask za figura
glow = Image.new("L", (S, S), 0)
gd = ImageDraw.Draw(glow)
gd.ellipse([S*0.18, S*0.10, S*0.82, S*0.92], fill=70)
glow = glow.resize((S//4, S//4)).resize((S, S))  # tanie rozmycie
white_layer = Image.new("RGB", (S, S), (255, 255, 255))
img = Image.composite(white_layer, img, glow.point(lambda p: p // 3))

d = ImageDraw.Draw(img)
W = (255, 255, 255)
cx = S * 0.5

# glowa
d.ellipse([cx - S*0.085, S*0.16, cx + S*0.085, S*0.16 + S*0.17], fill=W)
# tulow (trapez)
d.polygon([(cx - S*0.13, S*0.37), (cx + S*0.13, S*0.37),
           (cx + S*0.10, S*0.62), (cx - S*0.10, S*0.62)], fill=W)
# ramiona
d.polygon([(cx - S*0.13, S*0.375), (cx - S*0.30, S*0.50), (cx - S*0.25, S*0.545),
           (cx - S*0.095, S*0.44)], fill=W)
d.polygon([(cx + S*0.13, S*0.375), (cx + S*0.30, S*0.50), (cx + S*0.25, S*0.545),
           (cx + S*0.095, S*0.44)], fill=W)
# nogi
d.polygon([(cx - S*0.10, S*0.61), (cx - S*0.005, S*0.61), (cx - S*0.03, S*0.88),
           (cx - S*0.11, S*0.88)], fill=W)
d.polygon([(cx + S*0.10, S*0.61), (cx + S*0.005, S*0.61), (cx + S*0.03, S*0.88),
           (cx + S*0.11, S*0.88)], fill=W)

for name, size in [("app-icon-1024.png", 1024), ("icon-512.png", 512), ("icon-192.png", 192)]:
    img.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name))
    print("  ->", os.path.join("shared", "icons", name))

# kopia zrodla dla tauri
img.save(os.path.join(HERE, "tauri", "app-icon.png"))
print("  -> tauri/app-icon.png (zrodlo dla `npx tauri icon`)")
