# MusicXML Sanitizer & Normalizer

Ein robustes Tool zur Aufbereitung von MusicXML-Dateien für barrierefreie Anwendungen (Großdruck und Braille-Konvertierung). Entwickelt in Kooperation mit Anforderungen der *dzb lesen*.

## Features (Aktueller Stand)
- **Robust Parsing**: Liest .xml, .musicxml und .mxl (komprimiert).
- **Automatischer Fix**: Erkennt und korrigiert "unmögliche" Notenwerte (z.B. 2048stel), die zum Absturz in Notensatzprogrammen führen.
- **Takt-Analyse**: Identifiziert übervolle oder unvollständige Takte.
- **Web-Review**: Eine Web-Oberfläche (Verovio) zur visuellen Prüfung von Problemstellen.
- **Audit-Log**: Automatische Einsortierung in `output_cleaned` oder `needs_review`.

## Installation
1. Repository klonen
2. Abhängigkeiten installieren:
   ```bash
   pip install music21 lxml typer rich fastapi uvicorn python-multipart