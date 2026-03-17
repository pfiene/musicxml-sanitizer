import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS für Browser-Zugriff
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Pfade berechnen
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if not INDEX_FILE.exists():
        return f"<h1>Fehler</h1><p>index.html nicht gefunden in: {INDEX_FILE}</p>"
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/files")
async def list_files():
    file_list = []
    # Ordner, die wir scannen
    for folder_name in ["needs_review", "output_cleaned"]:
        folder_path = BASE_DIR / folder_name
        if folder_path.exists():
            # Suche alle .xml und .musicxml Dateien
            for pattern in ["*.xml", "*.musicxml"]:
                for f in folder_path.glob(pattern):
                    file_list.append({
                        "name": f.name, 
                        "folder": folder_name
                    })
    
    # Ausgabe im Terminal zur Kontrolle
    print(f"DEBUG: {len(file_list)} Dateien gefunden in {BASE_DIR}")
    return file_list

@app.get("/file/{folder}/{filename}")
async def get_file(folder: str, filename: str):
    # Validierung des Ordnernamens
    if folder not in ["needs_review", "output_cleaned"]:
        raise HTTPException(status_code=400, detail="Ungültiger Ordner")
        
    target = BASE_DIR / folder / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
        
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        return {"content": f.read()}