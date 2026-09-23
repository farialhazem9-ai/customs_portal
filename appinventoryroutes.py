from flask import Blueprint, request, redirect, session
import mysql.connector
from app import db_config

inventory_bp = Blueprint("inventory", __name__)

def get_db():
    return mysql.connector.connect(**db_config)

@inventory_bp.route("/add-product", methods=["POST"])
def add_product():
    if session.get("role") not in ["admin", "manager"]:
        return "Not allowed"

    name = request.form["name"]
    store_id = request.form["store_id"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO products (name, store_id) VALUES (%s, %s)",
        (name, store_id)
    )
    db.commit()

    return redirect("/dashboard")