import xml.etree.ElementTree as ET
import zipfile
import re

# Globaler Speicher für das aktuelle Protokoll
_current_log = []

def log_event(msg):
    _current_log.append(msg)

def get_last_log():
    return "\n".join(_current_log)

def clean_raw_xml(xml_string):
    global _current_log
    _current_log = [] # Protokoll zurücksetzen
    
    if not xml_string: return ""

    # 1. Namespace-Entfernung
    xml_string = re.sub(r'\sxmlns="[^"]+"', '', xml_string, count=1)
    
    # Rhythmus-Fixes mit Logging
    if "<type>2048th</type>" in xml_string:
        log_event("[RHYTHM] 2048th Noten zu 256th korrigiert.")
        xml_string = xml_string.replace("<type>2048th</type>", "<type>256th</type>")
    if "<type>1024th</type>" in xml_string:
        log_event("[RHYTHM] 1024th Noten zu 256th korrigiert.")
        xml_string = xml_string.replace("<type>1024th</type>", "<type>256th</type>")
    
    try:
        root = ET.fromstring(xml_string.encode("utf-8"))
        
        measure_idx = 0
        for part in root.findall('.//part'):
            part_id = part.get('id', 'P1')
            for measure in part.findall('.//measure'):
                measure_idx += 1
                m_num = measure.get('number', str(measure_idx))
                measure.set('id', f'm-idx-{measure_idx}')
                
                occupied_slots = {"1": set(), "2": set()}
                elements = list(measure)
                
                # Zeit-Analyse
                t = {"1": 0, "2": 0}
                last_start = {"1": 0, "2": 0}
                for el in elements:
                    if el.tag == 'note':
                        st = el.findtext('staff') or "1"
                        is_chord = el.find('chord') is not None
                        dur = int(el.findtext('duration') or 0)
                        start = last_start[st] if is_chord else t[st]
                        if el.find('rest') is None:
                            occupied_slots[st].add(start)
                        if not is_chord and el.find('grace') is None:
                            last_start[st] = t[st]
                            t[st] += dur
                    elif el.tag == 'backup':
                        d = int(el.findtext('duration') or 0)
                        for s in t: t[s] -= d
                    elif el.tag == 'forward':
                        d = int(el.findtext('duration') or 0)
                        for s in t: t[s] += d

                # Heilung & Logging
                t = {"1": 0, "2": 0}
                last_start = {"1": 0, "2": 0}
                for el in elements:
                    if el.tag == 'note':
                        st = el.findtext('staff') or "1"
                        is_chord = el.find('chord') is not None
                        dur = int(el.findtext('duration') or 0)
                        start = last_start[st] if is_chord else t[st]
                        
                        # Voice Merge Log
                        v_el = el.find('voice')
                        if v_el is not None and v_el.text not in ["1", "5"]:
                            old_v = v_el.text
                            new_v = "1" if st == "1" else "5"
                            v_el.text = new_v
                            log_event(f"[VOICE] Takt {m_num}: Note (Staff {st}) von Voice {old_v} nach {new_v} verschoben.")
                        
                        # Rest Removal Log
                        if el.find('rest') is not None:
                            if start in occupied_slots[st]:
                                measure.remove(el)
                                log_event(f"[CLEANUP] Takt {m_num}: Überlappende Pause bei Offset {start} (Staff {st}) entfernt.")
                        
                        if not is_chord and el.find('grace') is None:
                            last_start[st] = t[st]
                            t[st] += dur
                    elif el.tag == 'backup':
                        d = int(el.findtext('duration') or 0)
                        for s in t: t[s] -= d
                    elif el.tag == 'forward':
                        d = int(el.findtext('duration') or 0)
                        for s in t: t[s] += d

        return ET.tostring(root, encoding='unicode')

    except Exception as e:
        log_event(f"[ERROR] XML-Parsing fehlgeschlagen: {e}")
        return xml_string

def load_robustly(filepath):
    # (Bleibt gleich wie bisher, ruft clean_raw_xml auf)
    try:
        if str(filepath).lower().endswith('.mxl'):
            with zipfile.ZipFile(filepath, 'r') as z:
                for name in z.namelist():
                    if name.endswith('.xml') and "container" not in name:
                        return clean_raw_xml(z.read(name).decode('utf-8', errors='ignore'))
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return clean_raw_xml(f.read())
    except: return ""