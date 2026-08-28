from .base import BaseRouterAdapter
import paramiko

class OpenWrtSSHAdapter(BaseRouterAdapter):
    """
    SSH-Adapter für OpenWrt, DD-WRT und Linux-basierte Router.
    Nutzt 'uci' Befehle für die Konfiguration bei OpenWrt.
    """
    
    def __init__(self, ip: str):
        super().__init__(ip)
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
    def login(self, credentials: dict) -> bool:
        try:
            self.ssh.connect(
                hostname=self.ip,
                username=credentials.get("username", "root"),
                password=credentials.get("password", ""),
                timeout=5
            )
            self.is_logged_in = True
            return True
        except Exception as e:
            print(f"SSH Login fehlgeschlagen: {e}")
            return False

    def _run_cmd(self, cmd: str) -> str:
        if not self.is_logged_in:
            return ""
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        return stdout.read().decode('utf-8').strip()

    def get_current_config(self) -> dict:
        if not self.is_logged_in:
            return {}
        # Beispiel: uci get wireless.radio0.channel
        chan24 = self._run_cmd("uci get wireless.radio0.channel")
        return {"os": "OpenWrt", "channel_24": chan24}

    def set_channel(self, band: str, channel: int) -> bool:
        radio = "radio0" if band == "2.4" else "radio1"
        self._run_cmd(f"uci set wireless.{radio}.channel='{channel}'")
        self._run_cmd("uci commit wireless")
        self._run_cmd("wifi reload")
        return True

    def set_channel_width(self, band: str, width_mhz: int) -> bool:
        # Placeholder for HTmode
        return True

    def set_tx_power(self, band: str, percentage: int) -> bool:
        # Umrechnung in txpower dBm erforderlich
        return True

    def reboot(self) -> bool:
        self._run_cmd("reboot")
        return True
