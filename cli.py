import os
import json
import sys
from pathlib import Path
from music21 import converter

# =================================================================
# PFAD-LOGIK: Wir stellen sicher, dass 'core' gefunden wird
# =================================================================
root_dir = Path(__file__).resolve().parent
core_dir = root_dir / "core"

if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

# Importiere deine Module aus dem core-Ordner
try:
    import pre_processor
    from voice_analyzer import VoiceAnalyzer 
except ImportError as e:
    print(f"FEHLER beim Laden der Core-Module: {e}")
    sys.exit(1)

def run_pipeline():
    # Verzeichnisse definieren
    input_folder = root_dir / "input"
    output_folder = root_dir / "needs_review"
    output_folder.mkdir(exist_ok=True)

    print("--- Start MusicXML Sanitizer & Auditor Pipeline ---")

    # Suche nach Musikdateien (.mxl, .musicxml, .xml)
    files = []
    for ext in ["*.mxl", "*.musicxml", "*.xml"]:
        files.extend(list(input_folder.glob(ext)))
    
    if not files:
        print(f"Keine Dateien in {input_folder} gefunden!")
        return

    for file_path in files:
        print(f"\n>>> Verarbeite: {file_path.name}")
        
        # ---------------------------------------------------------
        # SCHRITT 1: SANITIZER (Heilung & Pre-Processing)
        # ---------------------------------------------------------
        print("-> Starte Sanitizer (Voice Merge & Rhythm Fix)...")
        cleaned_xml_content = pre_processor.load_robustly(str(file_path))
        
        # Hole das Protokoll der automatischen Heilungen
        healing_log = pre_processor.get_last_log()
        
        if not cleaned_xml_content:
            print("   FEHLER: Datei konnte nicht verarbeitet werden.")
            continue

        # Dateiname für das Ergebnis festlegen
        new_xml_name = f"{file_path.stem}_RAW_FIXED.musicxml"
        new_xml_path = output_folder / new_xml_name
        
        # Geheiltes XML speichern
        with open(new_xml_path, "w", encoding="utf-8") as f:
            f.write(cleaned_xml_content)
        print(f"   [OK] Geheiltes XML gespeichert: {new_xml_name}")

        # Heilungs-Protokoll (.log.txt) speichern
        log_file_path = output_folder / f"{new_xml_name}.log.txt"
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write("=== SANITIZER HEALING LOG ===\n")
            f.write(f"Ursprungsdatei: {file_path.name}\n")
            f.write("-" * 40 + "\n")
            if healing_log:
                f.write(healing_log)
            else:
                f.write("Keine automatischen Korrekturen notwendig.")
        print(f"   [OK] Heilungs-Log gespeichert: {log_file_path.name}")

        # ---------------------------------------------------------
        # SCHRITT 2: AUDITOR (Analyse des geheilten XMLs)
        # ---------------------------------------------------------
        print("-> Starte Auditor-Analyse (music21)...")
        try:
            # Wir laden das BEREITS GEHEILTE XML für den Audit
            score = converter.parse(str(new_xml_path))
            analyzer = VoiceAnalyzer()
            
            # Analyse durchführen
            issues = analyzer.process_score(score, new_xml_name)
            print(f"   [OK] Auditor hat {len(issues)} verbleibende Probleme gefunden.")
            
        except Exception as e:
            print(f"   FEHLER im Auditor: {e}")
            issues = []

        # ---------------------------------------------------------
        # SCHRITT 3: REPORT SPEICHERN (.json)
        # ---------------------------------------------------------
        report_data = {
            "file": new_xml_name,
            "status": "REVIEW_REQUIRED",
            "actions": issues 
        }

        report_path = output_folder / f"{new_xml_name}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=4)
        print(f"   [OK] JSON-Report gespeichert: {report_path.name}")

    print("\n--- Pipeline beendet. ---")
    print("Du kannst jetzt die Web-UI aktualisieren.")

if __name__ == "__main__":
    run_pipeline()
    