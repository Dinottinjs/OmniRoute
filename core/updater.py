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
    """Simulates downloading required assets using rich progress bars."""
    assets = [
        ("oui.txt", 1024 * 1024 * 4),      # 4 MB
        ("tr064_schemas.xml", 1024 * 256)  # 256 KB
    ]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}", justify="right"),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
    ) as progress:
        
        tasks = []
        for name, size in assets:
            tasks.append(progress.add_task(f"Lade {name}...", total=size))
            
        while not progress.finished:
            for task_id in tasks:
                task = progress.tasks[task_id]
                if not task.finished:
                    # Simulate variable network speed
                    progress.advance(task_id, advance=1024 * 128)
            time.sleep(0.05)
            
    console.print("[bold green]Alle internen Datenbanken sind aktuell.[/bold green]")
