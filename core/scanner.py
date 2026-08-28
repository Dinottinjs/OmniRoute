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
                    elif line.startswith("Kanal") or line.startswith("Channel"):
                        channel_str = line.split(":")[1].strip()
                        channel = int(channel_str) if channel_str.isdigit() else 0
                        if current_ssid:
                            networks.append({
                                "ssid": current_ssid,
                                "signal": signal,
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
                                "signal": int(match.group(3)), # RSSI
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
                            networks.append({
                                "ssid": parts[0],
                                "signal": int(parts[1]) if parts[1].isdigit() else 0,
                                "channel": int(parts[2]) if parts[2].isdigit() else 0
                            })
            except Exception:
                pass
                
        return networks

    def scan_topology(self):
        """Führt einen ARP-Scan im lokalen Subnetz (meist /24) durch."""
        try:
            import scapy.all as scapy
        except ImportError:
            return [{"ip": "Error", "mac": "Scapy nicht installiert"}]
            
        gateway_ip = self.find_gateway()
        if not gateway_ip:
            return []
            
        # Wir nehmen vereinfacht ein /24 Subnetz an
        target_ip = gateway_ip.rsplit('.', 1)[0] + '.0/24'
        
        try:
            arp = scapy.ARP(pdst=target_ip)
            ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether/arp
            
            # Senden und Empfangen der Pakete
            result = scapy.srp(packet, timeout=2, verbose=0)[0]
            
            devices = []
            for sent, received in result:
                devices.append({'ip': received.psrc, 'mac': received.hwsrc})
            return devices
        except Exception as e:
            return [{"ip": "Error", "mac": f"Fehler (Admin-Rechte prüfen?): {e}"}]
