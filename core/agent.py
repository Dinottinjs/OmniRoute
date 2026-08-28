import json
from google import genai

class RouterAgent:
    def __init__(self, config: dict):
        self.config = config
        self.api_key = config.get("api_keys", {}).get("gemini", "")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def analyze(self, networks: list, router_config: dict, mode: str = "manual"):
        """
        Analysiert die Spektrumsdaten und aktuelle Router-Konfiguration
        und gibt Optimierungsvorschläge zurück.
        """
        if not self.client:
            return "KI-Optimierung nicht verfügbar. Bitte füge einen gültigen Gemini API-Key in der config.json hinzu."
            
        system_prompt = (
            "Du bist ein leitender Netzwerk-Architekt. Deine Aufgabe ist es, das WLAN-Spektrum "
            "und die Konfiguration eines lokalen Routers zu analysieren. Berücksichtige Kanalüberlappung "
            "und Interferenzen (2.4 GHz und 5 GHz). "
            f"Der Nutzer wünscht den Modus: {mode}. "
            "Wenn 'manual', gib eine Schritt-für-Schritt-Anleitung für die Weboberfläche. "
            "Wenn 'auto', generiere eine knappe JSON-Payload zur direkten Anwendung durch die API."
        )
        
        user_prompt = f"Gefundene WLAN-Netzwerke in der Umgebung:\n{json.dumps(networks, indent=2)}\n\nAktuelle Router-Konfiguration:\n{json.dumps(router_config, indent=2)}"
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"System: {system_prompt}\n\nUser: {user_prompt}"
            )
            return response.text
        except Exception as e:
            return f"Fehler bei der KI-Analyse: {e}"
