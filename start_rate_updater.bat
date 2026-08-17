@echo off
REM Turgut Sarraf - Canli kur guncelleme dongusunu baslatir.
REM Bu dosya proje klasorunun (venv ile ayni yerde) icinde kalmali.

REM NOT: Kaynaktan (dovizgrafik.com/altin) her 3 saniyede bir tam sayfa cekiliyor.
REM Art arda hata alinirsa bekleme suresi otomatik uzar (backoff), site bu
REM sirada son bilinen fiyatlari gostermeye devam eder, hicbir zaman cokmez.

cd /d "%~dp0"
call venv\Scripts\activate.bat
python manage.py update_rates_loop --interval 3

pause
