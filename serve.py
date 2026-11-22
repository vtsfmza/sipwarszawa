#!/usr/bin/env python3
"""Lokalny serwer dla sip-autobus.html.
Serwuje plik z tego katalogu i przekazuje zapytania /api/action/... (GET i POST, razem z nagłówkiem
Authorization) do API m.st. Warszawy, dzięki czemu przeglądarka nie blokuje ich przez CORS.

  py serve.py            # port 8000 (Windows)   |   python3 serve.py
  py serve.py 8080       # inny port

Potem otwórz:  http://localhost:8000/sip-autobus.html
Kiosk:         http://localhost:8000/sip-autobus.html?kiosk=1&line=197&live=1&brig=12
Trasy i przystanki serwer buduje z GTFS (mkuran.pl/gtfs/warsaw.zip), bo stare API tras (api.um.warszawa.pl)
zostalo wylaczone. Wynik jest cache'owany w pliku gtfs-cache.json (odswiezany co 24 h).
"""
import os, sys, io, csv, json, time, zipfile, tempfile, threading, sqlite3, urllib.parse, urllib.request, urllib.error
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

UPSTREAMS = [u.strip().rstrip("/") for u in os.environ.get(
    "SIP_UPSTREAM", "https://dane.um.warszawa.pl").split(",") if u.strip()]


# ---------- trasy z GTFS (zastepuja wylaczone public_transport_routes) ----------
GTFS_URL = os.environ.get("SIP_GTFS", "https://mkuran.pl/gtfs/warsaw.zip")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gtfs-cache.json")
CACHE_TTL = 24 * 3600
MAX_VARIANTS = 6          # najczestsze sekwencje przystankow na kierunek
_lock = threading.Lock()

def _rows(zf, name):
    with zf.open(name) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", newline=""))

def build_routes(zip_path):
    """Z GTFS robi {stops:{id:[nazwa,lat,lon]}, routes:{linia:[{code,dir,headsign,stops:[[id,typ],..]}]}}."""
    with zipfile.ZipFile(zip_path) as zf:
        route_name, ltype = {}, {}
        TYPE_MAP = {"0": "tram", "900": "tram", "1": "metro", "400": "metro", "2": "bus", "3": "bus", "11": "bus", "700": "bus", "800": "bus"}
        for r in _rows(zf, "routes.txt"):
            nm = r.get("route_short_name") or r["route_id"]
            route_name[r["route_id"]] = nm
            ltype[nm] = TYPE_MAP.get((r.get("route_type") or "").strip(), "bus")
        trips = {}
        for t in _rows(zf, "trips.txt"):
            trips[t["trip_id"]] = (route_name.get(t["route_id"], t["route_id"]), t.get("direction_id") or "0",
                                   t.get("trip_headsign") or "")
        stops = {}
        for s in _rows(zf, "stops.txt"):
            try:
                stops[s["stop_id"]] = [s.get("stop_name", ""), round(float(s["stop_lat"]), 6), round(float(s["stop_lon"]), 6), s.get("wheelchair_boarding", "")]
            except (ValueError, KeyError):
                pass
        seqs = {}                         # (linia, kierunek) -> {(sekwencja): [licznik, headsign]}
        cur, buf = None, []

        def flush():
            if cur is None or cur not in trips or not buf:
                return
            buf.sort(key=lambda x: x[0])
            sig = tuple((sid, "2" if ond else "1") for _, sid, ond in buf)
            line, d, head = trips[cur]
            e = seqs.setdefault((line, d), {}).setdefault(sig, [0, head])
            e[0] += 1

        for r in _rows(zf, "stop_times.txt"):
            if r["trip_id"] != cur:
                flush(); cur, buf = r["trip_id"], []
            try:
                seq = int(r["stop_sequence"])
            except ValueError:
                continue
            buf.append((seq, r["stop_id"], (r.get("pickup_type") == "3" or r.get("drop_off_type") == "3")))
        flush()
    routes, used = {}, set()
    for (line, d), vs in seqs.items():
        best = sorted(vs.items(), key=lambda kv: -kv[1][0])[:MAX_VARIANTS]
        for n, (sig, (cnt, head)) in enumerate(best, 1):
            routes.setdefault(line, []).append({"code": "%s%d" % ("A" if d == "0" else "B", n), "dir": int(d),
                                                "headsign": head, "stops": [list(x) for x in sig]})
            used.update(x[0] for x in sig)
    for l in routes:
        routes[l].sort(key=lambda v: v["code"])
    return {"built": int(time.time()), "types": ltype, "stops": {k: v for k, v in stops.items() if k in used}, "routes": routes}

