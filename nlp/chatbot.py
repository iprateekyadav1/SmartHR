"""
nlp/chatbot.py  —  MEMBER 2
============================
HR Chatbot using Intent Classification.

HOW IT WORKS (NLP Pipeline):
  1. User types a query  →  "How many leaves do I have?"
  2. Preprocessing       →  lowercase, remove punctuation, stopword removal
  3. TF-IDF Vectorizer   →  converts text to numerical feature vector
  4. Naive Bayes Model   →  predicts the intent label  →  "check_leave_balance"
  5. Response Generator  →  maps intent → API data → human-readable answer

WHY TF-IDF? (NLP Theory)
  TF (Term Frequency) = how often a word appears in the query.
  IDF (Inverse Document Frequency) = penalises words common across ALL queries (e.g. "the").
  TF-IDF score = TF × IDF → gives high weight to discriminative words.

WHY LOGISTIC REGRESSION?
  A discriminative linear model: learns decision boundary P(intent | words).
  Outperforms Naive Bayes on short text when classes are imbalanced.
  Supports multi-class natively via one-vs-rest. Fast on CPU, no GPU needed.

  We combine word-level TF-IDF (semantic meaning) with character n-gram TF-IDF
  (typo tolerance) via FeatureUnion before feeding into the classifier.
"""

# ── Model version tag ─────────────────────────────────────────────────────────
# Bump this string whenever the classifier or feature pipeline changes.
# _load_or_train checks this tag inside the pickled file; mismatch forces retrain.
_MODEL_VERSION = "lr-v2"

import re
import pickle
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

# ── Training Data ─────────────────────────────────────────────────────────────
# Each (text, intent) pair teaches the model what queries map to which intent.
# In production you'd have hundreds; here ~6 per intent is enough for a demo.

TRAINING_DATA = [
    # Intent: check_leave_balance
    ("how many leaves do i have",             "check_leave_balance"),
    ("what is my leave balance",              "check_leave_balance"),
    ("can you tell me my remaining leave days", "check_leave_balance"),
    ("i want to know how many leave days are left", "check_leave_balance"),
    ("show me my current leave balance",       "check_leave_balance"),
    ("remaining leaves",                      "check_leave_balance"),
    ("how many casual leaves left",           "check_leave_balance"),
    ("show my leave status",                  "check_leave_balance"),
    ("leave balance remaining",               "check_leave_balance"),

    # Intent: apply_leave
    ("i want to apply for leave",             "apply_leave"),
    ("how to apply leave",                    "apply_leave"),
    ("please help me submit a leave request",  "apply_leave"),
    ("i need to take tomorrow off",            "apply_leave"),
    ("can i request sick leave for today",      "apply_leave"),
    ("request sick leave",                    "apply_leave"),
    ("submit leave application",              "apply_leave"),
    ("apply casual leave for tomorrow",       "apply_leave"),
    ("leave request form",                    "apply_leave"),

    # Intent: salary_info
    ("what is my salary",                     "salary_info"),
    ("show my pay details",                   "salary_info"),
    ("can you tell me my monthly salary",      "salary_info"),
    ("i need my salary information",           "salary_info"),
    ("what do i earn every month",             "salary_info"),
    ("salary slip",                           "salary_info"),
    ("how much do i earn",                    "salary_info"),
    ("payroll information",                   "salary_info"),
    ("monthly salary details",                "salary_info"),

    # Intent: employee_list
    ("list all employees",                    "employee_list"),
    ("show all staff",                        "employee_list"),
    ("who is working in the company",          "employee_list"),
    ("give me the employee directory",         "employee_list"),
    ("how many people are employed here",      "employee_list"),
    ("who works in engineering",              "employee_list"),
    ("employees in hr department",            "employee_list"),
    ("how many employees total",              "employee_list"),
    ("show employee directory",               "employee_list"),

    # Intent: performance_feedback
    ("show my performance review",            "performance_feedback"),
    ("what is my feedback",                   "performance_feedback"),
    ("show me the latest review comments",     "performance_feedback"),
    ("how is my performance looking",          "performance_feedback"),
    ("what feedback did i get this year",      "performance_feedback"),
    ("performance report",                    "performance_feedback"),
    ("view my appraisal",                     "performance_feedback"),
    ("show feedback history",                 "performance_feedback"),
    ("my rating this year",                   "performance_feedback"),

    # Intent: emotional_support
    ("i feel stressed at work",                "emotional_support"),
    ("i am feeling overwhelmed and anxious",   "emotional_support"),
    ("work has been hard lately",              "emotional_support"),
    ("i need someone to talk to",              "emotional_support"),
    ("i am not feeling okay",                  "emotional_support"),
    ("i feel burned out",                      "emotional_support"),
    ("i need support",                         "emotional_support"),
    ("i am struggling right now",              "emotional_support"),

    # Intent: greeting
    ("hello",                                 "greeting"),
    ("hi",                                    "greeting"),
    ("hey there",                             "greeting"),
    ("good morning",                          "greeting"),
    ("help",                                  "greeting"),
    ("what can you do",                       "greeting"),

    # Intent: farewell
    ("bye",                                   "farewell"),
    ("goodbye",                               "farewell"),
    ("see you",                               "farewell"),
    ("thanks bye",                            "farewell"),
    ("exit",                                  "farewell"),
]

