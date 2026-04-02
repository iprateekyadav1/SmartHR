"""
routes/chatbot_routes.py  —  MEMBER 2
=======================================
Flask endpoints for the HR chatbot.

Flow for each user message:
  1. Receive JSON  { "message": "...", "employee_id": 5 }
  2. chatbot.predict_intent(message) → intent label
  3. If intent needs DB data, fetch it here (routes layer handles DB)
  4. Pass data to chatbot.get_response() → formatted reply
  5. Return JSON  { "intent", "confidence", "response" }

This separation of concerns is important:
  - NLP module (chatbot.py) is pure ML — no DB calls.
  - Routes layer bridges ML and DB.
"""

from flask import Blueprint, request, jsonify
from nlp.chatbot import chatbot
from models.employee import Employee
from models.leave import Leave
from models.feedback import Feedback
from routes.leave_routes import get_leave_balance
from datetime import datetime
from nlp.sentiment import sentiment_analyzer

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chatbot")


@chatbot_bp.route("/message", methods=["POST"])
def chat():
    """
    Main chatbot endpoint.
    Accepts: { "message": str, "employee_id": int (optional) }
    Returns: { "intent": str, "confidence": float, "response": str }
    """
    data       = request.get_json() or {}
    message    = data.get("message", "").strip()
    emp_id     = data.get("employee_id")

    if not message:
        return jsonify({"error": "message is required"}), 400

    # Step 1: Predict intent (pure ML, no DB)
    intent, confidence = chatbot.predict_intent(message)

    # Step 2: Fetch DB data based on predicted intent
    db_value = _fetch_db_data(intent, emp_id)

    # Step 2b: If the message sounds negative or distressed, keep the bot empathetic.
    if intent == "unknown":
        sentiment = sentiment_analyzer.analyze(message)
        if sentiment["label"] == "NEGATIVE":
            db_value = "I am here to listen. If you want, tell me what happened and I will try to help."
            intent = "emotional_support"

    # Step 3: Build response
    result = chatbot.get_response(message, db_data={"value": db_value}, intent=intent, confidence=confidence)

    # Log conversation for future training data collection
    return jsonify(result)


def _fetch_db_data(intent: str, emp_id) -> str:
    """
    Intent-specific DB queries. Returns a human-readable string
    that gets injected into the response template.
    """
    try:
        if intent == "check_leave_balance" and emp_id:
            balance = get_leave_balance(int(emp_id))
            parts   = [f"{k}: {v}" for k, v in balance.items()]
            return " | ".join(parts)   # e.g. "CL: 10 | SL: 8 | EL: 12"

        elif intent == "salary_info" and emp_id:
            emp = Employee.query.get(emp_id)
            if emp:
                return f"₹{emp.salary:,.2f} per month"
            return "Employee not found"

        elif intent == "employee_list":
            count = Employee.query.filter_by(is_active=True).count()
            return str(count)

        elif intent == "performance_feedback" and emp_id:
            latest_fb = (
                Feedback.query
                .filter_by(employee_id=emp_id)
                .order_by(Feedback.created_at.desc())
                .first()
            )
            if latest_fb:
                return f"{latest_fb.sentiment_label} (score: {latest_fb.sentiment_score})"
            return "No feedback records found"

        elif intent == "emotional_support":
            return "You are not alone. Breathe slowly and share what is on your mind."

        if intent == "unknown":
            fallback = "HR at hr@smarthr.com"
            if emp_id:
                emp = Employee.query.get(emp_id)
                if emp:
                    manager = Employee.query.filter(Employee.department == emp.department, Employee.designation.ilike('%manager%')).first()
                    if not manager:
                        manager = Employee.query.filter(Employee.department == 'HR').first()
                    if manager:
                        fallback = f"{manager.name}, {manager.designation} at {manager.email}"
            return fallback

        return "N/A"

    except Exception:
        return "HR at hr@smarthr.com"


@chatbot_bp.route("/intents", methods=["GET"])
def list_intents():
    """Debug endpoint: lists all known intents and sample queries."""
    from nlp.chatbot import TRAINING_DATA
    intent_map = {}
    for text, intent in TRAINING_DATA:
        intent_map.setdefault(intent, []).append(text)
    return jsonify(intent_map)
