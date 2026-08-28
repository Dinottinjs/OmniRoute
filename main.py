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
    
    for net in networks:
        table.add_row(net['ssid'], str(net['channel']), f"{net['signal']}%")
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
    
    recommendation = agent.analyze(networks, current_router_config)
    
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
def interactive():
    """Startet OmniRoute im interaktiven UI-Modus."""
    options = [
        "Nach Updates suchen",
        "WLAN-Umgebung scannen (Spektrum)",
        "Netzwerk-Topologie anzeigen (Geräte, Router, Switches)",
        "KI-Analyse (Pros & Contras)",
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
                choice = Prompt.ask("\n[bold yellow]Bitte wähle eine Aktion (1-6)[/bold yellow]", choices=[str(i+1) for i in range(len(options))], default="6")
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
            manual_config()
        elif choice == "6":
            console.print("[bold green]Auf Wiedersehen![/bold green]")
            sys.exit(0)
            
        console.print("\n[dim]Drücke Enter, um zum Menü zurückzukehren...[/dim]")
        input()

if __name__ == "__main__":
    app()
