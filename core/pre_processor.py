import re
import zipfile

def clean_raw_xml(xml_string):
    """Bereinigt MusicXML und setzt stabile IDs."""
    if not xml_string: return ""
    
    # Rhythmus-Fixes
    xml_string = xml_string.replace("<type>2048th</type>", "<type>256th</type>")
    xml_string = xml_string.replace("<type>1024th</type>", "<type>256th</type>")
    
    # ID-Salat entfernen
    xml_string = re.sub(r'(<measure[^>]*?)\s+(?:xml:)?id="[^"]*"', r'\1', xml_string)

    # Stabile IDs setzen
    count = [0]
    def inject_id(match):
        count[0] += 1
        return f'<measure id="m-idx-{count[0]}" '

    xml_string = re.sub(r'<measure\s*', inject_id, xml_string)
    return xml_string

def load_robustly(filepath):
    """Lädt .mxl oder .musicxml aus dem Dateisystem."""
    content = ""
    try:
        if str(filepath).lower().endswith('.mxl'):
            with zipfile.ZipFile(filepath, 'r') as z:
                for name in z.namelist():
                    if name.endswith('.xml') and "container" not in name:
                        content = z.read(name).decode('utf-8', errors='ignore')
                        break
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
    except Exception as e:
        print(f"Fehler in core.pre_processor: {e}")
        return ""
    return clean_raw_xml(content)