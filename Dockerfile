# Nutze Python 3.11 als Basis-Image
FROM python:3.11-slim

# Verhindert, dass Python pyc-Dateien schreibt und puffert
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# System-Abhängigkeiten installieren, die für Netzwerkscans und Playwright benötigt werden
RUN apt-get update && apt-get install -y \
    iproute2 \
    wireless-tools \
    network-manager \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Kopiere die requirements.txt in den Container
COPY requirements.txt .

# Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Installiere Playwright Browser (Chromium)
RUN playwright install chromium
RUN playwright install-deps

# Kopiere den gesamten Quellcode in den Container
COPY . .

# Führe das Skript aus
# Standardbefehl (kann beim docker run überschrieben werden)
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
