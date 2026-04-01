import xml.etree.ElementTree as ET
import re
from parser import RobustParser  # Importiert die Klasse aus core/parser.py

_last_log = ""

def sort_note_children(n):
    order = ['grace', 'chord', 'pitch', 'rest', 'duration', 'tie', 'voice', 'type', 'dot', 'accidental', 'time-modification', 'stem', 'staff', 'beam', 'notations']
    children = list(n)
    children.sort(key=lambda x: order.index(x.tag) if x.tag in order else 99)
    for c in list(n): n.remove(c)
    for c in children: n.append(c)

def clean_and_scan(xml_string):
    proposals = []
    # Namespaces entfernen für einfachere Verarbeitung
    xml_string = re.sub(r'\sxmlns="[^"]+"', '', xml_string, count=1)
    xml_string = re.sub(r'\sxmlns:[^=]+="[^"]+"', '', xml_string)
    
    try:
        root = ET.fromstring(xml_string.encode("utf-8"))
        for el in root.iter():
            if '}' in el.tag: el.tag = el.tag.split('}', 1)[1]

        divs_el = root.find('.//divisions')
        divs = int(divs_el.text) if divs_el is not None else 480
        curr_beats, curr_type = 4, 4 

        for measure in root.findall('.//part/measure'):
            m_num = measure.get('number', '?')
            measure.set('id', f'm-idx-{m_num}')
            
            t_el = measure.find('.//time')
            if t_el is not None:
                curr_beats = int(t_el.findtext('beats', str(curr_beats)))
                curr_type = int(t_el.findtext('beat-type', str(curr_type)))
            
            limit = int(curr_beats * (4 / curr_type) * divs)
            st_durs = {"1": 0, "2": 0}

            for n in measure.findall('.//note'):
                if n.find('chord') is None and n.find('grace') is None:
                    st = n.findtext('staff', '1')
                    if st not in st_durs: st_durs[st] = 0
                    st_durs[st] += int(n.findtext('duration', '0'))
                sort_note_children(n)

            for st, dur in st_durs.items():
                if dur > limit + 5:
                    eff, nom = round(dur/divs, 2), round(limit/divs, 2)
                    proposals.append({
                        "type": "SUGGESTED_HEALING",
                        "measure": int(m_num) if m_num.isdigit() else m_num,
                        "message": f"Takt {m_num} überfüllt ({eff}/{nom}).",
                        "action_id": "convert_to_grace",
                        "xml_id": f"m-idx-{m_num}"
                    })

        out = ET.tostring(root, encoding='unicode', method='xml')
        header = '<?xml version="1.0" encoding="UTF-8"?>\n'
        return header + out, proposals
    except Exception as e:
        return xml_string, [{"type": "ERROR", "message": str(e)}]

def load_robustly(file_path):
    global _last_log
    # Hier nutzen wir den RobustParser aus der parser.py
    raw_xml_bytes = RobustParser.pre_clean_xml(file_path)
    
    if not raw_xml_bytes:
        _last_log = "Fehler: Datei konnte nicht gelesen werden."
        return ""

    xml_string = raw_xml_bytes.decode('utf-8', errors='ignore')
    cleaned_xml, proposals = clean_and_scan(xml_string)
    
    if proposals:
        _last_log = "\n".join([p['message'] for p in proposals])
    else:
        _last_log = "Keine Korrekturen notwendig."
        
    return cleaned_xml

def get_last_log():
    return _last_log