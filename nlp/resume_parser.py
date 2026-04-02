"""
nlp/resume_parser.py  —  MEMBER 3
===================================
Extracts structured data from uploaded resumes using NLP.

TECHNIQUES USED:
  1. Named Entity Recognition (NER) via spaCy
     - spaCy's pre-trained 'en_core_web_sm' model recognises:
       PERSON → candidate name, ORG → companies, DATE → experience years
  2. Regex pattern matching
     - Phone numbers, email addresses (structured data, not NER territory)
  3. Keyword matching for skills
     - We maintain a curated skill vocabulary and check each token against it.

INPUT:  .pdf / .docx / .txt file path
OUTPUT: dict with  {name, email, phone, skills, experience_years, education}

WHY NER?
  A resume has no fixed schema. Rule-based parsers break on formatting changes.
  NER reads the *meaning* of text chunks (entities), making it robust.
"""

import re
import os

# spaCy for NER
import spacy

# File readers
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

# ── Load spaCy model (download once: python -m spacy download en_core_web_sm) ─
try:
    nlp_model = spacy.load("en_core_web_sm")
except OSError:
    nlp_model = None   # graceful degradation if model not downloaded yet


# ── Skill Vocabulary ──────────────────────────────────────────────────────────
# Extend this list based on domain. Lowercased for case-insensitive matching.
SKILL_KEYWORDS = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "golang", "rust",
    "kotlin", "swift", "r", "scala", "php", "ruby",
    # Web
    "html", "css", "react", "angular", "vue", "nodejs", "flask", "django",
    "fastapi", "spring", "express",
    # Data / ML
    "machine learning", "deep learning", "nlp", "computer vision", "pandas",
    "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    # Databases
    "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
    # DevOps / Cloud
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux", "ci/cd",
    "jenkins", "terraform",
    # Other
    "agile", "scrum", "rest api", "graphql", "microservices",
}

# Education degree keywords
EDUCATION_KEYWORDS = [
    "b.tech", "btech", "b.e", "m.tech", "mtech", "mba", "phd",
    "bachelor", "master", "doctorate", "b.sc", "m.sc",
]


class ResumeParser:
    """Parses a resume file and returns structured employee data."""

    # ── Text Extraction ────────────────────────────────────────────────────────
    def extract_text(self, filepath: str) -> str:
        """Read raw text from PDF, DOCX, or TXT file."""
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif ext == ".pdf":
            if PyPDF2 is None:
                return ""
            text = []
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text() or "")
            return "\n".join(text)

        elif ext == ".docx":
            if DocxDocument is None:
                return ""
            doc  = DocxDocument(filepath)
            return "\n".join(para.text for para in doc.paragraphs)

        return ""

    # ── Name Extraction (NER) ──────────────────────────────────────────────────
    def extract_name(self, text: str) -> str:
        """
        Uses spaCy NER: looks for the first PERSON entity in the document.
        Resumes typically start with the candidate's name, so the first
        PERSON entity is usually correct.
        """
        if nlp_model is None:
            # Fallback: assume first non-empty line is the name
            for line in text.strip().split("\n"):
                line = line.strip()
                if line and len(line.split()) <= 5:
                    return line
            return "Unknown"

        doc = nlp_model(text[:1000])   # process first 1000 chars for speed
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text.strip()
        return "Unknown"

    # ── Email Extraction (Regex) ───────────────────────────────────────────────
    def extract_email(self, text: str) -> str:
        """
        Standard email regex.
        Pattern breakdown:
          [a-zA-Z0-9._%+-]+  → local part (before @)
          @                  → literal @
          [a-zA-Z0-9.-]+     → domain name
          \.[a-zA-Z]{2,}     → TLD (.com, .in, etc.)
        """
        pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
        match   = re.search(pattern, text)
        return match.group() if match else ""

    # ── Phone Extraction (Regex) ───────────────────────────────────────────────
    def extract_phone(self, text: str) -> str:
        """
        Matches common Indian/international phone number formats:
          +91-9876543210  |  9876543210  |  (022) 12345678
        """
        pattern = r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{4,6}"
        match   = re.search(pattern, text)
        return match.group().strip() if match else ""

    # ── Skills Extraction (Keyword Matching) ──────────────────────────────────
    def extract_skills(self, text: str) -> list[str]:
        """
        Converts text to lowercase, then checks each known skill keyword.
        Multi-word skills (e.g. 'machine learning') are checked as substrings.
        Returns sorted unique list.
        """
        lower_text = text.lower()
        found = set()
        for skill in SKILL_KEYWORDS:
            # Word-boundary check prevents "r" matching "react" etc.
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, lower_text):
                found.add(skill.title())   # Title-case for display
        return sorted(found)

    # ── Experience Extraction (NER + Regex) ───────────────────────────────────
    def extract_experience_years(self, text: str) -> int:
        """
        Looks for patterns like: '5 years', '3+ years experience', '2 yrs'.
        Returns the maximum number found (total experience estimate).
        """
        pattern = r"(\d+)\+?\s*(years?|yrs?)\s*(of\s+)?(experience|exp)?"
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            years = [int(m[0]) for m in matches if int(m[0]) < 50]
            return max(years) if years else 0
        return 0

    # ── Education Extraction ───────────────────────────────────────────────────
    def extract_education(self, text: str) -> str:
        """Returns highest degree found using keyword scan."""
        lower_text = text.lower()
        for degree in ["phd", "m.tech", "mtech", "mba", "m.sc", "b.tech", "btech", "b.e", "b.sc", "bachelor"]:
            if degree in lower_text:
                return degree.upper()
        return "Not specified"

    # ── Master Parse Method ────────────────────────────────────────────────────
    def parse(self, filepath: str) -> dict:
        """
        Full pipeline:
          file → raw text → NER + Regex → structured dict

        Returns dict ready to pre-fill the Employee creation form.
        """
        text = self.extract_text(filepath)
        if not text.strip():
            return {"error": "Could not extract text from file."}

        skills = self.extract_skills(text)

        return {
            "name":             self.extract_name(text),
            "email":            self.extract_email(text),
            "phone":            self.extract_phone(text),
            "skills":           skills,
            "skills_str":       ", ".join(skills),
            "experience_years": self.extract_experience_years(text),
            "education":        self.extract_education(text),
            "raw_text_preview": text[:300],   # first 300 chars for UI preview
        }


# Module-level singleton
resume_parser = ResumeParser()
