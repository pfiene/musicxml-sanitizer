import xml.etree.ElementTree as ET
import re

_last_log = ""

def sort_note_children(n):
    order = ['grace', 'chord', 'pitch', 'rest', 'duration', 'tie', 'voice', 'type', 'dot', 'accidental', 'time-modification', 'stem', 'staff', 'beam', 'notations']
    children = list(n)
    children.sort(key=lambda x: order.index(x.tag) if x.tag in order else 99)
    for c in list(n): n.remove(c)
    for c in children: n.append(c)

def clean_and_scan(xml_string):
    global _last_log
    _last_log = ""
    proposals = []
    fixes_count = 0
    
    # Namespaces entfernen
    xml_string = re.sub(r'\sxmlns="[^"]+"', '', xml_string, count=1)
    xml_string = re.sub(r'\sxmlns:[^=]+="[^"]+"', '', xml_string)
    
    try:
        root = ET.fromstring(xml_string.encode("utf-8"))
        
        # Divisions finden (Standard 480)
        divs_el = root.find('.//divisions')
        divs = int(divs_el.text) if divs_el is not None else 480
        
        # MATHEMATIK-FIX: 
        # Ein 256stel ist (divisions * 4) / 256  => divisions / 64
        # Alles was kleiner ist, bringt music21 zum Absturz.
        min_safe_duration = max(1, divs // 64)

        for note in root.findall('.//part/measure/note'):
            dur_el = note.find('duration')
            type_el = note.find('type')
            
            # 1. Check: Ist die Note zu kurz?
            if dur_el is not None and note.find('grace') is None:
                val = int(dur_el.text)
                if val < min_safe_duration:
                    dur_el.text = str(min_safe_duration)
                    if type_el is not None:
                        type_el.text = '256th'
                    fixes_count += 1
            
            # 2. Check: Ist der Typ verboten?
            if type_el is not None and type_el.text in ['2048th', '1024th', '512th']:
                type_el.text = '256th'
                if dur_el is not None:
                    dur_el.text = str(max(int(dur_el.text), min_safe_duration))
                fixes_count += 1

            sort_note_children(note)

        _last_log = f"Technik: {fixes_count} Micro-Noten (2048th) auf 256th-Niveau gehoben."
        out = ET.tostring(root, encoding='unicode', method='xml')
        header = '<?xml version="1.0" encoding="UTF-8"?>\n'
        return header + out, proposals

    except Exception as e:
        _last_log = f"Fehler: {e}"
        return xml_string, []

def load_robustly(file_path):
    from parser import RobustParser
    raw_bytes = RobustParser.pre_clean_xml(file_path)
    if not raw_bytes: return ""
    xml_str = raw_bytes.decode("utf-8", errors="ignore")
    cleaned_xml, _ = clean_and_scan(xml_str)
    return cleaned_xml

def get_last_log():
    global _last_log
    return _last_log