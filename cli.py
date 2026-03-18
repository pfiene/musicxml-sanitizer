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

# 2. Unsere Module laden
from core.voice_analyzer import VoiceAnalyzer
from core.pre_processor import load_robustly
from music21 import converter

app = typer.Typer()
console = Console()

class AuditLogger:
    def __init__(self):
        self.stats = []

    def log(self, file: str, status: str, issues_list: list):
        self.stats.append({
            "file": file,
            "status": status,
            "issues": len(issues_list),
            "actions": issues_list
        })

    def save_json(self, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=4)

def simple_safe_fix(score):
    """
    Ein minimalistischer Fix, der keine Typen auf None setzt, 
    sondern nur mathematische Grenzwerte erzwingt.
    """
    for n in score.flatten().getElementsByClass(['Note', 'Rest', 'Chord']):
        # Wenn die Dauer extrem klein ist, auf ein 256stel setzen
        if 0 < n.duration.quarterLength < 0.015625:
            n.duration.quarterLength = 0.015625
        # Wir fassen den 'type' hier NICHT manuell an, um Abstürze zu vermeiden

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
        task = progress.add_task("Verarbeite...", total=len(files))

        for file in files:
            progress.update(task, description=f"Analysiere {file.name}")
            temp_xml_path = "temp_preprocessing.xml"
            xml_data = ""
            current_issues = []
            
            try:
                # Schritt 1: Rohes XML laden & Text-Fixes (Pre-Processor)
                xml_data = load_robustly(file)
                with open(temp_xml_path, "w", encoding="utf-8") as f:
                    f.write(xml_data)
                
                # Schritt 2: Einlesen
                score = converter.parse(temp_xml_path)
                
                # Schritt 3: ANALYSE (Jetzt sofort, damit wir die Daten haben!)
                current_issues = analyzer.process_score(score, file.name)
                
                # Schritt 4: Vorsichtige Reparaturversuche
                try:
                    simple_safe_fix(score)
                except:
                    pass # Wenn der Fix scheitert, machen wir trotzdem weiter
                
                # Schritt 5: Speichern
                has_critical = any(i['type'] == "OVERFULL_MEASURE" for i in current_issues)
                target_dir = review_path if has_critical else output
                target_file = target_dir / f"{file.stem}.musicxml"
                
                try:
                    score.write('musicxml', fp=target_file)
                    status = "NEEDS_REVIEW" if has_critical else "CLEANED"
                except Exception as write_err:
                    # FALLBACK: Wenn der Export scheitert, nutzen wir das RAW-XML
                    status = "REVIEW_RAW_SAVE"
                    target_file = review_path / f"{file.stem}_RAW_FIXED.musicxml"
                    with open(target_file, "w", encoding="utf-8") as f:
                        f.write(xml_data)
                    console.print(f"[yellow]Warnung: Export-Fehler bei {file.name}. Raw-Fallback genutzt.[/yellow]")

                # Audit-Log schreiben (mit den gefundenen Issues!)
                audit.log(file.name, status, current_issues)
                
            except Exception as e:
                # Komplett-Absturz beim Laden
                console.print(f"[red]Fehler bei {file.name}: {e}[/red]")
                audit.log(file.name, "ERROR", [{"type": "SYSTEM_ERROR", "measure": 0, "xml_id": "", "info": str(e)}])
            
            finally:
                if os.path.exists(temp_xml_path):
                    os.remove(temp_xml_path)
            
            progress.advance(task)

    audit.save_json(Path("audit_report.json"))
    console.print("\n[bold green]Batch abgeschlossen.[/bold green]")

if __name__ == "__main__":
    app()