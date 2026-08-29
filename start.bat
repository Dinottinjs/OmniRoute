@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title OmniRoute (AetherNet) - Installer ^& Launcher
echo ========================================================
echo        OmniRoute (AetherNet) Multi-Tool 
echo        (c) 2026 Maximilian Holzer
echo ========================================================
echo.

set "TARGET_DIR=OmniRoute_Stable_Build"

IF EXIST "%TARGET_DIR%" GOTO RUN_APP

echo [Info] Ordner "%TARGET_DIR%" nicht gefunden.
echo [Info] Lade OmniRoute aus dem offiziellen Repository herunter...

where git >nul 2>&1
IF ERRORLEVEL 1 (
    echo [Fehler] Git ist auf diesem System nicht installiert!
    echo Bitte installiere Git unter: https://git-scm.com/
    pause
    exit /b 1
)

git clone https://github.com/Dinottinjs/OmniRoute.git "%TARGET_DIR%"
IF ERRORLEVEL 1 (
    echo [Fehler] Fehler beim Herunterladen von OmniRoute.
    pause
    exit /b 1
)
echo [Info] Download erfolgreich!

IF EXIST "config.json" (
    echo [Info] Kopiere lokale config.json in das Zielverzeichnis...
    copy /Y "config.json" "%TARGET_DIR%\config.json" >nul
)

:RUN_APP
cd "%TARGET_DIR%"

IF EXIST "venv" GOTO START_APP

echo [Info] Erstelle virtuelle Python-Umgebung...
python -m venv venv
IF ERRORLEVEL 1 (
    echo [Fehler] Fehler bei der Erstellung der virtuellen Umgebung. Ist Python 3 installiert?
    pause
    exit /b 1
)

echo [Info] Installiere Abhängigkeiten...
call venv\Scripts\activate
pip install -r requirements.txt
IF ERRORLEVEL 1 (
    echo [Fehler] Fehler bei der Installation der Abhängigkeiten.
    pause
    exit /b 1
)
GOTO START_NOW

:START_APP
call venv\Scripts\activate

:START_NOW
echo.
echo [Info] OmniRoute wird gestartet...
python main.py interactive
pause
