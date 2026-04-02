"""CSV export routes for SmartHR reports."""

import csv
import io

from flask import Blueprint, Response, jsonify

from models.employee import Employee
from models.leave import Leave
from models.feedback import Feedback
from routes.auth_utils import admin_required

report_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


def _csv_response(filename: str, headers: list[str], rows: list[list[str]]) -> Response:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    payload = buffer.getvalue()
    buffer.close()

    return Response(
        payload,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@report_bp.route("/employees.csv", methods=["GET"])
@admin_required
def export_employees():
    employees = Employee.query.order_by(Employee.id.asc()).all()
    rows = [
        [emp.id, emp.name, emp.email, emp.department, emp.designation, emp.salary, emp.is_active, emp.join_date]
        for emp in employees
    ]
    return _csv_response(
        "smarthr_employees.csv",
        ["id", "name", "email", "department", "designation", "salary", "is_active", "join_date"],
        rows,
    )


@report_bp.route("/leaves.csv", methods=["GET"])
@admin_required
def export_leaves():
    leaves = Leave.query.order_by(Leave.applied_on.desc()).all()
    rows = [
        [lv.id, lv.employee_id, lv.employee.name if lv.employee else "", lv.leave_type, lv.start_date, lv.end_date, lv.days, lv.status, lv.reason]
        for lv in leaves
    ]
    return _csv_response(
        "smarthr_leaves.csv",
        ["id", "employee_id", "employee_name", "leave_type", "start_date", "end_date", "days", "status", "reason"],
        rows,
    )


@report_bp.route("/feedback.csv", methods=["GET"])
@admin_required
def export_feedback():
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    rows = [
        [fb.id, fb.employee_id, fb.employee.name if fb.employee else "", fb.sentiment_label, fb.sentiment_score, fb.submitted_by, fb.created_at, fb.text]
        for fb in feedbacks
    ]
    return _csv_response(
        "smarthr_feedback.csv",
        ["id", "employee_id", "employee_name", "sentiment_label", "sentiment_score", "submitted_by", "created_at", "text"],
        rows,
    )


@report_bp.route("/summary", methods=["GET"])
@admin_required
def report_summary():
    return jsonify({
        "employees": Employee.query.count(),
        "leaves": Leave.query.count(),
        "feedbacks": Feedback.query.count(),
    })
