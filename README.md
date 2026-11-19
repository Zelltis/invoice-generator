# Invoice Automation Tool (Python / Tkinter / ReportLab)

Leichtgewichtige Desktop-Anwendung zur automatisierten Erstellung rechtssicherer Rechnungen (§ 19 UStG) aus unstrukturierten E-Mail-Terminbestätigungen.

## Nutzung für Endanwender (ohne Kommandozeile)
1. **Direkt als Windows-App (`.exe`):** Unter **Releases** die fertige `Rechnungs-Generator.exe` herunterladen und per Doppelklick starten (keine Python-Installation erforderlich).
2. **Alternativ per Doppelklick-Starter:** Repository herunterladen und `start.bat` doppelklicken – das Skript erkennt automatisch `py -3`, `py`, `python`, `python3` sowie Standard-Installationspfade, richtet beim ersten Start die virtuelle Umgebung ein und startet die GUI ohne Konsolenfenster.

Beim ersten Start öffnet sich automatisch der Reiter **Stammdaten & Empfänger**, in dem Name, Adresse, Bankverbindung, Steuernummer und Empfänger eingetragen werden. Über diesen zweiten Reiter lassen sich alle Angaben später jederzeit korrigieren oder neu eingeben.

## Features
- **E-Mail-Snippet-Parser:** Extrahiert Veranstaltungsnummern, Daten, Leistungsmonat und Honorarsätze automatisch per Regex.
- **PDF-Generierung:** Erzeugt DIN-A4-Rechnungen inklusive automatischer Seitenumbrüche und fortlaufender Rechnungsnummern.
- **Stammdaten-Verwaltung im eigenen Reiter:** Trennung von Code und Konfiguration über `config.json` inklusive Reset- und Editierfunktion in der Oberfläche.
- **CI & Automated Releases:** GitHub Actions für Linting (`ruff`), Unit-Tests (`pytest`) sowie automatische `.exe`-Builds bei Version-Tags.

## Architektur
- `src/models.py` – Unveränderliche Domain-Modelle (`@dataclass`, `Decimal`)
- `src/parser.py` – Regex-basierte Extraktionslogik ohne UI-Abhängigkeiten
- `src/pdf_generator.py` – Entkoppeltes ReportLab-Rendering
- `src/config.py` – Portable Persistenz für Stammdaten und Rechnungsnummernkreis
- `src/gui.py` – `tkinter`-Oberfläche mit Tabs für Rechnungserstellung und Stammdatenpflege

## Entwickler-Setup & Tests
```bash
py -m venv .venv   # bzw. python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest -v
py main.py
```
