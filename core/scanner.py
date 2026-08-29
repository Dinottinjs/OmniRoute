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
        import concurrent.futures
        
        devices = []
        gateway_ip = self.find_gateway()
        if not gateway_ip:
            return []
            
        try:
            subnet = gateway_ip.rsplit('.', 1)[0]
            ips_to_scan = [f"{subnet}.{i}" for i in range(1, 255)]
            
            def ping_target(ip_addr):
                if self.os_type == "Windows":
                    # Sehr kurzer Timeout (300ms), da wir nur den ARP-Request triggern wollen, 
                    # selbst wenn ICMP von Firewalls blockiert wird!
                    subprocess.run(["ping", "-n", "1", "-w", "300", ip_addr], capture_output=True)
                else:
                    subprocess.run(["ping", "-c", "1", "-W", "1", ip_addr], capture_output=True)
                    
            # 50 Threads parallel pingen lassen -> dauert insgesamt nur ca. 1.5 bis 2 Sekunden
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                executor.map(ping_target, ips_to_scan)
                
            if self.os_type == "Windows":
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
                # Linux/macOS ARP Cache auslesen
                result = subprocess.run(["arp", "-an"], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    match = re.search(r'\((.*?)\) at ([0-9a-fA-F:]+)', line)
                    if match:
                        devices.append({'ip': match.group(1), 'mac': match.group(2)})
                        
            # Filter duplicates and extract unique devices
            unique_devices = {dev['ip']: dev['mac'] for dev in devices}
            result_devices = [{'ip': ip, 'mac': mac} for ip, mac in unique_devices.items()]
            
            COMMON_OUI = {
                "B8:27:EB": "Raspberry Pi", "DC:A6:32": "Raspberry Pi", "E4:5F:01": "Raspberry Pi",
                "00:1A:11": "Google", "3C:5A:B4": "Google", "F4:F5:DB": "Google",
                "C0:25:06": "AVM (Fritz!Box)", "08:96:D7": "AVM (Fritz!Box)", "34:31:C4": "AVM (Fritz!Box)", 
                "3C:A6:2F": "AVM (Fritz!Box)", "44:4E:6D": "AVM (Fritz!Box)", "C8:0E:14": "AVM (Fritz!Box)",
                "FC:AF:6A": "Apple", "00:17:F2": "Apple", "00:1C:B3": "Apple", "00:1E:52": "Apple", 
                "00:23:12": "Apple", "00:25:BC": "Apple", "F4:0F:24": "Apple", "2C:F0:EE": "Apple",
                "00:15:6D": "Ubiquiti", "04:18:D6": "Ubiquiti", "18:E8:29": "Ubiquiti", "24:5A:4C": "Ubiquiti",
                "00:14:22": "Dell", "F8:DB:88": "Dell", "00:1D:09": "Dell", "E0:D5:5E": "Dell",
                "00:50:56": "VMware", "00:0C:29": "VMware", "00:05:69": "VMware", "08:00:27": "VirtualBox",
                "00:11:32": "Synology", "A8:5E:45": "Nintendo", "00:18:8E": "Nintendo",
                "00:22:D7": "Sony", "00:24:8D": "Sony", "00:1A:A9": "Sony",
                "00:23:CD": "TP-Link", "0C:E3:10": "TP-Link", "14:CC:20": "TP-Link", "50:C7:BF": "TP-Link",
                "00:E0:4C": "Realtek", "52:54:00": "QEMU", "00:25:9C": "Cisco"
            }
            
            # Hostnames auflösen (Multithreaded für maximale Geschwindigkeit)
            import socket
            def resolve_hostname(device):
                try:
                    socket.setdefaulttimeout(0.3)
                    hostname = socket.gethostbyaddr(device['ip'])[0]
                    device['hostname'] = hostname
                except Exception:
                    device['hostname'] = "Unbekannt"
                    
                mac_prefix = str(device['mac']).upper()[:8].replace("-", ":")
                device['vendor'] = COMMON_OUI.get(mac_prefix, "Unbekannt")
                    
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                executor.map(resolve_hostname, result_devices)
                
            # Eigenes (Host) Gerät zur Liste hinzufügen
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect((gateway_ip, 1))
                local_ip = s.getsockname()[0]
                s.close()
                
                import uuid
                mac_num = hex(uuid.getnode()).replace('0x', '').upper()
                local_mac = '-'.join(mac_num[i: i + 2] for i in range(0, 11, 2))
                
                host_entry = next((d for d in result_devices if d['ip'] == local_ip), None)
                if not host_entry:
                    result_devices.insert(0, {'ip': local_ip, 'mac': local_mac, 'hostname': f"{socket.gethostname()} (Dieses Gerät)"})
                else:
                    host_entry['hostname'] = f"{socket.gethostname()} (Dieses Gerät)"
            except Exception:
                pass
                
            return result_devices
            
        except Exception as e:
            return [{"ip": "Error", "mac": f"Fehler bei ARP-Scan: {e}"}]

    def port_scan(self, ip: str, ports: list = None):
        """Führt einen schnellen TCP-Portscan durch."""
        import socket
        if ports is None:
            # Häufige Router/Admin/Web-Ports + RDP, SMB, DNS, NetBIOS
            ports = [21, 22, 53, 80, 139, 443, 445, 3389, 5000, 7547, 8080, 8443]
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
