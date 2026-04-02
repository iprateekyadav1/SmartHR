"""
models/leave.py  —  MEMBER 1
=============================
Leave request table.

Key concept: FOREIGN KEY
    employee_id references employees.id — this enforces referential
    integrity at the DB level (can't create a leave for non-existent employee).

Leave Types follow standard HR practice:
    CL = Casual Leave (short personal leave)
    SL = Sick Leave   (medical)
    EL = Earned Leave (accrued over time, can be encashed)
    ML = Maternity/Paternity Leave
"""

from models import db
from datetime import datetime


class Leave(db.Model):
    __tablename__ = "leaves"

    id          = db.Column(db.Integer, primary_key=True)

    # FK ties each leave to exactly one employee
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)

    leave_type  = db.Column(db.String(10), nullable=False)   # CL / SL / EL / ML
    start_date  = db.Column(db.Date, nullable=False)
    end_date    = db.Column(db.Date, nullable=False)
    reason      = db.Column(db.Text)

    # Status lifecycle:  PENDING → APPROVED | REJECTED
    status      = db.Column(db.String(20), default="PENDING")
    applied_on  = db.Column(db.DateTime, default=datetime.utcnow)

    # Back-reference to Employee model
    employee = db.relationship("Employee", back_populates="leaves")

    @property
    def days(self):
        """Calculated property: number of leave days requested."""
        return (self.end_date - self.start_date).days + 1

    def to_dict(self):
        return {
            "id":           self.id,
            "employee_id":  self.employee_id,
            "employee_name": self.employee.name if self.employee else "",
            "leave_type":   self.leave_type,
            "start_date":   str(self.start_date),
            "end_date":     str(self.end_date),
            "days":         self.days,
            "reason":       self.reason,
            "status":       self.status,
            "applied_on":   str(self.applied_on),
        }
