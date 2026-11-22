@echo off
chcp 65001 >nul
rem === Uruchamia lokalny serwer (serve.py) i otwiera SIP w przegladarce ===
rem Trasy i przystanki serwer buduje z GTFS (mkuran.pl) - pierwsze pobranie moze potrwac okolo minuty.
rem Opcjonalnie wpisz parametry, np.:  set "QUERY=?kiosk=1&line=197&live=1&brig=12"
set "QUERY="
set "PORT=8000"
cd /d "%~dp0"

set "PY="
py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys" >nul 2>nul && set "PY=python"
if not defined PY (
  echo Nie znaleziono dzialajacego Pythona 3. Zainstaluj go z python.org
  echo ^(zaznacz "Add python.exe to PATH"^) i uruchom ten plik ponownie.
  pause
  exit /b 1
)

rem Okno serwera zostaje otwarte (cmd /k), zeby bylo widac ewentualny blad. NIE zamykaj go.
start "SIP serwer" cmd /k "%PY% serve.py %PORT%"

rem czekaj az serwer zacznie odpowiadac (max ok. 20 s)
set /a N=0
:wait
set /a N+=1
if %N% gtr 20 goto open
curl -s -o nul "http://localhost:%PORT%/" >nul 2>nul && goto open
timeout /t 1 /nobreak >nul
goto wait

:open
start "" "http://localhost:%PORT%/sip-autobus.html%QUERY%"
