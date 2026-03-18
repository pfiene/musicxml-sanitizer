# MusicXML Sanitizer & Auditor

Ein robustes Tool zur semantischen Reinigung, Fehlererkennung und Normalisierung von MusicXML-Dateien, speziell entwickelt für die Anforderungen der Barrierefreiheit (dzb lesen).

## Aktueller Funktionsumfang (PoC Phase 1)

- Robustes Pre-Processing: Repariert kritische MusicXML-Exportfehler (z.B. mathematisch ungültige 2048stel-Noten) auf Textebene, bevor sie die Musik-Engine erreichen.
- Takt-Analyse: Erkennt übervolle Takte und "hineinfabulierte" Pausen (Filler Rests) durch eine Voice-Slice-Analyse.
- Audit-Logging: Generiert einen detaillierten JSON-Report (audit_report.json) über alle gefundenen Probleme und vorgenommenen Korrekturen.
- Web-UI Review Queue: Visualisierung der Noten mit Verovio (WASM), geteilte Sidebar mit Dateiliste und dynamischer Problemliste pro Datei.
- RAW-Safe Fallback: Stellt sicher, dass selbst bei komplexesten Dateien (wie Beethoven) ein bereinigtes XML für die Sichtprüfung erhalten bleibt.

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