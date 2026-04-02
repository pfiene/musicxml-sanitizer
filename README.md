# MusicXML Sanitizer & Auditor: Meilenstein Interaktives Dashboard

Dieses Repository enthält den aktuellen Stand des MusicXML Sanitizers. In dieser Session wurde das Projekt von einem reinen Analyse-Tool zu einer interaktiven Web-Applikation mit Echtzeit-Feedback ausgebaut.

## Aktueller Stand (Ende Session 2)

### 1. Funktionale Highlights
- **Interaktives Healing-UI:** Integration von FastAPI (Backend) und Verovio-WASM (Frontend). Nutzer können nun über spezifische Buttons ("Pause entfernen", "Mit Pausen auffüllen", "Stichnoten umwandeln") Korrektur-Algorithmen triggern.
- **Punktgenaue MEI-Navigation:** Implementierung eines Namespace-agnostischen Sprung-Mechanismus. Das System analysiert das interne MEI-Modell von Verovio, findet die exakte SVG-ID des Taktes und navigiert (inkl. Seitenwechsel) direkt zum Ziel.
- **Visuelles Feedback (Gauge System):** Die UI bietet nun Echtzeit-Statusmeldungen ("Heile... ⏳", "Geheilt ✔️"). Buttons werden während des Prozesses deaktiviert, um inkonsistente Dateizustände zu verhindern.
- **Auditor-Intelligenz:** Reduzierung von False-Positives durch Erkennung von Auftakten (Anacrusis) an Wiederholungszeichen und Doppelstrichen.

### 2. Technische Infrastruktur
- `api/server.py`: Zentraler FastAPI-Server mit Endpunkten für Datei-Listing, Report-Abfrage und den `apply-fix`-Mechanismus.
- `core/voice_analyzer.py`: Mathematische Rhythmus-Validierung (music21) mit erweitertem Kontext-Bewusstsein für musikalische Strukturen.
- `core/reconstructor.py`: Bibliothek für chirurgische Eingriffe in den MusicXML-Stream (Grace-Note-Konvertierung, Filler-Rest-Deletion).

## Bekannte Hürden (Blocker für Session 3)

### Das "Takt 512" Paradoxon
Trotz mehrstufiger Reinigungsversuche (Regex & Objekt-Level) verweigert die Bibliothek `music21` den Export des Beethoven-Scores, solange in Takt 512 OMR-Artefakte mit einer Dauer von "2048th" existieren.
- **Symptom:** `Cannot convert "2048th" duration to MusicXML (too short)`.
- **Analyse:** Music21 berechnet beim Speichern interne Offsets neu; kleinste Rundungsdifferenzen in der Quelldatei triggern die Fehlermeldung, selbst wenn der Nutzer einen ganz anderen Takt heilen möchte.
- **Strategie:** In der nächsten Session wird ein "Pre-Parser" entwickelt, der diese Artefakte auf ElementTree-Ebene eliminiert, bevor das Objektmodell von music21 geladen wird.

## Projektstruktur
- `/api`: Backend-Logik (FastAPI)
- `/core`: Musikalische Analyse- und Heilungs-Module
- `/static`: Web-UI (HTML5, CSS3, JavaScript, Verovio WASM)
- `/input`: Quellverzeichnis für .mxl / .musicxml
- `/needs_review`: Arbeitsverzeichnis für den Auditor