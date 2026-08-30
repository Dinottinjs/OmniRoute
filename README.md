# 🌐 OmniRoute (AetherNet Multi-Tool) 🌐

© 2026 Maximilian Holzer

**Das ultimative Universal Wi-Fi Router & SysAdmin Multi-Tool für Diagnose, Optimierung, Topologie-Scans und Netzwerkverwaltung.**

---

## ✨ Features (SysAdmin Pro Edition)
- 🚀 **1-Klick Installer (`start.bat`):** Einfaches Herunterladen und Ausführen für Kollegen oder Kunden ohne Vorkenntnisse. Das Skript lädt alles selbst herunter und richtet es isoliert ein.
- 📡 **Live Positionierungs-Assistent:** Radar-Feature zur Echtzeit-Analyse der Signalstärke in Dezibel (dBm) beim Herumlaufen im Gebäude.
- 🕸️ **Erweiterter Topologie-Scan:** Aktiver Multithread-Ping-Sweep zur Erkennung *aller* verbundenen Geräte, inklusive Hostname-Auflösung und **MAC-Vendor Lookup (Herstellererkennung)**.
- 📻 **SDR-Scanner (Software Defined Radio):** Echte I/Q-Datenverarbeitung von RTL-SDR USB-Dongles. Scanne z.B. 433 MHz (Smart-Home) oder 1090 MHz (ADS-B) und beobachte den Pegel (dBFS) absolut in Echtzeit (FFT-basiert).
- 📉 **Live-Latenz & Packet Loss Monitor:** Echtzeit-Darstellung von Ping, Jitter und prozentualem Paketverlust (über ein 50-Ping rollierendes Fenster).
- ⚡ **Advanced Portscan:** Scanne Endgeräte blitzschnell auf eigene Ports oder Ranges. Standardmäßig werden essenzielle Admin-Ports (RDP, SMB, DNS, NetBIOS) geprüft.
- 🗺️ **Traceroute & DNS-Diagnose:** Integriertes Routing-Analyse Tool für das einfache Verfolgen von Hops ins Internet.
- 🔄 **In-App Auto-Updater:** Automatisiertes Update-System via Git.
- 🌈 **Modernes Rainbow-UI:** Atemberaubendes Terminal-Design, flüssig bedienbar mit Pfeiltasten, sicher abgefangen durch try-except (Keine Abstürze bei Strg+C!).

---

## 🛠️ Installation & Start

### ⚡ Für Kollegen & Admins (Der einfache Weg)
Kopiere dir einfach die Datei `start.bat` auf deinen PC oder lade sie herunter.
Doppelklicke auf die **`start.bat`**. Das Skript:
1. Erstellt einen sauberen Ordner (`OmniRoute_Stable_Build`).
2. Lädt automatisch die neueste, stabile Version herunter.
3. Wenn du vorab eine `config.json` mit deinem API-Key neben die `start.bat` gelegt hast, wird diese automatisch übernommen!
4. Installiert alle benötigten Abhängigkeiten.
5. Startet die Software sofort fehlerfrei.

### 💻 Für Entwickler (Der manuelle Weg)
1. Repository klonen:
   ```bash
   git clone https://github.com/Dinottinjs/OmniRoute.git
   cd OmniRoute
   ```

2. Virtuelle Umgebung erstellen und Abhängigkeiten installieren:
   ```bash
   python -m venv venv
   # Unter Windows: venv\Scripts\activate
   # Unter Linux/Mac: source venv/bin/activate
   pip install -r requirements.txt
   ```

3. (Optional) Konfiguration erstellen:
   Erstelle eine Datei namens `config.json` für die KI-Engine:
   ```json
   {
       "api_keys": {
           "gemini": "DEIN_API_KEY"
       }
   }
   ```

4. Software im interaktiven Menü starten:
   ```bash
   python main.py interactive
   ```

---

## 🎮 Bedienung & Handling
Das Tool wurde extrem nutzerfreundlich entwickelt. Du navigierst simpel über die **Pfeiltasten (Hoch/Runter)** und wählst Aktionen mit **ENTER** aus.
Lang andauernde Vorgänge wie Pings, Scans oder Traceroutes kannst du jederzeit sicher mit **Strg+C** abbrechen, ohne dass das Programm abstürzt. Du landest dann sofort wieder im Hauptmenü.
