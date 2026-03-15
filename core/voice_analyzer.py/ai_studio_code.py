def analyze_vocal_slices(measure):
    """
    Analysiert einen Takt auf überlappende Stimmen und 'Füll-Pausen'.
    """
    # 1. Alle Stimmen im Takt identifizieren
    voices = measure.voices
    if not voices:
        # Falls keine expliziten <voice> Tags da sind, behandeln wir alles als eine Stimme
        voices = [measure]

    slice_map = {} # Zeit-Stempel -> Liste von Elementen

    for v in voices:
        for element in v.flat.notesAndRests:
            offset = element.offset
            if offset not in slice_map:
                slice_map[offset] = []
            slice_map[offset].append(element)

    # 2. Konflikt-Erkennung
    for offset, elements in slice_map.items():
        if len(elements) > 1:
            # Hier liegt Musik übereinander!
            rests = [e for e in elements if e.isRest]
            notes = [e for e in elements if e.isNote]
            
            if rests and notes:
                # Klassischer Fall: Eine Pause liegt 'unter' einer Note
                for r in rests:
                    # Markiere als [SUSPECTED_FILLER] statt zu löschen
                    r.editorial.misc['sanitizer_action'] = 'hide_as_filler'
                    r.style.hideObjectOnPrint = True # Für Großdruck/Export