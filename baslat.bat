@echo off
REM Turgut Sarraf - TEK TIKLA TEST BASLATICI
REM Bu dosyaya cift tiklaman yeterli. Hicbir sey elle yazmana gerek yok.
REM
REM Ne yapiyor:
REM   1) Kur guncelleme dongusunu ayri bir pencerede baslatir (3 saniyede bir).
REM   2) Django gelistirme sunucusunu ayri bir pencerede baslatir.
REM   3) Birkac saniye bekleyip siteyi tarayicinda otomatik acar.
REM
REM Kapatmak icin: acilan iki siyah pencereyi kapat (ya da her birinde Ctrl+C).

cd /d "%~dp0"

echo Turgut Sarraf baslatiliyor...
echo.

start "Turgut Sarraf - Kur Guncelleme" cmd /k "call venv\Scripts\activate.bat && python manage.py update_rates_loop --interval 3"

start "Turgut Sarraf - Sunucu" cmd /k "call venv\Scripts\activate.bat && python manage.py runserver"

echo Sunucunun ayaga kalkmasi bekleniyor...
timeout /t 5 /nobreak >nul

start "" "http://127.0.0.1:8000/"

echo.
echo Hazir! Site tarayicida acildi: http://127.0.0.1:8000/
echo Piyasa Durumu: http://127.0.0.1:8000/piyasa-durumu/
echo Panel girisi:  http://127.0.0.1:8000/panel/giris/
echo.
echo Bu pencereyi kapatabilirsin, diger iki pencere (Kur Guncelleme ve Sunucu)
echo acik kaldigi surece site calismaya devam eder.
pause
