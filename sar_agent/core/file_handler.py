import fitz  # PyMuPDF for PDF
import docx
import pandas as pd
import xml.etree.ElementTree as ET

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_from_csv(file_path: str) -> str:
    df = pd.read_csv(file_path)
    return df.to_string()

def extract_text_from_xml(file_path: str) -> str:
    tree = ET.parse(file_path)
    root = tree.getroot()
    return ET.tostring(root, encoding="unicode")
