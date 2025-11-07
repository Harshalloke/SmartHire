import re
from typing import Tuple
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_pdf(path: str) -> str:
    text = []
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            text.append(page.extract_text() or "")
    except Exception:
        return ""
    return "\n".join(text)

def extract_text_from_docx(path: str) -> str:
    try:
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception:
        return ""

def extract_text_from_txt(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def extract_text_from_file(path: str) -> str:
    path_l = path.lower()
    if path_l.endswith(".pdf"):
        return extract_text_from_pdf(path)
    if path_l.endswith(".docx"):
        return extract_text_from_docx(path)
    if path_l.endswith(".txt"):
        return extract_text_from_txt(path)
    return ""

def clean_text(text: str) -> str:
    text = text.lower()
    # keep + # / - . because they appear in skills like c++, c#, ci/cd
    text = re.sub(r"[^a-z0-9\s\-\+\/\.\#]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_years_of_experience(text: str) -> Tuple[int, int]:
    """
    Very rough extractor: returns (min_years, max_years) found from patterns like '3 years', '2-4 years'.
    """
    years = []
    for rng in re.findall(r"(\d+)\s*-\s*(\d+)\s*years?", text, flags=re.I):
        years.extend([int(rng[0]), int(rng[1])])
    for single in re.findall(r"(\d+)\s*years?", text, flags=re.I):
        years.append(int(single))
    if not years:
        return (0, 0)
    return (min(years), max(years))
