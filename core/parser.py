import zipfile
import re
from lxml import etree

class RobustParser:
    @staticmethod
    def pre_clean_xml(file_path):
        try:
            xml_data = b""
            if str(file_path).lower().endswith('.mxl'):
                with zipfile.ZipFile(file_path, 'r') as z:
                    for name in z.namelist():
                        if name.endswith('.xml') and not name.startswith('META-INF'):
                            xml_data = z.read(name)
                            break
            else:
                with open(file_path, 'rb') as f:
                    xml_data = f.read()

            if not xml_data: return None

            # Wir arbeiten auf Byte-Ebene für maximale Sicherheit
            # Ersetzt alle extremen Notentypen durch 256th
            decoded = xml_data.decode('utf-8', errors='ignore')
            decoded = re.sub(r'<type>(2048th|1024th|512th)</type>', '<type>256th</type>', decoded)
            
            parser = etree.XMLParser(recover=True, remove_blank_text=True)
            root = etree.fromstring(decoded.encode('utf-8'), parser)
            
            return etree.tostring(root, encoding='utf-8', xml_declaration=True)
        except Exception as e:
            print(f"Parser-Fehler: {e}")
            return None