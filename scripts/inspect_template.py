import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def main():
    docx_path = Path(r"C:\Users\User\Desktop\Jurnal\JOIN Template 2025.docx")
    if not docx_path.exists():
        print(f"Error: {docx_path} not found")
        return

    with zipfile.ZipFile(docx_path) as z:
        xml_content = z.read("word/document.xml")

    root = ET.fromstring(xml_content)
    namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    paragraphs = []
    for p in root.findall(".//w:p", namespaces):
        # Check style if any
        pStyle = p.find(".//w:pPr/w:pStyle", namespaces)
        style_name = pStyle.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val") if pStyle is not None else ""

        texts = [node.text for node in p.findall(".//w:t", namespaces) if node.text]
        full_text = "".join(texts).strip()
        if full_text:
            paragraphs.append(f"[{style_name}] {full_text}")

    output_path = Path("template_structure.txt")
    output_path.write_text("\n".join(paragraphs), encoding="utf-8")
    print(f"Template extracted to {output_path} ({len(paragraphs)} paragraphs)")

if __name__ == "__main__":
    main()
