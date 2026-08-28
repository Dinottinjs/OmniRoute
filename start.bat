@echo off
setlocal
chcp 65001 >nul
title OmniRoute (AetherNet) - Installer & Launcher
echo ========================================================
echo       🌐 OmniRoute (AetherNet) Multi-Tool 🌐
echo       © 2026 Maximilian Holzer
echo ========================================================
echo.

set "TARGET_DIR=OmniRoute_Stable_Build"

IF NOT EXIST "%TARGET_DIR%" (
    echo [Info] Ordner "%TARGET_DIR%" nicht gefunden.
    echo [Info] Lade OmniRoute aus dem offiziellen Repository herunter...
    
    where git >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo [Fehler] Git ist auf diesem System nicht installiert!
        echo Bitte installiere Git (https://git-scm.com/) um OmniRoute herunterzuladen.
        pause
        exit /b 1
    )
    
    git clone https://github.com/Dinottinjs/OmniRoute.git "%TARGET_DIR%"
    IF %ERRORLEVEL% NEQ 0 (
        echo [Fehler] Fehler beim Herunterladen von OmniRoute.
        pause
        exit /b 1
    )
    echo [Info] Download erfolgreich!
)

cd "%TARGET_DIR%"

IF NOT EXIST "venv" (
    echo [Info] Erstelle virtuelle Python-Umgebung...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo [Fehler] Fehler bei der Erstellung der virtuellen Umgebung. Ist Python installiert?
        pause
        exit /b 1
    )
    
    echo [Info] Installiere Abhängigkeiten...
    call venv\Scripts\activate
    pip install -r requirements.txt
    IF %ERRORLEVEL% NEQ 0 (
        echo [Fehler] Fehler bei der Installation der Abhängigkeiten.
        pause
        exit /b 1
    )
) ELSE (
    call venv\Scripts\activate
)

echo.
echo [Info] OmniRoute wird gestartet...
python main.py interactive
pause
