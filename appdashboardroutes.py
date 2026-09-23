from flask import Blueprint, render_template, session, redirect

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    role = session.get("role")

    return render_template("dashboard.html", role=role)