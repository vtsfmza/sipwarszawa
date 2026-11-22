#!/usr/bin/env python3
"""Buduje led-font.js (czcionki matrycowe tablicy bocznej) z arkuszy-obrazków z kropkami.

Użycie:  python tools/build_led_font.py arkusz_9x8.jpg arkusz_24x12.jpg > led-font.js

Arkusz 9x8  : wiersz liter  "A Ą B C Ć D E Ę F G H I J K L Ł M N O Ó P R S Ś T U W Y Z Ź Ż Ń"
              wiersz znaków "0-9 . , : - + ( ) [ ] ' \""
Arkusz 24x12: wiersz cyfr   "1 2 3 4 5 6 7 8 9 0"
              wiersz liter  "A B C N P R T - E"
Kropki leżą na siatce co 10 px; faza siatki jest wykrywana automatycznie.
Brakujące w arkuszu V, X, Q i / są dorysowane tutaj w stylu czcionki.
"""
import sys, json
import numpy as np
from PIL import Image

PITCH = 10


def grid(path):
    a = np.asarray(Image.open(path).convert("L")).astype(float)
    H, W = a.shape

    def phase(axis):
        prof = a.mean(axis=axis)
        return int(np.argmax([prof[o::PITCH].mean() for o in range(PITCH)]))
    ox, oy = phase(0), phase(1)
    return np.array([[a[y, x] > 110 for x in range(ox, W, PITCH)] for y in range(oy, H, PITCH)], dtype=np.uint8)


def runs(band):
    ink, out, s = band.any(axis=0), [], None
    for x, v in enumerate(ink):
        if v and s is None:
            s = x
        if not v and s is not None:
            out.append((s, x - 1)); s = None
    if s is not None:
        out.append((s, len(ink) - 1))
    return out


def rows_to_ints(band, a, b):
    w = b - a + 1
    return [w] + [int("".join("1" if v else "0" for v in r[a:b + 1]), 2) for r in band]


def glyph_from(txt):
    rows = [r for r in txt.strip("\n").split("\n")]
    w = len(rows[0])
    return [w] + [int(r.replace("#", "1").replace(".", "0"), 2) for r in rows]


def main(p_small, p_big):
    gs, gb = grid(p_small), grid(p_big)
    small, big = {}, {}

    # --- 9x8 (12 wierszy na znak: kreska nad, 9 korpus, 2 ogonek) ---
    letters = list("AĄBCĆDEĘFGHIJKLŁMNOÓPRSŚTUWYZŹŻŃ")
    r1 = runs(gs[0:12])
    assert len(r1) == len(letters), (len(r1), len(letters))
    for ch, (a, b) in zip(letters, r1):
        small[ch] = rows_to_ints(gs[0:12], a, b)
    digits = list("0123456789")
    punct = list(".,:-+()[]'\"")
    band = gs[13:25]
    r2 = [r for r in runs(band) if r[0] < 200]          # odrzuć podpis autora na dole arkusza
    assert len(r2) == len(digits) + len(punct) - 1 + 1 or True
    seq = digits + punct
    # ostatni run (6 szer.) to dwa apostrofy = cudzysłów
    mapping = digits + list(".,:-+()[]'") + ['"']
    assert len(r2) == len(mapping), (len(r2), len(mapping))
    for ch, (a, b) in zip(mapping, r2):
        small[ch] = rows_to_ints(band, a, b)

    # --- dorysowane: V X Q / (korpus w wierszach 1..9, jak w oryginale) ---
    def body(lines, tail=()):
        rows = ["." * len(lines[0])] + list(lines) + list(tail)
        while len(rows) < 12:
            rows.append("." * len(lines[0]))
        return glyph_from("\n".join(rows))
    small["V"] = body(["##....##"] * 5 + [".##..##.", ".##..##.", "..####..", "...##..."])
    small["X"] = body(["##....##", ".##..##.", "..####..", "...##...", "...##...", "...##...", "..####..", ".##..##.", "##....##"])
    small["Q"] = body([".######.", "########", "##....##", "##....##", "##....##", "##..#.##", "##...###", "########", ".#######"], ["......##"])
    small["/"] = body(["....##", "....##", "...##.", "...##.", "..##..", "..##..", ".##...", ".##...", "##...."])

    # --- 24x12 (24 wiersze) ---
    d_order = list("1234567890")
    b1 = gb[1:25]
    rr1 = runs(b1)
    assert len(rr1) == len(d_order), len(rr1)
    for ch, (a, b) in zip(d_order, rr1):
        big[ch] = rows_to_ints(b1, a, b)
    l_order = list("ABCNPRT-E")
    b2 = gb[27:51]
    rr2 = [r for r in runs(b2) if r[0] < 200]
    assert len(rr2) == len(l_order), len(rr2)
    for ch, (a, b) in zip(l_order, rr2):
        big[ch] = rows_to_ints(b2, a, b)

    out = "// Wygenerowane przez tools/build_led_font.py z arkuszy czcionek matrycowych. Nie edytuj ręcznie.\n"
    out += "// Glif: [szerokość, wiersz0, wiersz1, ...]; bit najstarszy = lewa kolumna.\n"
    out += "var LEDFONT = " + json.dumps({"small": {"h": 12, "glyphs": small}, "big": {"h": 24, "glyphs": big}},
                                          ensure_ascii=False, separators=(",", ":")) + ";\n"
    sys.stdout.write(out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
