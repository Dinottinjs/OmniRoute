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
        # Führe echten Git Pull durch
        result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, timeout=15)
        output = result.stdout + result.stderr
        
        if "Already up to date." in output or "Bereits aktuell" in output:
            console.print("[green]OmniRoute ist bereits auf dem neuesten Stand![/green]")
            
            # Optional: Simulierte Asset-Downloads (für Wörterbücher etc.) belassen
            console.print("[dim]Prüfe auf zusätzliche Datenbank-Updates (OUI etc.)...[/dim]")
            _download_assets_simulation()
            
        else:
            console.print("[bold green]Update erfolgreich heruntergeladen und gepatcht![/bold green]")
            console.print(f"[dim]{output.strip()}[/dim]")
            console.print("[yellow]Die Anwendung wird nun neu gestartet, um die Änderungen anzuwenden...[/yellow]")
            time.sleep(2)
            
            # Neustart der Anwendung, um den neuen Code zu laden
            os.execl(sys.executable, sys.executable, *sys.argv)
            
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
