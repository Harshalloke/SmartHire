import re
from typing import Dict, Tuple, List
from .resume_parser import extract_years_of_experience

SENIOR_SIGNALS = {
    "architect","lead","principal","senior","owner","owned","mentored","managed","designed",
    "architected","scaled","roadmap","strategy","stakeholder","leadership"
}
MID_SIGNALS = {"independently","delivered","end-to-end","feature","module","ownership"}

def count_bullets(text: str) -> int:
    return len(re.findall(r"[\n\r]\s*(?:-|\u2022|\u25CF|\u25E6|\u2219)\s+", text))

def detect_level(text: str) -> Dict:
    t = text.lower()
    years_min, years_max = extract_years_of_experience(text)
    bullets = count_bullets(text)

    senior_hits = sum(1 for w in SENIOR_SIGNALS if w in t)
    mid_hits = sum(1 for w in MID_SIGNALS if w in t)

    # crude project count proxy
    projects = len(re.findall(r"\b(project|initiative|module|feature)\b", t))

    # rules
    level = "Fresher"
    if years_max >= 6 or senior_hits >= 3 or (years_max >= 4 and projects >= 6):
        level = "Senior"
    elif years_max >= 2 or mid_hits >= 2 or projects >= 3:
        level = "Mid"

    signals: List[str] = []
    if years_max: signals.append(f"Years mentioned: {years_min}–{years_max}")
    if bullets: signals.append(f"Bullet points: {bullets}")
    if senior_hits: signals.append(f"Senior keywords: {senior_hits}")
    if mid_hits and level != "Senior": signals.append(f"Mid-level keywords: {mid_hits}")
    if projects: signals.append(f"Project mentions: {projects}")

    return {
        "level": level,
        "years": {"min": years_min, "max": years_max},
        "signals": signals
    }
