from __future__ import annotations
import os
import csv
from collections import Counter
from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify
)
from werkzeug.utils import secure_filename

# --- Utils (make sure these files exist in utils/)
from utils.resume_parser import extract_text_from_file, clean_text
from utils.text_similarity import tfidf_match, suggest_missing_skills
from utils.ats_checker import quick_ats_check
from utils.experience import detect_level
from utils.db import init_db, save_run, list_runs, delete_run, clear_runs

# ---------------- App setup ----------------
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "dev-secret"  # replace for production
init_db()  # create data/app.db and table if missing

ALLOWED_EXT = {"pdf", "docx", "txt"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ---------------- Dataset helpers ----------------
def _jd_csv_path() -> str:
    return os.path.join(BASE_DIR, "data", "job_descriptions.csv")


def load_roles_list() -> list[dict]:
    roles: list[dict] = []
    csv_path = _jd_csv_path()
    try:
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                roles.append({
                    "role": (row.get("role") or "").strip(),
                    "description": (row.get("description") or "").strip()
                })
    except Exception:
        pass
    return roles


def load_role_descriptions(role: str | None) -> list[str]:
    descs: list[str] = []
    if not role:
        return descs
    csv_path = _jd_csv_path()
    try:
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get("role") or "").strip().lower() == role.lower():
                    d = (row.get("description") or "").strip()
                    if d:
                        descs.append(d)
    except Exception:
        pass
    return descs


# ---------------- Routes ----------------
@app.get("/")
def index():
    roles = load_roles_list()
    return render_template("index.html", roles=roles)


@app.post("/analyze")
def analyze():
    resume_file = request.files.get("resume")
    jd_text = (request.form.get("job_description") or "").strip()
    role_hint = (request.form.get("role_hint") or "").strip() or None

    # validations
    if not resume_file or resume_file.filename == "":
        flash("Please upload a resume (PDF/DOCX/TXT).")
        return redirect(url_for("index"))
    if not allowed_file(resume_file.filename):
        flash("Unsupported file type. Allowed: pdf, docx, txt.")
        return redirect(url_for("index"))
    if not jd_text and not role_hint:
        flash("Paste a Job Description or pick a role from dataset.")
        return redirect(url_for("index"))

    # save upload
    filename = secure_filename(resume_file.filename)
    saved_path = os.path.join(UPLOAD_DIR, filename)
    resume_file.save(saved_path)

    # parse + clean resume
    resume_raw = extract_text_from_file(saved_path)
    resume = clean_text(resume_raw)

    # JD bundle (either dropdown role or typed textarea)
    jd_list: list[str] = []
    if role_hint:
        jd_list = load_role_descriptions(role_hint)
    if jd_text:
        jd_list = [jd_text]
    if not jd_list:
        flash("No job descriptions found for the selected role.")
        return redirect(url_for("index"))

    # ---- Analysis over JD bundle: average score, union insights
    scores: list[float] = []
    agg_overlap, agg_missing, agg_top_terms = set(), set(), []

    for jd_one in jd_list:
        jd_clean = clean_text(jd_one)
        res = tfidf_match(resume, jd_clean)
        scores.append(res["match_percent"])
        agg_overlap |= set(res["top_overlap"])
        agg_missing |= set(res["missing_keywords"])
        agg_top_terms.extend(res["jd_top_terms"])

    match_percent = round(sum(scores) / max(1, len(scores)), 2)
    top_terms = [t for t, _ in Counter(agg_top_terms).most_common(15)]

    # ATS + Experience + Suggestions (use first JD text if textarea empty)
    ats = quick_ats_check(resume_raw)
    exp = detect_level(resume_raw)
    jd_for_suggest = jd_text if jd_text else (jd_list[0] if jd_list else "")
    missing_suggestions = suggest_missing_skills(resume_raw, jd_for_suggest, role_hint=role_hint)

    result = {
        "match_percent": match_percent,
        "top_keywords": sorted(list(agg_overlap))[:20],
        "missing_keywords": sorted(list(agg_missing))[:10],
        "jd_top_terms": top_terms,
        "suggested_skills": missing_suggestions[:10],
        "ats_score": ats["ats_score"],
        "ats_warnings": ats["warnings"],
        "filename": filename,
        "role_hint": role_hint or "",
        "experience": exp,
    }

    # save to history (non-blocking best-effort)
    try:
        save_run(
            filename=result.get("filename"),
            role_hint=result.get("role_hint"),
            match_percent=result.get("match_percent"),
            ats_score=result.get("ats_score"),
            top_keywords=result.get("top_keywords"),
            missing_keywords=result.get("missing_keywords"),
        )
    except Exception as e:
        app.logger.warning(f"Failed to save run: {e}")

    return render_template("result.html", result=result)


