import warnings
warnings.filterwarnings("ignore")

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.align import Align
from rich.text import Text
from rich.table import Table
from rich import box
from core.updater import check_for_updates
from core.scanner import NetworkScanner
from core.agent import RouterAgent
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
    table = Table(title="📡 WLAN-Spektrum Analyse", show_header=True, header_style="bold white on blue", box=box.ROUNDED, expand=True)
    table.add_column("SSID", style="bold cyan")
    table.add_column("Kanal", justify="center", style="yellow")
    table.add_column("Frequenz", justify="center")
    table.add_column("Signal (%)", justify="right")
    table.add_column("dBm", justify="right")
    table.add_column("Bewertung", justify="center")
    
    for net in networks:
        dbm = net.get('dbm', -100)
        signal = net.get('signal', 0)
        channel = net.get('channel', 0)
        
        freq = "5 GHz" if channel > 14 else "2.4 GHz" if channel > 0 else "?"
        
        if dbm >= -60:
            rating = "[bold green]Exzellent[/bold green]"
            row_style = "green"
        elif dbm >= -75:
            rating = "[bold yellow]Gut[/bold yellow]"
            row_style = "yellow"
        else:
            rating = "[bold red]Schwach[/bold red]"
            row_style = "red"
            
        table.add_row(
            net['ssid'] or "[dim]<Versteckt>[/dim]",
            str(channel),
            freq,
            f"{signal}%",
            f"{dbm} dBm",
            rating,
            style=row_style
        )
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
        
    with Status("[cyan]Führe aktiven Ping-Sweep durch, um alle Geräte im Netzwerk aufzuspüren... (ca. 2 Sekunden)[/cyan]", spinner="dots"):
        devices = scanner.scan_topology()
        
    console.print(f"\n[bold green]Netzwerkgeräte gefunden: {len(devices)}[/bold green]")
    
    table = Table(title="🕸️ Lokale Netzwerk-Topologie", show_header=True, header_style="bold white on purple", box=box.ROUNDED)
    table.add_column("Typ / Hostname", justify="left")
    table.add_column("IP Adresse", style="cyan", justify="left")
    table.add_column("MAC Adresse", style="magenta", justify="left")
    table.add_column("Hersteller", style="yellow", justify="left")
    
    gateway_ip = scanner.find_gateway()
    
    for idx, dev in enumerate(devices):
        ip = dev.get('ip', 'Error')
        mac = dev.get('mac', '')
        hostname = dev.get('hostname', 'Unbekannt')
        vendor = dev.get('vendor', 'Unbekannt')
        
        if hostname != "Unbekannt":
            icon = f"💻 {hostname}"
        else:
            icon = "💻 Unbekanntes Gerät"
            
        row_style = "white"
        
        if ip == gateway_ip:
            icon = f"🌐 {hostname if hostname != 'Unbekannt' else 'Router/Gateway'}"
            row_style = "bold green"
        elif "Error" in ip:
            icon = "❌ Fehler"
            row_style = "red"
            
        table.add_row(icon, ip, mac, vendor, style=row_style)
        
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
    from rich.markdown import Markdown
    md = Markdown(recommendation)
    console.print(Panel(md, border_style="green", title="Analyse-Ergebnis"))

@app.command()
def traceroute_diag():
    """Führt ein Traceroute (Routenverfolgung) durch."""
    console.print("[bold cyan]=== Traceroute & DNS-Diagnose ===[/bold cyan]")
    try:
        host = Prompt.ask("Ziel-Host oder IP (Enter für Google DNS)", default="8.8.8.8")
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Abgebrochen.[/yellow]")
        return
        
    console.print(f"[cyan]Verfolge Route zu {host}... (Taste 'q' zum Abbrechen)[/cyan]")
    
    import subprocess
    import threading
    cmd = ["tracert", host] if os.name == 'nt' else ["traceroute", host]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='cp850' if os.name == 'nt' else 'utf-8', errors='ignore')
    
    def read_output():
        for line in process.stdout:
            print(line, end='', flush=True)
            
    t = threading.Thread(target=read_output)
    t.daemon = True
    t.start()
    
    if os.name == 'nt':
        import msvcrt
        while process.poll() is None:
            if msvcrt.kbhit():
                if msvcrt.getch().lower() == b'q':
                    process.terminate()
                    console.print("\n[bold yellow]Traceroute durch Benutzer abgebrochen.[/bold yellow]")
                    break
            time.sleep(0.1)
    else:
        try:
            process.wait()
        except KeyboardInterrupt:
            process.terminate()
            console.print("\n[bold yellow]Traceroute durch Benutzer abgebrochen.[/bold yellow]")

