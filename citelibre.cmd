@echo off
rem CiteLibre demo launcher for Windows: double-click it to start the RendezVous demo,
rem or run "citelibre.cmd help" in a terminal. The logic is in citelibre.ps1.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0citelibre.ps1" %*
set CITELIBRE_EXIT=%ERRORLEVEL%
rem Keep the window open when started by a double-click
if "%~1"=="" pause
exit /b %CITELIBRE_EXIT%
