# MusicXML Sanitizer & Auditor

Ein intelligentes Tool-Set zur automatischen Bereinigung, Analyse und Visualisierung von MusicXML-Dateien. Speziell optimiert für komplexe Klavierliteratur (z. B. Beethoven-Sonaten) und die Vorbereitung für digitale Archivierung oder Web-Rendering.

## Kern-Features

### 1. Intelligenter Sanitizer (Pre-Processor)
- Voice Merging: Erkennt redundante Stimmen-Splits in Klaviersystemen und führt sie automatisch in Stimme 1 (rechts) bzw. Stimme 5 (links) zusammen.
- Chord Fusion: Erkennt durch backup/forward getrennte Noten auf derselben Zählzeit und transformiert sie in echte MusicXML chord-Strukturen.
- Redundancy Cleanup: Löscht automatisch Filler Rests (überlappende Pausen), die durch fehlerhafte Exporte oder OCR-Scans entstanden sind.
- Automatic Healing Log: Erstellt ein detailliertes Protokoll (.log.txt) über jeden automatischen Eingriff (z. B. verschobene Stimmen, gelöschte Pausen).

### 2. Rhythmus-Auditor (VoiceAnalyzer)
- Mathematische Bilanz: Nutzt music21, um die rhythmische Füllung jedes Taktes gegen die Taktart zu prüfen.
- Overfill Detection: Markiert Takte, die z. B. durch nicht-deklarierte Stichnoten (Grace Notes mit Duration) mathematisch zu lang sind.
- Audit Report: Generiert eine präzise actions.json für jede Datei zur Darstellung in der Web-UI.

### 3. Web-UI & Visualisierung
- Verovio-WASM Integration: High-Performance Rendering direkt im Browser.
- Präzise Navigation: Eigens entwickelte MEI-Analyse-Logik, die Taktnummern im internen Verovio-Modell lokalisiert. Garantiert korrekte Sprünge (z. B. Takt 512 auf Seite 18) auch bei Partituren mit 100+ Seiten.
- Synchronisierte Sidebar: Klickbare Issue-Liste führt sofort zur markierten Stelle im Notenbild.

## Projektstruktur
- cli.py: Haupt-Pipeline (Sanitize -> Audit -> Report)
- core/pre_processor.py: Musikalische Heilungs-Logik & XML-Fixes
- core/voice_analyzer.py: Rhythmus-Analyse via music21
- api/server.py: FastAPI Backend (Port 8001)
- static/index.html: Verovio Web-Frontend
- input/: Quell-Dateien (.mxl, .musicxml) [Ignoriert in Git]
- needs_review/: Output: Geheiltes XML, JSON-Report, Log-Protokoll [Ignoriert in Git]

## Installation & Start
1. Abhängigkeiten installieren:
   pip install fastapi uvicorn music21

2. Pipeline ausführen (Legt eine Datei in input/ ab):
   python cli.py

3. Web-UI starten:
   python api/server.py

Öffne danach http://127.0.0.1:8001 im Browser.

## Technischer Hintergrund: Der Sprung-Fix
Um große Partituren stabil zu navigieren, nutzt das Tool das getMEI()-Modul des Verovio-Toolkits. Da MusicXML-IDs beim Import oft transformiert werden, extrahiert die UI zur Laufzeit die internen xml:ids basierend auf der musikalischen Taktnummer (n) aus dem MEI-DOM. Dies löst das Problem von verschobenen Seitenindizes in großen Dateien.
