# MusicXML Sanitizer & Auditor

Ein intelligentes Tool-Set zur automatischen Bereinigung, Analyse und Visualisierung von MusicXML-Dateien. Optimiert für komplexe Klavierliteratur und die Vorbereitung für digitale Archivierung.

## Aktueller Meilenstein: Beethoven-Case (Op. 10 No. 1)
- **Erfolgreiche Heilung:** Reduzierung der Audit-Issues von 40 auf 5 durch intelligente Vorverarbeitung.
- **WASM-Stabilität:** Implementierung einer Strict-Ordering-Logik für XML-Tags zur Vermeidung von Speicherfehlern im Verovio-Frontend.

## Kern-Features

### 1. Intelligenter Sanitizer (Pre-Processor)
- In-Place Voice Merging: Schiebt fragmentarische Nebenstimmen in die Hauptstimme, sofern keine rhythmische Kollision vorliegt.
- Grace-Note-Transformation: Erkennt übervolle Takte und wandelt dekorative Kleinst-Notenwerte (16th bis 256th) automatisch in mathematisch neutrale Grace-Notes um.
- Redundancy Cleanup: Identifiziert und löscht Pausen, die exakt auf der Zeitposition einer Note liegen (Filler-Rest-Beseitigung).
- Strict Tag Ordering: Sortiert Kind-Elemente innerhalb der Note-Tags nach MusicXML-Schema, um Rendering-Abstürze (Out of bounds) zu verhindern.

### 2. Rhythmus-Auditor (VoiceAnalyzer)
- Nutzt music21 für eine tiefgehende mathematische Prüfung der Takt-Bilanz.
- Erzeugt präzise JSON-Berichte für jede bearbeitete Datei.

### 3. Web-UI & Visualisierung
- High-Performance Rendering via Verovio-WASM.
- MEI-Analyse-Navigation: Extrahiert zur Laufzeit IDs aus dem internen MEI-Modell, um punktgenaue Sprünge zu Taktnummern in großen Partituren zu ermöglichen.

## Projektstruktur
- cli.py: Haupt-Pipeline (Sanitize -> Audit -> Report)
- core/pre_processor.py: Musikalische Heilungs-Logik (In-Place Methode)
- core/voice_analyzer.py: Rhythmus-Analyse via music21
- api/server.py: FastAPI Backend (Port 8001)
- static/index.html: Verovio Web-Frontend

## Start
1. Abhängigkeiten: fastapi, uvicorn, music21
2. Pipeline: python cli.py (Verarbeitet input/ nach needs_review/)
3. Web-UI: python api/server.py (Öffne http://127.0.0.1:8001)

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
