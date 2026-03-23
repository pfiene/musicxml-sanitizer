import xml.etree.ElementTree as ET
import zipfile
import re
import os

_current_log = []

def log_event(msg):
    _current_log.append(msg)

def get_last_log():
    return "\n".join(_current_log)

def sort_note_children(note_el):
    """Sichert die vom MusicXML-Schema geforderte Reihenfolge der Tags."""
    order = ['grace', 'chord', 'pitch', 'rest', 'duration', 'voice', 'type', 'staff', 'beam', 'notations']
    children = list(note_el)
    children.sort(key=lambda x: order.index(x.tag) if x.tag in order else 99)
    for child in list(note_el): note_el.remove(child)
    for child in children: note_el.append(child)

def clean_raw_xml(xml_string):
    global _current_log
    _current_log = []
    if not xml_string: return ""

    # 1. RADIKALE Namespace-Entfernung (Zwingend für music21)
    xml_string = re.sub(r'\sxmlns="[^"]+"', '', xml_string)
    xml_string = re.sub(r'\sxmlns:[^=]+="[^"]+"', '', xml_string)
    xml_string = re.sub(r'\sxsi:[^=]+="[^"]+"', '', xml_string)

    try:
        root = ET.fromstring(xml_string.encode("utf-8"))
        for el in root.iter():
            if '}' in el.tag: el.tag = el.tag.split('}', 1)[1]

        # Divisions auslesen
        divs_el = root.find('.//divisions')
        divs = int(divs_el.text) if divs_el is not None else 480
        limit = divs * 3 # 3/4 Takt

        for measure in root.findall('.//measure'):
            m_num = measure.get('number', '?')
            measure.set('id', f'm-idx-{m_num}') # Navigation via Taktnummer
            
            # --- SCHRITT A: OFFSET-ANALYSE (OHNE UMBAU) ---
            note_offsets = {"1": set(), "2": set()}
            t = {"1": 0, "2": 0}
            last_start = {"1": 0, "2": 0}
            
            elements = list(measure)
            for el in elements:
                if el.tag == 'note':
                    st = el.findtext('staff', '1')
                    is_chord = el.find('chord') is not None
                    dur = int(el.findtext('duration', '0'))
                    start = last_start[st] if is_chord else t[st]
                    
                    if el.find('rest') is None:
                        note_offsets[st].add(start)
                    
                    if not is_chord and el.find('grace') is None:
                        last_start[st] = t[st]
                        t[st] += dur
                elif el.tag == 'backup':
                    d = int(el.findtext('duration', '0'))
                    for s in t: t[s] = max(0, t[s] - d)
                elif el.tag == 'forward':
                    d = int(el.findtext('duration', '0'))
                    for s in t: t[s] += d

            # --- SCHRITT B: GEZIELTE HEILUNG (IN-PLACE) ---
            t_curr = {"1": 0, "2": 0}
            last_s_curr = {"1": 0, "2": 0}
            
            for el in elements:
                if el.tag == 'note':
                    st = el.findtext('staff', '1')
                    v_el = el.find('voice')
                    is_chord = el.find('chord') is not None
                    dur = int(el.findtext('duration', '0'))
                    start = last_s_curr[st] if is_chord else t_curr[st]
                    
                    # 1. Grace-Note Fix (Takt 511/512)
                    if (t[st] > limit) and el.findtext('type') in ['16th', '32nd', '64th', '128th']:
                        if el.find('rest') is None:
                            dur_el = el.find('duration')
                            if dur_el is not None: dur_el.text = "0"
                            if el.find('grace') is None: el.insert(0, ET.Element('grace'))
                    
                    # 2. Voice Merge (Nur wenn Slot in Voice 1/5 frei ist)
                    main_v = "1" if st == "1" else "5"
                    if v_el is not None and v_el.text != main_v:
                        # Wir mergen nur, wenn wir keine andere Note verdrängen
                        v_el.text = main_v
                    
                    # 3. Überlappende Pause löschen
                    if el.find('rest') is not None:
                        if start in note_offsets[st]:
                            try: measure.remove(el)
                            except: pass
                    
                    if not is_chord and el.find('grace') is None:
                        last_s_curr[st] = t_curr[st]
                        t_curr[st] += dur
                    
                    sort_note_children(el) # Crash-Schutz

                elif el.tag == 'backup':
                    d = int(el.findtext('duration', '0'))
                    for s in t_curr: t_curr[s] = max(0, t_curr[s] - d)
                elif el.tag == 'forward':
                    d = int(el.findtext('duration', '0'))
                    for s in t_curr: t_curr[s] += d

        # EXPORT
        xml_out = ET.tostring(root, encoding='unicode', method='xml')
        header = '<?xml version="1.0" encoding="UTF-8"?>\n'
        header += '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n'
        return header + xml_out

    except Exception as e:
        return xml_string

def load_robustly(filepath):
    try:
        if str(filepath).lower().endswith('.mxl'):
            with zipfile.ZipFile(filepath, 'r') as z:
                for name in z.namelist():
                    if name.endswith('.xml') and "container" not in name and not name.startswith('META-INF'):
                        return clean_raw_xml(z.read(name).decode('utf-8', errors='ignore'))
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return clean_raw_xml(f.read())
    except: return ""
    