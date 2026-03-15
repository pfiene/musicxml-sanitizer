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

## Nutzung
1. Batch-Verarbeitung (CLI)
Lege deine Dateien in den Ordner input und starte:
python cli.py --input input
Die Ergebnisse landen in output_cleaned (sauber) oder needs_review (manuelle Prüfung nötig).
2. Web-UI (Review Queue)
Starte das Backend:
uvicorn api.server:app --reload
Öffne dann die webapp/index.html in deinem Browser.
## Roadmap / TODO

1. SATB-Normalisierung: Automatisches Aufspalten von 2-System-Chorsätzen in 4-System-SATB.

2. Shift-Left Algorithmus: Aktive rhythmische Korrektur durch Entfernen von Geister-Pausen.

3. Braille-Profil: Radikale Entfernung aller visuellen Layout-Tags für optimierten Braille-Export.
