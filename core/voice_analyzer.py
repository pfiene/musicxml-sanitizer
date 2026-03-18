from music21 import stream, note, duration

class VoiceAnalyzer:
    def __init__(self):
        self.audit_trail = []

    def analyze_measure(self, m, part_name, file_name):
        """Analysiert einen einzelnen Takt."""
        expected = m.barDuration.quarterLength
        actual = m.duration.quarterLength
        issues = []
        
        # 1. Suche nach überlappenden Pausen (Filler Rests)
        offsets = {}
        for el in m.flatten().notesAndRests:
            if el.offset not in offsets:
                offsets[el.offset] = []
            offsets[el.offset].append(el)

        for offset, elements in offsets.items():
            if len(elements) > 1:
                rests = [e for e in elements if e.isRest]
                notes = [e for e in elements if e.isNote]
                if rests and notes:
                    issues.append({
                        "type": "FILLER_REST",
                        "measure": m.measureNumber,
                        "part": part_name,
                        "offset": float(offset)
                    })

        # 2. Takt-Bilanz prüfen (mit Toleranz)
        tolerance = 0.02
        if actual > (expected + tolerance):
            issues.append({
                "type": "OVERFULL_MEASURE",
                "measure": m.measureNumber,
                "part": part_name,
                "actual": round(float(actual), 3),
                "expected": float(expected)
            })
            
        return issues

    def process_score(self, score, file_name):
        all_issues = []
        # Wir zählen ALLE Takte in der gesamten Datei global durch
        global_measure_idx = 0
        
        for p in score.parts:
            p_id = p.id
            for m in p.getElementsByClass('Measure'):
                global_measure_idx += 1
                issues = self.analyze_measure(m, p_id, file_name)
                
                # Wir verknüpfen jedes Problem mit der globalen Index-ID
                for issue in issues:
                    issue['xml_id'] = f"m-idx-{global_measure_idx}"
                all_issues.extend(issues)
        
        return all_issues