# 🌐 OmniRoute (AetherNet Multi-Tool) 🌐

© 2026 Maximilian Holzer

Universal Wi-Fi Router Multi-Tool & CLI-Agent für Diagnose, Optimierung, Topologie-Scans und Netzwerkverwaltung.

---

## ✨ Features
- 🚀 **1-Klick Installer (start.bat):** Einfaches Herunterladen und Ausführen für Kollegen ohne Vorkenntnisse.
- 📡 **Live Positionierungs-Assistent:** Radar-Feature zur Echtzeit-Analyse der Signalstärke in Dezibel (dBm) beim Herumlaufen im Haus.
- 🕸️ **Netzwerk-Topologie Scan:** Aktiver Multithread-Ping-Sweep zur 100% genauen Erkennung *aller* verbundenen Geräte (inkl. intelligenter Hostname-Auflösung 💻).
- 🤖 **KI-Netzwerkanalyse:** Automatisierte Diagnose und Fehlerbehebung im Netzwerk mithilfe von Google Gemini.
- 🔄 **In-App Auto-Updater:** Automatisiertes Update-System via Git, um immer auf der neusten Version zu sein.
- ⚡ **Quick-Portscan & Latenz-Monitor:** Echzeit-Ping und Portscanner für schnelle Fehlerdiagnosen.
- 🌈 **Modernes Rainbow-UI:** Atemberaubendes Terminal-Design, bedienbar mit Pfeiltasten und extrem flüssig dank `rich`.

---

## 🛠️ Installation & Start

### ⚡ Für Kollegen & Nutzer (Einfacher Weg)
Lade dir einfach das Repository herunter oder kopiere die `start.bat`.
Doppelklicke auf die **`start.bat`**. Das Skript:
1. Lädt automatisch die neueste, stabile Version von OmniRoute herunter.
2. Installiert alle benötigten Abhängigkeiten.
3. Startet die Software sofort fehlerfrei.

### 💻 Für Entwickler (Manueller Weg)
1. Repository klonen:
   ```bash
   git clone https://github.com/Dinottinjs/OmniRoute.git
   cd OmniRoute
   ```

2. Virtuelle Umgebung erstellen und Abhängigkeiten installieren:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unter Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Setup Playwright (falls der Web Scraper Adapter genutzt wird):
   ```bash
   playwright install
   ```

## 🎮 Bedienung
Führe das Hauptskript interaktiv aus, um in das Menü zu gelangen:
```bash
python main.py interactive
```

Alternativ kannst du die Hilfe im CLI aufrufen:
```bash
python main.py --help
```
