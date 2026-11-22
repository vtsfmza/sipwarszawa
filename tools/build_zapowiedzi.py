#!/usr/bin/env python3
"""Buduje zapowiedzi.json z pliku HTML z bankiem zapowiedzi (select #soundSelect1 = przystanki, #soundSelect2 = zapowiedzi).
Użycie:  python3 tools/build_zapowiedzi.py zapowiedzi_polaczone.html zapowiedzi.json"""
import re, sys, json, html
src = open(sys.argv[1], encoding="utf-8").read()
def block(sel_id):
    m = re.search(r'<select id="%s".*?</select>' % sel_id, src, re.S)
    body = re.sub(r'<!--.*?-->', '', m.group(0), flags=re.S)
    return [(html.unescape(v), html.unescape(t).strip()) for v, t in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)', body)]
out = {"base": {"1": "https://gtfscc.github.io/zapowiedzi/", "2": "https://gtfscc.github.io/zapowiedzi-2/",
                "3": "https://gtfscc.github.io/zapowiedzi-3/", "4": "https://gtfscc.github.io/zapowiedzi-4/"},
       "stops": {}, "sounds": {}}
for v, t in block("soundSelect1"):
    out["stops"].setdefault(t.lower(), v)
for v, t in block("soundSelect2"):
    out["sounds"].setdefault(t, v)
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(out["stops"]), "przystanków,", len(out["sounds"]), "zapowiedzi")
