// Cloudflare Worker: proxy CORS dla API Warszawy (tryb na żywo na GitHub Pages).
// Ustaw w stronie: ?api=https://TWOJ-WORKER.workers.dev/api/action/
// Przekazuje tylko ścieżki /api/... do dane.um.warszawa.pl razem z nagłówkiem Authorization.
const UP = ["https://dane.um.warszawa.pl", "https://api.um.warszawa.pl"];
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Authorization, Content-Type", "Access-Control-Allow-Methods": "GET, POST, OPTIONS" };
export default {
  async fetch(req) {
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
    const u = new URL(req.url);
    if (!u.pathname.startsWith("/api/")) return new Response("Nie znaleziono", { status: 404, headers: CORS });
    const body = req.method === "POST" ? await req.arrayBuffer() : undefined;
    let last;
    for (const up of UP) {
      const h = { "User-Agent": "sip-autobus" };
      for (const k of ["Authorization", "Content-Type"]) if (req.headers.get(k)) h[k] = req.headers.get(k);
      const r = await fetch(up + u.pathname + u.search, { method: req.method, headers: h, body });
      if ([404, 502, 503].includes(r.status)) { last = r; continue; }
      return new Response(r.body, { status: r.status, headers: { ...CORS, "Content-Type": r.headers.get("Content-Type") || "application/json" } });
    }
    return new Response(last ? last.body : "Błąd", { status: last ? last.status : 502, headers: CORS });
  }
};
