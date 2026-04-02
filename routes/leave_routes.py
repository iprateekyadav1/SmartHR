"""
routes/leave_routes.py  —  MEMBER 1
=====================================
Leave management endpoints.

Business Logic:
  - An employee can have max 12 CL, 12 SL, 15 EL per year.
  - Balance is calculated as (allotted - used).
  - HR can approve/reject a pending application.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from models import db
from models.leave import Leave
from models.employee import Employee
from routes.auth_utils import admin_required

leave_bp = Blueprint("leaves", __name__, url_prefix="/api/leaves")

# Annual leave allotment policy (configurable)
LEAVE_ALLOTMENT = {"CL": 12, "SL": 12, "EL": 15, "ML": 90}


def get_leave_balance(employee_id: int, year: int = None) -> dict:
    """
    Calculate remaining leave per type for an employee in a given year.

    Algorithm:
      balance = allotted - sum(approved leave days of that type in the year)
    """
    year = year or datetime.utcnow().year
    balance = {}

    for leave_type, allotted in LEAVE_ALLOTMENT.items():
        # Filter: approved leaves of this type, within the given year
        used_leaves = Leave.query.filter(
            Leave.employee_id == employee_id,
            Leave.leave_type  == leave_type,
            Leave.status      == "APPROVED",
            db.extract("year", Leave.start_date) == year,
        ).all()

        used_days = sum(lv.days for lv in used_leaves)
        balance[leave_type] = max(0, allotted - used_days)

    return balance


# ── GET leave balance ─────────────────────────────────────────────────────────
@leave_bp.route("/balance/<int:emp_id>", methods=["GET"])
def leave_balance(emp_id):
    Employee.query.get_or_404(emp_id)   # 404 if employee not found
    balance = get_leave_balance(emp_id)
    return jsonify({"employee_id": emp_id, "balance": balance})


# ── GET all leave applications ────────────────────────────────────────────────
@leave_bp.route("", methods=["GET"])
def get_leaves():
    emp_id = request.args.get("employee_id", type=int)
    status = request.args.get("status")

    query = Leave.query
    if emp_id:
        query = query.filter_by(employee_id=emp_id)
    if status:
        query = query.filter_by(status=status.upper())

    leaves = query.order_by(Leave.applied_on.desc()).all()
    return jsonify([lv.to_dict() for lv in leaves])


# ── POST apply for leave ──────────────────────────────────────────────────────
@leave_bp.route("", methods=["POST"])
def apply_leave():
    data = request.get_json()

    required = ["employee_id", "leave_type", "start_date", "end_date"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"'{f}' is required"}), 400

    leave_type = data["leave_type"].upper()
    if leave_type not in LEAVE_ALLOTMENT:
        return jsonify({"error": f"Invalid leave type. Use: {list(LEAVE_ALLOTMENT.keys())}"}), 400

    start = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
    end   = datetime.strptime(data["end_date"],   "%Y-%m-%d").date()

    if end < start:
        return jsonify({"error": "end_date must be >= start_date"}), 400

    # Check if sufficient balance exists
    balance  = get_leave_balance(data["employee_id"])
    req_days = (end - start).days + 1
    if balance.get(leave_type, 0) < req_days:
        return jsonify({
            "error": f"Insufficient {leave_type} balance. Available: {balance.get(leave_type, 0)} days, Requested: {req_days} days"
        }), 422

    leave = Leave(
        employee_id = data["employee_id"],
        leave_type  = leave_type,
        start_date  = start,
        end_date    = end,
        reason      = data.get("reason", ""),
        status      = "PENDING",
    )
    db.session.add(leave)
    db.session.commit()
    return jsonify(leave.to_dict()), 201


# ── PUT approve / reject ──────────────────────────────────────────────────────
@leave_bp.route("/<int:leave_id>/status", methods=["PUT"])
@admin_required
def update_leave_status(leave_id):
    """HR manager endpoint to approve or reject a leave request."""
    leave  = Leave.query.get_or_404(leave_id)
    data   = request.get_json()
    status = data.get("status", "").upper()

    if status not in ("APPROVED", "REJECTED"):
        return jsonify({"error": "status must be APPROVED or REJECTED"}), 400

    leave.status = status
    db.session.commit()
    return jsonify(leave.to_dict())
