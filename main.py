import warnings
warnings.filterwarnings("ignore")

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.align import Align
from rich.text import Text
from rich.table import Table
from core.updater import check_for_updates
from core.scanner import NetworkScanner
from core.agent import RouterAgent
from adapters.tr064 import TR064Adapter
from adapters.ssh_generic import OpenWrtSSHAdapter
from adapters.web_generic import GenericWebScraperAdapter
import json
import os
import sys
import time
import concurrent.futures
from rich.status import Status

app = typer.Typer(help="OmniRoute (AetherNet) - Universal Wi-Fi Router Multi-Tool")
console = Console()

def load_config():
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.command()
def update():
    """Prüft auf Updates für OmniRoute und seine Abhängigkeiten."""
    console.print("[bold blue]Starte Update-Prüfung...[/bold blue]")
    config = load_config()
    check_for_updates(config)

@app.command()
def scan_wifi():
    """Scannt die Umgebung nach WLAN-Netzwerken und Kanälen."""
    console.print("[bold blue]Starte WLAN-Spektrum-Scan...[/bold blue]")
    scanner = NetworkScanner()
    networks = scanner.scan_wifi()
    
    console.print(f"\n[bold green]Gefundene WLAN-Netzwerke: {len(networks)}[/bold green]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("SSID")
    table.add_column("Kanal", justify="right")
    table.add_column("Signal", justify="right")
    table.add_column("dBm", justify="right")
    
    for net in networks:
        dbm = net.get('dbm', '?')
        table.add_row(net['ssid'], str(net['channel']), f"{net['signal']}%", f"{dbm} dBm")
    console.print(table)

@app.command()
def scan_topology():
    """Scannt das lokale Netzwerk auf aktive Geräte (Router, Switches, etc.)."""
    console.print("[bold blue]Führe lokalen Netzwerk-Scan (Topologie) durch...[/bold blue]")
    console.print("[dim]Achtung: Dies erfordert Administratorrechte (scapy/arping).[/dim]")
    scanner = NetworkScanner()
    
    gateway = scanner.find_gateway()
    if gateway:
        console.print(f"Standard-Gateway (Router) erkannt: [cyan]{gateway}[/cyan]")
    else:
        console.print("[red]Standard-Gateway konnte nicht ermittelt werden.[/red]")
        
    devices = scanner.scan_topology()
    
    console.print(f"\n[bold green]Netzwerkgeräte gefunden: {len(devices)}[/bold green]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("IP Adresse")
    table.add_column("MAC Adresse")
    
    for dev in devices:
        table.add_row(dev['ip'], dev['mac'])
    console.print(table)

@app.command()
def optimize(router_ip: str = typer.Option(None, help="IP-Adresse des Routers")):
    """Nutzt den AI Agent zur Analyse und erstellt eine Pro/Contra-Liste."""
    console.print("[bold blue]Starte KI-Netzwerkanalyse...[/bold blue]")
    config = load_config()
    agent = RouterAgent(config)
    
    scanner = NetworkScanner()
    if not router_ip:
        router_ip = scanner.find_gateway()
    
    if not router_ip:
        console.print("[bold red]Fehler: Keine Router-IP gefunden.[/bold red]")
        return
        
    networks = scanner.scan_wifi()
    
    console.print("[cyan]Sammle Daten und sende sie an die KI...[/cyan]")
    current_router_config = {"gateway_ip": router_ip}
    
    start_time = time.time()
    recommendation = ""
    with Status("[cyan]KI-Analyse läuft... (0s)[/cyan]", spinner="dots") as status:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(agent.analyze, networks, current_router_config)
            while not future.done():
                elapsed = int(time.time() - start_time)
                status.update(f"[cyan]KI-Analyse läuft... ({elapsed}s)[/cyan]")
                time.sleep(0.5)
            recommendation = future.result()
    
    console.print("\n[bold green]KI-Netzwerkanalyse (Pros & Contras):[/bold green]")
    console.print(Panel(recommendation, border_style="green", title="Analyse-Ergebnis"))

@app.command()
def manual_config():
    """Erlaubt manuelle Einstellungsänderungen am Router über die verfügbaren Adapter."""
    console.print("[bold cyan]=== Manuelle Router-Konfiguration ===[/bold cyan]")
    scanner = NetworkScanner()
    default_ip = scanner.find_gateway() or "192.168.1.1"
    
    adapter_choice = Prompt.ask("Wähle Adapter (1: TR-064/FritzBox, 2: SSH/OpenWrt, 3: Web-Scraper)", choices=["1", "2", "3"], default="1")
    ip = Prompt.ask("Router IP", default=default_ip)
    username = Prompt.ask("Benutzername", default="admin")
    password = Prompt.ask("Passwort", password=True)
    
    adapter = None
    if adapter_choice == "1":
        adapter = TR064Adapter(ip)
    elif adapter_choice == "2":
        adapter = OpenWrtSSHAdapter(ip)
    elif adapter_choice == "3":
        adapter = GenericWebScraperAdapter(ip)
        
    console.print("[yellow]Verbindungsaufbau...[/yellow]")
    if adapter.login({"username": username, "password": password}):
        console.print("[green]Erfolgreich am Router eingeloggt![/green]")
        action = Prompt.ask("Aktion wählen (1: WLAN-Kanal ändern, 2: Router neustarten)", choices=["1", "2"], default="1")
        if action == "1":
            band = Prompt.ask("Frequenzband (2.4 oder 5)", default="2.4")
            channel = int(Prompt.ask("Kanal", default="6"))
            if adapter.set_channel(band, channel):
                console.print(f"[green]Kanal für {band}GHz erfolgreich auf {channel} gesetzt![/green]")
            else:
                console.print("[red]Fehler beim Setzen des Kanals.[/red]")
        elif action == "2":
            if adapter.reboot():
                console.print("[green]Neustart-Befehl erfolgreich gesendet![/green]")
            else:
                console.print("[red]Fehler beim Neustarten.[/red]")
    else:
        console.print("[red]Login fehlgeschlagen. Bitte Zugangsdaten und IP prüfen![/red]")

@app.command()
def positioning_assistant():
    """Startet ein Live-Radar zur Router-Positionierung (dBm Messung)."""
    console.print("[bold cyan]=== Positionierungs-Assistent ===[/bold cyan]")
    scanner = NetworkScanner()
    
    networks = scanner.scan_wifi()
    if not networks:
        console.print("[red]Keine Netzwerke gefunden![/red]")
        return
        
    unique_ssids = list(set([n['ssid'] for n in networks if n['ssid']]))
    if not unique_ssids:
        console.print("[red]Keine benannten Netzwerke gefunden![/red]")
        return
        
    for i, ssid in enumerate(unique_ssids):
        console.print(f"[{i+1}] {ssid}")
        
    choice = Prompt.ask("Wähle ein Netzwerk zur Beobachtung", choices=[str(i+1) for i in range(len(unique_ssids))])
    target_ssid = unique_ssids[int(choice)-1]
    
    console.print(f"\n[bold green]Starte Live-Tracking für '{target_ssid}'... (Abbruch mit Strg+C)[/bold green]")
    
    from rich.live import Live
    from rich.progress import Progress, BarColumn, TextColumn
    
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("{task.fields[dbm_text]}")
    )
    
    task_id = progress.add_task(target_ssid, total=100, dbm_text="Messung läuft...")
    
    try:
        with Live(progress, refresh_per_second=2, screen=False):
            while True:
                try:
                    nets = scanner.scan_wifi()
                    target_net = next((n for n in nets if n['ssid'] == target_ssid), None)
                    if target_net:
                        dbm = target_net.get('dbm', -100)
                        progress_val = max(0, min(100, (dbm + 100) * 2))
                        
                        color = "red"
                        if dbm >= -65:
                            color = "green"
                        elif dbm >= -80:
                            color = "yellow"
                            
                        progress.update(
                            task_id, 
                            completed=progress_val,
                            dbm_text=f"[{color}]{dbm} dBm[/]",
                            description=f"[bold blue]{target_ssid} (Kanal {target_net['channel']})"
                        )
                    else:
                        progress.update(task_id, completed=0, dbm_text="[red]Nicht gefunden[/red]")
                except Exception:
                    pass
                time.sleep(2)
    except KeyboardInterrupt:
        console.print("\n[yellow]Live-Tracking beendet.[/yellow]")

@app.command()
def interactive():
    """Startet OmniRoute im interaktiven UI-Modus."""
    options = [
        "Nach Updates suchen",
        "WLAN-Umgebung scannen (Spektrum)",
        "Netzwerk-Topologie anzeigen (Geräte, Router, Switches)",
        "KI-Analyse (Pros & Contras)",
        "Positionierungs-Assistent (Live dBm-Radar)",
        "Manuelle Router-Konfiguration",
        "Beenden"
    ]
    selected_idx = 0
    
    while True:
        # UI-Zeichenschleife für die Pfeiltasten-Navigation
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            title = Text("🌐 OmniRoute (AetherNet) Multi-Tool 🌐", style="bold cyan")
            
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Cursor", justify="right", style="bold yellow")
            table.add_column("Option", style="white")
            
            for i, opt in enumerate(options):
                if i == selected_idx:
                    # Hervorgehobene Auswahl
                    table.add_row(">", f"[black on white] {opt} [/black on white]")
                else:
                    if i == len(options) - 1:
                        table.add_row(" ", f"[red]{opt}[/red]")
                    else:
                        table.add_row(" ", opt)
            
            panel = Panel(
                Align.center(table),
                title=title,
                subtitle="© 2026 Maximilian Holzer",
                border_style="cyan",
                padding=(1, 4)
            )
            console.print(panel)
            console.print(Align.center("\n[dim]Nutze die Pfeiltasten (↑/↓) zum Navigieren und drücke ENTER.[/dim]"))
            
            # Tasten-Eingabe lesen (Windows-spezifisch)
            if os.name == 'nt':
                import msvcrt
                key = ord(msvcrt.getch())
                if key == 224: # Prefix für Spezialtasten
                    key = ord(msvcrt.getch())
                    if key == 72: # Pfeil hoch
                        selected_idx = (selected_idx - 1) % len(options)
                    elif key == 80: # Pfeil runter
                        selected_idx = (selected_idx + 1) % len(options)
                elif key == 13: # Enter
                    break
            else:
                # Fallback für andere OS (nur zur Sicherheit, falls nicht Windows)
                choice = Prompt.ask(f"\n[bold yellow]Bitte wähle eine Aktion (1-{len(options)})[/bold yellow]", choices=[str(i+1) for i in range(len(options))], default=str(len(options)))
                selected_idx = int(choice) - 1
                break
                
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Ausführen der gewählten Aktion
        choice = str(selected_idx + 1)
        if choice == "1":
            update()
        elif choice == "2":
            scan_wifi()
        elif choice == "3":
            scan_topology()
        elif choice == "4":
            optimize(router_ip=None)
        elif choice == "5":
            positioning_assistant()
        elif choice == "6":
            manual_config()
        elif choice == "7":
            console.print("[bold green]Auf Wiedersehen![/bold green]")
            sys.exit(0)
            
        console.print("\n[dim]Drücke Enter, um zum Menü zurückzukehren...[/dim]")
        input()

if __name__ == "__main__":
    app()
