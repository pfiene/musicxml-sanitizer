import typer
import os
import sys
import warnings
from pathlib import Path
from rich.console import Console
from rich.table import Table

# 1. Warnungen unterdrücken (macht die Konsole sauberer)
warnings.filterwarnings("ignore", category=UserWarning)

# 2. Eigene Module importieren
try:
    from core.voice_analyzer import VoiceAnalyzer
    from core.parser import RobustParser
    from music21 import converter
except ImportError as e:
    print(f"KRITISCHER FEHLER: Module konnten nicht geladen werden: {e}")
    sys.exit(1)

console = Console()

def main(
    input_dir: str = typer.Option("input", "--input", "-i", help="Ordner mit den Quelldaten"),
    output_dir: str = typer.Option("output_cleaned", "--output", "-o", help="Ordner für saubere Dateien"),
    profile: str = typer.Option("grossdruck", "--profile", "-p", help="Profil (grossdruck/braille)")
):
    """
    MusicXML Sanitizer - Reinigt und normalisiert Notendateien für die Barrierefreiheit (dzb lesen).
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    review_path = Path("needs_review")

    # Ordner anlegen
    output_path.mkdir(exist_ok=True)
    review_path.mkdir(exist_ok=True)

    if not input_path.exists():
        console.print(f"[red]Fehler: Ordner '{input_path}' nicht gefunden![/red]")
        return

    # Dateien suchen
    files = [f for f in input_path.iterdir() if f.suffix.lower() in [".xml", ".musicxml", ".mxl"]]
    
    console.print(f"[bold cyan]Sanitizer gestartet[/bold cyan]")
    console.print(f"Dateien gefunden: [bold]{len(files)}[/bold]\n")

    if not files:
        console.print("[yellow]Keine MusicXML oder MXL Dateien zum Verarbeiten gefunden.[/yellow]")
        return

    analyzer = VoiceAnalyzer()
    stats = []

    for file in files:
        console.print(f"-> Verarbeite [bold]{file.name}[/bold]...", end="")
        try:
            # 1. Vorreinigung (XML Text-Ebene, fixt 2048th Tags)
            cleaned_xml_bytes = RobustParser.pre_clean_xml(file)
            
            if cleaned_xml_bytes is None:
                raise ValueError("Parser konnte XML nicht extrahieren.")

            # 2. Laden in music21 (Format explizit musicxml)
            score = converter.parse(cleaned_xml_bytes, format='musicxml')
            
            # 3. Analysieren & Reparieren (Quantisierung & Taktprüfung)
            issues = analyzer.process_score(score)
            
            # 4. Status bestimmen
            status = "CLEANED"
            target_folder = output_path
            
            # Wenn ernste Probleme (Overfull) da sind -> Review
            if any(i['type'] == "OVERFULL" for i in issues):
                status = "NEEDS_REVIEW"
                target_folder = review_path
            # Wenn nur automatische Korrekturen (Mini-Noten) gemacht wurden -> AUTO_FIXED
            elif any(i['type'] == "AUTO_FIXED" for i in issues):
                status = "AUTO_FIXED"

            # 5. Speichern
            try:
                out_file = target_folder / f"{file.stem}.musicxml"
                score.write('musicxml', fp=out_file)
                
                stats.append({"file": file.name, "status": status, "issues": len(issues)})
                
                color = "green" if status in ["CLEANED", "AUTO_FIXED"] else "yellow"
                console.print(f" [[{color}]{status}[/{color}]]")
            except Exception as write_err:
                # Hier knallt es oft bei Beethoven/Liszt, falls die Korrektur nicht reichte
                stats.append({"file": file.name, "status": "WRITE_ERROR", "issues": 0})
                console.print(f" [[red]WRITE_ERROR[/red]]")
                console.print(f"    [dim red]{str(write_err)[:100]}...[/dim red]")
            
        except Exception as e:
            console.print(f" [[red]LOAD_ERROR[/red]]")
            console.print(f"    [dim red]{str(e)[:100]}...[/dim red]")
            stats.append({"file": file.name, "status": "ERROR", "issues": 0})

    # --- TABELLE ---
    console.print("\n[bold magenta]Zusammenfassung des Batch-Jobs:[/bold magenta]")
    table = Table(show_header=True, header_style="bold white")
    table.add_column("Datei", style="dim", width=40)
    table.add_column("Status", justify="center")
    table.add_column("Fixes/Issues", justify="right")

    for s in stats:
        color = "green" if s["status"] in ["CLEANED", "AUTO_FIXED"] else "red"
        if s["status"] == "NEEDS_REVIEW": color = "yellow"
        
        table.add_row(
            s["file"], 
            f"[{color}]{s['status']}[/{color}]", 
            str(s["issues"])
        )

    console.print(table)
    console.print(f"\n[bold green]Verarbeitung abgeschlossen.[/bold green]")

if __name__ == "__main__":
    # Benutze typer.run für maximale Kompatibilität ohne Unterbefehle
    typer.run(main)