import sys
import json
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from music21 import converter

# Pfade
api_dir = Path(__file__).resolve().parent
root_dir = api_dir.parent
core_dir = root_dir / "core"

if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

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
    return [{"name": f.name, "folder": "needs_review"} for f in MUSIC_FOLDER.glob("*.musicxml")]

@app.get("/file/{folder}/{name}")
async def get_music_file(folder: str, name: str):
    file_path = root_dir / folder / name
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"name": name, "content": content}

@app.get("/report/{name}")
async def get_audit_report(name: str):
    report_file = MUSIC_FOLDER / f"{name}.json"
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"actions": []}

@app.post("/apply-fix")
async def apply_fix(data: dict):
    filename = data.get("filename")
    measure_num = data.get("measure")
    fix_type = data.get("type")
    
    file_path = MUSIC_FOLDER / filename
    try:
        # 1. Roh-Cleanup (Regex)
        with open(file_path, "r", encoding="utf-8") as f:
            xml_raw = f.read()
        xml_cleaned = re.sub(r'2048th|1024th|512th', '256th', xml_raw)
        
        # 2. Laden in music21
        score = converter.parse(xml_cleaned, format='musicxml')
        
        # --- DER RADIKAL-REINIGER ---
        # Wir entfernen JEDES Element im GANZEN Dokument, das kürzer als ein 256stel ist.
        # Das sind OMR-Fehler, die den Export blockieren.
        for p in score.parts:
            for m in p.getElementsByClass('Measure'):
                to_remove = []
                for n in m.flatten().notesAndRests:
                    if n.duration.quarterLength < 0.01: # Alles unter 1/100 eines Viertels
                        to_remove.append(n)
                for r in to_remove:
                    m.remove(r)

        # 3. Den gewünschten Takt heilen
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
                    m.editorial.comments.append("User: Markiert als korrekt")
                    success = True
        
        if success:
            # 4. Speichern
            score.write('musicxml', fp=str(file_path))
            return {"status": "success", "message": "Geheilt"}
        
        return {"status": "error", "message": "Heilung im Code nicht angeschlagen"}

    except Exception as e:
        print(f"Kritischer Fehler: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)