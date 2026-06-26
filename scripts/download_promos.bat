@echo off
REM Schedule: Tuesdays @ 11:00 PM
REM Downloads promos only (Northwest Outdoors promo)

cd /d "%~dp0"
AudioDownloader.exe --source "Download Promo"
