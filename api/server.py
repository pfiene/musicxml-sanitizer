import sys
import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# --- PFAD-LOGIK ---
current_file_path = Path(__file__).resolve()
root_dir = current_file_path.parent.parent
core_dir = root_dir / "core"

# Den core-Ordner für den Preprocessor erreichbar machen
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

import pre_processor # Importiert D:\$Entwicklung\musicxml-sanitizer\core\pre_processor.py

app = FastAPI()

# Ordner-Definitionen
MUSIC_FOLDERS = ["needs_review", "input", "output", "processed"] 
STATIC_DIR = root_dir / "static"
GLOBAL_REPORT_FILE = root_dir / "audit_report.json" # <--- HIER liegt dein Report

# Statische Dateien (Frontend)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def get_index():
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/files")
async def list_files():
    """Listet alle gefundenen Musikdateien auf."""
    files = []
    for folder_name in MUSIC_FOLDERS:
        folder_path = root_dir / folder_name
        if folder_path.exists():
            for item in folder_path.iterdir():
                if item.suffix.lower() in [".xml", ".musicxml", ".mxl"]:
                    files.append({"name": item.name, "folder": folder_name})
    return files

@app.get("/file/{folder}/{name}")
async def get_music_file(folder: str, name: str):
    """Lädt die Datei und wendet den Pre-Processor an."""
    file_path = root_dir / folder / name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    
    # Nutzt core/pre_processor.py
    content = pre_processor.load_robustly(str(file_path))
    return {"name": name, "content": content}

@app.get("/report/{name}")
async def get_audit_report(name: str):
    """Lädt die Issues aus der zentralen audit_report.json."""
    if GLOBAL_REPORT_FILE.exists():
        print(f"--- Lade globalen Report: {GLOBAL_REPORT_FILE} ---")
        try:
            with open(GLOBAL_REPORT_FILE, "r", encoding="utf-8") as f:
                report_data = json.load(f)
                
                # Falls der Report ein Dictionary ist, das Dateinamen als Keys nutzt:
                if isinstance(report_data, dict) and name in report_data:
                    return report_data[name]
                
                # Falls der Report eine einfache Liste von Issues ist (vom letzten Lauf):
                return report_data
        except Exception as e:
            print(f"Fehler beim Lesen des Reports: {e}")
            return []
    
    print(f"WARNUNG: {GLOBAL_REPORT_FILE} nicht gefunden.")
    return []

if __name__ == "__main__":
    import uvicorn
    print(f"Server läuft auf http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)