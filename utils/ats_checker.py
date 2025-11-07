import re
from typing import Dict, List

ACTION_VERBS = {
    "led","built","created","developed","designed","implemented","optimized","improved",
    "delivered","launched","migrated","automated","analyzed","architected","debugged",
    "deployed","maintained","mentored","owned","refactored","reduced","increased","saved"
}
SECTION_KEYWORDS = ["experience","work experience","projects","education","skills","summary","profile"]
BULLET_CHARS = r"[\-\u2022\u25CF\u25E6\u2219]"
ODD_SYMBOLS = r"[✓✔✗✘★☆◆◼︎►▸•➤➢➔➜➤]"

def flesch_reading_ease(text: str) -> float:
    # lightweight readability estimate
    words = re.findall(r"[A-Za-z]+", text)
    sents = re.split(r"[.!?]+", text)
    syls = sum(len(re.findall(r"[aeiouyAEIOUY]+", w)) or 1 for w in words)
    w = max(len(words), 1)
    s = max(len([x for x in sents if x.strip()]), 1)
    # Flesch Reading Ease (approx)
    return 206.835 - 1.015*(w/s) - 84.6*(syls/w)

def quick_ats_check(raw_resume_text: str) -> Dict:
    warnings: List[str] = []
    txt = raw_resume_text or ""

    # Length
    words = len(re.findall(r"\w+", txt))
    if words < 200: warnings.append("Resume may be too short. Add role-specific details.")
    if words > 1600: warnings.append("Resume may be too long for quick ATS skim.")

    # Contact info
    if not re.search(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", txt): warnings.append("Email not detected as plain text.")
    if not re.search(r"\b(\+?\d[\d\-\s]{7,})\b", txt): warnings.append("Phone number not detected as plain text.")

    # Sections
    found_secs = sum(1 for s in SECTION_KEYWORDS if s in txt.lower())
    if found_secs < 3: warnings.append("Standard sections (Experience/Education/Skills) not clearly labeled.")

    # Bullets and symbols
    if not re.search(BULLET_CHARS, txt): warnings.append("Use simple hyphen or • bullets for readability.")
    if re.search(ODD_SYMBOLS, txt): warnings.append("Avoid decorative symbols; ATS may not parse them correctly.")

    # Dates format
    if not re.search(r"\b(20\d{2}|19\d{2})\b", txt):
        warnings.append("Job dates (years) not detected. Add years for each role.")

    # Action verbs
    verbs_found = sum(1 for v in ACTION_VERBS if re.search(rf"\b{re.escape(v)}\b", txt, flags=re.I))
    if verbs_found < 4: warnings.append("Use strong action verbs (built, implemented, optimized, etc.).")

    # Readability
    fre = flesch_reading_ease(txt)
    if words >= 250 and fre < 40:
        warnings.append("Sentences may be too complex. Shorten for clarity.")

    # Score (start 100, subtract weighted penalties)
    penalty = (
        8 * (words < 200) +
        6 * (words > 1600) +
        8 * (not re.search(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", txt)) +
        8 * (not re.search(r"\b(\+?\d[\d\-\s]{7,})\b", txt)) +
        6 * (found_secs < 3) +
        4 * (not re.search(BULLET_CHARS, txt)) +
        3 * (re.search(ODD_SYMBOLS, txt) is not None) +
        5 * (not re.search(r"\b(20\d{2}|19\d{2})\b", txt)) +
        5 * (verbs_found < 4) +
        4 * (words >= 250 and fre < 40)   # updated condition
    )
    score = max(0, 100 - min(60, penalty))
    return {"ats_score": int(round(score)), "warnings": warnings}