# ── Response Templates ────────────────────────────────────────────────────────
# The {data} placeholder is filled dynamically from the DB at runtime.
RESPONSES = {
    "check_leave_balance": (
        "Your current leave balance: {data}. "
        "You can apply via the Leave Management section."
    ),
    "apply_leave":         "To apply for leave, go to the Leave section and click 'Apply Leave'.",
    "salary_info":         "Your latest salary details: {data}.",
    "employee_list":       "There are {data} active employees in the system.",
    "performance_feedback":"Your latest feedback sentiment: {data}.",
    "emotional_support":   (
        "I’m here with you. Take one small step at a time, breathe slowly, and if you want, "
        "tell me what is weighing on you. I can help you find the right HR support too."
    ),
    "greeting":            "Hello! I'm SmartHR Assistant. I can help with leaves, salary, employee info, and feedback. What do you need?",
    "farewell":            "Goodbye! Have a productive day!",
    "unknown":             "I'm not sure about that. Please contact {data}.",
}


class HRChatbot:
    """Trains and runs the intent-classification chatbot."""

    MODEL_PATH = os.path.join(os.path.dirname(__file__), "chatbot_model.pkl")

    def __init__(self):
        self.pipeline = None
        self._load_or_train()

    # ── Training ───────────────────────────────────────────────────────────────
    def _train(self):
        """
        Build a sklearn Pipeline:
          Step 1 — FeatureUnion: word TF-IDF ⊕ char n-gram TF-IDF → combined feature matrix
          Step 2 — LogisticRegression: matrix → predicted intent (multi-class softmax)

        Word TF-IDF captures meaning; char n-grams handle typos and unseen words.
        Pipeline bundles both steps so .predict() works on raw text directly.
        """
        texts   = [t for t, _ in TRAINING_DATA]
        intents = [i for _, i in TRAINING_DATA]

        self.pipeline = Pipeline([
            ("features", FeatureUnion([
                ("word", TfidfVectorizer(
                    ngram_range=(1, 2),
                    stop_words="english",
                    max_features=1200,
                )),
                ("char", TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    max_features=2000,
                )),
            ])),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ])

        self.pipeline.fit(texts, intents)

        # Persist trained model + version tag to disk
        with open(self.MODEL_PATH, "wb") as f:
            pickle.dump({"version": _MODEL_VERSION, "pipeline": self.pipeline}, f)

    def _load_or_train(self):
        """
        Load saved model only if it matches the current version tag.
        A version mismatch (e.g. switched from NB → LR) forces a retrain,
        preventing silent errors from stale cached pipelines.
        """
        if os.path.exists(self.MODEL_PATH):
            try:
                with open(self.MODEL_PATH, "rb") as f:
                    bundle = pickle.load(f)
                # Support old format (raw pipeline, no version key)
                if isinstance(bundle, dict) and bundle.get("version") == _MODEL_VERSION:
                    self.pipeline = bundle["pipeline"]
                    return
            except Exception:
                pass
            # Version mismatch or corrupt file — retrain
            os.remove(self.MODEL_PATH)
        self._train()

    # ── Preprocessing ──────────────────────────────────────────────────────────
    @staticmethod
    def preprocess(text: str) -> str:
        """
        Clean raw user input before prediction.
        Steps: lowercase → strip punctuation → collapse whitespace
        """
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)  # remove punctuation
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ── Prediction ─────────────────────────────────────────────────────────────
    def predict_intent(self, text: str) -> tuple[str, float]:
        """
        Returns (intent_label, confidence_score).
        Confidence = probability of the top class from Naive Bayes.
        If confidence < threshold → return 'unknown' intent.
        """
        cleaned = self.preprocess(text)
        if not cleaned:
            return "unknown", 0.0

        proba  = self.pipeline.predict_proba([cleaned])[0]   # shape: (n_classes,)
        max_p  = float(np.max(proba))
        intent = self.pipeline.classes_[np.argmax(proba)]

        if max_p < 0.30:   # confidence threshold
            intent = "unknown"

        return intent, round(max_p, 3)

    # ── Response Builder ───────────────────────────────────────────────────────
    def get_response(self, text: str, db_data: dict = None, intent: str = None, confidence: float = None) -> dict:
        """
        Full chatbot flow:
          1. Predict intent
          2. Fetch relevant DB data (passed in from route layer)
          3. Format response string
          4. Return structured JSON

        Args:
            text    : raw user query
            db_data : dict with DB-fetched values, e.g. {"leave_balance": "CL:8, SL:5"}
        """
        if intent is None or confidence is None:
            intent, confidence = self.predict_intent(text)

        template  = RESPONSES.get(intent, RESPONSES["unknown"])
        db_data   = db_data or {}

        if intent == "unknown":
            lowered = text.lower()
            support_terms = ("stress", "anxious", "overwhelmed", "burnout", "burned out", "sad", "panic", "lonely", "need support", "not okay")
            if any(term in lowered for term in support_terms):
                template = RESPONSES["emotional_support"]
                intent = "emotional_support"

        # Fill in dynamic data placeholder if present
        response_text = template.format(data=db_data.get("value", "N/A"))

        return {
            "intent":     intent,
            "confidence": confidence,
            "response":   response_text,
        }


# Module-level singleton — imported by the Flask route
chatbot = HRChatbot()
