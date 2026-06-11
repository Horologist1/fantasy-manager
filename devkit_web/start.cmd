@echo off
REM Fantasy Manager Devkit launcher (Windows).
REM Double-click this file. Starts a local server and opens the default browser.
REM Close the window or press Ctrl+C to stop.

setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js is required but was not found on PATH.
  echo Install Node 18+ from https://nodejs.org/ and try again.
  pause
  exit /b 1
)
node serve.mjs
pause
