"""
nlp/sentiment.py  —  MEMBER 4
===============================
Sentiment analysis for employee feedback text.

TOOL: VADER (Valence Aware Dictionary and sEntiment Reasoner)
  - Rule-based NLP model from NLTK, designed for SHORT social/workplace text.
  - No training data needed — uses a pre-built lexicon of ~7,500 words
    each rated on a sentiment scale.
  - Works without a GPU — perfect for CPU-only environments.

VADER OUTPUT (compound score):
  +1.0 → Most Positive   (e.g. "Great work, excellent performance!")
   0.0 → Neutral         (e.g. "Attended the meeting.")
  -1.0 → Most Negative   (e.g. "Terrible attitude, always late.")

THRESHOLD (standard):
  compound ≥  0.05  → POSITIVE
  compound ≤ -0.05  → NEGATIVE
  else              → NEUTRAL

BONUS: We also run department-level aggregation to spot team morale trends.
"""

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import defaultdict

# Download VADER lexicon on first run (requires internet, ~1MB)
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

# ── Domain-specific adjustments ───────────────────────────────────────────────
# VADER was trained on social media; add HR-domain terms to its lexicon.
HR_CUSTOM_LEXICON = {
    "underperforming": -2.5,
    "hardworking":      2.5,
    "punctual":         1.8,
    "absent":          -1.5,
    "collaborative":    2.0,
    "disciplinary":    -1.5,
    "promoted":         3.0,
    "terminated":      -3.0,
    "innovative":       2.5,
    "micromanaging":   -2.0,
}


class SentimentAnalyzer:
    """Wraps VADER and adds department-level aggregation."""

    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        # Inject HR domain words into VADER's internal lexicon
        self.sia.lexicon.update(HR_CUSTOM_LEXICON)

    # ── Single Text Analysis ───────────────────────────────────────────────────
    def analyze(self, text: str) -> dict:
        """
        Analyse a single feedback string.

        VADER returns four scores:
          pos  — proportion of positive sentiment
          neg  — proportion of negative sentiment
          neu  — proportion of neutral content
          compound — normalised weighted composite [-1, +1]

        We use compound for the final label.
        """
        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.0, "details": {}}

        scores = self.sia.polarity_scores(text)
        compound = scores["compound"]

        if compound >= 0.05:
            label = "POSITIVE"
        elif compound <= -0.05:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"

        return {
            "label":    label,
            "score":    round(compound, 4),
            "details": {              # granular breakdown for analytics
                "positive": round(scores["pos"], 3),
                "negative": round(scores["neg"], 3),
                "neutral":  round(scores["neu"], 3),
            },
        }

    # ── Batch Analysis ─────────────────────────────────────────────────────────
    def analyze_batch(self, feedbacks: list[dict]) -> list[dict]:
        """
        Analyse a list of feedback dicts  [{text, employee_id, department}, ...]
        Returns each dict enriched with sentiment results.
        """
        results = []
        for fb in feedbacks:
            sentiment = self.analyze(fb.get("text", ""))
            results.append({**fb, **sentiment})
        return results

    # ── Department Morale Report ───────────────────────────────────────────────
    def department_morale(self, feedbacks: list[dict]) -> dict:
        """
        Aggregates sentiment scores by department.
        Returns {dept: {"avg_score": float, "label": str, "count": int}}

        Use case: HR dashboard shows which team needs attention.
        """
        dept_scores = defaultdict(list)
        for fb in feedbacks:
            dept = fb.get("department", "Unknown")
            result = self.analyze(fb.get("text", ""))
            dept_scores[dept].append(result["score"])

        report = {}
        for dept, scores in dept_scores.items():
            avg = sum(scores) / len(scores)
            if avg >= 0.05:
                label = "POSITIVE"
            elif avg <= -0.05:
                label = "NEGATIVE"
            else:
                label = "NEUTRAL"
            report[dept] = {
                "avg_score": round(avg, 3),
                "label":     label,
                "count":     len(scores),
            }
        return report

    # ── Keyword Highlights ─────────────────────────────────────────────────────
    def highlight_keywords(self, text: str) -> dict:
        """
        Returns words that most influenced the sentiment score.
        Looks up each word in VADER's lexicon and returns top positive/negative.
        """
        words  = text.lower().split()
        scored = []
        for word in words:
            score = self.sia.lexicon.get(word)
            if score:
                scored.append((word, score))

        scored.sort(key=lambda x: abs(x[1]), reverse=True)
        top = scored[:5]   # top 5 most influential words

        return {
            "top_words": [{"word": w, "score": round(s, 2)} for w, s in top],
        }


# Module-level singleton
sentiment_analyzer = SentimentAnalyzer()
