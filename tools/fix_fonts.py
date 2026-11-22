#!/usr/bin/env python3
"""Naprawia czcionki Frutiger z folderu Fonts/ i zapisuje je do Fonts/pl/:
 1) dodaje poprawną tablicę Unicode (oryginał ma kodowanie symbolowe),
 2) dorabia polskie litery ą ć ę ń ś ź ż (małe i wielkie) z liter bazowych i akcentów.
Użycie: python3 tools/fix_fonts.py   (wymaga: pip install fonttools)"""
import glob, os
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.agl import toUnicode

COMBOS = {  # znak: (baza, akcent)
    "ą": ("a", "ogonek"), "ę": ("e", "ogonek"), "Ą": ("A", "ogonek"), "Ę": ("E", "ogonek"),
    "ć": ("c", "acute"), "ń": ("n", "acute"), "ś": ("s", "acute"), "ź": ("z", "acute"),
    "Ć": ("C", "acute"), "Ń": ("N", "acute"), "Ś": ("S", "acute"), "Ź": ("Z", "acute"),
    "ż": ("z", "dotaccent"), "Ż": ("Z", "dotaccent"),
}
UNI_NAME = {"ą": "aogonek", "ę": "eogonek", "Ą": "Aogonek", "Ę": "Eogonek", "ć": "cacute", "ń": "nacute", "ś": "sacute",
            "ź": "zacute", "Ć": "Cacute", "Ń": "Nacute", "Ś": "Sacute", "Ź": "Zacute", "ż": "zdotaccent", "Ż": "Zdotaccent"}

def bounds(gs, name):
    bp = BoundsPen(gs); gs[name].draw(bp); return bp.bounds

def fix(src, dst):
    f = TTFont(src); gs = f.getGlyphSet(); order = f.getGlyphOrder()
    # --- 1. cmap Unicode z nazw glifów
    cmap = {}
    for g in order:
        try:
            u = toUnicode(g)
        except Exception:
            continue
        if len(u) == 1 and g not in (".notdef", ".null"):
            cmap.setdefault(ord(u), g)
    cmap[0xA0] = "space"
    # --- 2. dorobione litery
    glyf, hmtx = f["glyf"], f["hmtx"]
    def draw_into(pen, name, dx=0, dy=0):
        gs[name].draw(TransformPen(pen, (1, 0, 0, 1, dx, dy)))
    # odniesienie: gdzie leży akcent nad e / E
    ref = {}
    for base, composed in (("e", "eacute"), ("E", "Eacute")):
        bb, cb, ab = bounds(gs, base), bounds(gs, composed), bounds(gs, "acute")
        ref[base] = (cb[3] - ab[3]) + ab[1] - bb[3]        # odstęp dolnej krawędzi akcentu od górnej krawędzi litery
    new = []
    for ch, (base, acc) in COMBOS.items():
        name = UNI_NAME[ch]
        bb, ab = bounds(gs, base), bounds(gs, acc)
        pen = TTGlyphPen(gs)
        draw_into(pen, base)
        if acc == "ogonek":
            dx = bb[2] - ab[2] + (ab[2] - ab[0]) * 0.35
            draw_into(pen, acc, dx, -ab[3] if ab[3] > 0 else 0)
        else:
            gap = ref["E" if base.isupper() else "e"]
            dx = (bb[0] + bb[2]) / 2 - (ab[0] + ab[2]) / 2
            if base.islower() is False and base in "CNSZ": dx += 0
            draw_into(pen, acc, dx, bb[3] + gap - ab[1])
        glyf[name] = pen.glyph(); new.append(name)
        hmtx[name] = (hmtx[base][0], 0)
        cmap[ord(ch)] = name
    full = list(dict.fromkeys(list(order) + new)); f.setGlyphOrder(full); glyf.glyphOrder = full
    for t in ("hdmx", "VDMX", "LTSH"):
        if t in f: del f[t]
    for g in new:                                              # przelicz lsb
        gl = glyf[g]; gl.recalcBounds(glyf); hmtx[g] = (hmtx[g][0], getattr(gl, "xMin", 0))
    # --- 3. nowa tablica cmap (Unicode BMP)
    ct = newTable("cmap"); ct.tableVersion = 0
    st = CmapSubtable.newSubtable(4); st.platformID, st.platEncID, st.language = 3, 1, 0; st.cmap = cmap
    ct.tables = [st]; f["cmap"] = ct
    f["maxp"].numGlyphs = len(f.getGlyphOrder())
    f["post"].formatType = 2.0
    f.save(dst)

if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Fonts")
    os.makedirs(os.path.join(root, "pl"), exist_ok=True)
    for src in sorted(glob.glob(os.path.join(root, "Frutiger_*.ttf"))):
        fix(src, os.path.join(root, "pl", os.path.basename(src))); print("OK", os.path.basename(src))
