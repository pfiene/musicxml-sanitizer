import sys
import json
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from music21 import converter

# Pfade berechnen (da Datei in /api liegt)
api_dir = Path(__file__).resolve().parent
root_dir = api_dir.parent
core_dir = root_dir / "core"

# Core-Pfad hinzufügen, damit die Module gefunden werden
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

# JETZT DIE IMPORTS (Wichtig!)
import pre_processor 
import reconstructor

app = FastAPI()

MUSIC_FOLDER = root_dir / "needs_review"
STATIC_DIR = root_dir / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def get_index():
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/files")
async def list_files():
    files = []
    if MUSIC_FOLDER.exists():
        for ext in ["*.musicxml", "*.xml"]:
            files.extend([{"name": f.name, "folder": "needs_review"} for f in MUSIC_FOLDER.glob(ext)])
    return files

@app.get("/file/{folder}/{name}")
async def get_music_file(folder: str, name: str):
    file_path = root_dir / folder / name
    # Nutzt den Pre-Processor für sauberes Laden (2048th-Fix)
    content = pre_processor.load_robustly(str(file_path))
    return {"name": name, "content": content}

@app.get("/report/{name}")
async def get_audit_report(name: str):
    report_file = MUSIC_FOLDER / f"{name}.json"
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"actions": []}

# In api/server.py: Der apply_fix Endpunkt

@app.post("/apply-fix")
async def apply_fix(data: dict):
    filename = data.get("filename")
    measure_num = data.get("measure")
    fix_type = data.get("type")
    
    file_path = MUSIC_FOLDER / filename
    try:
        # 1. Laden und technische Vorreinigung (Pre-Processor)
        cleaned_xml = pre_processor.load_robustly(str(file_path))
        score = converter.parse(cleaned_xml, format='musicxml')
        
        # 2. GLOBALER CLEANER: Wir säubern das gesamte Dokument von "Micro-Durations"
        # Das verhindert den 2048th-Absturz beim Speichern
        for n in score.flatten().notesAndRests:
            # Alles was kürzer als ein 256stel ist (0.015625), wird auf 0 gesetzt (Grace)
            if not n.duration.isGrace and n.duration.quarterLength < 0.015:
                n.duration.quarterLength = 0.0
                n.duration.type = '256th' # Sicherheitstyp

        # 3. Den eigentlichen Takt-Fix anwenden
        success = False
        for p in score.parts:
            m = p.measure(int(measure_num))
            if m:
                if "FILLER_REST" in fix_type:
                    success = reconstructor.Reconstructor.fix_overfull_measure(m)
                elif "INCOMPLETE_MEASURE" in fix_type:
                    success = reconstructor.Reconstructor.fill_with_rests(m)
                elif "CONVERT_GRACE" in fix_type or "OVERFULL" in fix_type:
                    success = reconstructor.Reconstructor.convert_to_grace(m)
                elif "IGNORE" in fix_type:
                    m.editorial.comments.append("User: Marked as Correct")
                    success = True
        
        if success:
            # 4. Speichern
            score.write('musicxml', fp=str(file_path))
            return {"status": "success", "message": "Takt erfolgreich bearbeitet."}
        
        return {"status": "error", "message": "Heil-Logik nicht angeschlagen."}

    except Exception as e:
        print(f"Kritischer Fehler: {e}")
        return {"status": "error", "message": str(e)}
        
if __name__ == "__main__":
    import uvicorn
    print(f"--- SERVER STARTET AUF http://127.0.0.1:8001 ---")
    uvicorn.run(app, host="127.0.0.1", port=8001)