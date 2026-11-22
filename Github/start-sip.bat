@echo off
chcp 65001 >nul
rem === Uruchamia lokalny serwer (serve.py) i otwiera SIP w przegladarce ===
rem Trasy i przystanki serwer buduje z GTFS (mkuran.pl) - pierwsze uruchomienie moze potrwac okolo minuty.
rem Opcjonalnie wpisz parametry, np.:  set "QUERY=?kiosk=1&line=197&live=1&brig=12"
set "QUERY="
set "PORT=8000"
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo Nie znaleziono Pythona. Zainstaluj go z python.org ^(trasy wymagaja serve.py^).
  pause
  exit /b 1
)

start "SIP serwer" /min %PY% serve.py %PORT%
timeout /t 2 /nobreak >nul

set "URL=http://localhost:%PORT%/sip-autobus.html"
start "" "%URL%%QUERY%"
