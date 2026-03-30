import xml.etree.ElementTree as ET
import re

def sort_note_children(n):
    order = ['grace', 'chord', 'pitch', 'rest', 'duration', 'tie', 'voice', 'type', 'dot', 'accidental', 'time-modification', 'stem', 'staff', 'beam', 'notations']
    children = list(n); children.sort(key=lambda x: order.index(x.tag) if x.tag in order else 99)
    for c in list(n): n.remove(c)
    for c in children: n.append(c)

def clean_and_scan(xml_string):
    """
    Macht technische Fixes (IDs, Tag-Order) und gibt eine Liste 
    von HEALING_PROPOSALS zurück, ohne das XML musikalisch zu verändern.
    """
    proposals = []
    xml_string = re.sub(r'\sxmlns="[^"]+"', '', xml_string, count=1)
    xml_string = re.sub(r'\sxmlns:[^=]+="[^"]+"', '', xml_string)
    
    try:
        root = ET.fromstring(xml_string.encode("utf-8"))
        for el in root.iter():
            if '}' in el.tag: el.tag = el.tag.split('}', 1)[1]

        divs = int(root.find('.//divisions').text) if root.find('.//divisions') is not None else 480
        curr_beats, curr_type = 3, 4 # Start Beethoven

        for measure in root.findall('.//part/measure'):
            m_num = measure.get('number', '?')
            measure.set('id', f'm-idx-{m_num}') # Nav-ID
            
            # Taktart-Tracking
            t_el = measure.find('.//time')
            if t_el is not None:
                curr_beats = int(t_el.findtext('beats', str(curr_beats)))
                curr_type = int(t_el.findtext('beat-type', str(curr_type)))
            
            limit = int(curr_beats * (4 / curr_type) * divs)
            
            # Analyse der Dauer
            st_durs = {"1": 0, "2": 0}
            for n in measure.findall('.//note'):
                if n.find('chord') is None and n.find('grace') is None:
                    st = n.findtext('staff', '1')
                    st_durs[st] += int(n.findtext('duration', '0'))
                sort_note_children(n) # IMMER technischer Fix

            # VORSCHLÄGE GENERIEREN (statt direkt heilen)
            for st, dur in st_durs.items():
                if dur > limit + 5:
                    eff, nom = round(dur/divs, 2), round(limit/divs, 2)
                    proposals.append({
                        "type": "SUGGESTED_HEALING",
                        "measure": int(m_num) if m_num.isdigit() else m_num,
                        "message": f"Takt überfüllt ({eff}/{nom}). Kleine Noten zu Grace-Notes machen?",
                        "action_id": "convert_to_grace",
                        "xml_id": f"m-idx-{m_num}"
                    })

        # XML zurückgeben (nur technisch bereinigt)
        out = ET.tostring(root, encoding='unicode', method='xml')
        header = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n'
        return header + out, proposals

    except:
        return xml_string, []
    