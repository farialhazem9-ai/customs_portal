import os
import secrets
from urllib.parse import urlparse


def _build_db_config_from_url():
    db_url = os.environ.get("MYSQL_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        return {
            "host": os.environ.get("DB_HOST") or os.environ.get("MYSQLHOST") or os.environ.get("DATABASE_HOST") or "localhost",
            "user": os.environ.get("DB_USER") or os.environ.get("MYSQLUSER") or "root",
            "password": os.environ.get("DB_PASSWORD") or os.environ.get("MYSQLPASSWORD") or "",
            "database": os.environ.get("DB_NAME") or os.environ.get("MYSQLDATABASE") or "customs_portal",
            "port": int(os.environ.get("DB_PORT") or os.environ.get("MYSQLPORT") or "3306"),
            "connection_timeout": int(os.environ.get("DB_CONNECTION_TIMEOUT", "5")),
            "autocommit": False,
        }

    parsed = urlparse(db_url)
    return {
        "host": parsed.hostname or os.environ.get("DB_HOST") or os.environ.get("MYSQLHOST") or os.environ.get("DATABASE_HOST") or "localhost",
        "user": parsed.username or os.environ.get("DB_USER") or os.environ.get("MYSQLUSER") or "root",
        "password": parsed.password or os.environ.get("DB_PASSWORD") or os.environ.get("MYSQLPASSWORD") or "",
        "database": (parsed.path or "/" + (os.environ.get("DB_NAME") or os.environ.get("MYSQLDATABASE") or "customs_portal")).lstrip("/"),
        "port": parsed.port or int(os.environ.get("DB_PORT") or os.environ.get("MYSQLPORT") or "3306"),
        "connection_timeout": int(os.environ.get("DB_CONNECTION_TIMEOUT", "5")),
        "autocommit": False,
    }


class Config:
    SECRET_KEY = os.environ.get("APP_SECRET_KEY") or secrets.token_hex(32)
    DB_CONFIG = _build_db_config_from_url()