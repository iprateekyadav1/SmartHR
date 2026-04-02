"""
models/employee.py  —  MEMBER 1
==============================
Defines the Employee table using SQLAlchemy ORM.

ORM (Object-Relational Mapping) means we write Python classes
instead of raw SQL. SQLAlchemy translates each class → SQL table,
each attribute → column, each object → row.

DBMS concept: Normalization — Employee has its own table;
Leave and Feedback reference it via foreign keys (1-to-many relationship).
"""

from models import db
from datetime import datetime


class Employee(db.Model):
    __tablename__ = "employees"

    # ── Primary Key ───────────────────────────────────────────────────────────
    # Auto-incrementing integer; uniquely identifies each employee row.
    id = db.Column(db.Integer, primary_key=True)

    # ── Personal Info ─────────────────────────────────────────────────────────
    name       = db.Column(db.String(100), nullable=False)
    age        = db.Column(db.Integer)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    phone      = db.Column(db.String(20))
    address    = db.Column(db.Text)
    photo      = db.Column(db.String(255), default="")

    # ── Professional Info ─────────────────────────────────────────────────────
    department  = db.Column(db.String(50), nullable=False)   # e.g. "Engineering"
    designation = db.Column(db.String(100), nullable=False)  # e.g. "Software Engineer"
    salary      = db.Column(db.Float, default=0.0)
    basic_pay   = db.Column(db.Float, default=0.0)
    hra         = db.Column(db.Float, default=0.0)
    da          = db.Column(db.Float, default=0.0)
    pf_deduction = db.Column(db.Float, default=0.0)
    net_salary  = db.Column(db.Float, default=0.0)
    pay_grade   = db.Column(db.String(20), default="")
    skills      = db.Column(db.Text, default="")   # comma-separated, filled by resume parser

    # ── Status ────────────────────────────────────────────────────────────────
    is_active   = db.Column(db.Boolean, default=True)
    join_date   = db.Column(db.Date, default=datetime.utcnow)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────────────────────
    # back_populates creates a two-way link:
    #   employee.leaves  → list of Leave objects for this employee
    #   leave.employee   → back-reference to the Employee
    leaves    = db.relationship("Leave",    back_populates="employee", cascade="all, delete-orphan")
    feedbacks = db.relationship("Feedback", back_populates="employee", cascade="all, delete-orphan")

    def to_dict(self):
        """Serialize to JSON-safe dict for API responses."""
        return {
            "id":          self.id,
            "name":        self.name,
            "email":       self.email,
            "phone":       self.phone,
            "address":     self.address,
            "department":  self.department,
            "designation": self.designation,
            "salary":      self.salary,
            "skills":      self.skills.split(",") if self.skills else [],
            "is_active":   self.is_active,
            "join_date":   str(self.join_date),
            "created_at":  str(self.created_at),
        }

    def __repr__(self):
        return f"<Employee {self.name} [{self.department}]>"
