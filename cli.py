import os
import json
import sys
import re
import warnings
from pathlib import Path
from music21 import converter

# =================================================================
# SETUP: Warnungen und Pfade
# =================================================================

# Unterdrückt die Requests/Urllib3 Warnung im Terminal
warnings.filterwarnings("ignore", message=".*urllib3.*")
warnings.filterwarnings("ignore", message=".*chardet.*")

root_dir = Path(__file__).resolve().parent
core_dir = root_dir / "core"

if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

# Import der Core-Module
try:
    import pre_processor
    from voice_analyzer import VoiceAnalyzer 
    print("-> Module erfolgreich geladen.")
except ImportError as e:
    print(f"FEHLER beim Laden der Core-Module aus {core_dir}: {e}")
    sys.exit(1)

def run_pipeline():
    # Verzeichnisse definieren
    input_folder = root_dir / "input"
    output_folder = root_dir / "needs_review"
    output_folder.mkdir(exist_ok=True)

    # Suche nach Musikdateien (.mxl, .musicxml, .xml)
    files = []
    for ext in ["*.mxl", "*.musicxml", "*.xml"]:
        files.extend(list(input_folder.glob(ext)))
    
    if not files:
        print(f"Keine Dateien in {input_folder} gefunden!")
        return

    print(f"--- Starte Analyse für {len(files)} Datei(en) ---")

    for file_path in files:
        print(f"\n>>> VERARBEITE: {file_path.name}")
        
        # ---------------------------------------------------------
        # SCHRITT 1: SANITIZER (Musikalische Heilung)
        # ---------------------------------------------------------
        # Lädt und heilt die Datei (Voice Merge, Grace Notes, etc.)
        cleaned_xml_content = pre_processor.load_robustly(str(file_path))
        healing_log = pre_processor.get_last_log()
        
        if not cleaned_xml_content:
            print("   [!] Fehler: Pre-Processor lieferte keinen Inhalt.")
            continue

        new_xml_name = f"{file_path.stem}_RAW_FIXED.musicxml"
        new_xml_path = output_folder / new_xml_name
        
        # Geheiltes XML speichern (Namespace bleibt für Verovio erhalten)
        with open(new_xml_path, "w", encoding="utf-8") as f:
            f.write(cleaned_xml_content)
        
        # Heilungs-Log speichern (mit den neuen musikalischen Werten)
        with open(output_folder / f"{new_xml_name}.log.txt", "w", encoding="utf-8") as f:
            f.write("=== MUSICXML HEALING LOG ===\n")
            f.write(f"Quelle: {file_path.name}\n")
            f.write("-" * 40 + "\n")
            f.write(healing_log if healing_log else "Keine Korrekturen notwendig.")
        print(f"   [OK] Sanitizer fertig. Log geschrieben.")

        # ---------------------------------------------------------
        # SCHRITT 2: AUDITOR (Analyse via music21)
        # ---------------------------------------------------------
        print("-> Starte Audit-Analyse...")
        try:
            # NAMESPACE-BRÜCKE: Für den Auditor entfernen wir den Namespace kurz im Speicher
            content_for_auditor = re.sub(r'\sxmlns="[^"]+"', '', cleaned_xml_content)
            
            # music21 parst den String
            score = converter.parse(content_for_auditor)
            
            analyzer = VoiceAnalyzer()
            issues = analyzer.process_score(score, new_xml_name)
            
            # ---------------------------------------------------------
            # SCHRITT 3: REPORT SPEICHERN (.json)
            # ---------------------------------------------------------
            report_data = {
                "file": new_xml_name,
                "status": "REVIEW",
                "actions": issues 
            }

            report_path = output_folder / f"{new_xml_name}.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=4)
            
            print(f"   [OK] Audit abgeschlossen. {len(issues)} Issues verbleibend.")
            
        except Exception as e:
            print(f"   [!] Fehler im Auditor-Schritt: {e}")

    print("\n--- Pipeline beendet. ---")

if __name__ == "__main__":
    run_pipeline()
    