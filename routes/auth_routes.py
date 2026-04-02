"""Authentication routes for SmartHR."""

from flask import Blueprint, render_template, request, redirect, url_for, session
from sqlalchemy import func, or_

from models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")

        user = (
            User.query.filter(
                or_(
                    func.lower(User.username) == identifier,
                    func.lower(User.email) == identifier,
                )
            ).first()
        )

        if user and user.is_active and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session["full_name"] = user.full_name
            session["role"] = user.role
            return redirect(url_for("dashboard"))

        error = "Invalid credentials. Use the demo credentials shown on the page."

    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/guest")
def guest_mode():
    session.clear()
    session["username"] = "guest"
    session["full_name"] = "Guest User"
    session["role"] = "guest"
    return redirect(url_for("dashboard"))
