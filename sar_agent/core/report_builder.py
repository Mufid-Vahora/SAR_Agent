from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import xml.etree.ElementTree as ET

def build_pdf_report(text: str, output_path: str = "report.pdf"):
    doc = SimpleDocTemplate(output_path)
    styles = getSampleStyleSheet()
    flowables = [Paragraph(text, styles["Normal"])]
    doc.build(flowables)
    return output_path

def build_xml_report(data: dict, output_path: str = "report.xml"):
    root = ET.Element("SARReport")
    for key, value in data.items():
        child = ET.SubElement(root, key)
        child.text = str(value)
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return output_path
