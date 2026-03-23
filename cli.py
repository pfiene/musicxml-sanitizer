import os
import json
import sys
import re
from pathlib import Path
from music21 import converter

# =================================================================
# PFAD-LOGIK: Sicherstellen, dass der 'core'-Ordner gefunden wird
# =================================================================
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
        # Erzeugt valides MusicXML mit Namespace für Verovio
        cleaned_xml_content = pre_processor.load_robustly(str(file_path))
        healing_log = pre_processor.get_last_log()
        
        if not cleaned_xml_content:
            print("   [!] Fehler: Pre-Processor lieferte keinen Inhalt.")
            continue

        new_xml_name = f"{file_path.stem}_RAW_FIXED.musicxml"
        new_xml_path = output_folder / new_xml_name
        
        # Auf Festplatte speichern (für Frontend & Archiv)
        with open(new_xml_path, "w", encoding="utf-8") as f:
            f.write(cleaned_xml_content)
        
        # Heilungs-Log speichern
        with open(output_folder / f"{new_xml_name}.log.txt", "w", encoding="utf-8") as f:
            f.write("=== MUSICXML HEALING LOG ===\n")
            f.write(f"Quelle: {file_path.name}\n")
            f.write("-" * 40 + "\n")
            f.write(healing_log if healing_log else "Keine Korrekturen notwendig.")

        # ---------------------------------------------------------
        # SCHRITT 2: AUDITOR (Analyse via music21)
        # ---------------------------------------------------------
        print("-> Starte Audit-Analyse...")
        try:
            # HIER DIE LÖSUNG FÜR DAS NAMESPACE-PROBLEM:
            # Wir lesen den eben gespeicherten Content und entfernen den 
            # Namespace NUR für music21 im Arbeitsspeicher.
            content_for_auditor = re.sub(r'\sxmlns="[^"]+"', '', cleaned_xml_content)
            
            # music21 parst nun den "nackten" String ohne Fehlermeldung
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
            print(f"   [!] Kritischer Fehler im Auditor: {e}")

    print("\n--- Pipeline beendet. ---")
    print(f"Ergebnisse liegen in: {output_folder}")

if __name__ == "__main__":
    run_pipeline()
    