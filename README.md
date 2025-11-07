


# 🧠 SmartHire — AI Resume Analyzer

SmartHire is an **AI-powered Resume & Job Description Analyzer** built with **Python + Flask**.  
It compares resumes to job descriptions, checks for **ATS (Applicant Tracking System)** compliance,  
and suggests **missing skills** and **keywords** to improve your chances of landing interviews.

---

## 🚀 Features

- 🔍 **Smart Resume ↔ JD Matching** using TF-IDF cosine similarity  
- 🧩 **Keyword Insights** — overlap, missing, and suggested skills  
- 📊 **ATS Check** — evaluates resume formatting & content  
- 🎓 **Experience Detection** — auto-extracts seniority level  
- 💾 **History Page** — saves past analyses locally (SQLite)  
- 📘 **Docs Page** — explains logic, scoring, and API usage  
- 🪩 **Modern UI** — glassmorphism theme, dark/light mode toggle  
- 🌐 **Optional REST API** for integration with other tools

---

## 🏗️ Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python, Flask |
| ML/NLP | scikit-learn, NumPy, TF-IDF |
| Resume Parsing | PyPDF2, python-docx |
| Frontend | HTML5, CSS3 (Glassmorphism), Vanilla JS |
| Database | SQLite (local persistent storage) |
| Hosting | Render / Railway / Fly.io (choose any) |

---

## ⚙️ Local Setup

```bash
# 1️⃣ Clone the repo
git clone https://github.com/<your-username>/smarthire.git
cd smarthire

# 2️⃣ Create virtual environment
python -m venv venv
venv\Scripts\activate     # on Windows
# or source venv/bin/activate on macOS/Linux

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Run locally
python app.py

# 5️⃣ Visit
http://127.0.0.1:5000
````

---

## 🗂️ Project Structure

```
smarthire/
│
├── app.py                     # Main Flask app
├── utils/
│   ├── resume_parser.py       # Extracts text from PDF/DOCX
│   ├── text_similarity.py     # TF-IDF matcher & skill suggestions
│   ├── ats_checker.py         # ATS scoring logic
│   ├── experience.py          # Experience level detection
│   └── db.py                  # SQLite database helper
│
├── templates/                 # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   ├── result.html
│   ├── history.html
│   └── docs.html
│
├── static/
│   ├── css/style.css          # Glassmorphism theme
│   ├── js/dashboard.js        # Charts & UI logic
│   └── icons/...
│
├── data/
│   ├── job_descriptions.csv   # Example dataset
│   └── app.db                 # Local history DB (auto-created)
│
├── uploads/                   # Temporary uploaded resumes
├── requirements.txt
└── Procfile                   # for Render/Railway deployment
```

---

## 🧠 Example Usage

1️⃣ Upload your **resume** (PDF/DOCX/TXT).
2️⃣ Paste or select a **job description**.
3️⃣ Click **Analyze** → see results:

* **Match %**
* **Top Overlapping Keywords**
* **Missing Keywords**
* **ATS Score**
* **Experience Level**
* **TF-IDF Insights**
* **Suggested Skills**

---

## 🌍 Deployment (Render — Free Tier)

1. Push your repo to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Connect your repo
4. **Start Command:**

   ```
   gunicorn app:app --workers=2 --threads=4 --timeout=120
   ```
5. Add a **Disk**:

   * Mount path: `/opt/render/project/src/data`
   * Size: 1 GB (for history persistence)
6. Open your public URL 🎉

Full Render guide → in `/docs.html`

---

## 🔌 API Usage

### Endpoint

```
POST /api/analyze
```

### Example (cURL)

```bash
curl -X POST https://smarthire.onrender.com/api/analyze \
  -F "role_hint=Data Analyst" \
  -F "job_description=Python SQL Excel dashboards" \
  -F "resume=@/path/to/resume.pdf"
```

### Response

```json
{
  "match_percent": 82.5,
  "ats_score": 78,
  "top_keywords": ["python","sql","dashboard"],
  "missing_keywords": ["tableau","business"],
  "suggested_skills": ["etl","metrics","reporting"]
}
```

---

## 🧩 Optional Pages

| Page       | Route                | Purpose             |
| ---------- | -------------------- | ------------------- |
| `/`        | Upload & Analyze     | Main interface      |
| `/history` | History of past runs | View/Delete/Clear   |
| `/docs`    | Documentation        | Learn about scoring |

---

## 🧠 Future Improvements

* Add user login for cloud saves
* Use sentence embeddings (e.g., SBERT) for deeper semantic matching
* PDF text area highlighting
* Multi-resume comparison
* Export report as PDF

---

## 🪪 License

MIT License © 2025 [Your Name]

---

### 💬 Credits

Developed by **Harshal Loke**

> "Helping job seekers build smarter resumes with AI."

```

---

Would you like me to make a **shorter README** (for Render only) or an **aesthetic version with badges and screenshots** for your GitHub page?
```
