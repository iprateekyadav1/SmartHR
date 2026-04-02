from models import db
from datetime import datetime

class Performance(db.Model):
    __tablename__ = "performance"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    quarter = db.Column(db.String(10), nullable=False) # Q1-2025, etc.
    score = db.Column(db.Float, nullable=False) # 1-5 scale

    employee = db.relationship("Employee", backref=db.backref("performance", cascade="all, delete-orphan"))
