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

## Ulice, dzielnice, dostępność
- Nazwy ulic i dzielnice pobiera w tle `serve.py` z OpenStreetMap (Nominatim, 1 zapytanie/s) i zapamiętuje w `geo_cache.sqlite`. Pierwsze otwarcie długiej linii wypełnia się około minuty, potem jest od razu. Możesz ustawić `SIP_CONTACT=twoj@mail` (zalecane przez Nominatim).
- Ikony wózka przy przystankach biorą się z `wheelchair_boarding` w GTFS (2 = czerwona ikona).
- Przesiadki to linie zatrzymujące się na przystankach o tej samej nazwie.
- Gdyby trasy się nie wczytywały: usuń `gtfs-cache.json` i uruchom ponownie (serwer pobierze GTFS od nowa).
