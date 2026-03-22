# MusicXML Sanitizer & Auditor

Ein robustes Tool zur semantischen Reinigung, Fehlererkennung und Normalisierung von MusicXML-Dateien, speziell entwickelt für die Anforderungen der Barrierefreiheit (dzb lesen).

## Aktueller Status (Stand: heute)
*   **Backend:** FastAPI Server läuft auf Port 8001. Er lädt MusicXML/MXL Dateien und wendet einen Pre-Processor an.
*   **Pre-Processor:** Injektion von stabilen IDs (`m-idx-X`) in `<measure>` Tags zur Identifikation im Frontend.
*   **Frontend:** Verovio-WASM Integration mit MEI-basierter Navigation.
*   **Navigation:** Gelöst! Große Dateien (Beethoven, 19 Seiten) werden nun präzise durchsucht. Die UI analysiert das interne MEI-Modell von Verovio, um die korrekte Seite für den Takt-Sprung zu finden (getMEI-Analyse).

## Bekannte Probleme / Next Steps
*   **Stichnoten-Audit:** Auditor erkennt übervolle Takte durch kleine Notenköpfe (Grace-Notes mit falscher Duration). 
*   **Fix-Modus:** Implementierung eines "Heilungs-Buttons", um verdächtige Noten im XML zu `<grace/>` Tags mit Duration 0 zu konvertieren.
*   **Report-Mapping:** Die UI zeigt aktuell noch "Unbekannter Fehler", da die JSON-Struktur (`file`, `status`, `issues`, `actions`) im Frontend gemappt werden muss.

## Starten
1. Server: `python api/server.py` oder `uvicorn api.server:app --port 8001`
2. Browser: `http://127.0.0.1:8001`

## Installation & Start

1. Abhängigkeiten installieren:
   python -m pip install typer rich music21 lxml fastapi uvicorn

2. CLI Batch-Processing:
   Lege MusicXML/MXL Dateien in den Ordner input/ und starte:
   python cli.py --input input

3. Web-UI starten:
   python -m uvicorn api.server:app --port 8001
   Öffne http://127.0.0.1:8001 im Browser.

## Projektstruktur
- core/pre_processor.py: XML-Reparatur auf Textebene.
- core/voice_analyzer.py: Musikalische Logikprüfung.
- api/server.py: Backend für die Web-Vorschau.
- static/index.html: Frontend mit Verovio-Integration.