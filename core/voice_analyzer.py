from music21 import stream, note, duration, bar

class VoiceAnalyzer:
    def __init__(self):
        self.audit_trail = []

    def analyze_measure(self, m, part_name, file_name):
        """
        Analysiert einen Takt auf rhythmische Korrektheit.
        Ignoriert Auftakte am Anfang und an Wiederholungszeichen (Anacrusis).
        """
        # Erwartete Dauer laut Taktart (z.B. 4.0 für 4/4 Takt)
        expected = float(m.barDuration.quarterLength)
        # Tatsächliche Dauer der enthaltenen Elemente
        actual = float(m.duration.quarterLength)
        
        issues = []
        tolerance = 0.05 # Puffer für music21 Rundungsungenauigkeiten

        # --- FALL 1: ÜBERFÜLLT (Overfull) ---
        if actual > (expected + tolerance):
            found_filler = False
            offsets = {}
            
            # Nutze .flatten() statt .flat zur Vermeidung von Warnungen
            elements = m.flatten().notesAndRests
            
            for el in elements:
                if el.offset not in offsets:
                    offsets[el.offset] = []
                offsets[el.offset].append(el)

            for offset, o_elements in offsets.items():
                if len(o_elements) > 1:
                    rests = [e for e in o_elements if e.isRest]
                    notes = [e for e in o_elements if e.isNote]
                    # Wenn an einem Schlag sowohl Note als auch Pause existiert
                    if rests and notes:
                        issues.append({
                            "type": "FILLER_REST",
                            "measure": m.measureNumber,
                            "part": part_name,
                            "offset": float(offset),
                            "message": f"Takt überfüllt ({round(actual, 2)}/{expected}). Pause bei Schlag {offset + 1} überlappt mit Note."
                        })
                        found_filler = True

            # Falls keine überlappende Pause gefunden wurde, aber der Takt zu lang ist
            if not found_filler:
                issues.append({
                    "type": "OVERFULL_MEASURE",
                    "measure": m.measureNumber,
                    "part": part_name,
                    "actual": round(actual, 3),
                    "expected": expected,
                    "message": f"Takt zu lang: {round(actual, 2)} statt {expected} Viertel."
                })

        # --- FALL 2: ZU KURZ (Incomplete / Auftakt) ---
        elif actual < (expected - tolerance):
            # DETEKTION VON AUFTAKTEN (Anacrusis)
            is_intentional_upbeat = False
            
            # 1. Check: Anfang des Stücks (Takt 0 oder 1)
            if m.measureNumber <= 1:
                is_intentional_upbeat = True
            
            # 2. Check: Wiederholungszeichen am Taktende oder Anfang
            # (Wichtig für Takt 397/443)
            if m.leftBarline is not None and m.leftBarline.type in ['repeat', 'double']:
                is_intentional_upbeat = True
            if m.rightBarline is not None and m.rightBarline.type in ['repeat', 'double']:
                is_intentional_upbeat = True
            
            # 3. Check: Existieren Wiederholungs-Objekte im Takt-Stream?
            barlines = m.getElementsByClass('Barline')
            if len(barlines) > 0:
                is_intentional_upbeat = True

            # Wenn es ein legitimer Auftakt an einer Struktur-Grenze ist, ignorieren wir ihn
            if is_intentional_upbeat:
                return []

            # Ansonsten: Echtes rhythmisches Problem
            issues.append({
                "type": "INCOMPLETE_MEASURE",
                "measure": m.measureNumber,
                "part": part_name,
                "actual": round(actual, 3),
                "expected": expected,
                "message": f"Takt zu kurz: {round(actual, 2)} statt {expected} Viertel."
            })
            
        return issues

    def process_score(self, score, file_name):
        """
        Hauptfunktion: Scannt alle Parts der Partitur.
        """
        all_issues = []
        # Wir zählen Takte global für die UI-Verknüpfung
        global_measure_idx = 0
        
        for p in score.parts:
            p_id = p.id if p.id else "Part"
            # Hole alle Measures (Takte)
            measures = p.getElementsByClass('Measure')
            for m in measures:
                global_measure_idx += 1
                measure_issues = self.analyze_measure(m, p_id, file_name)
                
                # Verknüpfe jedes Problem mit der xml_id für Verovio
                for issue in measure_issues:
                    issue['xml_id'] = f"m-idx-{global_measure_idx}"
                    all_issues.append(issue)
        
        return all_issues