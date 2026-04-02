from models import db

class LeaveBalance(db.Model):
    __tablename__ = "leave_balances"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    casual_leave = db.Column(db.Integer, default=12)
    sick_leave = db.Column(db.Integer, default=6)
    earned_leave = db.Column(db.Integer, default=15)

    employee = db.relationship("Employee", backref=db.backref("leave_balance", uselist=False, cascade="all, delete-orphan"))