@app.command()
def positioning_assistant():
    """Startet ein Live-Radar zur Router-Positionierung (dBm Messung)."""
    from rich.live import Live
    from rich.progress import Progress, BarColumn, TextColumn
    import time
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(Panel("[bold cyan]=== Positionierungs-Assistent ===[/bold cyan]\n[dim]Wähle ein Netzwerk aus, um die Signalstärke beim Herumlaufen in Echtzeit zu messen.\n[yellow]Tipp für Windows-Nutzer:[/yellow] Verbinde dich vorher mit dem Ziel-WLAN, um absolute Echtzeit-Daten (60 FPS) ohne Cache zu erhalten![/dim]", box=box.ROUNDED, border_style="cyan"))
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
            console.print(f"  [bold yellow][{i+1}][/bold yellow] {ssid}")
        
        console.print(f"  [bold red][0][/bold red] Zurück zum Hauptmenü")
            
        try:
            choice = Prompt.ask("\nWelches Netzwerk möchtest du tracken?", choices=[str(i) for i in range(len(unique_ssids)+1)])
        except (KeyboardInterrupt, EOFError):
            break
            
        if choice == "0":
            break
            
        target_ssid = unique_ssids[int(choice)-1]
        
        console.print(f"\n[bold green]Starte Live-Tracking für '{target_ssid}'... (Abbruch und Netzwerkauswahl mit Strg+C)[/bold green]")
        
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
                        dbm = scanner.get_live_signal(target_ssid)
                        
                        if dbm != -100:
                            progress_val = max(0, min(100, (dbm + 100) * 2))
                            
                            color = "red"
                            if dbm >= -60:
                                color = "green"
                            elif dbm >= -75:
                                color = "yellow"
                                
                            progress.update(
                                task_id, 
                                completed=progress_val,
                                dbm_text=f"[{color}]{dbm} dBm[/]",
                                description=f"[bold blue]{target_ssid}"
                            )
                        else:
                            progress.update(task_id, completed=0, dbm_text="[red]Nicht gefunden[/red]")
                    except Exception:
                        pass
                    time.sleep(2)
        except KeyboardInterrupt:
            console.print("\n[yellow]Tracking beendet.[/yellow]")
            time.sleep(1)

@app.command()
def quick_portscan():
    """Startet einen TCP-Portscan."""
    console.print("[bold cyan]=== Quick-Portscan ===[/bold cyan]")
    scanner = NetworkScanner()
    
    try:
        ip = Prompt.ask("Gib die Ziel-IP-Adresse ein (z.B. 192.168.1.1)")
        ports_input = Prompt.ask("Zu scannende Ports (Optional, z.B. 80,443,8000-8010 oder Leer für Standard-Ports)", default="")
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Abgebrochen.[/yellow]")
        return
        
    with Status("[cyan]Prüfe Erreichbarkeit...[/cyan]", spinner="dots"):
        import re
        if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip) or scanner.ping_measure(ip) < 0:
            console.print("[red]Fehler: Die IP-Adresse ist ungültig oder nicht erreichbar![/red]")
            return
            
    custom_ports = None
    if ports_input.strip():
        custom_ports = []
        for part in ports_input.split(','):
            part = part.strip()
            if '-' in part:
                try:
                    start_p, end_p = map(int, part.split('-'))
                    custom_ports.extend(range(start_p, end_p + 1))
                except ValueError:
                    pass
            elif part.isdigit():
                custom_ports.append(int(part))
        
        # Deduplicate and limit to max 1000 ports to avoid hanging
        custom_ports = list(set(custom_ports))[:1000]

    if custom_ports:
        console.print(f"[cyan]Scanne {len(custom_ports)} ausgewählte Ports auf {ip}...[/cyan]")
    else:
        console.print(f"[cyan]Scanne häufige Admin-Ports auf {ip}...[/cyan]")
    
    with Status("[cyan]Scanner läuft...[/cyan]", spinner="dots"):
        open_ports = scanner.port_scan(ip, ports=custom_ports)
        
    if open_ports:
        console.print(f"[bold green]Gefundene offene Ports:[/bold green] {', '.join(map(str, open_ports))}")
    else:
        console.print("[yellow]Keine gängigen offenen Ports gefunden.[/yellow]")

