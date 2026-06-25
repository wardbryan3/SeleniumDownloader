@echo off
REM Schedule: Thursdays @ 11:00 PM
REM Downloads all global feature sources (Melinda Myers, NW Outdoors, Whittler, Clear Out West, Weekend In The Country)

cd /d "%~dp0"
AudioDownloader.exe --download-all
