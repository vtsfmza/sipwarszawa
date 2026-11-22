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
Trasa, kropki, strzałka i nazwa przystanku są fioletowe (jak na prawdziwych wyświetlaczach). Od typu linii zależy kolor numeru: zwykła/okresowa – czarny, przyspieszona – czerwony, strefowa – zielony, nocna – biały.

## Ulice, dzielnice, dostępność
- Nazwy ulic i dzielnice pobiera w tle `serve.py` z OpenStreetMap (Nominatim, 1 zapytanie/s) i zapamiętuje w `geo_cache.sqlite`. Pierwsze otwarcie długiej linii wypełnia się około minuty, potem jest od razu. Możesz ustawić `SIP_CONTACT=twoj@mail` (zalecane przez Nominatim).
- Ikony wózka przy przystankach biorą się z `wheelchair_boarding` w GTFS (2 = czerwona ikona).
- Przesiadki to linie zatrzymujące się na przystankach o tej samej nazwie.
- Gdyby trasy się nie wczytywały: usuń `gtfs-cache.json` i uruchom ponownie (serwer pobierze GTFS od nowa).

## Zapowiedzi głosowe
Zaznacz „Zapowiedzi głosowe” (albo otwórz stronę z `?voice=1`). Przy każdym kroku odtwarza się: gong, „Następny przystanek” + nazwa (oraz „na żądanie” i przesiadka do M1/M2), a na przystanku: gong, „Przystanek” + nazwa. Na pierwszym przystanku dodatkowo „Linia … kierunek …”, a na ostatnim „Przystanek końcowy, prosimy o opuszczenie pojazdu”.
Nagrania pochodzą z banku `gtfscc.github.io/zapowiedzi*` (katalog w `zapowiedzi.json`, budowany skryptem `tools/build_zapowiedzi.py` z pliku HTML z bankiem). Przystanki bez nagrania są pomijane (nazwa trafia do konsoli przeglądarki).
Tryb kiosku: Chrome blokuje dźwięk bez kliknięcia, więc uruchom go z `--autoplay-policy=no-user-gesture-required`.

## SIP Metro
`sip-metro.html` to osobny ekran w stylu wagonu warszawskiego metra (1280×800, tło `img/metro-bg.png`). Działa bez serwera: wystarczy otworzyć plik (albo przez `serve.py`: http://localhost:8000/sip-metro.html).
Parametry: `?line=M1|M2`, `dir=1|-1` (kierunek), `idx=N` (stacja startowa), `auto=0` (bez automatycznego przesuwania), `kiosk=1` (pełny ekran bez panelu), `en=0` (bez zmiany etykiety na angielską co 5 s).
Dane M1 (stacje, minuty, dzielnice) pochodzą z ekranu w wagonie; **dane M2 są przybliżone** (czasy i dzielnice do sprawdzenia). Dane stacji są na początku skryptu w obiekcie `LINES`. Minuty liczone są od bieżącej pozycji; stacje miniętę są szare. Przesiadka M1↔M2 na Świętokrzyskiej jest oznaczona plakietką. Zapowiedzi głosowych w metrze nie ma.
