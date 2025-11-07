# utils/sections.py
import re

SECTION_PATTERNS = [
    ("experience", r"(experience|work experience|employment)\b"),
    ("projects", r"(projects?)\b"),
    ("skills", r"(skills|technologies|tech stack)\b"),
    ("education", r"(education|academics)\b"),
    ("summary", r"(summary|objective|profile)\b"),
]

def split_sections(text: str):
    t = text or ""
    # simple heading-based split
    indices = []
    for name, pat in SECTION_PATTERNS:
        for m in re.finditer(rf"(?im)^.*{pat}.*$", t):
            indices.append((m.start(), name))
    indices.sort()
    chunks = []
    for i, (pos, name) in enumerate(indices):
        end = indices[i+1][0] if i + 1 < len(indices) else len(t)
        chunks.append((name, t[pos:end]))
    # fallback: whole text as summary if no headings
    if not chunks:
        chunks = [("summary", t)]
    return chunks
