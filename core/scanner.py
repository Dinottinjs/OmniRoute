import subprocess
import re
import platform

class NetworkScanner:
    def __init__(self):
        self.os_type = platform.system()

    def find_gateway(self):
        """Ermittelt die IP des lokalen Standard-Gateways (Router)."""
        gateway_ip = None
        if self.os_type == "Windows":
            try:
                result = subprocess.run(["route", "print", "0.0.0.0"], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if "0.0.0.0" in line and "Auf Verbindung" not in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            gateway_ip = parts[2]
                            break
            except Exception:
                pass
        elif self.os_type == "Linux":
            try:
                result = subprocess.run(["ip", "route"], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if line.startswith("default via"):
                        gateway_ip = line.split()[2]
                        break
            except Exception:
                pass
        elif self.os_type == "Darwin": # macOS
            try:
                result = subprocess.run(["route", "-n", "get", "default"], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if "gateway:" in line:
                        gateway_ip = line.split()[1]
                        break
            except Exception:
                pass
                
        return gateway_ip

    def scan_wifi(self):
        """
        Scannt die WLAN-Umgebung nach SSIDs, Signalstärke und Kanälen.
        Gibt eine Liste von Dictionaries zurück.
        """
        networks = []
        if self.os_type == "Windows":
            try:
                # netsh wlan show networks mode=bssid
                result = subprocess.run(["netsh", "wlan", "show", "networks", "mode=bssid"], capture_output=True, text=True, encoding='cp850')
                output = result.stdout
                
                current_ssid = ""
                for line in output.split('\n'):
                    line = line.strip()
                    if line.startswith("SSID"):
                        parts = line.split(":")
                        if len(parts) > 1:
                            current_ssid = parts[1].strip()
                    elif line.startswith("Signal"):
                        signal_str = line.split(":")[1].strip().replace("%", "")
                        signal = int(signal_str) if signal_str.isdigit() else 0
                        dbm = int((signal / 2) - 100)
                    elif line.startswith("Kanal") or line.startswith("Channel"):
                        channel_str = line.split(":")[1].strip()
                        channel = int(channel_str) if channel_str.isdigit() else 0
                        if current_ssid:
                            networks.append({
                                "ssid": current_ssid,
                                "signal": signal,
                                "dbm": dbm,
                                "channel": channel
                            })
            except Exception as e:
                print(f"Fehler beim WLAN-Scan unter Windows: {e}")
                
        elif self.os_type == "Darwin":
            # macOS Airport Tool
            airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
            try:
                result = subprocess.run([airport_path, "-s"], capture_output=True, text=True)
                lines = result.stdout.split('\n')[1:] # Skip header
                for line in lines:
                    if line.strip():
                        # Parsing SSID, BSSID, RSSI, Channel, etc.
                        # Simple regex for typical output
                        match = re.search(r'^(.*?)\s+([0-9a-fA-F:]+)\s+(-\d+)\s+(\d+)', line)
                        if match:
                            networks.append({
                                "ssid": match.group(1).strip(),
                                "signal": 0, # RSSI percent placeholder
                                "dbm": int(match.group(3)),
                                "channel": int(match.group(4))
                            })
            except Exception:
                pass
                
        elif self.os_type == "Linux":
            try:
                # Require nmcli
                result = subprocess.run(["nmcli", "-t", "-f", "SSID,SIGNAL,CHAN", "dev", "wifi"], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split(':')
                        if len(parts) == 3:
                            signal_val = int(parts[1]) if parts[1].isdigit() else 0
                            networks.append({
                                "ssid": parts[0],
                                "signal": signal_val,
                                "dbm": int((signal_val / 2) - 100),
                                "channel": int(parts[2]) if parts[2].isdigit() else 0
                            })
            except Exception:
                pass
                
        return networks

    def scan_topology(self):
        """Führt einen lokalen Netzwerk-Scan durch Auslesen der ARP-Tabelle durch (ohne externe Npcap-Abhängigkeiten)."""
        devices = []
        gateway_ip = self.find_gateway()
        if not gateway_ip:
            return []
            
        try:
            if self.os_type == "Windows":
                # Quick broadcast ping to populate ARP cache
                subnet = gateway_ip.rsplit('.', 1)[0]
                subprocess.run(["ping", "-n", "1", "-w", "200", f"{subnet}.255"], capture_output=True)
                
                result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    # Typical windows arp -a line: 192.168.1.1       00-11-22-33-44-55     dynamisch
                    if len(line) > 0 and not line.startswith("Schnittstelle") and not line.startswith("Interface") and not line.startswith("Internetadresse"):
                        parts = line.split()
                        if len(parts) >= 2 and parts[0].count('.') == 3 and parts[1].count('-') == 5:
                            ip = parts[0]
                            mac = parts[1]
                            # Filter out multicast/broadcast addresses
                            if ip != "255.255.255.255" and not ip.startswith("224.") and not ip.startswith("239.") and not ip.endswith(".255"):
                                devices.append({'ip': ip, 'mac': mac})
                                
            else:
                # Linux/macOS
                subnet = gateway_ip.rsplit('.', 1)[0]
                subprocess.run(["ping", "-c", "1", "-W", "1", f"{subnet}.255"], capture_output=True)
                result = subprocess.run(["arp", "-an"], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    match = re.search(r'\((.*?)\) at ([0-9a-fA-F:]+)', line)
                    if match:
                        devices.append({'ip': match.group(1), 'mac': match.group(2)})
                        
            # Filter duplicates
            unique_devices = {dev['ip']: dev['mac'] for dev in devices}
            return [{'ip': ip, 'mac': mac} for ip, mac in unique_devices.items()]
            
        except Exception as e:
            return [{"ip": "Error", "mac": f"Fehler bei ARP-Scan: {e}"}]

    def port_scan(self, ip: str, ports: list = None):
        """Führt einen schnellen TCP-Portscan durch."""
        import socket
        if ports is None:
            # Häufige Router/Admin/Web-Ports
            ports = [21, 22, 80, 443, 8080, 8443, 7547, 5000]
        open_ports = []
        for port in ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    result = s.connect_ex((ip, port))
                    if result == 0:
                        open_ports.append(port)
            except Exception:
                pass
        return open_ports

    def ping_measure(self, host="1.1.1.1"):
        """Misst die Latenz (Ping) zu einem Host und gibt sie in ms zurück."""
        try:
            if self.os_type == "Windows":
                result = subprocess.run(["ping", "-n", "1", "-w", "1000", host], capture_output=True, text=True, encoding='cp850', errors='ignore')
                # Parse: Zeit=12ms or time=12ms or Zeit<1ms
                match = re.search(r"Zeit[=<](\d+)ms|time[=<](\d+)ms", result.stdout, re.IGNORECASE)
                if match:
                    val = match.group(1) if match.group(1) else match.group(2)
                    return int(val)
            else:
                result = subprocess.run(["ping", "-c", "1", "-W", "1", host], capture_output=True, text=True, errors='ignore')
                match = re.search(r"time=(\d+\.?\d*) ms", result.stdout)
                if match:
                    return int(float(match.group(1)))
        except Exception:
            pass
        return -1

    def get_live_signal(self, target_ssid: str) -> int:
        """
        Gibt die Echtzeit-Signalstärke in dBm für eine SSID zurück.
        Auf Windows wird die verbundene SSID live ohne Caching abgefragt.
        """
        if self.os_type == "Windows":
            try:
                result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, encoding='cp850', errors='ignore')
                connected_ssid = None
                dbm = -100
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith("SSID") and not line.startswith("SSID-") and not line.startswith("BSSID"):
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            connected_ssid = parts[1].strip()
                    elif line.startswith("RSSI"):
                        parts = line.split(":")
                        if len(parts) > 1:
                            rssi_str = parts[1].strip()
                            if rssi_str.lstrip('-').isdigit():
                                dbm = int(rssi_str)
                    elif line.startswith("Signal") and dbm == -100:
                        parts = line.split(":")
                        if len(parts) > 1:
                            sig_str = parts[1].strip().replace("%", "")
                            if sig_str.isdigit():
                                dbm = int((int(sig_str) / 2) - 100)
                                
                if connected_ssid == target_ssid and dbm != -100:
                    return dbm
            except Exception:
                pass
                
        # Fallback auf gecachten Scan (oder macOS/Linux)
        nets = self.scan_wifi()
        target = next((n for n in nets if n['ssid'] == target_ssid), None)
        if target:
            return target.get('dbm', -100)
        return -100
