from music21 import duration

class VoiceAnalyzer:
    def sanitize_durations(self, score):
        """
        Bereinigt mathematisch zu kleine Notenwerte, die den Export verhindern.
        """
        # Ein 256stel ist 1/64 eines Viertels (0.015625)
        min_ql = 0.015625 
        fixes = 0
        
        # Wir gehen durch alle Noten, Pausen und Akkorde
        for el in score.flatten().notesAndRests:
            # Wenn die Note zu kurz ist (aber nicht 0, wie bei manchen Grace Notes)
            if 0 < el.duration.quarterLength < min_ql:
                # 1. Mathematische Dauer auf 256stel setzen
                el.duration.quarterLength = min_ql
                # 2. Den Typ explizit erzwingen, damit music21 nicht neu rechnet
                el.duration.type = '256th'
                # 3. Falls Tuplets (Triolen etc.) dran hängen, die zu klein sind, entfernen
                el.duration.tuplets = ()
                fixes += 1
        return fixes

    def process_score(self, score):
        all_issues = []
        
        # Schritt 1: Radikale Sanierung der Dauern (verhindert den WRITE_ERROR)
        fixes = self.sanitize_durations(score)
        if fixes > 0:
            all_issues.append({"type": "AUTO_FIXED", "msg": f"{fixes} Notenwerte begradigt."})
        
        # Schritt 2: Taktprüfung
        for p in score.parts:
            for m in p.getElementsByClass('Measure'):
                if m.measureNumber <= 0: continue
                try:
                    expected = m.barDuration.quarterLength
                    actual = m.duration.quarterLength
                    
                    if abs(actual - expected) > 0.1: # Toleranz erhöht
                        all_issues.append({"type": "OVERFULL", "measure": m.measureNumber})
                        for n in m.flatten().notes:
                            n.style.color = '#FF0000'
                except:
                    continue
        return all_issues