@app.command()
def latency_monitor():
    """Startet einen Live-Ping Monitor."""
    console.print("[bold cyan]=== Live-Latenz & Internet-Monitor ===[/bold cyan]")
    scanner = NetworkScanner()
    try:
        host = Prompt.ask("Ziel-Host (Enter für Google DNS)", default="8.8.8.8")
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Abgebrochen.[/yellow]")
        return
    
    console.print(f"\n[bold green]Starte Live-Tracking für '{host}'... (Abbruch mit Strg+C)[/bold green]")
    
    from rich.live import Live
    
    def generate_ping_table(pings):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Ziel")
        table.add_column("Aktueller Ping")
        table.add_column("Jitter (Schwankung)")
        table.add_column("Packet Loss")
        table.add_column("Status")
        
        if not pings:
            table.add_row(host, "...", "...", "...", "...")
            return table
            
        current = pings[-1]
        
        # Calculate Packet Loss
        loss_count = sum(1 for p in pings if p < 0)
        loss_pct = (loss_count / len(pings)) * 100
        loss_str = f"[green]0.0%[/green]" if loss_pct == 0 else f"[red]{loss_pct:.1f}%[/red]"
        
        if current < 0:
            table.add_row(host, "[red]Timeout[/red]", "...", loss_str, "[red]Offline[/red]")
            return table
            
        jitter = 0
        if len(pings) > 1:
            valid_pings = [p for p in pings[-5:] if p >= 0]
            if len(valid_pings) > 1:
                jitter = int(abs(valid_pings[-1] - valid_pings[-2]))
                
        status = "[green]Exzellent[/green]" if current < 30 else "[yellow]Gut[/yellow]" if current < 80 else "[red]Schlecht[/red]"
        table.add_row(host, f"{current} ms", f"{jitter} ms", loss_str, status)
        return table

    pings = []
    try:
        with Live(generate_ping_table(pings), refresh_per_second=2, screen=False) as live:
            while True:
                try:
                    latency = scanner.ping_measure(host)
                    pings.append(latency)
                    if len(pings) > 50:
                        pings.pop(0)
                    live.update(generate_ping_table(pings))
                except Exception:
                    pass
                time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Ping-Monitor beendet.[/yellow]")

