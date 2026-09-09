import time
import subprocess
import sys
import os
from rich.progress import Progress, SpinnerColumn, DownloadColumn, TransferSpeedColumn, TextColumn
from rich.console import Console

console = Console()

def check_for_updates(config: dict):
    """
    Prüft auf neue Versionen via git pull und lädt diese direkt herunter.
    """
    console.print("[cyan]Suche nach neuesten Patches im GitHub Repository...[/cyan]")
    
    try:
        # Führe Git Fetch durch, um den Remote-Status zu holen
        subprocess.run(["git", "fetch", "origin", "main"], capture_output=True, text=True, timeout=15)
        
        # Vergleiche lokale und remote Version
        local_hash = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        remote_hash = subprocess.run(["git", "rev-parse", "origin/main"], capture_output=True, text=True).stdout.strip()
        
        if local_hash != remote_hash and remote_hash != "":
            # Zwinge das lokale Repo auf den exakten Stand von origin/main
            result = subprocess.run(["git", "reset", "--hard", "origin/main"], capture_output=True, text=True, timeout=15)
            
            console.print("[bold green]Update erfolgreich heruntergeladen und gepatcht![/bold green]")
            console.print(f"[dim]{result.stdout.strip()}[/dim]")
            console.print("[yellow]Die Anwendung wird nun neu gestartet, um die Änderungen anzuwenden...[/yellow]")
            time.sleep(2)
            
            # Neustart der Anwendung in den interaktiven Modus
            os.execl(sys.executable, sys.executable, sys.argv[0], "interactive")
            
        else:
            console.print("[green]OmniRoute ist bereits auf dem neuesten Stand![/green]")
            
            # Optional: Simulierte Asset-Downloads (für Wörterbücher etc.) belassen
            console.print("[dim]Prüfe auf zusätzliche Datenbank-Updates (OUI etc.)...[/dim]")
            _download_assets_simulation()
            
    except Exception as e:
        console.print(f"[red]Fehler beim Update-Check: {e}[/red]")

def _download_assets_simulation():
    """Lädt aktuelle Datenbanken wie die offizielle IEEE OUI-Liste herunter."""
    console.print("[dim]Prüfe und aktualisiere IEEE OUI Datenbank (MAC Hersteller)...[/dim]")
    
    try:
        import requests
        import os
        
        url = "https://raw.githubusercontent.com/boundary/wireshark/master/manuf"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
        ) as progress:
            
            # Start request with stream
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Die Dateigröße kann bei raw.githubusercontent.com manchmal fehlen, Fallback auf ~1.8 MB
            total_size = int(response.headers.get('content-length', 1800000))
            task_id = progress.add_task("Lade IEEE OUI Datenbank...", total=total_size)
            
            with open("oui.txt", "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task_id, advance=len(chunk))
                        
        console.print("[bold green]Alle internen Datenbanken sind aktuell.[/bold green]")
    except ImportError:
        console.print("[red]Fehler: Das 'requests' Modul fehlt. Bitte installiere die requirements.txt![/red]")
    except Exception as e:
        console.print(f"[red]Fehler beim Herunterladen der OUI-Datenbank: {e}[/red]")
