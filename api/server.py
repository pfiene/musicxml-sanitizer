import sys
import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

current_file_path = Path(__file__).resolve()
root_dir = current_file_path.parent.parent
core_dir = root_dir / "core"

if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

import pre_processor 

app = FastAPI()

# Wir arbeiten nur in needs_review
MUSIC_FOLDER = root_dir / "needs_review"
STATIC_DIR = root_dir / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def get_index():
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/files")
async def list_files():
    """Listet nur MusicXML-Dateien auf."""
    files = []
    if MUSIC_FOLDER.exists():
        for item in MUSIC_FOLDER.iterdir():
            if item.suffix.lower() in [".xml", ".musicxml", ".mxl"]:
                files.append({"name": item.name, "folder": "needs_review"})
    return files

@app.get("/file/{folder}/{name}")
async def get_music_file(folder: str, name: str):
    file_path = root_dir / folder / name
    content = pre_processor.load_robustly(str(file_path))
    return {"name": name, "content": content}

@app.get("/report/{name}")
async def get_audit_report(name: str):
    """Lädt den individuellen JSON-Report: needs_review/{name}.json"""
    # Beispiel: beethoven.musicxml -> beethoven.musicxml.json
    report_file = MUSIC_FOLDER / f"{name}.json"
    
    if report_file.exists():
        print(f"--- Lade individuellen Report: {report_file.name} ---")
        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Falls dein Auditor den Report noch in ein Array [ {actions:[]} ] packt:
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
            
    print(f"--- Kein Report gefunden für {name} unter {report_file} ---")
    return {"actions": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)