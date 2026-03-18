import re
import zipfile

def clean_raw_xml(xml_string):
    # 1. Rhythmus-Fixes
    xml_string = xml_string.replace("<type>2048th</type>", "<type>256th</type>")
    xml_string = xml_string.replace("<type>1024th</type>", "<type>256th</type>")
    
    # 2. Globaler Takt-Zähler (ignoriert Sätze/Movements)
    count = 0
    def id_replacer(match):
        nonlocal count
        count += 1
        # Wir setzen eine absolut eindeutige ID: m-idx-1, m-idx-2...
        return f'<measure xml:id="m-idx-{count}"'

    # Ersetzt den Anfang jedes <measure ... Tags
    xml_string = re.sub(r'<measure', id_replacer, xml_string)
    
    return xml_string

def load_robustly(filepath):
    try:
        if str(filepath).lower().endswith('.mxl'):
            with zipfile.ZipFile(filepath, 'r') as z:
                for name in z.namelist():
                    if name.endswith('.xml') and "container" not in name:
                        return clean_raw_xml(z.read(name).decode('utf-8', errors='ignore'))
    except: pass
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return clean_raw_xml(f.read())