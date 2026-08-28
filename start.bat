@echo off
:: Batch-Skript für OmniRoute - Fordert Administratorrechte an und startet die App

:: Prüfen auf Administratorrechte
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Administratorrechte erfolgreich geprueft.
) else (
    echo Fordere Administratorrechte an...
    goto UACPrompt
)

goto StartApp

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "cmd.exe", "/c ""%~s0""", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:StartApp
cd /d "%~dp0"
echo.
echo ===========================================
echo       Starte OmniRoute (AetherNet)
echo ===========================================
echo.

:: Prüfen, ob virtuelles Environment existiert, falls nicht erstellen und Abhängigkeiten installieren
if not exist "venv\" (
    echo Virtuelles Environment nicht gefunden. Erstelle venv...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installiere Abhaengigkeiten...
    pip install -r requirements.txt
    playwright install
) else (
    call venv\Scripts\activate.bat
)

:: App starten
echo Starte OmniRoute CLI...
python main.py --help
cmd /k
