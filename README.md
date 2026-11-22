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
