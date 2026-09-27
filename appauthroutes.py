from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import check_password_hash
from app.db import get_db

auth_bp = Blueprint("auth", __name__)


def password_matches(stored_hash, password):
    if not stored_hash or not password:
        return False

    stored_hash = str(stored_hash).strip()
    password = str(password)

    if stored_hash == password:
        return True

    try:
        return check_password_hash(stored_hash, password)
    except (TypeError, ValueError, AttributeError):
        return False


@auth_bp.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT * FROM users
            WHERE username=%s AND status='active'
        """, (username,))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and password_matches(user["password_hash"], password):
            session["user"] = user["username"]
            return redirect("/dashboard")

        return render_template("login.html", error="بيانات غير صحيحة")

    return render_template("login.html")