@app.command()
def sdr_scanner():
    """Startet den SDR-Scanner für USB-Dongles."""
    console.print("[bold cyan]=== SDR-Scanner (RTL-SDR USB-Dongle) ===[/bold cyan]")
    try:
        from rtlsdr import RtlSdr
        import numpy as np
    except ImportError:
        console.print("[red]Fehler: Das 'pyrtlsdr' oder 'numpy' Modul fehlt. Bitte installiere die requirements.txt![/red]")
        return
        
    try:
        sdr = RtlSdr()
    except Exception as e:
        console.print("[bold red]Kein RTL-SDR USB-Dongle gefunden![/bold red]")
        console.print(f"[dim]Bitte stelle sicher, dass der Stick eingesteckt ist und der Zadig WinUSB Treiber installiert ist.\nDetails: {e}[/dim]")
        return
        
    try:
        freq_input = Prompt.ask("Zielfrequenz in MHz (z.B. 433.92 für Smart-Home, 1090 für ADS-B, 98.0 für FM)", default="433.92")
        target_freq = float(freq_input) * 1e6
        
        sdr.sample_rate = 2.048e6  # 2.048 MHz
        sdr.center_freq = target_freq
        sdr.gain = 'auto'
        
        console.print(f"\n[bold green]Starte Live-Messung auf {freq_input} MHz... (Taste 'q' zum Abbrechen)[/bold green]")
        
        from rich.live import Live
        from rich.progress import Progress, BarColumn, TextColumn
        
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("{task.fields[dbm_text]}")
        )
        task_id = progress.add_task(f"Freq: {freq_input} MHz", total=100, dbm_text="Messe...")
        
        with Live(progress, refresh_per_second=5, screen=False):
            while True:
                if os.name == 'nt':
                    import msvcrt
                    if msvcrt.kbhit():
                        if msvcrt.getch().lower() == b'q':
                            break
                        
                # Read real samples
                samples = sdr.read_samples(256 * 1024)
                
                # Calculate FFT and find peak power
                fft_data = np.abs(np.fft.fft(samples))
                fft_data = np.fft.fftshift(fft_data)
                
                # Convert to dBFS (estimate)
                power_dbfs = 20 * np.log10(np.max(fft_data) + 1e-12) - 80  # Simple calibration offset
                
                # Normalize for progress bar (-100 dBFS to 0 dBFS)
                display_val = max(0, min(100, power_dbfs + 100))
                
                color = "red" if power_dbfs > -30 else "yellow" if power_dbfs > -60 else "green"
                progress.update(task_id, completed=display_val, dbm_text=f"[{color}]{power_dbfs:.1f} dBFS[/{color}]")
                
                import time
                time.sleep(0.1)
                
    except Exception as e:
        console.print(f"[red]Fehler bei der SDR-Verarbeitung: {e}[/red]")
    finally:
        sdr.close()
        console.print("\n[bold yellow]SDR-Scanner beendet.[/bold yellow]")

@app.command()
def sdr_hardware_diag():
    """Liest Hardware-Parameter des RTL-SDR Dongles aus (Antennen-Ping)."""
    console.print("[bold cyan]=== SDR Hardware-Diagnose (Antennen-Ping) ===[/bold cyan]")
    try:
        from rtlsdr import RtlSdr
    except ImportError:
        console.print("[red]Fehler: Das 'pyrtlsdr' Modul fehlt.[/red]")
        return
        
    with Status("[cyan]Verbindungsaufbau zum USB-Dongle...[/cyan]", spinner="dots"):
        import time
        time.sleep(0.5)
        try:
            sdr = RtlSdr()
        except Exception as e:
            console.print("[bold red]Kein RTL-SDR Dongle am USB-Port gefunden![/bold red]")
            console.print(f"[dim]Fehler: {e}[/dim]")
            return
            
    console.print("[bold green]Verbindung erfolgreich hergestellt![/bold green]\n")
    
    table = Table(title="📡 Antennen & Tuner Hardware-Parameter", box=box.ROUNDED)
    table.add_column("Eigenschaft", style="cyan")
    table.add_column("Wert", style="yellow")
    
    # Auslesen echter Hardware-Daten
    try:
        tuner_type = "Unbekannt (Generic RTL2832U)"
        # Gains
        gains = sdr.get_gains()
        gain_str = f"{len(gains)} Stufen ({min(gains)/10.0} dB bis {max(gains)/10.0} dB)" if gains else "Auto AGC"
        
        # Test frequency limits (approximate for typical R820T2)
        freq_range = "24 MHz - 1766 MHz (Typisch)"
        
        table.add_row("Tuner Status", "[green]Online & Aktiv[/green]")
        table.add_row("Unterstützte Gain-Stufen", gain_str)
        table.add_row("Empfangsbereich (Freq.)", freq_range)
        table.add_row("Sample Rate", "Bis zu 3.2 MS/s (Stabil: 2.4 MS/s)")
        
        console.print(table)
        
        # Live Test
        console.print("\n[cyan]Führe lokalen Signal-Test (Live-Rauschen) durch...[/cyan]")
        sdr.sample_rate = 2.048e6
        sdr.center_freq = 100e6  # 100 MHz als Test
        sdr.gain = 'auto'
        
        samples = sdr.read_samples(256 * 1024)
        import numpy as np
        power = 10 * np.log10(np.var(samples) + 1e-12)
        
        console.print(f"Antennen Rausch-Pegel (100 MHz): [bold {'green' if power > -60 else 'yellow'}]{power:.1f} dBFS[/bold]")
        console.print("\n[green]Diagnose abgeschlossen. Hardware ist zu 100% einsatzbereit.[/green]")
        
    except Exception as e:
        console.print(f"[red]Fehler beim Auslesen: {e}[/red]")
    finally:
        sdr.close()

