# utils/text_similarity.py
from __future__ import annotations
import re
from typing import List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---- Phrase canonicalization & variant expansion
PHRASE_MAP: list[tuple[str, str]] = [
    (r"\b(power[\s\-]?bi)\b", "power bi"),
    (r"\b(a[\s\-\/]?b[\s\-]?testing)\b", "a/b testing"),
    (r"\b(a\s+b\s+testing)\b", "a/b testing"),
    (r"\b(ci[\s\-\/]?cd)\b", "ci/cd"),
    (r"\b(scikit[\s\-]?learn)\b", "scikit-learn"),
    (r"\b(data\s+visualization)\b", "data visualization"),
    (r"\b(machine\s+learning)\b", "machine learning"),
]

# Shorthands in JDs we expand into both terms so overlap works
ALT_EXPANSIONS: list[tuple[str, str]] = [
    (r"\btableau\s*\/\s*power(?:\s*bi)?\b", "tableau power bi"),
    (r"\bpower(?:\s*bi)?\s*\/\s*tableau\b", "power bi tableau"),
]

# Lightweight stopwords to keep setup simple (no NLTK download)
STOP = {
    "the","a","an","and","or","to","of","for","with","on","in","by","is","are","as","be",
    "this","that","it","at","from","we","you","your","our","their","they","i","me","my",
    "into","about","over","under","using","use","used","via"
}

# Simple alias map to lift overlap when wording differs
ALIASES: dict[str, set[str]] = {
    "visualization": {"viz","data viz"},
    "statistics": {"statistical","stats"},
    "sql": {"mysql","postgresql","postgres","mssql"},
    "excel": {"spreadsheets"},
    "dashboards": {"dashboard"},
    "reporting": {"reports"},
    "etl": {"data pipeline","pipelines"},
}

TOKEN_RE = re.compile(r"[a-z0-9\+\#\.\/\-]+")

def _apply_phrase_map(s: str) -> str:
    for pat, repl in PHRASE_MAP:
        s = re.sub(pat, repl, s)
    return s

def _expand_alternatives(s: str) -> str:
    for pat, repl in ALT_EXPANSIONS:
        s = re.sub(pat, repl, s)
    return s

def _singularize(token: str) -> str:
    # light singularization: dashboards -> dashboard, reports -> report
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token

