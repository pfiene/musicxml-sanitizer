import os
import zipfile
import io
from lxml import etree
from music21 import converter

INPUT_DIR = "input"
OUTPUT_DIR = "output_cleaned"
LOG_FILE = "audit_log.txt"

def log_message(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")
    print(message)

def extract_mxl(filepath):
    """Extrahiert das XML aus einer komprimierten .mxl Datei ohne music21."""
    try:
        with zipfile.ZipFile(filepath, 'r') as z:
            # Suche nach der eigentlichen Musik-Datei (meistens nicht META-INF)
            for name in z.namelist():
                if name.endswith('.xml') and not name.startswith('META-INF'):
                    return z.read(name)
    except Exception as e:
        log_message(f"  [Error] MXL-Extraktion fehlgeschlagen: {e}")
    return None

def clean_xml_content(xml_data):
    """Reinigt das XML auf Element-Ebene (lxml)."""
    try:
        parser = etree.XMLParser(remove_blank_text=True, recover=True)
        root = etree.fromstring(xml_data, parser)

        # 1. Layout-Ballast entfernen
        bad_tags = ['print', 'defaults', 'appearance', 'work', 'identification', 'defaults']
        bad_attrs = ['default-x', 'default-y', 'relative-x', 'relative-y']

        for tag in bad_tags:
            for el in root.xpath(f'//{tag}'):
                el.getparent().remove(el)

        for attr in bad_attrs:
            for el in root.xpath(f'//*[@{attr}]'):
                el.attrib.pop(attr)

        # 2. Fix: Unmögliche Notenwerte (2048th etc.) abfangen
        # Wir ersetzen extrem kurze Werte, die music21 zum Absturz bringen
        for type_el in root.xpath("//type"):
            if type_el.text in ["2048th", "1024th", "512th"]:
                log_message(f"  [Fix] Zu kurze Note ({type_el.text}) in 256th korrigiert.")
                type_el.text = "256th"

        return etree.tostring(root, encoding="utf-8", xml_declaration=True)
    except Exception as e:
        log_message(f"  [Error] XML-Bereinigung fehlgeschlagen: {e}")
        return None

def run_robust_sanitizer():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    open(LOG_FILE, "w").close() # Log leeren

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.xml', '.musicxml', '.mxl'))]
    
    for filename in files:
        log_message(f"\n--- Verarbeite: {filename} ---")
        in_path = os.path.join(INPUT_DIR, filename)
        
        # 1. Daten laden (MXL oder XML)
        raw_xml = None
        if filename.lower().endswith('.mxl'):
            raw_xml = extract_mxl(in_path)
        else:
            with open(in_path, 'rb') as f:
                raw_xml = f.read()

        if not raw_xml: continue

        # 2. XML-Struktur reinigen
        cleaned_xml = clean_xml_content(raw_xml)
        if not cleaned_xml: continue

        # 3. Finales Normalisieren mit music21
        out_filename = os.path.splitext(filename)[0] + "_cleaned.musicxml"
        out_path = os.path.join(OUTPUT_DIR, out_filename)

        try:
            # Wir laden das bereits bereinigte XML in music21
            score = converter.parse(cleaned_xml)
            score.write('musicxml', fp=out_path)
            log_message(f"  [Erfolg] Validiert und gespeichert.")
        except Exception as e:
            # Falls music21 immer noch scheitert, speichern wir zumindest das 'cleaned' XML
            with open(out_path, 'wb') as f:
                f.write(cleaned_xml)
            log_message(f"  [Warnung] Musik-Logik-Fehler. Struktur wurde trotzdem gerettet: {e}")

if __name__ == "__main__":
    run_robust_sanitizer()
    