from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

app = FastAPI(title="MusicXML Sanitizer API")

# Erlaube dem Browser den Zugriff
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = Path("output_cleaned")
REVIEW_DIR = Path("needs_review")

@app.get("/files")
def list_files():
    """Listet alle Dateien auf."""
    review_files = [f.name for f in REVIEW_DIR.glob("*.musicxml")]
    clean_files = [f.name for f in OUTPUT_DIR.glob("*.musicxml")]
    return {
        "needs_review": review_files,
        "cleaned": clean_files
    }

@app.get("/get-xml/{folder}/{filename}")
def get_xml(folder: str, filename: str):
    """Liest den Inhalt einer MusicXML-Datei."""
    base_path = REVIEW_DIR if folder == "review" else OUTPUT_DIR
    file_path = base_path / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return {"xml": f.read()}