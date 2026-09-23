import mysql.connector
from flask import current_app

def get_db():
    return mysql.connector.connect(**current_app.config["DB_CONFIG"])