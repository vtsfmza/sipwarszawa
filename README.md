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
- Ikony wózka przy przystankach biorą się z `wheelchair_boarding` w GTFS: 2 (i `p`) = niebieska ikona „utrudniony dostęp”. Czerwonej „niedostępny” nie rysujemy, bo dane nie mają takiego stanu; w legendzie na dole ekranu są obie.
- Przesiadki to linie zatrzymujące się na przystankach o tej samej nazwie.
- Gdyby trasy się nie wczytywały: usuń `gtfs-cache.json` i uruchom ponownie (serwer pobierze GTFS od nowa).

## Strefy biletowe i długie trasy
- Strefy czytane są z kolumny `zone_id` w GTFS (1, 2 oraz 1+2 na granicy; po zmianie `serve.py` usuń `gtfs-cache.json`, żeby cache zbudował się z kolumną stref). Tylko linie, które wyjeżdżają poza strefę 1, mają pasek „strefa 2” / „strefa 1” pod trasą oraz czerwoną etykietę „granica strefy biletowej” przy przystanku granicznym (ta sama etykieta pojawia się w nagłówku, gdy to bieżący przystanek, a nazwa granicy jest też w panelu pod ekranem). Linie tylko w strefie 1 nie mają żadnych oznaczeń stref.
- Zbyt długa trasa: pierwszy przystanek zostaje po lewej, a przejechany odcinek zwija się w szary pasek „>>>” zawsze z tyłu. Z przodu (przed przystankiem końcowym) takiego paska nie ma: gdy reszta trasy się nie mieści, zmniejsza się tylko rozstaw przystanków. Gdy cała trasa mieści się bez nakładania, pasek znika.
- Minuty na schemacie liczone są od bieżącego przystanku: aktualny ma 0', kolejne rosną, a przystanki miniete nie mają już minut.
- Przesiadki w nagłówku: najpierw metro, potem tramwaje, na końcu autobusy. Łącznie do 12 linii, ale każda grupa ma gwarantowane miejsce (min. 4), więc tramwaje nie wypychają autobusów.
- Czerwony pasek pokazuje wyłącznie miasto (poza Warszawą) albo dzielnicę Warszawy, nic innego.
- Zbyt długa nazwa bieżącego przystanku w nagłówku ma stałą wielkość pisma i przesuwa się od prawej do lewej. Tak samo nazwa przy przystanku na schemacie: nic się nie skraca ani nie ściska, a przesuwają się od prawej do lewej tylko te nazwy, które się nie mieszczą.
- Przedrostek miejscowości jest obcinany tylko przy spacji („Ząbki Maczka” → „Maczka”); nazwy z łącznikiem („Sowia Wola-Szkoła”) zostają w całości.

## Zapowiedzi głosowe
Zaznacz „Zapowiedzi głosowe” (albo otwórz stronę z `?voice=1`). Przy każdym kroku odtwarza się: gong, „Następny przystanek” + nazwa (oraz „na żądanie”), a na przystanku: gong, „Przystanek” + nazwa. Na pierwszym przystanku dodatkowo „Linia … kierunek …”, a na ostatnim „Przystanek końcowy, prosimy o opuszczenie pojazdu”.
Nagrania pochodzą z banku `gtfscc.github.io/zapowiedzi*` (katalog w `zapowiedzi.json`, budowany skryptem `tools/build_zapowiedzi.py` z pliku HTML z bankiem). Przystanki bez nagrania są pomijane (nazwa trafia do konsoli przeglądarki).
Tryb kiosku: Chrome blokuje dźwięk bez kliknięcia, więc uruchom go z `--autoplay-policy=no-user-gesture-required`.

## SIP Metro
`sip-metro.html` to osobny ekran w stylu wagonu warszawskiego metra (1280×800, tło `img/metro-bg.png`). Działa bez serwera: wystarczy otworzyć plik (albo przez `serve.py`: http://localhost:8000/sip-metro.html).
Parametry: `?line=M1|M2`, `dir=1|-1` (kierunek), `idx=N` (stacja startowa), `auto=0` (bez automatycznego przesuwania), `kiosk=1` (pełny ekran bez panelu), `en=0` (bez zmiany etykiety na angielską co 5 s).
Dane M1 (stacje, minuty, dzielnice) pochodzą z ekranu w wagonie; **dane M2 są przybliżone** (czasy i dzielnice do sprawdzenia). Dane stacji są na początku skryptu w obiekcie `LINES`. Minuty liczone są od bieżącej pozycji; stacje miniętę są szare. Przesiadka M1↔M2 na Świętokrzyskiej jest oznaczona plakietką. Zapowiedzi głosowych w metrze nie ma.

## Czcionki
Oryginalne pliki Frutiger w `Fonts/` mają zepsute kodowanie (symbolowe) i nie zawierają polskich liter ą ć ę ń ś ź ż, przez co przeglądarka podstawiała inną czcionkę w środku słowa. Skrypt `tools/fix_fonts.py` (wymaga `pip install fonttools`) tworzy poprawione kopie w `Fonts/pl/` z dorobionymi polskimi literami, a strona używa właśnie ich.

## Tablica boczna i podsufitka (połączone z SIP)
`sip-autobus.html` publikuje w `localStorage` ("sip_state") linię, cel (ostatni przystanek), listę **ulic** trasy (te same, które są na pasku ulic) oraz bieżący przystanek. Strony poniżej odbierają to na żywo przez zdarzenie `storage`, więc muszą być otwarte **w tej samej przeglądarce i pod tym samym adresem** co SIP (np. http://localhost:8000). Przycisk „Tablica boczna ↗” w SIP otwiera pierwszą z nich.

- **`sip-boczny.html`**: matryca LED 192×24. Numer linii dużą czcionką 24×12, cel czcionką 9×8, na dole przewijane `TRASA: ULICA-ULICA-…` (ulice, nie przystanki; „Aleja/Aleje” skracane do „Al.”, „Plac” do „Pl.”). Opcje w adresie: `?kiosk=1`, `link=0&line=256&dest=...&route=Ulica1,Ulica2`, `speed=14|22|34`. Znaki z arkuszy czcionek są w `led-font.js`, generowanym przez `tools/build_led_font.py <arkusz 9x8> <arkusz 24x12>`. W arkuszu brakuje V, X, Q i `/`, więc są dorysowane w skrypcie.
- **`sip-podsufitka.html`**: ekran 1280×720 pod sufitem (numer, cel i trasa w ulicach przewijane, pod spodem bieżący przystanek i pasek postępu; w postoju zegar). Bez SIP działa na własnych danych (`?kiosk=1`, `view=clock`, `short=1`).

Ulice pochodzą z `api/geo` (serve.py), więc bez serwera wiersz TRASA jest pusty.
