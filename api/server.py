import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Pfade absolut berechnen
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"
REVIEW_DIR = BASE_DIR / "needs_review"
CLEANED_DIR = BASE_DIR / "output_cleaned"

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if not INDEX_FILE.exists():
        return f"<h1>Fehler</h1><p>index.html nicht gefunden in: {INDEX_FILE}</p>"
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/files")
async def list_files():
    file_list = []
    for folder in [REVIEW_DIR, CLEANED_DIR]:
        if folder.exists():
            for pattern in ["*.xml", "*.musicxml"]:
                for f in folder.glob(pattern):
                    file_list.append({"name": f.name, "folder": folder.name})
    return file_list

@app.get("/file/{folder}/{filename}")
async def get_file(folder: str, filename: str):
    target = BASE_DIR / folder / filename
    if not target.exists():
        raise HTTPException(status_code=404)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        return {"content": f.read()}

@app.get("/report/{filename}")
async def get_report(filename: str):
    report_path = BASE_DIR / "audit_report.json"
    if not report_path.exists(): return []
    
    # Tolerante Suche nach dem Dateinamen
    base_search = filename.split('_RAW')[0].split('.musicxml')[0].split('.mxl')[0]
    
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for entry in data:
            entry_base = entry["file"].split('.mxl')[0].split('.musicxml')[0]
            if base_search in entry_base or entry_base in base_search:
                return entry["actions"] if isinstance(entry["actions"], list) else []
    return []