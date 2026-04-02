"""
routes/nlp_routes.py  —  NLP Utility Routes
=============================================
Stub blueprint kept for forward-compatibility.
Actual NLP endpoints are handled by:
  - /api/chatbot/*  (chatbot_routes.py)
  - /api/analytics/feedback  (analytics_routes.py)
  - /api/employees/parse-resume  (employee_routes.py)
"""

from flask import Blueprint

nlp_bp = Blueprint("nlp", __name__, url_prefix="/api/nlp")
