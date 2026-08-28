import typer
from rich.console import Console
from core.updater import check_for_updates
from core.scanner import NetworkScanner
from core.agent import RouterAgent
import json
import os

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
def scan():
    """Scannt die Umgebung nach WLAN-Netzwerken, Kanälen und dem Gateway-Router."""
    console.print("[bold blue]Starte Netzwerk- und Spektrum-Scan...[/bold blue]")
    scanner = NetworkScanner()
    networks = scanner.scan_wifi()
    gateway = scanner.find_gateway()
    
    console.print("\n[bold green]Scan-Ergebnisse:[/bold green]")
    if gateway:
        console.print(f"Standard-Gateway (Router): [cyan]{gateway}[/cyan]")
    else:
        console.print("[red]Konnte kein Standard-Gateway finden![/red]")
        
    console.print(f"\nGefundene WLAN-Netzwerke: {len(networks)}")
    for net in networks:
        console.print(f"- {net['ssid']} (Kanal: {net['channel']}, Signal: {net['signal']}%)")

@app.command()
def optimize(
    mode: str = typer.Option("manual", help="Optimierungsmodus: 'manual' (Ratgeber) oder 'auto' (automatische Anpassung)"),
    router_ip: str = typer.Option(None, help="IP-Adresse des Routers (Fallback auf Standard-Gateway)"),
):
    """Nutzt den AI Agent zur Analyse und Optimierung der Router-Konfiguration."""
    console.print("[bold blue]Starte AI Router Optimizer...[/bold blue]")
    config = load_config()
    agent = RouterAgent(config)
    
    scanner = NetworkScanner()
    if not router_ip:
        router_ip = scanner.find_gateway()
    
    if not router_ip:
        console.print("[bold red]Fehler: Keine Router-IP angegeben und automatisches Erkennen fehlgeschlagen.[/bold red]")
        raise typer.Exit(code=1)
        
    networks = scanner.scan_wifi()
    
    console.print(f"[cyan]Sammle Daten für Router {router_ip}...[/cyan]")
    # TODO: Login to router, fetch current config via adapter
    # For now, passing an empty dictionary as a placeholder for router config
    current_router_config = {} 
    
    console.print("[cyan]Sende Daten an den AI Agenten zur Analyse...[/cyan]")
    recommendation = agent.analyze(networks, current_router_config, mode=mode)
    
    console.print("\n[bold green]KI-Empfehlung:[/bold green]")
    console.print(recommendation)

if __name__ == "__main__":
    app()