# ---------------- JSON API ----------------
@app.post("/api/analyze")
def api_analyze():
    # Accept either uploaded file OR raw resume_text
    resume_text = (
        request.form.get("resume_text")
        or (request.json.get("resume_text") if request.is_json else None)
        or ""
    )
    jd_text = (
        request.form.get("job_description")
        or (request.json.get("job_description") if request.is_json else None)
        or ""
    )
    role_hint = (
        request.form.get("role_hint")
        or (request.json.get("role_hint") if request.is_json else None)
        or None
    )

    # If file provided, parse it
    if "resume" in request.files and request.files["resume"].filename:
        f = request.files["resume"]
        if allowed_file(f.filename):
            path = os.path.join(UPLOAD_DIR, secure_filename(f.filename))
            f.save(path)
            resume_text = extract_text_from_file(path)

    if not resume_text:
        return jsonify({"error": "Provide resume_text or upload a resume file."}), 400
    if not jd_text and not role_hint:
        return jsonify({"error": "Provide job_description or role_hint."}), 400

    # Clean + build JD list
    resume_clean = clean_text(resume_text)
    jd_list: list[str] = []
    if role_hint:
        jd_list = load_role_descriptions(role_hint)
    if jd_text:
        jd_list = [jd_text]
    if not jd_list:
        return jsonify({"error": "No job descriptions found for the selected role."}), 400

    scores: list[float] = []
    agg_overlap, agg_missing, agg_top_terms = set(), set(), []
    for jd_one in jd_list:
        jd_clean = clean_text(jd_one)
        res = tfidf_match(resume_clean, jd_clean)
        scores.append(res["match_percent"])
        agg_overlap |= set(res["top_overlap"])
        agg_missing |= set(res["missing_keywords"])
        agg_top_terms.extend(res["jd_top_terms"])

    match_percent = round(sum(scores) / max(1, len(scores)), 2)
    top_terms = [t for t, _ in Counter(agg_top_terms).most_common(15)]

    ats = quick_ats_check(resume_text)
    exp = detect_level(resume_text)
    jd_for_suggest = jd_text if jd_text else (jd_list[0] if jd_list else "")
    missing_suggestions = suggest_missing_skills(resume_text, jd_for_suggest, role_hint=role_hint)

    result = {
        "match_percent": match_percent,
        "top_keywords": sorted(list(agg_overlap))[:20],
        "missing_keywords": sorted(list(agg_missing))[:10],
        "jd_top_terms": top_terms,
        "suggested_skills": missing_suggestions[:10],
        "ats_score": ats["ats_score"],
        "ats_warnings": ats["ats_warnings"] if isinstance(ats, dict) and "ats_warnings" in ats else ats.get("warnings", []),
        "experience": exp,
        "role_hint": role_hint or "",
    }
    return jsonify(result)


# ---------------- History pages ----------------
@app.get("/history")
def history():
    q = (request.args.get("q") or "").strip() or None
    runs = list_runs(search=q, limit=200, offset=0)
    return render_template("history.html", runs=runs, q=q or "")


@app.post("/history/delete")
def history_delete():
    run_id = int(request.form.get("id") or 0)
    if run_id:
        delete_run(run_id)
    return redirect(url_for("history"))


@app.post("/history/clear")
def history_clear():
    clear_runs()
    return redirect(url_for("history"))


# ---------------- Docs page ----------------
@app.get("/docs")
def docs():
    return render_template("docs.html")


# ---------------- Dev server ----------------
if __name__ == "__main__":
    # For development only
    app.run(debug=True, host="127.0.0.1", port=5000)
