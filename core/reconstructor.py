from music21 import duration

class Reconstructor:
    @staticmethod
    def fix_overfull_measure(measure):
        """
        Versucht einen Takt zu retten, indem 'Füll-Pausen' (die unter Noten liegen)
        entfernt werden und der Rest nach links rückt.
        """
        # 1. Finde alle Pausen, die exakt gleichzeitig mit einer Note starten
        to_remove = []
        for r in measure.getElementsByClass('Rest'):
            # Prüfe, ob am selben Offset eine Note existiert
            overlapping_notes = [n for n in measure.getElementsByOffset(r.offset).notes if n.isNote]
            if overlapping_notes:
                to_remove.append(r)

        if not to_remove:
            return False # Nichts zum Reparieren gefunden

        # 2. Entferne die Pausen
        for r in to_remove:
            measure.remove(r)
            
        # 3. 'Shift-Left': In music21 korrigiert .flat die Offsets oft automatisch,
        # aber wir markieren den Takt als 'bearbeitet'.
        measure.editorial.comments.append("Shift-Left: Filler rests removed.")
        return True

    @staticmethod
    def mark_for_review(measure, message):
        """Markiert den Takt für die Web-UI rot."""
        for n in measure.flat.notes:
            n.style.color = '#FF0000' # Rot für Verovio