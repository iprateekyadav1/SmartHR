"""
routes/analytics_routes.py  —  MEMBER 4 + MEMBER 5
====================================================
Analytics data endpoints for the dashboard.

Provides aggregated statistics consumed by Chart.js on the frontend:
  - Department-wise headcount
  - Leave status breakdown (pie chart)
  - Monthly joining trend (line chart)
  - Department sentiment scores (bar chart)
  - Feedback management (submit + list)
"""

from flask import Blueprint, request, jsonify
from models import db
from models.employee import Employee
from models.leave import Leave
from models.feedback import Feedback
from nlp.sentiment import sentiment_analyzer
from datetime import datetime
from sqlalchemy import func

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


# ── Dashboard Summary Cards ───────────────────────────────────────────────────
@analytics_bp.route("/summary", methods=["GET"])
def summary():
    """Quick counts for the 4 stat cards at top of dashboard."""
    total_employees  = Employee.query.filter_by(is_active=True).count()
    pending_leaves   = Leave.query.filter_by(status="PENDING").count()
    total_feedbacks  = Feedback.query.count()

    # Average sentiment score across all feedbacks
    avg_sentiment = db.session.query(func.avg(Feedback.sentiment_score)).scalar() or 0.0

    return jsonify({
        "total_employees": total_employees,
        "pending_leaves":  pending_leaves,
        "total_feedbacks": total_feedbacks,
        "avg_sentiment":   round(float(avg_sentiment), 3),
    })


# ── Department Headcount (for Bar/Pie chart) ──────────────────────────────────
@analytics_bp.route("/departments", methods=["GET"])
def departments():
    """
    Uses SQLAlchemy GROUP BY to count employees per department.
    Returns format Chart.js expects: { labels: [...], data: [...] }
    """
    rows = (
        db.session.query(Employee.department, func.count(Employee.id))
        .filter_by(is_active=True)
        .group_by(Employee.department)
        .all()
    )
    labels = [r[0] for r in rows]
    data   = [r[1] for r in rows]
    return jsonify({"labels": labels, "data": data})


# ── Leave Status Breakdown (for Doughnut chart) ───────────────────────────────
@analytics_bp.route("/leaves/status", methods=["GET"])
def leave_status():
    rows = (
        db.session.query(Leave.status, func.count(Leave.id))
        .group_by(Leave.status)
        .all()
    )
    return jsonify({r[0]: r[1] for r in rows})


# ── Monthly Joining Trend (for Line chart) ────────────────────────────────────
@analytics_bp.route("/joining-trend", methods=["GET"])
def joining_trend():
    rows = (
        db.session.query(
            func.strftime("%Y-%m", Employee.join_date).label("month"),
            func.count(Employee.id).label("count")
        )
        .group_by("month")
        .order_by("month")
        .all()
    )
    return jsonify([{"month": r[0], "count": r[1]} for r in rows])

# ── Attendance Trend (for Line chart) ────────────────────────────────────
@analytics_bp.route("/attendance-trend", methods=["GET"])
def attendance_trend():
    from models.attendance import Attendance
    rows = (
        db.session.query(
            Attendance.date,
            func.count(Attendance.id)
        )
        .filter(Attendance.status == "Present")   # explicit column filter avoids ORM ambiguity
        .group_by(Attendance.date)
        .order_by(Attendance.date.desc())
        .limit(14)
        .all()
    )
    # Reverse to get chronological order (oldest → newest) for line chart
    return jsonify([{"date": str(r[0]), "present": r[1]} for r in reversed(rows)])

# ── Salary Distribution (for Bar chart) ─────────────────────────────────────
@analytics_bp.route("/salary/departments", methods=["GET"])
def dept_salary():
    rows = (
        db.session.query(Employee.department, func.avg(Employee.net_salary))
        .filter(Employee.net_salary > 0)
        .group_by(Employee.department)
        .all()
    )
    return jsonify([{"department": r[0], "avg_salary": round(float(r[1]), 2)} for r in rows])

# ── Performance Trend (for Bar chart) ─────────────────────────────────────
@analytics_bp.route("/performance-trend", methods=["GET"])
def performance_trend():
    from models.performance import Performance
    rows = (
        db.session.query(Performance.quarter, func.avg(Performance.score))
        .group_by(Performance.quarter)
        .order_by(Performance.quarter)
        .all()
    )
    return jsonify([{"quarter": r[0], "avg_score": round(float(r[1]), 2)} for r in rows])

# ── Department Sentiment (for Bar chart) ─────────────────────────────────────
@analytics_bp.route("/sentiment/departments", methods=["GET"])
def dept_sentiment():
    """
    Joins Feedback → Employee to get department, then aggregates
    average sentiment score per department.
    """
    rows = (
        db.session.query(Employee.department, func.avg(Feedback.sentiment_score))
        .join(Feedback, Employee.id == Feedback.employee_id)
        .group_by(Employee.department)
        .all()
    )
    return jsonify([
        {"department": r[0], "avg_sentiment": round(float(r[1]), 3)}
        for r in rows
    ])



# ── POST submit feedback (runs NLP sentiment) ─────────────────────────────────
@analytics_bp.route("/feedback", methods=["POST"])
def submit_feedback():
    """
    MEMBER 4's core endpoint.
    1. Save the feedback text.
    2. Run VADER sentiment analysis.
    3. Store label + score back into the row.
    """
    data = request.get_json()

    if not data.get("employee_id") or not data.get("text"):
        return jsonify({"error": "employee_id and text are required"}), 400

    # Run NLP
    sentiment_result = sentiment_analyzer.analyze(data["text"])
    highlights       = sentiment_analyzer.highlight_keywords(data["text"])

    fb = Feedback(
        employee_id     = data["employee_id"],
        text            = data["text"],
        sentiment_label = sentiment_result["label"],
        sentiment_score = sentiment_result["score"],
        submitted_by    = data.get("submitted_by", "manager"),
    )
    db.session.add(fb)
    db.session.commit()

    return jsonify({
        **fb.to_dict(),
        "sentiment_details": sentiment_result["details"],
        "keyword_highlights": highlights["top_words"],
    }), 201


# ── GET all feedbacks ─────────────────────────────────────────────────────────
@analytics_bp.route("/feedback", methods=["GET"])
def get_feedbacks():
    emp_id = request.args.get("employee_id", type=int)
    query  = Feedback.query
    if emp_id:
        query = query.filter_by(employee_id=emp_id)
    feedbacks = query.order_by(Feedback.created_at.desc()).all()
    return jsonify([f.to_dict() for f in feedbacks])
