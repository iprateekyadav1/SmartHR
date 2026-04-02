# SmartHR — AI-Powered HR Management System

> B.Tech CS Final Year Project (10 Credits)
> A full-stack HR platform with NLP, 3D visualizations, payroll engine, and live analytics.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey?style=flat-square&logo=flask)
![spaCy](https://img.shields.io/badge/NLP-spaCy%20%2B%20NLTK-09A3D5?style=flat-square)
![Three.js](https://img.shields.io/badge/3D-Three.js-black?style=flat-square&logo=three.js)

---

## Features

| Module | Description |
|---|---|
| **Employee Management** | Full CRUD with soft delete, department filtering, skill tags |
| **AI Resume Parser** | Upload PDF/DOCX → spaCy NER extracts name, email, skills, experience |
| **HR Chatbot** | TF-IDF + Logistic Regression intent classifier (8 intents) |
| **Sentiment Analysis** | VADER NLP scores employee feedback on −1 → +1 compound scale |
| **Payroll Engine** | Basic + HRA + DA + Bonus − PF − Tax = Net Salary |
| **Payslip PDF** | Client-side jsPDF — polished A4 PDF, instant browser download |
| **Live Dashboard** | 7 Chart.js charts with dark neon theme + 3D department globe |
| **Leave Management** | Apply, approve/reject, circular SVG balance indicators |
| **Reports & Export** | CSV export for employees, leaves, feedback |

## 3D & Immersive UI

- **Login page** — Three.js animated particle field (1,400 particles, orbiting rings, mouse parallax)
- **Dashboard globe** — Interactive draggable 3D sphere with department nodes and connection lines
- **KPI cards** — CSS 3D perspective tilt on hover (`perspective: 1000px`)
- **Dark design system** — Deep space navy + cyan `#00d4ff` + purple `#7c3aed`, glassmorphism cards

## Tech Stack

**Backend:** Flask 3.x · SQLAlchemy · SQLite
**NLP/ML:** spaCy · NLTK VADER · scikit-learn (TF-IDF + LogisticRegression) · PyPDF2 · python-docx
**Frontend:** Jinja2 · Bootstrap 5 · Three.js · Chart.js · jsPDF · Vanilla JS
**Data:** Faker-generated 200 employees · 28,000+ records

## Quick Start

```bash
# 1. Clone
git clone https://github.com/iprateekyadav1/SmartHR.git
cd SmartHR

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m nltk.downloader vader_lexicon

# 4. Seed the database (200 employees + all records)
python seed.py

# 5. Run
python app.py
# → http://127.0.0.1:5000
```

## Demo Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@123` |
| Employee | `employee` | `Employee@123` |
| Guest | — | Click "Guest Mode" |

## Project Structure

```
SmartHR/
├── app.py              # Flask app factory + page routes
├── config.py           # Configuration
├── seed.py             # Database seeder (200 employees)
├── models/             # SQLAlchemy ORM models
├── routes/             # Flask Blueprint API routes
├── nlp/                # Resume parser, chatbot, sentiment
├── templates/          # Jinja2 HTML templates
└── static/             # CSS design system + JS (Three.js, payslip)
```

## NLP Pipeline

```
User Input → Preprocess → TF-IDF Vectorize → Logistic Regression
         → Intent (confidence ≥ 30%) → DB Query → Response
```

---

*Developed as a 10-credit B.Tech CS Final Year Project.*
