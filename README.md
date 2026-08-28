# OmniRoute (AetherNet Multi-Tool)

Universal Wi-Fi Router Multi-Tool CLI & Agent for diagnostics, optimization, and configuration.

## Features
- **Bootstrap & Asset-Updater:** Automatic downloading of updates and dependencies with visual progress.
- **Universal Router Adapter Layer:** Abstracted interfaces for routers using TR-064/UPnP, SSH, and generic Playwright-based web scraping.
- **AI Optimization Agent:** Google Gemini AI-powered spectrum analysis and channel planning.
- **Interactive CLI:** Modern CLI built with `typer` and `rich`.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Dinottinjs/OmniRoute.git
   cd OmniRoute
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Setup Playwright (if using the Web Scraper Adapter):
   ```bash
   playwright install
   ```

4. Configure your API Keys and settings in `config.json`.

## Usage
Run the CLI to see available commands:
```bash
python main.py --help
```
