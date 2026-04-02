from models import db
from datetime import datetime

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False) # Present, Absent, Half-Day, Leave

    employee = db.relationship("Employee", backref=db.backref("attendance", cascade="all, delete-orphan"))