def normalize_text(s: str) -> str:
    s = s.lower()
    # keep + # / - . because they appear in skills like c++, c#, ci/cd
    s = re.sub(r"[^\w\+\#\/\-\.\s]", " ", s)
    # drop trailing dots "reporting." -> "reporting"
    s = re.sub(r"\.(\s|$)", " ", s)
    s = _apply_phrase_map(s)
    s = _expand_alternatives(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def tokenize(raw: str) -> List[str]:
    s = normalize_text(raw)
    toks: List[str] = []
    for t in TOKEN_RE.findall(s):
        t = t.strip(".-")
        if not t or len(t) <= 2:
            continue
        if t in STOP:
            continue
        # ignore lonely "cd" noise (but keep "ci/cd" via phrase map)
        if t == "cd":
            continue
        t = _singularize(t)
        toks.append(t)

    # expand aliases (adds canonical root token alongside variant)
    expanded: List[str] = []
    for t in toks:
        expanded.append(t)
        for root, variants in ALIASES.items():
            if t == root or t in variants:
                expanded.append(root)
    # dedupe while preserving order
    deduped = list(dict.fromkeys(expanded))
    return deduped

def build_tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(
        tokenizer=tokenize,
        ngram_range=(1, 2),
        min_df=1,
        max_df=1.0,      # keep shared terms for 2-doc fit
        sublinear_tf=True,
        use_idf=True,
        lowercase=False
    )

# ---- Section-weighted similarity
from .sections import split_sections

SECTION_WEIGHTS = {
    "experience": 1.0,
    "projects":   0.9,
    "skills":     0.7,
    "education":  0.4,
    "summary":    0.5,
}

def weighted_cosine(resume_text: str, jd_text: str) -> Dict:
    r_secs = split_sections(resume_text)
    j_secs = split_sections(jd_text)
    if not j_secs:
        return {"score": 0.0}

    vec = build_tfidf()
    sims: list[float] = []
    weights: list[float] = []

    # For each JD section, take the best matching resume section (same name preferred)
    for jname, jchunk in j_secs:
        jw = float(SECTION_WEIGHTS.get(jname, 0.5))
        best = 0.0
        jn = normalize_text(jchunk)
        for rname, rchunk in r_secs:
            rn = normalize_text(rchunk)
            X = vec.fit_transform([jn, rn])
            if X[0].nnz == 0 or X[1].nnz == 0:
                sim = 0.0
            else:
                sim = float(cosine_similarity(X[0], X[1])[0][0])
            if rname == jname:
                sim *= 1.05  # tiny boost for same-section match
            if sim > best:
                best = sim
        sims.append(best)
        weights.append(jw)

    sims_arr = np.array(sims, dtype=float)
    w_arr = np.array(weights, dtype=float)
    score = float((sims_arr * w_arr).sum() / max(1e-9, w_arr.sum()))
    return {"score": score}

# ---- Final TF-IDF matcher (blends global + section-weighted)
def tfidf_match(resume_text: str, jd_text: str) -> Dict:
    # global (whole-doc) similarity
    vec = build_tfidf()
    jd_norm = normalize_text(jd_text)
    res_norm = normalize_text(resume_text)
    X = vec.fit_transform([jd_norm, res_norm])
    if X[0].nnz == 0 or X[1].nnz == 0:
        sim_global = 0.0
    else:
        sim_global = float(cosine_similarity(X[0], X[1])[0][0])

    # section-weighted similarity
    sw = weighted_cosine(resume_text, jd_text)["score"]

    # calibrated blend
    sim = 0.7 * sw + 0.3 * sim_global
    match_percent = round(sim * 100, 2)

    # term intel for UI
    jd_terms = set(tokenize(jd_text))
    res_terms = set(tokenize(resume_text))
    overlap = sorted(jd_terms & res_terms)
    missing = sorted(jd_terms - res_terms)

    feature_names = vec.get_feature_names_out()
    if X[0].nnz:
        jd_vec = X[0].toarray()[0]
        top_idx = jd_vec.argsort()[::-1][:15]
        top_terms = [feature_names[i] for i in top_idx]
    else:
        top_terms = []

    return {
        "match_percent": match_percent,
        "top_overlap": overlap[:20],
        "missing_keywords": missing[:20],
        "jd_top_terms": top_terms
    }

# ---- Skill suggestions
def suggest_missing_skills(resume_text: str, jd_text: str, role_hint: str | None = None) -> List[str]:
    from .skills_catalog import load_skill_set, normalize as norm2
    jd_norm = normalize_text(jd_text)
    skill_pool = load_skill_set(extra_text=jd_norm, role=role_hint)

    res_norm = normalize_text(resume_text)
    res_tokens = set(tokenize(resume_text))

    suggestions: List[str] = []
    for s in sorted(skill_pool):
        s_norm = norm2(s)
        if " " in s_norm:
            if s_norm not in res_norm:
                suggestions.append(s_norm)
        else:
            if s_norm not in res_tokens:
                suggestions.append(s_norm)

    priority = ["python","sql","excel","tableau","power bi","pandas","numpy",
                "javascript","react","tensorflow","pytorch","a/b testing","ci/cd",
                "etl","metrics"]
    suggestions = sorted(suggestions, key=lambda x: (0 if x in priority else 1, x))
    return suggestions[:20]

# ---- Back-compat wrapper (templates call this name)
def quick_match_summary(resume: str, jd: str):
    res = tfidf_match(resume, jd)
    return {
        "match_percent": res["match_percent"],
        "top_keywords": res["top_overlap"],
        "missing_keywords": res["missing_keywords"],
        "jd_top_terms": res["jd_top_terms"],
    }
