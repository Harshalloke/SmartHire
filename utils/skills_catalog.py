# utils/skills_catalog.py
import re

# Curated, deduped core skills per common roles (expand anytime)
ROLE_SKILLS = {
    "Data Analyst": {
        "python","sql","excel","power bi","tableau","data visualization","statistics",
        "pandas","numpy","etl","dashboard","reporting","a/b testing","communication"
    },
    "Machine Learning Engineer": {
        "python","scikit-learn","tensorflow","pytorch","mlops","docker","cloud","feature engineering",
        "data pipelines","model deployment","numpy","pandas","experiment tracking","api"
    },
    "Frontend Developer": {
        "html","css","javascript","react","typescript","webpack","accessibility","performance",
        "responsive design","testing","vite","redux","rest api"
    }
}

def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\+\#\.\-\/\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def load_skill_set(extra_text: str | None = None, role: str | None = None) -> set[str]:
    base: set[str] = set()
    if role and role in ROLE_SKILLS:
        base |= {normalize(x) for x in ROLE_SKILLS[role]}
    if extra_text:
        # pick probable skills (simple heuristic for now)
        tokens = {t for t in normalize(extra_text).split() if len(t) > 2}
        base |= tokens
    # keep multi-word curated phrases intact
    return base
