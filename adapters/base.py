from abc import ABC, abstractmethod

class BaseRouterAdapter(ABC):
    """
    Abstrakte Basisklasse für alle Router-Adapter.
    Jeder spezifische Adapter muss diese Methoden implementieren.
    """
    
    def __init__(self, ip: str):
        self.ip = ip
        self.session = None
        self.is_logged_in = False
        
    @abstractmethod
    def login(self, credentials: dict) -> bool:
        """Führt den Login am Router durch."""
        pass
        
    @abstractmethod
    def get_current_config(self) -> dict:
        """Ruft die aktuelle WLAN- und System-Konfiguration ab."""
        pass
        
    @abstractmethod
    def set_channel(self, band: str, channel: int) -> bool:
        """Setzt den WLAN-Kanal (band z.B. '2.4' oder '5')."""
        pass
        
    @abstractmethod
    def set_channel_width(self, band: str, width_mhz: int) -> bool:
        """Setzt die Kanalbandbreite (20/40/80/160)."""
        pass
        
    @abstractmethod
    def set_tx_power(self, band: str, percentage: int) -> bool:
        """Setzt die Sendeleistung (in Prozent)."""
        pass
        
    @abstractmethod
    def reboot(self) -> bool:
        """Startet den Router neu."""
        pass
