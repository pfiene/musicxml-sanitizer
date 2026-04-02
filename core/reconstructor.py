from music21 import note

class Reconstructor:
    @staticmethod
    def fix_overfull_measure(measure):
        to_remove = []
        for r in measure.flatten().getElementsByClass('Rest'):
            overlapping = [n for n in measure.flatten().getElementsByOffset(r.offset).notes if n.isNote]
            if overlapping: to_remove.append(r)
        for r in to_remove: measure.remove(r)
        return len(to_remove) > 0

    @staticmethod
    def fill_with_rests(measure):
        expected = float(measure.barDuration.quarterLength)
        actual = float(measure.duration.quarterLength)
        needed = expected - actual
        if needed > 0.01:
            r = note.Rest()
            r.duration.quarterLength = needed
            measure.append(r)
            return True
        return False

    @staticmethod
    def convert_to_grace(measure):
        """Wandelt Noten in Grace-Notes um, indem die Dauer auf 0 gesetzt wird."""
        notes = list(measure.flatten().notes)
        if not notes: return False
        for n in notes:
            # Der sicherste Weg in music21: Dauer auf 0 und Typ festlegen
            n.duration.quarterLength = 0.0
            if not n.duration.type or n.duration.type == 'zero':
                n.duration.type = '16th' 
        return True

    @staticmethod
    def mark_for_review(measure, message="Review"):
        for n in measure.flatten().notes: n.style.color = '#FF0000'
        return True