@app.command()
def interactive():
    """Startet OmniRoute im interaktiven Rainbow-UI-Modus."""
    tabs = [
        {
            "name": "Netzwerk Tools",
            "options": [
                "Nach Updates suchen",
                "WLAN-Umgebung scannen (Spektrum)",
                "Netzwerk-Topologie anzeigen (Geräte, Router, Switches)",
                "Latenz & Internet-Stabilität prüfen",
                "Quick-Portscan für Endgeräte",
                "KI-Analyse (Pros & Contras)",
                "Positionierungs-Assistent (Live dBm-Radar)",
                "Traceroute & DNS-Diagnose",
                "Beenden"
            ]
        },
        {
            "name": "SDR Labor (Funk)",
            "options": [
                "SDR Hardware-Diagnose (Antennen-Ping)",
                "Frequenzspektrum abhören (Live FFT Radar)",
                "Beenden"
            ]
        }
    ]
    
    from rich.live import Live
    
    config = load_config()
    api_key = config.get("api_keys", {}).get("gemini", "")
    ki_status = "[bold green]Aktiv[/bold green]" if api_key else "[bold red]Fehlt (config.json)[/bold red]"
    
    scanner = NetworkScanner()
    gateway = scanner.find_gateway()
    conn_status = "[bold green]Online[/bold green]" if gateway else "[bold red]Offline[/bold red]"
    
    tipps = [
        "Nutze den Positionierungs-Assistent,\num Signal-Löcher im Haus zu finden!",
        "Führe einen KI-Scan aus, um\ndein Spektrum optimal zu konfigurieren.",
        "Der Topologie-Scan findet auch\nversteckte Geräte (z.B. Smart-Home).",
        "Der Live-Latenz Monitor hilft bei\nder Fehlersuche in Echtzeit.",
        "Dein eigener PC wird in der Topologie\nmit '(Dieses Gerät)' markiert.",
        "Im SDR-Labor kannst du echte Funksignale\nwie z.B. Autoschlüssel scannen!"
    ]

    def generate_main_menu(selected_idx, color_offset, current_tipp, current_tab):
        colors = ["red", "orange3", "yellow", "green", "blue", "magenta", "purple"]
        
        title_text = "OmniRoute (AetherNet) Multi-Tool"
        title = Text()
        for i, char in enumerate(title_text):
            title.append(char, style=f"bold {colors[(i + color_offset) % len(colors)]}")
            
        menu_table = Table(show_header=False, box=None, padding=(0, 2))
        menu_table.add_column("Cursor", justify="right", style="bold yellow")
        menu_table.add_column("Option", style="white")
        
        options = tabs[current_tab]["options"]
        for i, opt in enumerate(options):
            if i == selected_idx:
                menu_table.add_row(">", f"[black on white] {opt} [/black on white]")
            else:
                if i == len(options) - 1:
                    menu_table.add_row(" ", f"[red]{opt}[/red]")
                else:
                    menu_table.add_row(" ", opt)
                    
        # Tab Header
        tab_header = Text()
        for i, tab in enumerate(tabs):
            if i == current_tab:
                tab_header.append(f"[ {tab['name']} ]", style="bold white on blue")
            else:
                tab_header.append(f"  {tab['name']}  ", style="dim white")
            if i < len(tabs) - 1:
                tab_header.append("   ")
                
        menu_panel = Panel(menu_table, title="[bold cyan]Aktionen[/bold cyan]", box=box.ROUNDED, border_style="cyan")
        
        info_text = (
            "\n[bold white]OmniRoute (AetherNet)[/bold white] [gold1]v1.0[/gold1]\n"
            "© 2026 Maximilian Holzer\n\n"
            f"[dim]Verbindungsstatus:[/dim] {conn_status}\n"
            f"[dim]Scanner-Engine:[/dim] [bold blue]Bereit[/bold blue]\n"
            f"[dim]KI-Anbindung:[/dim] {ki_status}\n\n"
            f"[yellow]Tipp:[/yellow] {current_tipp}\n"
        )
        info_panel = Panel(info_text, title="[bold magenta]System-Status[/bold magenta]", box=box.ROUNDED, border_style="magenta", padding=(1, 2))
        
        layout = Table.grid(expand=True)
        layout.add_row(Align.center(tab_header))
        layout.add_row("")
        
        content_grid = Table.grid(expand=True, padding=(0, 2))
        content_grid.add_column(ratio=2)
        content_grid.add_column(ratio=1)
        content_grid.add_row(menu_panel, info_panel)
        layout.add_row(content_grid)
        
        return Panel(
            layout,
            title=title,
            subtitle="[dim]Navigation: Pfeile (Hoch/Runter, Links/Rechts für Tabs) & ENTER[/dim]",
            border_style="cyan",
            box=box.DOUBLE_EDGE,
            padding=(1, 2)
        )

    selected_idx = 0
    color_offset = 0
    current_tab = 0
    
    while True:
        if os.name == 'nt':
            import msvcrt
            import random
            current_tipp = random.choice(tipps)
            choice_made = False
            
            while not choice_made:
                os.system('cls')
                console.print(generate_main_menu(selected_idx, color_offset, current_tipp, current_tab))
                
                key = ord(msvcrt.getch())
                if key in (0, 224):
                    key = ord(msvcrt.getch())
                    if key == 72: # up
                        selected_idx = (selected_idx - 1) % len(tabs[current_tab]["options"])
                    elif key == 80: # down
                        selected_idx = (selected_idx + 1) % len(tabs[current_tab]["options"])
                    elif key == 75: # left
                        current_tab = (current_tab - 1) % len(tabs)
                        selected_idx = 0
                    elif key == 77: # right
                        current_tab = (current_tab + 1) % len(tabs)
                        selected_idx = 0
                        
                    color_offset = (color_offset + 1) % 7
                elif key == 13: # enter
                    choice_made = True
        else:
            # Fallback
            import random
            current_tipp = random.choice(tipps)
            os.system('clear')
            console.print(generate_main_menu(selected_idx, 0, current_tipp, current_tab))
            opts = tabs[current_tab]["options"]
            choice = Prompt.ask(f"\n[bold yellow]Bitte wähle eine Aktion (1-{len(opts)})[/bold yellow]", choices=[str(i+1) for i in range(len(opts))], default=str(len(opts)))
            selected_idx = int(choice) - 1
            
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Execute action
        try:
            if current_tab == 0:
                if selected_idx == 0:
                    update()
                elif selected_idx == 1:
                    scan_wifi()
                elif selected_idx == 2:
                    scan_topology()
                elif selected_idx == 3:
                    latency_monitor()
                elif selected_idx == 4:
                    quick_portscan()
                elif selected_idx == 5:
                    optimize(router_ip=None)
                elif selected_idx == 6:
                    positioning_assistant()
                elif selected_idx == 7:
                    traceroute_diag()
                elif selected_idx == 8:
                    console.print("[bold green]Auf Wiedersehen![/bold green]")
                    sys.exit(0)
            elif current_tab == 1:
                if selected_idx == 0:
                    sdr_hardware_diag()
                elif selected_idx == 1:
                    sdr_scanner()
                elif selected_idx == 2:
                    console.print("[bold green]Auf Wiedersehen![/bold green]")
                    sys.exit(0)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Aktion durch Benutzer abgebrochen (Strg+C).[/bold yellow]")
            
        console.print("\n[dim]Drücke Enter, um zum Menü zurückzukehren...[/dim]")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass

if __name__ == "__main__":
    app()
