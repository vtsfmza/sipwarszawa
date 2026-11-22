# SIP Autobus

Wyświetlacz informacji pasażerskiej (1920×540) wzorowany na warszawskich autobusach.

## Uruchomienie
Strony nie da się otworzyć bez serwera: `localhost:8000` działa tylko wtedy, gdy `start-sip.bat` (lub `python serve.py`) jest uruchomiony na Twoim komputerze. Okno serwera musi zostać otwarte.

1. Zainstaluj Pythona 3.
2. Uruchom `start-sip.bat` (albo `python serve.py` i otwórz http://localhost:8000/sip-autobus.html).
3. Kliknij „Pobierz trasy” – serwer buduje trasy i przystanki z GTFS (mkuran.pl/gtfs/warsaw.zip); pierwsze pobranie trwa ok. minuty, potem cache 24 h (`gtfs-cache.json`).
4. Tryb na żywo wymaga klucza API z dane.um.warszawa.pl (wklejany w kroku 1).

Stare API `api.um.warszawa.pl` jest wyłączone; nazw ulic nie ma w GTFS, więc pasek ulic jest pusty.

## Kolory linii
Kolor numeru, trasy, kropek, strzałki i znacznika autobusu zależy od typu linii: zwykła/okresowa/specjalna – czarny, przyspieszona – czerwony, strefowa – zielony, nocna – fioletowy.

## GitHub Pages
Strona publikuje się sama (workflow `.github/workflows/pages.yml`, przy każdym pushu i codziennie o 3:17 UTC, wtedy też odświeżają się trasy z GTFS).
Adres: https://vtsfmza.github.io/sipwarszawa/
Tryb symulacji działa od razu. Tryb „na żywo” potrzebuje proxy CORS: wgraj `worker.js` jako Cloudflare Worker i otwórz stronę z `?api=https://TWOJ-WORKER.workers.dev/api/action/` (możesz też wpisać adres w `CONFIG.api`).