def get_routes_json():
    with _lock:
        try:
            if time.time() - os.path.getmtime(CACHE) < CACHE_TTL:
                with open(CACHE, "rb") as f:
                    data = f.read()
                if b'"types"' in data[:200]:        # starszy cache bez typów linii: zbuduj od nowa
                    return data
        except OSError:
            pass
        print("Pobieram GTFS z %s ..." % GTFS_URL, flush=True)
        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        try:
            req = urllib.request.Request(GTFS_URL, headers={"User-Agent": "sip-autobus"})
            with urllib.request.urlopen(req, timeout=120) as r:
                while True:
                    ch = r.read(1 << 20)
                    if not ch:
                        break
                    tmp.write(ch)
            tmp.close()
            data = json.dumps(build_routes(tmp.name), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            with open(CACHE, "wb") as f:
                f.write(data)
            print("GTFS gotowy (%d KB)." % (len(data) // 1024), flush=True)
            return data
        except Exception as e:
            try:
                with open(CACHE, "rb") as f:        # przeterminowany cache lepszy niz nic
                    print("GTFS: blad pobierania (%s), uzywam starego cache." % e, flush=True)
                    return f.read()
            except OSError:
                raise e
        finally:
            try:
                tmp.close(); os.unlink(tmp.name)
            except OSError:
                pass

# ---------- ulice i dzielnice z OpenStreetMap (Nominatim), cache w geo_cache.sqlite ----------
# Nominatim pozwala na max 1 zapytanie/s i wymaga rozpoznawalnego User-Agent (ustaw SIP_CONTACT=twoj@mail).
GEOCODER = os.environ.get("SIP_GEOCODER", "https://nominatim.openstreetmap.org/reverse")
GEO_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo_cache.sqlite")
DISTRICT_KEYS = ("suburb", "city_district", "borough", "quarter", "neighbourhood")
STREET_KEYS = ("road", "pedestrian", "footway", "path", "cycleway")
_geo_queue, _geo_lock = [], threading.Lock()
_geo_ids = set()

def _db():
    c = sqlite3.connect(GEO_DB, timeout=30)
    c.execute("CREATE TABLE IF NOT EXISTS geo (id TEXT PRIMARY KEY, street TEXT, district TEXT)")
    return c

def _stop_coords():
    try:
        with open(CACHE, "rb") as f:
            return json.loads(f.read().decode("utf-8")).get("stops", {})
    except (OSError, ValueError):
        return {}

def geo_lookup(ids):
    """Zwraca ({id: {street, district}}, liczba_oczekujacych); brakujace przystanki trafiaja do kolejki."""
    out, pending = {}, 0
    db = _db()
    try:
        coords = None
        for sid in ids:
            row = db.execute("SELECT street, district FROM geo WHERE id=?", (sid,)).fetchone()
            if row:
                out[sid] = {"street": row[0] or "", "district": row[1] or ""}
                continue
            pending += 1
            with _geo_lock:
                if sid not in _geo_ids:
                    if coords is None:
                        coords = _stop_coords()
                    if sid in coords:
                        _geo_ids.add(sid); _geo_queue.append((sid, coords[sid][1], coords[sid][2]))
    finally:
        db.close()
    return out, pending

def _geo_worker():
    contact = os.environ.get("SIP_CONTACT", "")
    ua = "sip-autobus/1.0 (%s)" % (contact or "https://github.com/vtsfmza/sipwarszawa")
    while True:
        with _geo_lock:
            item = _geo_queue.pop(0) if _geo_queue else None
        if not item:
            time.sleep(1); continue
        sid, lat, lon = item
        street = district = ""
        ok = True
        try:
            q = urllib.parse.urlencode({"format": "jsonv2", "lat": lat, "lon": lon, "zoom": 18, "addressdetails": 1, "accept-language": "pl"})
            sep = "&" if "?" in GEOCODER else "?"
            with urllib.request.urlopen(urllib.request.Request(GEOCODER + sep + q, headers={"User-Agent": ua}), timeout=20) as r:
                a = json.loads(r.read().decode("utf-8")).get("address", {})
            street = next((a[k] for k in STREET_KEYS if a.get(k)), "")
            district = next((a[k] for k in DISTRICT_KEYS if a.get(k)), "")
        except Exception as e:
            ok = False
            print("Nominatim: %s (przystanek %s) - sprobuje ponownie pozniej" % (e, sid), flush=True)
        if ok:
            db = _db()
            try:
                db.execute("INSERT OR REPLACE INTO geo VALUES (?,?,?)", (sid, street, district)); db.commit()
            finally:
                db.close()
        with _geo_lock:
            _geo_ids.discard(sid)
        time.sleep(1.1 if ok else 10)

class Handler(SimpleHTTPRequestHandler):
    def _proxy(self, method):
        body = None
        if method == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n) if n else b""
        last = None
        for up in UPSTREAMS:
            headers = {"User-Agent": "sip-autobus"}
            for h in ("Authorization", "Content-Type"):
                if self.headers.get(h):
                    headers[h] = self.headers[h]
            try:
                req = urllib.request.Request(up + self.path, data=body, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=60) as r:
                    return self._send(r.status, r.read(), r.headers.get("Content-Type", "application/json"))
            except urllib.error.HTTPError as e:
                data = e.read()
                if e.code in (404, 502, 503):      # spróbuj następnego adresu
                    last = e
                    continue
                return self._send(e.code, data, e.headers.get("Content-Type", "application/json"))
            except Exception as e:
                last = e
        self.send_error(502, "Nie udalo sie polaczyc z API: %s" % last)

    def _send(self, code, data, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/geo":
            ids = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("ids", [""])[0].split(",")
            geo, pending = geo_lookup([i for i in ids if i][:200])
            return self._send(200, json.dumps({"geo": geo, "pending": pending}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
        if self.path.startswith("/api/"):
            return self._proxy("GET")
        if self.path.split("?")[0] == "/gtfs/routes.json":
            try:
                return self._send(200, get_routes_json(), "application/json; charset=utf-8")
            except Exception as e:
                return self._send(502, json.dumps({"error": "Nie udalo sie pobrac GTFS: %s" % e}).encode("utf-8"), "application/json")
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            return self._proxy("POST")
        self.send_error(405)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def log_message(self, fmt, *args):  # bez klucza API w logach
        print("%s %s" % (self.address_string(), (fmt % args).split("?")[0]))

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print("SIP: http://localhost:%d/sip-autobus.html   (API przez: %s)" % (port, ", ".join(UPSTREAMS)))
    threading.Thread(target=_geo_worker, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
