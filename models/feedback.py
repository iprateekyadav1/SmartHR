"""
models/feedback.py  —  MEMBER 1 + MEMBER 4
===========================================
Stores employee feedback/reviews.
After saving, Member 4's sentiment module will score the text
and populate the `sentiment_score` and `sentiment_label` columns.

Sentiment label values: POSITIVE | NEUTRAL | NEGATIVE
Score range: -1.0 (most negative) to +1.0 (most positive)
"""

from models import db
from datetime import datetime


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id          = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)

    # The actual free-text feedback submitted
    text        = db.Column(db.Text, nullable=False)

    # NLP-populated columns (filled by sentiment.py after submission)
    sentiment_label = db.Column(db.String(20), default="NEUTRAL")
    sentiment_score = db.Column(db.Float,      default=0.0)

    # Who submitted: 'self' (employee) or 'manager'
    submitted_by = db.Column(db.String(50), default="manager")
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship("Employee", back_populates="feedbacks")

    def to_dict(self):
        return {
            "id":              self.id,
            "employee_id":     self.employee_id,
            "employee_name":   self.employee.name if self.employee else "",
            "text":            self.text,
            "sentiment_label": self.sentiment_label,
            "sentiment_score": self.sentiment_score,
            "submitted_by":    self.submitted_by,
            "created_at":      str(self.created_at),
        }
