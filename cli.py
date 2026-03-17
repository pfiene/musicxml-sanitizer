import os
import json
import warnings
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# 1. Warnungen unterdrücken
warnings.filterwarnings("ignore")

from core.voice_analyzer import VoiceAnalyzer
from core.pre_processor import load_robustly
from music21 import converter

app = typer.Typer()
console = Console()

class AuditLogger:
    def __init__(self):
        self.stats = []
    def log(self, file: str, status: str, issues: int, actions: list):
        self.stats.append({"file": file, "status": status, "issues": issues, "actions": actions})
    def save_json(self, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=4)

def heavy_duty_fix(score):
    """
    Zwingt den Beethoven-Score in ein gültiges Raster.
    Löscht 2048stel und andere mathematische 'Geister'.
    """
    try:
        # Quantisierung: Alles wird auf das nächste 64stel oder 128stel 'eingerastet'
        # Das entfernt die winzigen Rundungsfehler (2048stel)
        score.quantize((64, 128), processOffsets=True, processDurations=True, inPlace=True)
    except:
        pass

    for n in score.flatten().getElementsByClass(['Note', 'Rest', 'Chord']):
        # Zwinge music21, den 'Type' (Viertel, Achtel...) komplett neu zu berechnen
        n.duration.type = None 
        n.duration.quarterLength = n.duration.quarterLength # Trigger für Neuberechnung
        
        # Falls es immer noch zu klein ist, auf 256stel aufrunden
        if 0 < n.duration.quarterLength < 0.015625:
            n.duration.quarterLength = 0.015625
        
        # WICHTIG: Tuplets (Triolenklammern) entfernen, wenn sie korrupt sind
        if n.duration.quarterLength > 0:
            n.duration.tuplets = [] 

@app.command()
def main(
    input: Path = typer.Option(Path("input"), "--input", "-i"),
    output: Path = typer.Option(Path("output_cleaned"), "--output", "-o")
):
    review_path = Path("needs_review")
    for p in [output, review_path]:
        if not p.exists(): p.mkdir(parents=True)

    files = [f for f in list(input.glob("*.*")) if f.suffix.lower() in [".xml", ".musicxml", ".mxl"]]
    
    analyzer = VoiceAnalyzer()
    audit = AuditLogger()

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), console=console) as progress:
        task = progress.add_task("Bearbeite...", total=len(files))

        for file in files:
            progress.update(task, description=f"Analysiere {file.name}")
            temp_xml_path = "temp_preprocessing.xml"
            
            try:
                # 1. Text-Reinigung (2048th -> 256th)
                xml_data = load_robustly(file)
                with open(temp_xml_path, "w", encoding="utf-8") as f:
                    f.write(xml_data)
                
                # 2. Einlesen
                score = converter.parse(temp_xml_path)
                
                # 3. Rhythmus-Wäsche (Die Nuklear-Option)
                heavy_duty_fix(score)
                
                # 4. Analyse
                issues = analyzer.process_score(score, file.name)
                has_critical = any(i['type'] == "OVERFULL_MEASURE" for i in issues)
                
                # 5. Speichern
                target_dir = review_path if has_critical else output
                target_file = target_dir / f"{file.stem}.musicxml"
                
                # Versuch zu speichern
                score.write('musicxml', fp=target_file)
                audit.log(file.name, "CLEANED" if not has_critical else "NEEDS_REVIEW", len(issues), [])

            except Exception as e:
                # FALLBACK: Wenn music21 beim SCHREIBEN scheitert
                console.print(f"[yellow]Warnung bei {file.name}: Music21 Export fehlgeschlagen. Nutze RAW-Safe.[/yellow]")
                target_file = review_path / f"{file.stem}_RAW_FIXED.musicxml"
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(xml_data) # Wir speichern das vom Pre-Processor gereinigte XML
                audit.log(file.name, "REVIEW_RAW", 0, [str(e)[:100]])
            
            finally:
                if os.path.exists(temp_xml_path): os.remove(temp_xml_path)
            
            progress.advance(task)

    console.print("\n[bold green]Batch abgeschlossen.[/bold green]")
    audit.save_json(Path("audit_report.json"))

if __name__ == "__main__":
    app()