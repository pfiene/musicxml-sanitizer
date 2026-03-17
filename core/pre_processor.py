import re
import zipfile
import io

def clean_raw_xml(xml_string):
    """Repariert Beethoven/Liszt-Fehler auf Textebene."""
    # Ersetze alle mathematisch unmöglichen Notentypen durch 256stel
    invalid_types = ["2048th", "1024th", "512th"]
    for t in invalid_types:
        xml_string = xml_string.replace(f"<type>{t}</type>", "<type>256th</type>")
    
    # Manchmal gibt es <duration>0</duration> innerhalb von Noten, 
    # was music21 beim Exportieren hasst. Wir setzen ein Minimum von 1.
    xml_string = xml_string.replace("<duration>0</duration>", "<duration>1</duration>")
    
    # Korrupte MIDI-Daten entfernen
    xml_string = re.sub(r'<midi-device.*/>', '', xml_string)
    xml_string = re.sub(r'<midi-instrument.*?>.*?</midi-instrument>', '', xml_string, flags=re.DOTALL)
    
    return xml_string

def load_robustly(filepath):
    """Extrahiert XML aus MXL oder liest XML direkt."""
    try:
        if str(filepath).lower().endswith('.mxl'):
            with zipfile.ZipFile(filepath, 'r') as z:
                # Suche die Haupt-Musik-Datei
                for name in z.namelist():
                    if name.endswith('.xml') and "container.xml" not in name and "META-INF" not in name:
                        content = z.read(name).decode('utf-8', errors='ignore')
                        return clean_raw_xml(content)
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return clean_raw_xml(f.read())
    except Exception as e:
        print(f"Konnte Datei nicht lesen: {e}")
    return ""