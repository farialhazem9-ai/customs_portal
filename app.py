import os
import secrets
from pathlib import Path
from flask import Flask, render_template, request, redirect, session, flash, Blueprint, jsonify
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError, generate_csrf
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import json
import urllib.request
import threading
import webbrowser
import mysql.connector

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

try:
    from hr_api import bp as hr_bp
except ImportError as e:
    missing = str(e).lower()
    if "sqlalchemy" in missing or "hr_api" in missing:
        hr_bp = Blueprint("hr", __name__, url_prefix="/hr")

        @hr_bp.route("/", defaults={"path": ""})
        @hr_bp.route("/<path:path>")
        def hr_unavailable(path):
            return render_template(
                "login.html",
                error="قسم شئون العاملين غير متاح حالياً. الرجاء تثبيت المتطلبات وتشغيل التطبيق مرة أخرى."
            )
    else:
        raise

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET_KEY') or secrets.token_hex(32)

# Flask-WTF / CSRF configuration (professional defaults)
app.config.setdefault('WTF_CSRF_TIME_LIMIT', None)
app.config.setdefault('WTF_CSRF_ENABLED', True)

# Session cookie security settings
app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
# In production, ensure SESSION_COOKIE_SECURE=True (requires HTTPS)
app.config.setdefault('SESSION_COOKIE_SECURE', not app.debug)

csrf = CSRFProtect(app)

# Expose csrf_token() in Jinja templates (generate_csrf is a callable)
app.jinja_env.globals['csrf_token'] = generate_csrf

db_config = {
    "host": os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST') or os.environ.get('DATABASE_HOST') or 'localhost',
    "user": os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'root',
    "password": os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or 'Hazem@2026',
    "database": os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'customs_portal',
    "port": int(os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT') or '3306'),
    "connection_timeout": int(os.environ.get('DB_CONNECTION_TIMEOUT', '5')),
    "autocommit": False
}

try:
    from hr_db import init_hr_db
    init_hr_db(db_config)
except Exception as exc:
    print(f"HR database initialization warning: {exc}")


def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except Exception as e:
        print(f"DB Connection Error: {e}")
        raise


def bootstrap_database_schema(sql_file=None):
    """Create the application schema when the database is empty."""
    sql_file = Path(sql_file) if sql_file else Path(__file__).resolve().with_name('customs_portal.sql')
    if not sql_file.exists():
        raise FileNotFoundError(f"Database schema file not found: {sql_file}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SHOW TABLES')
        tables = {row[0].lower() for row in cur.fetchall()}

        required_tables = {'users', 'items', 'roles', 'permissions', 'suppliers'}
        if required_tables.issubset(tables):
            return False

        sql_text = sql_file.read_text(encoding='utf-8')
        statements = []
        for part in sql_text.split(';'):
            statement = part.strip()
            if statement:
                statements.append(statement)

        for statement in statements:
            try:
                cur.execute(statement)
                conn.commit()
            except Exception as exc:
                print(f"SQL import warning: {exc}")
                try:
                    conn.rollback()
                except Exception:
                    pass

        return True
    except mysql.connector.Error as exc:
        print(f"SQL import error: {exc}")
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        cur.close()
        conn.close()


def ensure_database_ready():
    """Ensure the core application tables exist before login or other DB access."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('SHOW TABLES')
            tables = {row[0].lower() for row in cur.fetchall()}
            if {'users', 'items', 'roles', 'permissions'}.issubset(tables):
                return False
        finally:
            cur.close()
            conn.close()

        return bootstrap_database_schema()
    except Exception:
        return bootstrap_database_schema()


def get_current_user_id(conn=None):
    username = session.get("user")
    if not username:
        return None

    close_conn = conn is None
    if conn is None:
        conn = get_db_connection()

    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM users WHERE username=%s LIMIT 1", (username,))
        row = cur.fetchone()
        return row["id"] if row else None
    finally:
        cur.close()
        if close_conn:
            conn.close()


def get_client_ip():
    headers_to_check = [
        request.headers.get('X-Forwarded-For'),
        request.headers.get('X-Real-IP'),
        request.headers.get('CF-Connecting-IP'),
        request.headers.get('True-Client-IP'),
    ]

    for header_value in headers_to_check:
        if not header_value:
            continue
        for part in header_value.split(','):
            candidate = part.strip()
            if candidate and candidate != 'unknown':
                return candidate

    return request.remote_addr or 'unknown'


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


def get_client_ip_details():
    remote_ip = request.remote_addr or 'unknown'
    forwarded_ip = None

    for header_name in ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP', 'True-Client-IP']:
        header_value = request.headers.get(header_name)
        if not header_value:
            continue
        for part in str(header_value).split(','):
            candidate = part.strip()
            if candidate and candidate != 'unknown':
                forwarded_ip = candidate
                break
        if forwarded_ip:
            break

    if forwarded_ip and forwarded_ip != remote_ip:
        return {
            'external_ip': forwarded_ip,
            'local_ip': remote_ip,
            'display': f'{forwarded_ip} / {remote_ip}'
        }

    return {
        'external_ip': remote_ip,
        'local_ip': remote_ip,
        'display': remote_ip
    }


def ensure_user_login_tracking_columns():
    try:
        for column_name, ddl in [
            ('last_login_at', "ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL AFTER status"),
            ('last_login_ip', "ALTER TABLE users ADD COLUMN last_login_ip VARCHAR(45) NULL AFTER last_login_at"),
        ]:
            if has_column('users', column_name):
                continue

            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute(ddl)
                conn.commit()
                schema_cache.pop(f"users.{column_name}", None)
            except mysql.connector.Error as exc:
                conn.rollback()
                if exc.errno == 1060:
                    schema_cache[f"users.{column_name}"] = True
                    continue
                raise
            finally:
                cur.close()
                conn.close()
    except Exception as exc:
        print(f"Database warning/error: {exc}")
        pass


def get_user_permissions():
    username = session.get('user')
    if not username:
        return set()

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT DISTINCT p.permission_key
            FROM users u
            LEFT JOIN user_permissions up ON up.user_id = u.id AND up.allow_access = 1
            LEFT JOIN permissions p ON p.id = up.permission_id
            LEFT JOIN role_permissions rp ON rp.role_id = u.role_id
            LEFT JOIN permissions rp_p ON rp_p.id = rp.permission_id
            WHERE u.username = %s
        """, (username,))
        rows = cur.fetchall() or []

        permissions = {row['permission_key'] for row in rows if row.get('permission_key')}

        cur.execute("SELECT r.name FROM users u JOIN roles r ON r.id = u.role_id WHERE u.username = %s LIMIT 1", (username,))
        role = cur.fetchone()
        if role and role.get('name') == 'Admin':
            permissions.add('admin')

        return permissions
    finally:
        cur.close()
        conn.close()


def has_permission(permission_key):
    if not session.get('user'):
        return False
    if 'admin' in get_user_permissions():
        return True
    return permission_key in get_user_permissions()


def has_department_access(department):
    if 'admin' in get_user_permissions():
        return True
    return f'department.{department}.view' in get_user_permissions()


schema_cache = {}

def has_column(table, column):
    key = f"{table}.{column}"
    if key in schema_cache:
        return schema_cache[key]

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema=%s AND table_name=%s AND column_name=%s",
            (db_config["database"], table, column)
        )
        exists = cur.fetchone()[0] == 1
        schema_cache[key] = exists
        return exists
    finally:
        cur.close()
        conn.close()


def normalize_department_key(value):
    if value is None:
        return 'local_purchases'

    normalized = str(value).strip().lower()
    aliases = {
        'local_purchases': 'local_purchases',
        'local purchase': 'local_purchases',
        'local purchases': 'local_purchases',
        'local': 'local_purchases',
        'المشتريات المحلية': 'local_purchases',
        'مشتريات محلية': 'local_purchases',
        'محلي': 'local_purchases',
        'external_purchases': 'external_purchases',
        'external purchase': 'external_purchases',
        'external purchases': 'external_purchases',
        'foreign_purchases': 'external_purchases',
        'foreign purchase': 'external_purchases',
        'foreign purchases': 'external_purchases',
        'المشتريات الخارجية': 'external_purchases',
        'مشتريات خارجية': 'external_purchases',
        'خارجي': 'external_purchases',
    }

    if normalized in aliases:
        return aliases[normalized]

    if 'local' in normalized or 'محلي' in normalized:
        return 'local_purchases'
    if 'external' in normalized or 'foreign' in normalized or 'خارج' in normalized:
        return 'external_purchases'

    return 'local_purchases'


def build_department_stock_summary(rows):
    summary = {'local_purchases': 0, 'external_purchases': 0}
    for row in rows or []:
        key = normalize_department_key(row.get('department'))
        qty = float(row.get('current_stock') or 0)
        summary[key] = summary.get(key, 0) + qty
    return summary


def build_item_entry_path(department):
    normalized = normalize_department_key(department)
    return f"/items/add/{normalized}"


def build_department_items_path(department):
    normalized = normalize_department_key(department)
    return f"/items/department/{normalized}"


def ensure_suppliers_table():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SHOW TABLES LIKE 'suppliers'")
            if cur.fetchone():
                return
        finally:
            cur.close()
            conn.close()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                CREATE TABLE suppliers (
                    id INT NOT NULL AUTO_INCREMENT,
                    supplier_name VARCHAR(255) NOT NULL,
                    supplier_code VARCHAR(100) NULL,
                    phone VARCHAR(100) NULL,
                    email VARCHAR(255) NULL,
                    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_suppliers_code (supplier_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            conn.commit()
        except Exception as exc:
            print(f"Database warning/error: {exc}")
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            cur.close()
            conn.close()
    except Exception as exc:
        print(f"Database warning/error: {exc}")
        pass


def ensure_item_department_column():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM items LIMIT 1")
            cur.fetchone()
        except Exception as exc:
            print(f"Database warning/error: {exc}")
            return
        finally:
            cur.close()
            conn.close()

        if has_column('items', 'department'):
            return

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "ALTER TABLE items ADD COLUMN department VARCHAR(255) NOT NULL DEFAULT 'local_purchases' AFTER item_type"
            )
            conn.commit()
        except Exception as exc:
            print(f"Database warning/error: {exc}")
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            cur.close()
            conn.close()
    except Exception as exc:
        print(f"Database warning/error: {exc}")
        pass


def ensure_item_current_balance_column():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM items LIMIT 1")
            cur.fetchone()
        except Exception as exc:
            print(f"Database warning/error: {exc}")
            return
        finally:
            cur.close()
            conn.close()

        if has_column('items', 'current_balance'):
            return

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "ALTER TABLE items ADD COLUMN current_balance DECIMAL(15,2) NOT NULL DEFAULT 0.00"
            )
            conn.commit()
            schema_cache['items.current_balance'] = True
        except Exception as exc:
            print(f"Database warning/error: {exc}")
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            cur.close()
            conn.close()
    except Exception as exc:
        print(f"Database warning/error: {exc}")
        pass


def ensure_companies_table():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_code VARCHAR(50) NOT NULL UNIQUE,
                    company_name VARCHAR(255) NOT NULL,
                    contact_person VARCHAR(255) NULL,
                    contact_title VARCHAR(150) NULL,
                    phone VARCHAR(50) NULL,
                    alternate_phone VARCHAR(50) NULL,
                    whatsapp VARCHAR(50) NULL,
                    email VARCHAR(255) NULL,
                    alternate_email VARCHAR(255) NULL,
                    website VARCHAR(255) NULL,
                    address VARCHAR(500) NULL,
                    city VARCHAR(100) NULL,
                    country VARCHAR(100) NULL,
                    tax_number VARCHAR(100) NULL,
                    commercial_register VARCHAR(100) NULL,
                    activity VARCHAR(255) NULL,
                    specialization VARCHAR(255) NULL,
                    notes TEXT NULL,
                    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            for column_name, column_definition in (
                ('alternate_email', 'VARCHAR(255) NULL AFTER email'),
                ('specialization', 'VARCHAR(255) NULL AFTER activity'),
            ):
                if not has_column('companies', column_name):
                    cur.execute(
                        f"ALTER TABLE companies ADD COLUMN {column_name} {column_definition}"
                    )
            conn.commit()
        finally:
            cur.close()
            conn.close()
    except Exception as exc:
        print(f"Database warning/error: {exc}")
        pass


def ensure_issue_voucher_reference_column():
    try:
        columns = (
            ('reference_no', 'VARCHAR(100) NULL AFTER voucher_no'),
            ('service_type', 'VARCHAR(50) NULL AFTER reference_no'),
            ('rental_company_id', 'INT NULL AFTER service_type'),
        )
        if all(has_column('issue_vouchers', column_name) for column_name, _ in columns):
            return

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            for column_name, column_definition in columns:
                if not has_column('issue_vouchers', column_name):
                    cur.execute(
                        f"ALTER TABLE issue_vouchers ADD COLUMN {column_name} {column_definition}"
                    )
            conn.commit()
        except mysql.connector.Error as exc:
            conn.rollback()
            if exc.errno != 1060:
                print(f"Database warning/error: {exc}")
                return
        finally:
            cur.close()
            conn.close()
    except Exception as exc:
        print(f"Database warning/error: {exc}")
        pass


def ensure_department_permissions():
    try:
        permissions = (
            ('department.dashboard.view', 'رؤية لوحة التحكم', 'الإدارات'),
            ('department.balances.view', 'رؤية أرصدة الإدارات', 'الإدارات'),
            ('department.local.view', 'رؤية المشتريات المحلية', 'الإدارات'),
            ('department.external.view', 'رؤية المشتريات الخارجية', 'الإدارات'),
            ('department.customs.view', 'رؤية إدارة الجمارك', 'الإدارات'),
            ('department.users.view', 'رؤية إدارة المستخدمين', 'الإدارات'),
            ('department.hr.view', 'رؤية شئون العاملين', 'الإدارات'),
            ('department.payroll.view', 'رؤية إعدادات الرواتب', 'الإدارات'),
            ('department.exchange.view', 'رؤية أسعار العملات', 'الإدارات'),
            ('department.companies.view', 'رؤية دليل الشركات', 'الإدارات'),
            ('department.reports.view', 'رؤية التقارير', 'الإدارات'),
        )
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            for permission_key, permission_name, module_name in permissions:
                cur.execute(
                    "SELECT id FROM permissions WHERE permission_key=%s LIMIT 1",
                    (permission_key,)
                )
                if not cur.fetchone():
                    cur.execute(
                        "INSERT INTO permissions (permission_key, permission_name, module_name) VALUES (%s, %s, %s)",
                        (permission_key, permission_name, module_name)
                    )
            conn.commit()
        finally:
            cur.close()
            conn.close()
    except Exception as exc:
        print(f"Database warning/error: {exc}")
        pass


try:
    ensure_database_ready()
except Exception as exc:
    print(f"Database bootstrap warning: {exc}")

ensure_item_department_column()
ensure_item_current_balance_column()
ensure_suppliers_table()
ensure_companies_table()
ensure_issue_voucher_reference_column()
ensure_department_permissions()


@app.context_processor
def inject_user_data():
    user = session.get("user")
    low_stock_count = 0
    low_stock_items = []

    if user:
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT id, item_name_ar, current_stock
                FROM items
                WHERE current_stock IS NOT NULL AND current_stock < 5
                ORDER BY current_stock ASC
                LIMIT 5
            """)
            low_stock_items = cur.fetchall() or []
            low_stock_count = len(low_stock_items)
            cur.close()
        except Exception as e:
            print(f"Low stock query error: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

    return {
        "user": user,
        "user_permissions": get_user_permissions(),
        "low_stock_count": low_stock_count,
        "low_stock_items": low_stock_items
    }


@app.before_request
def enforce_permission_checks():
    if not session.get('user'):
        return None

    if request.path.startswith('/static'):
        return None

    allowed_without_permission = {
        '/', '/logout', '/dev-login', '/dashboard', '/search'
    }
    if request.path in allowed_without_permission:
        return None

    path = request.path
    department = request.args.get('department')
    default_local_paths = {
        '/items', '/categories', '/stores', '/suppliers', '/requisition/add',
        '/requisitions', '/purchase-orders', '/create_order'
    }
    if path in default_local_paths and not department:
        department = 'local_purchases'

    if (path.startswith('/local-purchases') or
            path == '/items/add/local_purchases' or
            department == 'local_purchases'):
        if not has_department_access('local'):
            flash('ليس لديك صلاحية رؤية إدارة المشتريات المحلية.', 'danger')
            return redirect('/dashboard')
    if (path.startswith('/external-purchases') or
            path == '/items/add/external_purchases' or
            department == 'external_purchases'):
        if not has_department_access('external'):
            flash('ليس لديك صلاحية رؤية إدارة المشتريات الخارجية.', 'danger')
            return redirect('/dashboard')
    if path.startswith('/customs-management'):
        if not has_department_access('customs'):
            flash('ليس لديك صلاحية رؤية إدارة الجمارك.', 'danger')
            return redirect('/dashboard')

    section_access = (
        ('/department-balances', 'balances'),
        ('/roles', 'users'),
        ('/hr/settings', 'payroll'),
        ('/hr/', 'hr'),
        ('/exchange-rates', 'exchange'),
        ('/companies', 'companies'),
        ('/reports', 'reports'),
    )
    for prefix, section in section_access:
        if path.startswith(prefix) and not has_department_access(section):
            flash('ليس لديك صلاحية رؤية هذه الإدارة.', 'danger')
            return redirect('/dashboard')

    required_permission = None

    if path == '/roles':
        required_permission = 'users.view' if request.method == 'GET' else 'users.create'
    elif path == '/items' or path.startswith('/items?'):
        required_permission = 'inventory.view'
    elif path.startswith('/items/add'):
        required_permission = 'inventory.create'
    elif path.startswith('/items/edit/'):
        required_permission = 'inventory.edit'
    elif path.startswith('/items/delete/'):
        required_permission = 'inventory.delete'
    elif path.startswith('/items/add-balance/') or path.startswith('/items/remove-balance/'):
        required_permission = 'inventory.edit'
    elif path == '/stores' or path.startswith('/stores?'):
        required_permission = 'stores.view'
    elif path.startswith('/stores/add'):
        required_permission = 'stores.create'
    elif path.startswith('/stores/edit/'):
        required_permission = 'stores.edit'
    elif path.startswith('/stores/delete/'):
        required_permission = 'stores.delete'
    elif path.startswith('/purchase-orders') or path.startswith('/create_order'):
        required_permission = 'purchase.view' if request.method == 'GET' else 'purchase.create'
    elif path.startswith('/requisition/') or path.startswith('/requisitions'):
        required_permission = 'purchase.view' if request.method == 'GET' else 'purchase.create'
    elif path.startswith('/customs-management'):
        required_permission = 'customs.view'
    elif path.startswith('/issue'):
        required_permission = 'maintenance.view'
    elif path.startswith('/reports'):
        required_permission = 'reports.view'
    elif path.startswith('/suppliers') or path.startswith('/categories'):
        required_permission = 'inventory.view'

    if required_permission and not has_permission(required_permission):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة.', 'danger')
        return redirect('/dashboard')

    return None


# ======================
# تسجيل الدخول
# ======================
@app.route("/", methods=["GET", "POST"])
def login():
    try:
        ensure_database_ready()
    except Exception as exc:
        print(f"Login bootstrap attempt failed: {exc}")
        return render_template("login.html", error="قاعدة البيانات غير جاهزة، يرجى المحاولة بعد قليل.")

    ensure_user_login_tracking_columns()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s AND status='active'", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and password_matches(user["password_hash"], password):
            session["user"] = user["username"]
            ip_details = get_client_ip_details()
            ip_address = ip_details['external_ip'] or ip_details['local_ip'] or 'unknown'
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    "UPDATE users SET last_login_at=NOW(), last_login_ip=%s WHERE id=%s",
                    (ip_address, user["id"])
                )
                conn.commit()
            finally:
                cur.close()
                conn.close()
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="بيانات الدخول غير صحيحة")

    return render_template("login.html")


# Development helper: dev login (only enabled when DEV_LOGIN_ALLOWED=1)
@app.route('/dev-login')
def dev_login():
    if os.environ.get('DEV_LOGIN_ALLOWED') != '1':
        return "Dev login disabled", 403
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT username FROM users LIMIT 1")
    u = cur.fetchone()
    cur.close()
    conn.close()
    if not u:
        return "No user found", 404
    session['user'] = u['username']
    return redirect('/dashboard')


# ======================
# لوحة التحكم
# ======================
@app.route('/roles', methods=['GET', 'POST'])
def manage_roles():
    ensure_user_login_tracking_columns()

    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("SELECT id FROM users WHERE username=%s LIMIT 1", (session['user'],))
        current_user = cur.fetchone()
        if not current_user:
            flash('المستخدم الحالي غير موجود.', 'danger')
            return redirect('/dashboard')

        cur.execute("SELECT r.name FROM roles r JOIN users u ON u.role_id = r.id WHERE u.id=%s LIMIT 1", (current_user['id'],))
        current_role = cur.fetchone()
        if not current_role or current_role['name'] != 'Admin':
            flash('ليس لديك صلاحية إدارة المستخدمين.', 'danger')
            return redirect('/dashboard')

        current_user_id = current_user['id']
        cur.execute("SELECT id, name, description FROM roles ORDER BY id")
        roles = cur.fetchall() or []

        cur.execute("SELECT id, permission_key, permission_name, module_name FROM permissions ORDER BY module_name, permission_name")
        permissions = cur.fetchall() or []

        cur.execute("""
            SELECT
                u.id,
                u.full_name,
                u.username,
                u.email,
                u.status,
                u.last_login_at,
                u.last_login_ip,
                r.name AS role_name,
                COUNT(up.permission_id) AS permissions_count
            FROM users u
            LEFT JOIN roles r ON r.id = u.role_id
            LEFT JOIN user_permissions up ON up.user_id = u.id
            GROUP BY u.id, u.full_name, u.username, u.email, u.status, u.last_login_at, u.last_login_ip, r.name
            ORDER BY u.id DESC
        """)
        users = cur.fetchall() or []
    finally:
        cur.close()
        conn.close()

    if request.method == 'POST':
        full_name = (request.form.get('full_name') or '').strip()
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        password = request.form.get('password') or ''
        role_id = request.form.get('role_id')
        status = request.form.get('status') or 'active'
        permission_ids = request.form.getlist('permissions')

        if not full_name or not username or not password or not role_id:
            flash('يرجى تعبئة اسم المستخدم، اسم كامل، كلمة المرور، والدور.', 'danger')
            return redirect('/roles')

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT id FROM users WHERE username=%s LIMIT 1", (username,))
            if cur.fetchone():
                flash('اسم المستخدم موجود مسبقاً.', 'danger')
                return redirect('/roles')

            if email:
                cur.execute("SELECT id FROM users WHERE email=%s LIMIT 1", (email,))
                if cur.fetchone():
                    flash('البريد الإلكتروني موجود مسبقاً.', 'danger')
                    return redirect('/roles')

            hashed_password = generate_password_hash(password)
            cur.execute(
                """
                INSERT INTO users (role_id, full_name, username, email, password_hash, phone, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (int(role_id), full_name, username, email or None, hashed_password, phone or None, status)
            )
            new_user_id = cur.lastrowid

            for permission_id in permission_ids:
                cur.execute(
                    "INSERT INTO user_permissions (user_id, permission_id, allow_access) VALUES (%s, %s, 1)",
                    (new_user_id, int(permission_id))
                )

            conn.commit()
            flash('تم إنشاء المستخدم الجديد بنجاح.', 'success')
            return redirect('/roles')
        except Exception as exc:
            conn.rollback()
            flash(f'حدث خطأ أثناء إنشاء المستخدم: {str(exc)}', 'danger')
            return redirect('/roles')
        finally:
            cur.close()
            conn.close()

    return render_template('roles.html', roles=roles, permissions=permissions, users=users, current_user_id=current_user_id)


@app.route('/roles/<int:user_id>/password', methods=['GET', 'POST'])
def change_user_password(user_id):
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, username, full_name, role_id FROM users WHERE id=%s LIMIT 1", (user_id,))
        target_user = cur.fetchone()
        if not target_user:
            flash('المستخدم غير موجود.', 'danger')
            return redirect('/roles')

        cur.execute("SELECT id FROM users WHERE username=%s LIMIT 1", (session['user'],))
        current_user = cur.fetchone()
        if not current_user:
            flash('المستخدم الحالي غير موجود.', 'danger')
            return redirect('/dashboard')

        cur.execute("SELECT r.name FROM roles r JOIN users u ON u.role_id = r.id WHERE u.id=%s LIMIT 1", (current_user['id'],))
        current_role = cur.fetchone()
        if not current_role or current_role['name'] != 'Admin':
            flash('ليس لديك صلاحية تغيير كلمة المرور.', 'danger')
            return redirect('/dashboard')
    finally:
        cur.close()
        conn.close()

    if request.method == 'POST':
        new_password = (request.form.get('new_password') or '').strip()
        confirm_password = (request.form.get('confirm_password') or '').strip()

        if not new_password or len(new_password) < 4:
            flash('يجب أن تكون كلمة المرور 4 أحرف على الأقل.', 'danger')
            return redirect(f'/roles/{user_id}/password')

        if new_password != confirm_password:
            flash('كلمتا المرور غير متطابقتين.', 'danger')
            return redirect(f'/roles/{user_id}/password')

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE users SET password_hash=%s WHERE id=%s",
                (generate_password_hash(new_password), user_id)
            )
            conn.commit()
            if user_id == current_user['id']:
                flash('تم تحديث كلمة المرور الخاصة بك بنجاح.', 'success')
            else:
                flash(f'تم تحديث كلمة مرور المستخدم {target_user["username"]} بنجاح.', 'success')
        except Exception as exc:
            conn.rollback()
            flash(f'حدث خطأ أثناء تحديث كلمة المرور: {str(exc)}', 'danger')
        finally:
            cur.close()
            conn.close()

        return redirect('/roles')

    return render_template('role_password.html', user=target_user, is_self=(user_id == current_user['id']))


@app.route('/roles/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, username FROM users WHERE username=%s LIMIT 1", (session['user'],))
        current_user = cur.fetchone()
        if not current_user:
            flash('المستخدم الحالي غير موجود.', 'danger')
            return redirect('/dashboard')

        cur.execute("SELECT r.name FROM roles r JOIN users u ON u.role_id = r.id WHERE u.id=%s LIMIT 1", (current_user['id'],))
        current_role = cur.fetchone()
        if not current_role or current_role['name'] != 'Admin':
            flash('ليس لديك صلاحية تعديل المستخدمين.', 'danger')
            return redirect('/dashboard')

        cur.execute("SELECT id, full_name, username, email, phone, role_id, status FROM users WHERE id=%s LIMIT 1", (user_id,))
        user = cur.fetchone()
        if not user:
            flash('المستخدم غير موجود.', 'danger')
            return redirect('/roles')

        cur.execute("SELECT id, name, description FROM roles ORDER BY id")
        roles = cur.fetchall() or []

        cur.execute("SELECT id, permission_key, permission_name, module_name FROM permissions ORDER BY module_name, permission_name")
        permissions = cur.fetchall() or []

        cur.execute("SELECT permission_id FROM user_permissions WHERE user_id=%s", (user_id,))
        selected_permission_ids = {row['permission_id'] for row in cur.fetchall() or []}
    finally:
        cur.close()
        conn.close()

    if request.method == 'POST':
        full_name = (request.form.get('full_name') or '').strip()
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        role_id = request.form.get('role_id')
        status = request.form.get('status') or 'active'
        permission_ids = request.form.getlist('permissions')

        if not full_name or not username or not role_id:
            flash('يرجى تعبئة الاسم الكامل واسم المستخدم والدور.', 'danger')
            return redirect(f'/roles/{user_id}/edit')

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT id FROM users WHERE username=%s AND id!=%s LIMIT 1", (username, user_id))
            if cur.fetchone():
                flash('اسم المستخدم موجود مسبقاً.', 'danger')
                return redirect(f'/roles/{user_id}/edit')

            if email:
                cur.execute("SELECT id FROM users WHERE email=%s AND id!=%s LIMIT 1", (email, user_id))
                if cur.fetchone():
                    flash('البريد الإلكتروني موجود مسبقاً.', 'danger')
                    return redirect(f'/roles/{user_id}/edit')

            cur.execute(
                """
                UPDATE users
                SET full_name=%s, username=%s, email=%s, phone=%s, role_id=%s, status=%s
                WHERE id=%s
                """,
                (full_name, username, email or None, phone or None, int(role_id), status, user_id)
            )

            cur.execute("DELETE FROM user_permissions WHERE user_id=%s", (user_id,))
            for permission_id in permission_ids:
                cur.execute(
                    "INSERT INTO user_permissions (user_id, permission_id, allow_access) VALUES (%s, %s, 1)",
                    (user_id, int(permission_id))
                )

            conn.commit()
            flash('تم تحديث بيانات المستخدم بنجاح.', 'success')
            return redirect('/roles')
        except Exception as exc:
            conn.rollback()
            flash(f'حدث خطأ أثناء تحديث المستخدم: {str(exc)}', 'danger')
            return redirect(f'/roles/{user_id}/edit')
        finally:
            cur.close()
            conn.close()

    return render_template(
        'role_edit.html',
        user=user,
        roles=roles,
        permissions=permissions,
        selected_permission_ids=selected_permission_ids,
        current_user_id=current_user['id']
    )


@app.route('/roles/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, username FROM users WHERE username=%s LIMIT 1", (session['user'],))
        current_user = cur.fetchone()
        if not current_user:
            flash('المستخدم الحالي غير موجود.', 'danger')
            return redirect('/dashboard')

        cur.execute("SELECT r.name FROM roles r JOIN users u ON u.role_id = r.id WHERE u.id=%s LIMIT 1", (current_user['id'],))
        current_role = cur.fetchone()
        if not current_role or current_role['name'] != 'Admin':
            flash('ليس لديك صلاحية حذف المستخدمين.', 'danger')
            return redirect('/dashboard')

        if user_id == current_user['id']:
            flash('لا يمكنك حذف حسابك الشخصي من خلال الإدارة.', 'warning')
            return redirect('/roles')

        cur.execute("SELECT id, username FROM users WHERE id=%s LIMIT 1", (user_id,))
        target_user = cur.fetchone()
        if not target_user:
            flash('المستخدم غير موجود.', 'danger')
            return redirect('/roles')

        cur.execute("DELETE FROM user_permissions WHERE user_id=%s", (user_id,))
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        flash(f'تم حذف المستخدم {target_user["username"]} بنجاح.', 'success')
    except Exception as exc:
        conn.rollback()
        flash(f'حدث خطأ أثناء حذف المستخدم: {str(exc)}', 'danger')
    finally:
        cur.close()
        conn.close()

    return redirect('/roles')


@app.route('/roles/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, username, status FROM users WHERE username=%s LIMIT 1", (session['user'],))
        current_user = cur.fetchone()
        if not current_user:
            flash('المستخدم الحالي غير موجود.', 'danger')
            return redirect('/dashboard')

        cur.execute("SELECT r.name FROM roles r JOIN users u ON u.role_id = r.id WHERE u.id=%s LIMIT 1", (current_user['id'],))
        current_role = cur.fetchone()
        if not current_role or current_role['name'] != 'Admin':
            flash('ليس لديك صلاحية تغيير حالة المستخدمين.', 'danger')
            return redirect('/dashboard')

        if user_id == current_user['id']:
            flash('لا يمكنك تغيير حالة حسابك الشخصي من هنا.', 'warning')
            return redirect('/roles')

        cur.execute("SELECT id, username, status FROM users WHERE id=%s LIMIT 1", (user_id,))
        target_user = cur.fetchone()
        if not target_user:
            flash('المستخدم غير موجود.', 'danger')
            return redirect('/roles')

        new_status = 'inactive' if target_user['status'] == 'active' else 'active'
        cur.execute("UPDATE users SET status=%s WHERE id=%s", (new_status, user_id))
        conn.commit()
        flash(f'تم تحديث حالة المستخدم {target_user["username"]} إلى {new_status}.', 'success')
    except Exception as exc:
        conn.rollback()
        flash(f'حدث خطأ أثناء تحديث حالة المستخدم: {str(exc)}', 'danger')
    finally:
        cur.close()
        conn.close()

    return redirect('/roles')


@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) total FROM items")
    items_count = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) total FROM stores")
    stores_count = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) total FROM users")
    users_count = cur.fetchone()["total"]

    cur.execute("""
        SELECT COUNT(*) total
        FROM maintenance_requests
    """)
    requests_count = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        items_count=items_count,
        stores_count=stores_count,
        users_count=users_count,
        requests_count=requests_count
    )


@app.route("/local-purchases")
def local_purchases_management():
    if "user" not in session:
        return redirect("/")
    return render_template("local_purchases_management.html")


@app.route("/external-purchases")
def external_purchases_management():
    if "user" not in session:
        return redirect("/")
    return render_template("external_purchases_management.html")


@app.route("/department-balances")
def department_balances():
    if "user" not in session:
        return redirect("/")

    ensure_item_current_balance_column()
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            department,
            COUNT(*) AS items_count,
            SUM(COALESCE(current_stock, 0)) AS total_stock,
            SUM(COALESCE(current_balance, 0)) AS total_balance
        FROM items
        GROUP BY department
        ORDER BY department
    """)
    department_rows = cur.fetchall() or []

    department_summary = {}
    for row in department_rows:
        key = normalize_department_key(row.get('department'))
        department_summary[key] = {
            'items_count': int(row.get('items_count') or 0),
            'total_stock': float(row.get('total_stock') or 0),
            'total_balance': float(row.get('total_balance') or 0),
        }

    departments = [
        {
            'key': 'local_purchases',
            'label': 'المشتريات المحلية',
            'items_count': department_summary.get('local_purchases', {}).get('items_count', 0),
            'total_stock': department_summary.get('local_purchases', {}).get('total_stock', 0),
            'total_balance': department_summary.get('local_purchases', {}).get('total_balance', 0),
        },
        {
            'key': 'external_purchases',
            'label': 'المشتريات الخارجية',
            'items_count': department_summary.get('external_purchases', {}).get('items_count', 0),
            'total_stock': department_summary.get('external_purchases', {}).get('total_stock', 0),
            'total_balance': department_summary.get('external_purchases', {}).get('total_balance', 0),
        }
    ]

    cur.execute("""
        SELECT
            id,
            item_code,
            item_name_ar,
            department,
            current_stock,
            current_balance
        FROM items
        ORDER BY department, item_name_ar
    """)
    items = cur.fetchall() or []

    cur.close()
    conn.close()

    return render_template(
        'department_balances.html',
        departments=departments,
        items=items,
        user=session['user']
    )


@app.route("/stock/card/<int:item_id>")
def stock_card(item_id):

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            i.*,
            u.unit_name
        FROM items i
        LEFT JOIN units u
            ON i.unit_id=u.id
        WHERE i.id=%s
    """, (item_id,))

    item = cur.fetchone()

    cur.execute("""
        SELECT
            st.*,
            w.warehouse_name
        FROM stock_transactions st
        LEFT JOIN warehouses w
            ON st.warehouse_id=w.id
        WHERE st.item_id=%s
        ORDER BY st.created_at ASC
    """, (item_id,))

    transactions = cur.fetchall()

    balance = 0
    total_in = 0
    total_out = 0

    for row in transactions:

        qty = float(row["qty"])

        if row["transaction_type"] == "IN":

            total_in += qty

            row["qty_in"] = qty
            row["qty_out"] = 0

            balance += qty

        else:

            total_out += qty

            row["qty_in"] = 0
            row["qty_out"] = qty

            balance -= qty

        row["balance"] = balance

    current_balance = balance

    cur.close()
    conn.close()

    return render_template(
        "stock_card.html",
        item=item,
        transactions=transactions,
        total_in=total_in,
        total_out=total_out,
        current_balance=current_balance,
        user=session["user"]
    )
@app.route("/stock/balance")
def stock_balance():

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            item_code,
            item_name_ar,
            current_balance
        FROM items
        ORDER BY item_name_ar
    """)

    items = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "stock_balance.html",
        items=items
    )
@app.route("/stock/in", methods=["GET", "POST"])
def stock_in():

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":

        item_id = request.form["item_id"]
        warehouse_id = request.form["warehouse_id"]
        qty = float(request.form["qty"])

        cur.execute("""
            INSERT INTO stock_transactions
            (item_id, warehouse_id, transaction_type, qty)
            VALUES (%s,%s,%s,%s)
        """, (
            item_id,
            warehouse_id,
            "IN",
            qty
        ))

        cur.execute("""
            UPDATE items
            SET current_balance =
                current_balance + %s
            WHERE id=%s
        """, (
            qty,
            item_id
        ))

        conn.commit()

    cur.close()
    conn.close()

    return "تم إضافة الوارد"
@app.route("/stock/out", methods=["POST"])
def stock_out():

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    item_id = request.form["item_id"]
    qty = float(request.form["qty"])

    cur.execute("""
        SELECT current_balance
        FROM items
        WHERE id=%s
    """, (item_id,))

    item = cur.fetchone()

    if item["current_balance"] < qty:
        return "الرصيد غير كاف"

    cur.execute("""
        INSERT INTO stock_transactions
        (item_id, warehouse_id, transaction_type, qty)
        VALUES (%s,%s,%s,%s)
    """, (
        item_id,
        request.form["warehouse_id"],
        "OUT",
        qty
    ))

    cur.execute("""
        UPDATE items
        SET current_balance =
            current_balance - %s
        WHERE id=%s
    """, (
        qty,
        item_id
    ))

    conn.commit()

    cur.close()
    conn.close()

    return "تم الصرف"
# ======================
# إضافة صنف
# ======================
@app.route("/items/add", methods=["GET", "POST"])
def add_item():
    target_department = request.args.get('department') or 'local_purchases'
    return redirect(build_item_entry_path(target_department), code=302)


@app.route("/items/add/<department>", methods=["GET", "POST"])
def add_item_for_department(department):

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    try:
        selected_department = normalize_department_key(department or 'local_purchases')

        # تحميل الفئات
        cur.execute("""
            SELECT id, category_name_ar
            FROM categories
            ORDER BY category_name_ar
        """)
        categories = cur.fetchall()

        # تحميل الوحدات
        cur.execute("""
            SELECT id, unit_name
            FROM units
            ORDER BY unit_name
        """)
        units = cur.fetchall()

        if request.method == "POST":

            item_code = request.form["item_code"].strip()
            item_name_ar = request.form["item_name_ar"].strip()

            item_type = request.form.get("item_type", "")
            receipt_no = request.form.get("receipt_no", "")
            po_number = request.form.get("po_number", "")
            department = selected_department

            qty = float(request.form.get("qty", 0) or 0)
            unit_price = float(request.form.get("unit_price", 0) or 0)
            price = float(request.form.get("price", 0) or 0)
            weight = float(request.form.get("weight", 0) or 0)
            shipping_cost = float(request.form.get("shipping_cost", 0) or 0)

            total_cost = (qty * unit_price) + shipping_cost

            category_id = request.form["category_id"]
            unit_id = request.form["unit_id"]

            cur.execute(
                "SELECT id FROM items WHERE item_code=%s",
                (item_code,)
            )

            exists = cur.fetchone()

            if exists:
                return "❌ كود الصنف موجود مسبقاً"

            cur.execute("""
                INSERT INTO items
                (
                    category_id,
                    unit_id,
                    item_code,
                    item_name_ar,
                    item_type,
                    department,
                    receipt_no,
                    po_number,
                    qty,
                    unit_price,
                    price,
                    weight,
                    shipping_cost,
                    total_cost
                )
                VALUES
                (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
            """, (
                category_id,
                unit_id,
                item_code,
                item_name_ar,
                item_type,
                department,
                receipt_no,
                po_number,
                qty,
                unit_price,
                price,
                weight,
                shipping_cost,
                total_cost
            ))

            conn.commit()

            return redirect(f"/items?department={selected_department}")

    except Exception as e:

        conn.rollback()

        return f"""
        <h3>خطأ أثناء الحفظ</h3>
        <pre>{str(e)}</pre>
        """

    finally:

        cur.close()
        conn.close()

    return render_template(
        "add_item.html",
        categories=categories,
        units=units,
        user=session["user"],
        selected_department=selected_department
    )


@app.route("/items")
def list_items():

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    department = normalize_department_key(request.args.get('department') or 'local_purchases')

    cur.execute("""
        SELECT
            i.*,
            c.category_name_ar,
            u.unit_name
        FROM items i
        LEFT JOIN categories c
            ON i.category_id = c.id
        LEFT JOIN units u
            ON i.unit_id = u.id
        WHERE i.department = %s
        ORDER BY i.id DESC
    """, (department,))

    items = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "items.html",
        items=items,
        user=session["user"],
        selected_department=department,
        department_locked=False
    )


@app.route("/items/department/<department>")
def department_items(department):
    if "user" not in session:
        return redirect("/")

    norm_department = normalize_department_key(department or 'local_purchases')
    return redirect(f"/items?department={norm_department}")

# ======================
# إضافة رصيد للصنف
# ======================
@app.route("/items/add-balance/<int:item_id>", methods=["POST"])
def add_balance(item_id):

    if "user" not in session:
        return redirect("/")

    try:

        qty = float(request.form.get("qty", 0))
        department = normalize_department_key(request.form.get("department") or 'local_purchases')

        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()

        cur.execute("""
            UPDATE items
            SET current_balance = current_balance + %s,
                current_stock = current_stock + %s
            WHERE id = %s AND department = %s
        """, (qty, qty, item_id, department))

        conn.commit()

        print("Rows affected:", cur.rowcount)
        print("Item:", item_id, "Qty:", qty)

        flash("تمت إضافة الرصيد بنجاح", "success")

    except Exception as e:

        print("ERROR:", str(e))
        flash(str(e), "danger")

    finally:

        try:
            cur.close()
            conn.close()
        except:
            pass

    return redirect("/items")
@app.route("/items/remove-balance/<int:item_id>", methods=["POST"])
def remove_balance(item_id):

    if "user" not in session:
        return redirect("/")

    try:
        qty = float(request.form.get("qty", 0))
        department = normalize_department_key(request.form.get("department") or 'local_purchases')

        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)

        cur.execute(
            "SELECT current_balance FROM items WHERE id=%s AND department=%s",
            (item_id, department)
        )

        item = cur.fetchone()

        if not item:
            flash("الصنف غير موجود", "danger")
            return redirect("/items")

        if float(item["current_balance"]) < qty:
            flash("الرصيد غير كافٍ", "danger")
            return redirect("/items")

        cur.execute("""
            UPDATE items
            SET current_balance = current_balance - %s,
                current_stock = current_stock - %s
            WHERE id = %s AND department = %s
        """, (qty, qty, item_id, department))

        conn.commit()

        flash("تم صرف الرصيد بنجاح", "success")

    except Exception as e:
        flash(str(e), "danger")

    finally:
        cur.close()
        conn.close()

    return redirect("/items")
# ======================
# تعديل صنف
# ======================
@app.route("/items/edit/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":

        item_code = request.form["item_code"]
        item_name_ar = request.form["item_name_ar"]
        item_type = request.form.get("item_type", "")
        receipt_no = request.form.get("receipt_no", "")
        po_number = request.form.get("po_number", "")
        department = normalize_department_key(request.form.get("department") or 'local_purchases')
        qty = float(request.form.get("qty", 0))
        unit_price = float(request.form.get("unit_price", 0))
        price = float(request.form.get("price", 0))
        weight = float(request.form.get("weight", 0))
        shipping_cost = float(request.form.get("shipping_cost", 0))

        category_id = request.form["category_id"]
        unit_id = request.form["unit_id"]

        total_cost = (qty * unit_price) + shipping_cost

        cur.execute("""
            UPDATE items
            SET
                category_id=%s,
                unit_id=%s,
                item_code=%s,
                item_name_ar=%s,
                item_type=%s,
                department=%s,
                receipt_no=%s,
                po_number=%s,
                qty=%s,
                unit_price=%s,
                price=%s,
                weight=%s,
                shipping_cost=%s,
                total_cost=%s
            WHERE id=%s
        """, (
            category_id,
            unit_id,
            item_code,
            item_name_ar,
            item_type,
            department,
            receipt_no,
            po_number,
            qty,
            unit_price,
            price,
            weight,
            shipping_cost,
            total_cost,
            item_id
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash("تم تحديث الصنف بنجاح", "success")

        return redirect("/items")

    # جلب بيانات الصنف
    cur.execute("SELECT * FROM items WHERE id=%s", (item_id,))
    item = cur.fetchone()

    # جلب الفئات
    cur.execute("""
        SELECT id, category_name_ar
        FROM categories
        ORDER BY category_name_ar
    """)
    categories = cur.fetchall()

    # جلب الوحدات
    cur.execute("""
        SELECT id, unit_name
        FROM units
        ORDER BY unit_name
    """)
    units = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "edit_item.html",
        item=item,
        categories=categories,
        units=units,
        user=session["user"]
    )

# ======================
# حذف صنف
# ======================
@app.route("/items/delete/<int:id>", methods=["POST"])
def delete_item(id):
    if "user" not in session:
        return redirect("/")

    if 'admin' not in get_user_permissions():
        flash("حذف الأصناف مسموح للأدمن فقط.", "danger")
        return redirect("/items")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        tables_to_check = [
            ("stock_movements", "item_id"),
            ("store_items", "item_id"),
            ("issue_voucher_items", "item_id"),
            ("purchase_order_items", "item_id"),
            ("goods_receipt_items", "item_id"),
            ("inventory_count_items", "item_id"),
            ("customs_items", "item_id"),
            ("job_items", "item_id"),
            ("stock_transfer_items", "item_id"),
            ("workshop_items", "item_id"),
        ]

        for table_name, column_name in tables_to_check:
            cur.execute(f"SELECT COUNT(*) AS row_count FROM {table_name} WHERE {column_name}=%s", (id,))
            row_count = cur.fetchone().get("row_count") or 0
            if row_count > 0:
                flash("لا يمكن حذف الصنف لأنه مرتبط بسجلات أو حركات مخزون أو طلبات شراء/إصدار سابقاً.", "danger")
                return redirect("/items")

        cur.execute("DELETE FROM items WHERE id=%s", (id,))
        conn.commit()
        flash("تم حذف الصنف بنجاح.", "success")
    except Exception as exc:
        conn.rollback()
        flash(f"تعذّر حذف الصنف: {str(exc)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect("/items")

@app.route("/issue/add", methods=["GET","POST"])
def add_issue(department=None):

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    requested_department = department or request.args.get('department') or request.form.get('department')
    selected_department = normalize_department_key(requested_department) if requested_department else None

    if selected_department:
        cur.execute("""
            SELECT id,item_code,item_name_ar,current_stock,price
            FROM items
            WHERE department=%s
            ORDER BY item_name_ar
        """, (selected_department,))
    else:
        cur.execute("""
            SELECT id,item_code,item_name_ar,current_stock,price
            FROM items
            ORDER BY item_name_ar
        """)
    items = cur.fetchall()

    cur.execute("""
        SELECT id,store_name
        FROM stores
        ORDER BY store_name
    """)
    stores = cur.fetchall()

    if request.method == "POST":

        item_id = request.form["item_id"]
        store_id = request.form["store_id"]

        qty = float(request.form["qty"])

        if selected_department:
            cur.execute("""
                SELECT current_stock, current_balance, price
                FROM items
                WHERE id=%s AND department=%s
            """, (item_id, selected_department))
        else:
            cur.execute("""
                SELECT current_stock, current_balance, price
                FROM items
                WHERE id=%s
            """, (item_id,))

        item = cur.fetchone()

        if qty > float(item["current_stock"]):

            flash("الكمية المطلوبة أكبر من الرصيد")
            return redirect(
                "/local-purchases/issue/add"
                if selected_department == 'local_purchases' else "/issue/add"
            )
        if item.get("current_balance") is not None and qty > float(item["current_balance"]):
            flash("الكمية المطلوبة أكبر من الرصيد الإجمالي المتاح")
            return redirect(
                "/local-purchases/issue/add"
                if selected_department == 'local_purchases' else "/issue/add"
            )

        try:
            # Create an issue voucher record and its item, then deduct stock and record movement
            voucher_no = f"IV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            issue_date = datetime.now().date()

            cur.execute("""
                INSERT INTO issue_vouchers
                (voucher_no, issue_date, department, receiver_name, notes, created_by, status, approved_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,NOW())
            """, (
                voucher_no,
                issue_date,
                selected_department,
                session.get("user"),
                None,
                session.get("user"),
                'approved'
            ))

            voucher_id = cur.lastrowid

            # Insert voucher item
            unit_price = float(item.get("price") or 0)
            cur.execute("""
                INSERT INTO issue_voucher_items
                (voucher_id, item_id, qty, unit_price, total)
                VALUES (%s,%s,%s,%s,%s)
            """, (
                voucher_id,
                item_id,
                qty,
                unit_price,
                qty * unit_price
            ))

            # Deduct from items current_stock
            cur.execute("""
                UPDATE items
                SET current_stock=current_stock-%s,
                    current_balance=COALESCE(current_balance, 0)-%s
                WHERE id=%s AND department=%s
            """, (qty, qty, item_id, selected_department))

            # Insert stock movement record for audit
            cur.execute("""
                INSERT INTO stock_movements
                (item_id, warehouse_id, movement_type, qty, reference_type, reference_id)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                item_id,
                store_id or 1,
                'OUT',
                qty,
                'ISSUE_VOUCHER',
                voucher_id
            ))

            conn.commit()

            flash("تم إنشاء إذن الصرف وصرف الكمية بنجاح", "success")

            return redirect(
                "/local-purchases/issue-vouchers"
                if selected_department == 'local_purchases' else "/issue-vouchers"
            )

        except Exception as e:
            conn.rollback()
            flash(str(e), "danger")
            return redirect(
                "/local-purchases/issue/add"
                if selected_department == 'local_purchases' else "/issue/add"
            )

    return render_template(
        "issue_add.html",
        items=items,
        stores=stores,
        selected_department=selected_department,
        user=session["user"]
    )


@app.route('/local-purchases/issue/add', methods=['GET', 'POST'])
def local_purchase_add_issue():
    return add_issue(department='local_purchases')

# ======================
# إدارة المخازن
# ======================
# عرض المخازن
@app.route("/stores")
def stores():

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM stores
        ORDER BY store_name
    """)

    stores = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "stores.html",
        stores=stores,
        user=session["user"]
    )


# إضافة مخزن
@app.route("/stores/add", methods=["GET", "POST"])
def add_store():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO stores
            (
                store_code,
                store_name,
                location,
                manager,
                phone,
                description,
                is_active
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            request.form["store_code"],
            request.form["store_name"],
            request.form.get("location"),
            request.form.get("manager"),
            request.form.get("phone"),
            request.form.get("description"),
            1 if request.form.get("status") == "active" else 0
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect("/stores")

    return render_template(
        "add_store.html",
        user=session["user"]
    )


# تعديل مخزن
@app.route("/stores/edit/<int:id>", methods=["GET", "POST"])
def edit_store(id):

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":

        cur.execute("""
            UPDATE stores
            SET
                store_code=%s,
                store_name=%s,
                location=%s,
                manager=%s,
                phone=%s,
                description=%s,
                is_active=%s
            WHERE id=%s
        """, (
            request.form["store_code"],
            request.form["store_name"],
            request.form.get("location"),
            request.form.get("manager"),
            request.form.get("phone"),
            request.form.get("description"),
            1 if request.form.get("status") == "active" else 0,
            id
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect("/stores")

    cur.execute(
        "SELECT * FROM stores WHERE id=%s",
        (id,)
    )

    store = cur.fetchone()

    cur.close()
    conn.close()

    if not store:
        return "المخزن غير موجود", 404

    return render_template(
        "edit_store.html",
        store=store,
        user=session["user"]
    )


# حذف مخزن
@app.route("/stores/delete/<int:id>", methods=["GET", "POST"])
def delete_store(id):

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM stores WHERE id=%s",
        (id,)
    )

    store = cur.fetchone()

    if not store:
        cur.close()
        conn.close()
        return "المخزن غير موجود", 404

    if request.method == "POST":

        cur.execute(
            "DELETE FROM stores WHERE id=%s",
            (id,)
        )

        conn.commit()

        cur.close()
        conn.close()

        return redirect("/stores")

    cur.close()
    conn.close()

    return render_template(
        "delete_store.html",
        store=store,
        user=session["user"]
    )

# ======================
# التقارير
# ======================
@app.route("/reports/current-stock")
def current_stock_report():

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM vw_current_stock
        ORDER BY item_name_ar
    """)

    stock = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "reports.html",
        stock=stock
    )


@app.route("/reports")
def reports():
    return redirect("/reports/current-stock")


@app.route("/exchange-rates")
def exchange_rates():
    rates = []
    updated_at = None
    try:
        with urllib.request.urlopen("https://open.er-api.com/v6/latest/EGP", timeout=5) as response:
            data = json.load(response)
            if data.get("result") == "success":
                updated_at = data.get("time_last_update_utc")
                for code, value in data.get("rates", {}).items():
                    if code == "EGP":
                        continue
                    try:
                        rate = 1 / float(value) if value else None
                    except Exception:
                        rate = None
                    rates.append({
                        "code": code,
                        "name": code,
                        "rate": rate
                    })
    except Exception:
        rates = []

    return render_template(
        "exchange_rates.html",
        rates=rates,
        updated_at=updated_at
    )


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    section = request.args.get("section", "all")
    results = {
        "items": [],
        "categories": [],
        "stores": [],
        "suppliers": [],
        "requisitions": [],
        "purchase_orders": []
    }
    has_results = False

    if query:
        search_pattern = f"%{query}%"
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        if section in ("all", "items"):
            cur.execute(
                "SELECT id, item_code, item_name_ar, current_stock FROM items "
                "WHERE item_code LIKE %s OR item_name_ar LIKE %s "
                "LIMIT 50",
                (search_pattern, search_pattern)
            )
            results["items"] = cur.fetchall()

        if section in ("all", "categories"):
            cur.execute(
                "SELECT id, category_name_ar FROM categories "
                "WHERE category_name_ar LIKE %s LIMIT 50",
                (search_pattern,)
            )
            results["categories"] = cur.fetchall()

        if section in ("all", "stores"):
            cur.execute(
                "SELECT id, store_code, store_name, location, manager, phone, is_active AS status "
                "FROM stores WHERE store_name LIKE %s OR store_code LIKE %s LIMIT 50",
                (search_pattern, search_pattern)
            )
            results["stores"] = cur.fetchall()

        if section in ("all", "suppliers"):
            cur.execute(
                "SELECT id, supplier_name, supplier_code, phone, email FROM suppliers "
                "WHERE supplier_name LIKE %s OR supplier_code LIKE %s LIMIT 50",
                (search_pattern, search_pattern)
            )
            results["suppliers"] = cur.fetchall()

        if section in ("all", "requisitions"):
            if has_column('purchase_requisitions', 'store_id'):
                cur.execute(
                    "SELECT pr.id, i.item_name_ar, i.current_stock, s.store_name, pr.quantity, pr.user, pr.reason, pr.status "
                    "FROM purchase_requisitions pr "
                    "LEFT JOIN items i ON pr.item_id=i.id "
                    "LEFT JOIN stores s ON pr.store_id=s.id "
                    "WHERE i.item_name_ar LIKE %s OR s.store_name LIKE %s OR pr.user LIKE %s OR pr.reason LIKE %s "
                    "LIMIT 50",
                    (search_pattern, search_pattern, search_pattern, search_pattern)
                )
            else:
                cur.execute(
                    "SELECT pr.id, i.item_name_ar, i.current_stock, NULL AS store_name, pr.quantity, pr.user, pr.reason, pr.status "
                    "FROM purchase_requisitions pr "
                    "LEFT JOIN items i ON pr.item_id=i.id "
                    "WHERE i.item_name_ar LIKE %s OR pr.user LIKE %s OR pr.reason LIKE %s "
                    "LIMIT 50",
                    (search_pattern, search_pattern, search_pattern)
                )
            results["requisitions"] = cur.fetchall()

        if section in ("all", "purchase_orders"):
            cur.execute(
                "SELECT po.id, po.po_number, s.supplier_name, po.subtotal, po.status "
                "FROM purchase_orders po "
                "LEFT JOIN suppliers s ON po.vendor_id=s.id "
                "WHERE po.po_number LIKE %s OR s.supplier_name LIKE %s "
                "LIMIT 50",
                (search_pattern, search_pattern)
            )
            results["purchase_orders"] = cur.fetchall()

        cur.close()
        conn.close()

        has_results = any(results.values())

    return render_template(
        "search_results.html",
        query=query,
        section=section,
        results=results,
        has_results=has_results
    )


@app.route("/requisition/add", methods=["GET", "POST"])
def add_requisition():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT id, item_name_ar, current_stock, '' AS store_name FROM items ORDER BY item_name_ar"
    )
    items = cur.fetchall()

    cur.execute(
        "SELECT id, store_name FROM stores ORDER BY store_name"
    )
    stores = cur.fetchall()

    selected_item = request.args.get("item_id")

    if request.method == "POST":
        item_id = request.form.get("item_id")
        store_id = request.form.get("store_id")
        quantity = float(request.form.get("quantity", 0) or 0)
        reason = request.form.get("reason", "")

        if not item_id or quantity <= 0:
            flash("يرجى تعبئة جميع الحقول المطلوبة", "danger")
            return redirect("/requisition/add")

        if has_column('purchase_requisitions', 'store_id'):
            if not store_id:
                flash("يرجى اختيار المخزن", "danger")
                return redirect("/requisition/add")
            cur.execute(
                "INSERT INTO purchase_requisitions "
                "(item_id, store_id, quantity, reason, `user`, status) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (item_id, store_id, quantity, reason, session.get("user"), "pending")
            )
        else:
            cur.execute(
                "INSERT INTO purchase_requisitions "
                "(item_id, quantity, reason, `user`, status) "
                "VALUES (%s,%s,%s,%s,%s)",
                (item_id, quantity, reason, session.get("user"), "pending")
            )
        conn.commit()
        cur.close()
        conn.close()
        flash("تم تقديم طلب الشراء بنجاح", "success")
        return redirect("/requisitions")

    cur.close()
    conn.close()

    return render_template(
        "add_requisition.html",
        items=items,
        stores=stores,
        requester=session.get("user"),
        selected_item=selected_item
    )


@app.route("/requisition/edit/<int:req_id>", methods=["GET", "POST"])
def edit_requisition(req_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if has_column('purchase_requisitions', 'store_id'):
        cur.execute(
            "SELECT pr.*, i.item_name_ar, s.store_name "
            "FROM purchase_requisitions pr "
            "LEFT JOIN items i ON pr.item_id=i.id "
            "LEFT JOIN stores s ON pr.store_id=s.id "
            "WHERE pr.id=%s",
            (req_id,)
        )
    else:
        cur.execute(
            "SELECT pr.*, i.item_name_ar, NULL AS store_name "
            "FROM purchase_requisitions pr "
            "LEFT JOIN items i ON pr.item_id=i.id "
            "WHERE pr.id=%s",
            (req_id,)
        )
    req = cur.fetchone()

    if not req:
        cur.close()
        conn.close()
        return "طلب الشراء غير موجود", 404

    if request.method == "POST":
        quantity = float(request.form.get("quantity", 0) or 0)
        reason = request.form.get("reason", "")
        cur.execute(
            "UPDATE purchase_requisitions SET quantity=%s, reason=%s WHERE id=%s",
            (quantity, reason, req_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("تم تحديث طلب الشراء", "success")
        return redirect("/requisitions")

    cur.close()
    conn.close()

    return render_template(
        "edit_requisition.html",
        req=req
    )


@app.route("/requisition/delete/<int:req_id>", methods=["POST"])
def delete_requisition(req_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM purchase_requisitions WHERE id=%s", (req_id,))
    conn.commit()
    cur.close()
    conn.close()

    flash("تم حذف طلب الشراء", "success")
    return redirect("/requisitions")


@app.route("/requisition/approve/<int:req_id>", methods=["POST"])
def approve_requisition(req_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT status FROM purchase_requisitions WHERE id=%s", (req_id,))
    req = cur.fetchone()
    if not req:
        cur.close()
        conn.close()
        flash("طلب الشراء غير موجود", "danger")
        return redirect("/requisitions")

    if req["status"] == "approved":
        flash("طلب الشراء تم اعتماده مسبقاً", "warning")
    else:
        cur.execute(
            "UPDATE purchase_requisitions SET status='approved' WHERE id=%s",
            (req_id,)
        )
        conn.commit()
        flash("تم اعتماد طلب الشراء", "success")

    cur.close()
    conn.close()
    return redirect("/requisitions")


@app.route("/requisition/reject/<int:req_id>", methods=["POST"])
def reject_requisition(req_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT status FROM purchase_requisitions WHERE id=%s", (req_id,))
    req = cur.fetchone()
    if not req:
        cur.close()
        conn.close()
        flash("طلب الشراء غير موجود", "danger")
        return redirect("/requisitions")

    if req["status"] == "rejected":
        flash("طلب الشراء تم رفضه مسبقاً", "warning")
    else:
        cur.execute(
            "UPDATE purchase_requisitions SET status='rejected' WHERE id=%s",
            (req_id,)
        )
        conn.commit()
        flash("تم رفض طلب الشراء", "success")

    cur.close()
    conn.close()
    return redirect("/requisitions")


@app.route("/requisitions")
def requisitions():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    department = request.args.get('department')
    department = normalize_department_key(department) if department else None
    if has_column('purchase_requisitions', 'store_id'):
        query = ("SELECT pr.*, i.item_name_ar, i.current_stock, s.store_name "
                 "FROM purchase_requisitions pr "
                 "LEFT JOIN items i ON pr.item_id=i.id "
                 "LEFT JOIN stores s ON pr.store_id=s.id ")
    else:
        query = ("SELECT pr.*, i.item_name_ar, i.current_stock, NULL AS store_name "
                 "FROM purchase_requisitions pr "
                 "LEFT JOIN items i ON pr.item_id=i.id ")
    params = []
    if department:
        query += "WHERE i.department=%s "
        params.append(department)
    query += "ORDER BY pr.id DESC"
    cur.execute(query, params)
    requisitions = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "requisitions.html",
        requisitions=requisitions,
        selected_department=department
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/categories")
def categories_page():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM categories ORDER BY category_name_ar")
    categories = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "categories.html",
        categories=categories
    )


@app.route("/categories/add", methods=["GET", "POST"])
def add_category():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO categories (category_name_ar) VALUES (%s)",
            (request.form["category_name_ar"],)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/categories")

    return render_template("add_category.html")


@app.route("/categories/edit/<int:id>", methods=["GET", "POST"])
def edit_category(id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        cur.execute(
            "UPDATE categories SET category_name_ar=%s WHERE id=%s",
            (request.form["category_name_ar"], id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/categories")

    cur.execute("SELECT * FROM categories WHERE id=%s", (id,))
    category = cur.fetchone()
    cur.close()
    conn.close()

    if not category:
        return "الفئة غير موجودة", 404

    return render_template(
        "edit_category.html",
        category=category
    )


@app.route("/categories/delete/<int:id>", methods=["POST"])
def delete_category(id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT COUNT(*) AS item_count FROM items WHERE category_id=%s", (id,))
        item_count = cur.fetchone()["item_count"] or 0

        cur.execute("SELECT COUNT(*) AS child_count FROM categories WHERE parent_id=%s", (id,))
        child_count = cur.fetchone()["child_count"] or 0

        if item_count > 0 or child_count > 0:
            flash("لا يمكن حذف الفئة لأنه يوجد أصناف أو فئات فرعية مرتبطة بها.", "danger")
            return redirect("/categories")

        cur.execute("DELETE FROM categories WHERE id=%s", (id,))
        conn.commit()
        flash("تم حذف الفئة بنجاح.", "success")
    except Exception as exc:
        conn.rollback()
        flash(f"تعذّر حذف الفئة: {str(exc)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect("/categories")


@app.route("/suppliers")
def suppliers_page():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM suppliers ORDER BY supplier_name")
    suppliers = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "suppliers.html",
        suppliers=suppliers
    )


@app.route("/suppliers/add", methods=["GET", "POST"])
def add_supplier():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO suppliers (supplier_name, supplier_code, phone, email) VALUES (%s,%s,%s,%s)",
            (
                request.form.get("supplier_name"),
                request.form.get("supplier_code"),
                request.form.get("phone"),
                request.form.get("email")
            )
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/suppliers")

    return render_template("add_supplier.html")


@app.route("/suppliers/edit/<int:id>", methods=["GET", "POST"])
def edit_supplier(id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        cur.execute(
            "UPDATE suppliers SET supplier_name=%s, phone=%s, email=%s WHERE id=%s",
            (
                request.form.get("supplier_name"),
                request.form.get("phone"),
                request.form.get("email"),
                id
            )
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/suppliers")

    cur.execute("SELECT * FROM suppliers WHERE id=%s", (id,))
    supplier = cur.fetchone()
    cur.close()
    conn.close()

    if not supplier:
        return "المورد غير موجود", 404

    return render_template(
        "edit_supplier.html",
        supplier=supplier
    )


@app.route("/suppliers/delete/<int:id>", methods=["POST"])
def delete_supplier(id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM suppliers WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/suppliers")


@app.route("/companies")
def companies_page():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM companies ORDER BY company_name")
    companies = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("companies.html", companies=companies)


@app.route("/companies/add", methods=["GET", "POST"])
def add_company():
    if "user" not in session:
        return redirect("/")

    fields = [
        "company_code", "company_name", "contact_person", "contact_title",
        "phone", "alternate_phone", "whatsapp", "email", "alternate_email", "website",
        "address", "city", "country", "tax_number", "commercial_register",
        "activity", "specialization", "notes", "status"
    ]
    if request.method == "POST":
        values = [request.form.get(field, "").strip() or None for field in fields]
        if not values[0] or not values[1]:
            flash("اسم الشركة وكود الشركة مطلوبان.", "danger")
            return render_template("company_form.html", company=request.form, is_edit=False)

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO companies
                (company_code, company_name, contact_person, contact_title, phone,
                 alternate_phone, whatsapp, email, alternate_email, website, address,
                 city, country, tax_number, commercial_register, activity,
                 specialization, notes, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            flash("تمت إضافة الشركة بنجاح.", "success")
            return redirect("/companies")
        except mysql.connector.Error as exc:
            conn.rollback()
            flash(f"تعذر حفظ الشركة: {exc}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template("company_form.html", company=None, is_edit=False)


@app.route("/companies/edit/<int:id>", methods=["GET", "POST"])
def edit_company(id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM companies WHERE id=%s", (id,))
    company = cur.fetchone()
    cur.close()
    conn.close()
    if not company:
        return "الشركة غير موجودة", 404

    if request.method == "POST":
        fields = [
            "company_code", "company_name", "contact_person", "contact_title",
            "phone", "alternate_phone", "whatsapp", "email", "alternate_email", "website",
            "address", "city", "country", "tax_number", "commercial_register",
            "activity", "specialization", "notes", "status"
        ]
        values = [request.form.get(field, "").strip() or None for field in fields]
        if not values[0] or not values[1]:
            flash("اسم الشركة وكود الشركة مطلوبان.", "danger")
            company.update(request.form.to_dict())
            return render_template("company_form.html", company=company, is_edit=True)

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE companies SET
                    company_code=%s, company_name=%s, contact_person=%s, contact_title=%s,
                    phone=%s, alternate_phone=%s, whatsapp=%s, email=%s, alternate_email=%s,
                    website=%s,
                    address=%s, city=%s, country=%s, tax_number=%s,
                    commercial_register=%s, activity=%s, specialization=%s,
                    notes=%s, status=%s
                WHERE id=%s
            """, values + [id])
            conn.commit()
            flash("تم تحديث بيانات الشركة بنجاح.", "success")
            return redirect("/companies")
        except mysql.connector.Error as exc:
            conn.rollback()
            flash(f"تعذر تحديث الشركة: {exc}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template("company_form.html", company=company, is_edit=True)


@app.route("/companies/delete/<int:id>", methods=["POST"])
def delete_company(id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM companies WHERE id=%s", (id,))
        conn.commit()
        flash("تم حذف الشركة.", "success")
    except mysql.connector.Error as exc:
        conn.rollback()
        flash(f"تعذر حذف الشركة: {exc}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect("/companies")


@app.route("/store_items")
def store_items_page():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT si.*, s.store_name, i.item_name_ar
        FROM store_items si
        LEFT JOIN stores s ON s.id = si.store_id
        LEFT JOIN items i ON i.id = si.item_id
        ORDER BY si.id DESC
    """)
    store_items = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "store_items.html",
        store_items=store_items
    )


@app.route("/store_items/add")
def add_store_item():
    if "user" not in session:
        return redirect("/")
    flash("الوظيفة غير متوفرة حالياً", "warning")
    return redirect("/store_items")


@app.route("/store_items/edit/<int:item_id>")
def edit_store_item(item_id):
    if "user" not in session:
        return redirect("/")
    flash("الوظيفة غير متوفرة حالياً", "warning")
    return redirect("/store_items")


@app.route("/store_items/delete/<int:item_id>")
def delete_store_item(item_id):
    if "user" not in session:
        return redirect("/")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM store_items WHERE id=%s", (item_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/store_items")


@app.route("/add-quotation/<int:req_id>", methods=["GET", "POST"])
def add_quotation(req_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM purchase_requisitions WHERE id=%s", (req_id,))
    req = cur.fetchone()

    if not req:
        cur.close()
        conn.close()
        flash("طلب الشراء غير موجود", "danger")
        return redirect("/requisitions")

    cur.execute("SELECT id, supplier_name FROM suppliers ORDER BY supplier_name")
    vendors = cur.fetchall()

    if request.method == "POST":
        vendor_id = request.form.get("vendor_id")
        price = float(request.form.get("price", 0) or 0)

        cur.execute("SELECT supplier_name FROM suppliers WHERE id=%s", (vendor_id,))
        vendor = cur.fetchone()
        supplier_name = vendor["supplier_name"] if vendor else None

        cur.execute("""
            INSERT INTO price_quotations
            (supplier_name, item_id, price, valid_until, notes, requisition_id, vendor_id, unit_price, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'pending')
        """, (
            supplier_name,
            req["item_id"],
            price,
            None,
            None,
            req_id,
            vendor_id,
            price
        ))
        conn.commit()
        cur.close()
        conn.close()
        flash("تم حفظ عرض السعر", "success")
        return redirect("/requisitions")

    cur.close()
    conn.close()

    return render_template(
        "add_quotation.html",
        req_id=req_id,
        vendors=vendors
    )


@app.route("/quotations/add")
def add_quotation_page():
    flash("يرجى اختيار طلب شراء لإضافة عرض السعر", "warning")
    return redirect("/requisitions")


@app.route("/quotation/order/<int:quote_id>")
def quotation_order(quote_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM price_quotations WHERE id=%s", (quote_id,))
    quote = cur.fetchone()
    if not quote:
        cur.close()
        conn.close()
        flash("عرض السعر غير موجود", "danger")
        return redirect("/purchase-orders")

    po_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    cur.execute("""
        INSERT INTO purchase_orders
        (po_number, vendor_id, order_date, expected_delivery_date, status, subtotal, tax_amount, total_amount, notes, created_by, requisition_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        po_number,
        quote["vendor_id"],
        datetime.now().date(),
        None,
        "draft",
        quote["price"],
        0,
        quote["price"],
        f"أمر شراء من عرض السعر {quote_id}",
        session.get("user"),
        quote["requisition_id"]
    ))
    order_id = cur.lastrowid

    cur.execute("""
        INSERT INTO purchase_order_items
        (purchase_order_id, item_id, quantity, unit_price, line_total, remarks)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        order_id,
        quote["item_id"],
        1,
        quote["price"],
        quote["price"],
        f"أمر شراء مبني على عرض السعر {quote_id}"
    ))

    cur.execute("UPDATE price_quotations SET status='accepted' WHERE id=%s", (quote_id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/purchase-orders")

# ======================
# أوامر الشراء
# ======================
@app.route("/purchase-orders")
def purchase_orders():

    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    department = request.args.get('department')
    department = normalize_department_key(department) if department else None

    query = """
        SELECT
            po.*,
            s.supplier_name AS supplier_name,
            IFNULL(
                (SELECT SUM(quantity) FROM purchase_order_items WHERE purchase_order_id=po.id),
                0
            ) AS total_quantity,
            IFNULL(
                (
                    SELECT GROUP_CONCAT(i.item_name_ar SEPARATOR ', ')
                    FROM purchase_order_items poi
                    JOIN items i ON i.id = poi.item_id
                    WHERE poi.purchase_order_id = po.id
                ),
                ''
            ) AS items_list
        FROM purchase_orders po
        LEFT JOIN suppliers s ON s.id = po.vendor_id
    """
    params = []
    if department:
        query += "WHERE EXISTS (SELECT 1 FROM purchase_order_items filter_poi JOIN items filter_i ON filter_i.id=filter_poi.item_id WHERE filter_poi.purchase_order_id=po.id AND filter_i.department=%s) "
        params.append(department)
    query += "ORDER BY po.id DESC"
    cur.execute(query, params)

    orders = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "purchase_orders.html",
        orders=orders,
        selected_department=department
    )
@app.route("/purchase-orders/add", methods=["GET", "POST"])
def add_purchase_order():

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":

        vendor_id = request.form["vendor_id"]
        order_date = request.form["order_date"]
        expected_delivery_date = request.form["expected_delivery_date"]
        notes = request.form["notes"]

        po_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cur.execute("""
            INSERT INTO purchase_orders
            (
                po_number,
                vendor_id,
                order_date,
                expected_delivery_date,
                status,
                subtotal,
                tax_amount,
                total_amount,
                notes
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            po_number,
            vendor_id,
            order_date,
            expected_delivery_date,
            "draft",
            0,
            0,
            0,
            notes
        ))

        conn.commit()

        order_id = cur.lastrowid

        cur.close()
        conn.close()

        return redirect(
            f"/purchase-orders/details/{order_id}"
        )

    cur.execute("""
        SELECT id, supplier_name AS vendor_name
        FROM suppliers
        ORDER BY supplier_name
    """)

    vendors = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "add_purchase_order.html",
        vendors=vendors
    )

@app.route("/create_order")
def create_order():

    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT id, supplier_name
        FROM suppliers
        ORDER BY supplier_name
    """)
    vendors = cur.fetchall()

    cur.execute("""
        SELECT id, item_name_ar
        FROM items
        ORDER BY item_name_ar
    """)
    items = cur.fetchall()

    # Get pending requisitions
    if has_column('purchase_requisitions', 'store_id'):
        cur.execute("""
            SELECT pr.id, pr.quantity, i.item_name_ar, i.id as item_id, pr.reason
            FROM purchase_requisitions pr
            LEFT JOIN items i ON pr.item_id = i.id
            WHERE pr.status = 'approved'
            ORDER BY pr.id DESC
        """)
    else:
        cur.execute("""
            SELECT pr.id, pr.quantity, i.item_name_ar, i.id as item_id, pr.reason
            FROM purchase_requisitions pr
            LEFT JOIN items i ON pr.item_id = i.id
            WHERE pr.status = 'approved'
            ORDER BY pr.id DESC
        """)
    
    requisitions = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "create_purchase_order.html",
        vendors=vendors,
        items=items,
        requisitions=requisitions
    )

@app.route("/save_purchase_order", methods=["POST"])
def save_purchase_order():
    if "user" not in session:
        return redirect("/")

    vendor_id = request.form.get("vendor_id", "").strip()
    item_id = request.form.get("item_id", "").strip()
    quantity_str = request.form.get("quantity", "").strip()
    unit_price_str = request.form.get("unit_price", "0").strip()
    order_date = request.form.get("order_date", "").strip()
    requisition_id = request.form.get("requisition_id", "").strip()

    # Validate required fields
    if not vendor_id:
        flash("يرجى اختيار المورد", "danger")
        return redirect("/create_order")
    
    if not item_id:
        flash("يرجى اختيار الصنف", "danger")
        return redirect("/create_order")
    
    if not quantity_str:
        flash("يرجى إدخال الكمية", "danger")
        return redirect("/create_order")
    
    if not order_date:
        flash("يرجى اختيار تاريخ الطلب", "danger")
        return redirect("/create_order")

    # Convert to appropriate types
    try:
        quantity = float(quantity_str)
        unit_price = float(unit_price_str) if unit_price_str else 0
    except ValueError:
        flash("يرجى إدخال قيم رقمية صحيحة للكمية والسعر", "danger")
        return redirect("/create_order")

    if quantity <= 0:
        flash("الكمية يجب أن تكون أكبر من صفر", "danger")
        return redirect("/create_order")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Get user ID from username
    user_name = session.get("user")
    cur.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (user_name,))
    user_result = cur.fetchone()
    user_id = user_result['id'] if user_result else 1
    
    # Get default warehouse_id
    cur.execute("SELECT id FROM warehouses LIMIT 1")
    warehouse_result = cur.fetchone()
    warehouse_id = warehouse_result['id'] if warehouse_result else 1
    
    cur.close()

    cur = conn.cursor()

    try:
        po_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Insert into purchase_orders
        cur.execute("""
            INSERT INTO purchase_orders
            (
                po_number,
                vendor_id,
                order_date,
                expected_delivery_date,
                status,
                subtotal,
                tax_amount,
                total_amount,
                notes,
                created_by,
                requisition_id
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            po_number,
            int(vendor_id),
            order_date,
            None,
            "draft",
            quantity * unit_price,
            0,
            quantity * unit_price,
            None,
            user_id,
            int(requisition_id) if requisition_id else None
        ))

        order_id = cur.lastrowid

        # Insert purchase order items
        cur.execute("""
            INSERT INTO purchase_order_items
            (
                purchase_order_id,
                item_id,
                quantity,
                unit_price,
                line_total,
                remarks
            )
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            order_id,
            int(item_id),
            quantity,
            unit_price,
            quantity * unit_price,
            None
        ))

        # Update current_balance in items table (stock-in operation)
        cur.execute("""
            UPDATE items
            SET current_balance = current_balance + %s,
                current_stock = current_stock + %s
            WHERE id = %s
        """, (
            quantity,
            quantity,
            int(item_id)
        ))

        # Insert into stock_transactions for record keeping
        cur.execute("""
            INSERT INTO stock_transactions
            (item_id, warehouse_id, transaction_type, qty, reference_no, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            int(item_id),
            warehouse_id,
            "IN",
            quantity,
            po_number,
            f"تم الشراء من خلال أمر الشراء"
        ))

        conn.commit()
        flash(f"تم حفظ أمر الشراء بنجاح (رقم الأمر: {po_number}) وتحديث الرصيد", "success")
        return redirect(f"/purchase-orders/details/{order_id}")

    except Exception as e:
        conn.rollback()
        flash(f"خطأ أثناء حفظ أمر الشراء: {str(e)}", "danger")
        import traceback
        traceback.print_exc()
        return redirect("/create_order")

    finally:
        cur.close()
        conn.close()


@app.route(
    "/purchase-orders/details/<int:order_id>",
    methods=["GET", "POST"]
)
def view_purchase_order(order_id):

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":

        item_id = request.form["item_id"]
        quantity = float(request.form["quantity"])
        unit_price = float(request.form["unit_price"])
        remarks = request.form.get("remarks", "")

        line_total = quantity * unit_price

        cur.execute("""
            INSERT INTO purchase_order_items
            (
                purchase_order_id,
                item_id,
                quantity,
                unit_price,
                line_total,
                remarks
            )
            VALUES
            (%s,%s,%s,%s,%s,%s)
        """, (
            order_id,
            item_id,
            quantity,
            unit_price,
            line_total,
            remarks
        ))

        cur.execute("""
            UPDATE purchase_orders
            SET subtotal =
            (
                SELECT IFNULL(SUM(line_total),0)
                FROM purchase_order_items
                WHERE purchase_order_id=%s
            ),
            total_amount =
            (
                SELECT IFNULL(SUM(line_total),0)
                FROM purchase_order_items
                WHERE purchase_order_id=%s
            )
            WHERE id=%s
        """, (
            order_id,
            order_id,
            order_id
        ))

        conn.commit()

    cur.execute("""
        SELECT po.*, s.supplier_name AS supplier_name
        FROM purchase_orders po
        LEFT JOIN suppliers s ON s.id = po.vendor_id
        WHERE po.id=%s
    """, (order_id,))

    order = cur.fetchone()

    cur.execute("""
        SELECT id,item_name_ar
        FROM items
        ORDER BY item_name_ar
    """)

    items = cur.fetchall()

    cur.execute("""
        SELECT
            poi.*,
            i.item_name_ar
        FROM purchase_order_items poi
        JOIN items i
            ON i.id = poi.item_id
        WHERE poi.purchase_order_id=%s
    """, (order_id,))

    order_items = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "purchase_order_detail.html",
        order=order,
        items=items,
        order_items=order_items
    )

@app.route("/purchase-orders/approve/<int:order_id>", methods=["POST"])
def approve_purchase_order(order_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "UPDATE purchase_orders SET status='approved', approved_at=NOW() WHERE id=%s",
            (order_id,)
        )
        conn.commit()
        flash("تم اعتماد أمر الشراء", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()

    return redirect("/purchase-orders")


@app.route("/purchase-orders/delete/<int:order_id>", methods=["POST"])
def delete_purchase_order(order_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("SELECT id, po_number FROM purchase_orders WHERE id=%s LIMIT 1", (order_id,))
        order = cur.fetchone()
        if not order:
            flash("أمر الشراء غير موجود.", "danger")
            return redirect("/purchase-orders")

        cur.execute("DELETE FROM purchase_orders WHERE id=%s", (order_id,))
        conn.commit()
        flash(f"تم حذف أمر الشراء {order['po_number']} بنجاح.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"تعذّر حذف أمر الشراء: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect("/purchase-orders")

# ======================
# إدارة أذونات الصرف (Blueprint)
# ======================
issue_vouchers_bp = Blueprint(
    "issue_vouchers",
    __name__
)

# ==========================
# قائمة أذونات الصرف
# ==========================

@issue_vouchers_bp.route('/issue-vouchers')
def issue_vouchers(department=None):

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    department = department or request.args.get('department')
    if department:
        cur.execute(
            "SELECT * FROM issue_vouchers WHERE department=%s ORDER BY id DESC",
            (department,)
        )
    else:
        cur.execute("SELECT * FROM issue_vouchers ORDER BY id DESC")

    vouchers = cur.fetchall()

    cur.close()
    conn.close()


    # Build grouped_vouchers structure expected by the template
    grouped_vouchers = {}

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    for v in vouchers or []:
        vid = v["id"]

        cur.execute("""
            SELECT GROUP_CONCAT(i.item_name_ar SEPARATOR ', ') AS items_list
            FROM issue_voucher_items iv
            LEFT JOIN items i ON i.id = iv.item_id
            WHERE iv.voucher_id=%s
        """, (vid,))

        row = cur.fetchone()
        items_list = row["items_list"] if row else ""

        v["items_list"] = items_list

        dept = v.get("department") or "عام"

        if dept not in grouped_vouchers:
            grouped_vouchers[dept] = []

        grouped_vouchers[dept].append(v)

    cur.close()
    conn.close()

    return render_template(
        "issue_vouchers.html",
        grouped_vouchers=grouped_vouchers,
        selected_department=department
    )


@app.route('/local-purchases/issue-vouchers')
def local_purchase_issue_vouchers():
    return issue_vouchers(department='local_purchases')


# ==========================
# إضافة إذن صرف
# ==========================
def add_issue_voucher():

    if "user" not in session:
        return redirect("/")

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":

        try:

            voucher_no = request.form["voucher_no"]
            issue_date = request.form["issue_date"]
            department = request.form["department"]
            receiver_name = request.form["receiver_name"]
            notes = request.form.get("notes", "")

            cur.execute("""
                INSERT INTO issue_vouchers
                (
                    voucher_no,
                    issue_date,
                    department,
                    receiver_name,
                    notes,
                    created_by
                )
                VALUES
                (%s,%s,%s,%s,%s,%s)
            """, (
                voucher_no,
                issue_date,
                department,
                receiver_name,
                notes,
                session["user"]
            ))

            voucher_id = cur.lastrowid

            item_ids = request.form.getlist("item_id[]")
            qtys = request.form.getlist("qty[]")
            prices = request.form.getlist("unit_price[]")

            for item_id, qty, price in zip(
                item_ids,
                qtys,
                prices
            ):

                if not item_id:
                    continue

                qty = float(qty or 0)
                price = float(price or 0)

                cur.execute("""
                    INSERT INTO issue_voucher_items
                    (
                        voucher_id,
                        item_id,
                        qty,
                        unit_price,
                        total
                    )
                    VALUES
                    (%s,%s,%s,%s,%s)
                """, (
                    voucher_id,
                    item_id,
                    qty,
                    price,
                    qty * price
                ))

            # immediately deduct from stock_movements (create OUT movement)
            try:
                cur.execute("""
                    INSERT INTO stock_movements
                    (item_id, warehouse_id, movement_type, qty, reference_type, reference_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    item_id,
                    1,                # default warehouse id, adjust as needed
                    'OUT',
                    qty,
                    'ISSUE_VOUCHER',
                    voucher_id
                ))
            except Exception as e:
                # log and continue; rollback handled at outer exception
                print('Stock movement insert failed:', e)

            conn.commit()

            flash(
            "تم إنشاء إذن الصرف وتنفيذ الخصم من المخزون",
            "success"
            )

            return redirect("/issue-vouchers")

        except Exception as e:

            conn.rollback()

            flash(
                str(e),
                "danger"
            )

    cur.execute("""
        SELECT
            id,
            item_name_ar
        FROM items
        ORDER BY item_name_ar
    """)

    items = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "add_issue_voucher.html",
        items=items
    )


# ==========================
# عرض إذن صرف
# ==========================

@issue_vouchers_bp.route(
    '/issue-vouchers/view/<int:voucher_id>'
)
def view_issue_voucher(voucher_id):

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM issue_vouchers
        WHERE id=%s
    """, (voucher_id,))

    voucher = cur.fetchone()

    cur.execute("""
        SELECT
            d.*,
            i.item_name_ar AS item_name
        FROM issue_voucher_items d
        LEFT JOIN items i
            ON i.id=d.item_id
        WHERE d.voucher_id=%s
    """, (voucher_id,))

    items = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "issue_vouchersapprove.html",
        voucher=voucher,
        items=items
    )


# ==========================
# اعتماد إذن الصرف
# ==========================

@issue_vouchers_bp.route(
    '/issue-vouchers/approve/<int:voucher_id>',
    methods=['POST']
)
@issue_vouchers_bp.route(
    '/issue-vouchers/<int:voucher_id>/approve',
    methods=['POST']
)
def approve_issue_voucher(voucher_id):

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    try:

        cur.execute("""
            SELECT *
            FROM issue_vouchers
            WHERE id=%s
        """, (voucher_id,))

        voucher = cur.fetchone()

        if not voucher:

            flash(
                "الإذن غير موجود",
                "danger"
            )

            return redirect(
                "/issue-vouchers"
            )

        if voucher["status"] == "approved":

            flash(
                "تم الاعتماد مسبقاً",
                "warning"
            )

            return redirect(
                "/issue-vouchers"
            )

        cur.execute("""
            SELECT *
            FROM issue_voucher_items
            WHERE voucher_id=%s
        """, (voucher_id,))

        details = cur.fetchall()

        for row in details:

            cur.execute("""
                INSERT INTO stock_movements
                (
                    item_id,
                    warehouse_id,
                    movement_type,
                    qty,
                    reference_type,
                    reference_id
                )
                VALUES
                (
                    %s,
                    1,
                    'OUT',
                    %s,
                    'ISSUE_VOUCHER',
                    %s
                )
            """, (
                row["item_id"],
                row["qty"],
                voucher_id
            ))

        cur.execute("""
            UPDATE issue_vouchers
            SET
                status='approved',
                approved_at=NOW()
            WHERE id=%s
        """, (voucher_id,))

        conn.commit()

        flash(
            "تم اعتماد إذن الصرف",
            "success"
        )

    except Exception as e:

        conn.rollback()

        flash(
            str(e),
            "danger"
        )

    finally:

        cur.close()
        conn.close()

    return redirect(
        "/issue-vouchers"
    )


# ==========================
# إلغاء إذن الصرف
# ==========================

@issue_vouchers_bp.route(
    '/issue-vouchers/cancel/<int:voucher_id>'
)
def cancel_issue_voucher(voucher_id):

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()

    cur.execute("""
        UPDATE issue_vouchers
        SET status='cancelled'
        WHERE id=%s
    """, (voucher_id,))

    conn.commit()

    cur.close()
    conn.close()

    flash(
        "تم إلغاء الإذن",
        "warning"
    )

    return redirect(
        "/issue-vouchers"
    )


# ==========================
# حذف إذن الصرف
# ==========================

@issue_vouchers_bp.route(
    '/issue-vouchers/delete/<int:voucher_id>'
)
def delete_issue_voucher(voucher_id):

    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM issue_voucher_items WHERE voucher_id=%s",
        (voucher_id,)
    )

    cur.execute(
        "DELETE FROM issue_vouchers WHERE id=%s",
        (voucher_id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    flash(
        "تم حذف الإذن",
        "success"
    )

    return redirect(
        "/issue-vouchers"
    )

@app.route('/customs-management')
def customs_management():

    if "user" not in session:
        return redirect("/")

    try:
        ensure_customs_clearance_columns()
        ensure_customs_status_enum()
    except Exception:
        pass

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
                SELECT
                    cd.id,
                    cd.declaration_no,
                    cd.declaration_date,
                    cd.importer_name,
                    cd.destination_country,
                    cd.regime_type,
                    cd.port_of_loading,
                    cd.port_of_destination,
                    cd.port_of_discharge,
                    cd.total_weight,
                    cd.package_count,
                    cd.currency,
                    cd.tax_card_number,
                    cd.commercial_register_number,
                    cd.status,
                    cd.approval_date,
                    cd.total_value,
                    cd.customs_fee,
                    (
                        SELECT COALESCE(SUM(ci.quantity * ci.unit_price), 0)
                        FROM customs_items ci
                        WHERE ci.declaration_id = cd.id
                    ) AS total_amount
                FROM customs_declarations cd
                ORDER BY cd.created_at DESC
            """
        )
        customs_items = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        flash(str(e), 'danger')
        customs_items = []

    return render_template(
        "customs_management.html",
        customs_items=customs_items
    )


@app.route('/customs-management/demo-seed', methods=['POST'])
def customs_management_demo_seed():
    if "user" not in session:
        return redirect("/")

    try:
        seed_demo_customs_data()
        flash('تم إنشاء وارد تجريبي بنجاح.', 'success')
    except Exception as e:
        flash(str(e), 'danger')

    return redirect('/customs-management')


def render_free_zone_section(title, subtitle, inbound_type=None, status=None):
    customs_items = []
    if inbound_type or status:
        ensure_customs_declaration_columns()
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        try:
            filters = []
            params = []
            if inbound_type:
                filters.append("inbound_type = %s")
                params.append(inbound_type)
            if status:
                filters.append("status = %s")
                params.append(status)
            cur.execute(
                f"""
                SELECT
                    id,
                    declaration_no,
                    acid,
                    declaration_date,
                    inbound_type,
                    importer_name,
                    exporter_name,
                    origin_country,
                    destination_country,
                    regime_type,
                    regime_details,
                    port_of_discharge,
                    total_weight,
                    package_count,
                    currency,
                    tax_card_number,
                    commercial_register_number,
                    clearance_officer_name,
                    clearance_officer_location,
                    clearance_officer_phone,
                    status,
                    total_value,
                    customs_fee,
                    notes,
                    created_at
                FROM customs_declarations
                WHERE {' AND '.join(filters)}
                ORDER BY created_at DESC
                """,
                params
            )
            customs_items = cur.fetchall() or []
        finally:
            cur.close()
            conn.close()

    return render_template(
        "customs_free_zone.html",
        title=title,
        subtitle=subtitle,
        customs_items=customs_items,
        inbound_type=inbound_type
    )


@app.route('/customs-management/free-zone')
def customs_free_zone():
    if "user" not in session:
        return redirect("/")
    return redirect('/customs-management')


@app.route('/customs-management/free-zone/receiving-foreign-shipments')
def customs_free_zone_receiving_foreign_shipments():
    if "user" not in session:
        return redirect("/")
    return render_free_zone_section("استلامات الشحنات الخارجية", "إدارة استلام الشحنات القادمة من الخارج", "external")


@app.route('/customs-management/free-zone/local-shipments')
def customs_free_zone_local_shipments():
    if "user" not in session:
        return redirect("/")
    return render_free_zone_section("الشحنات المحلية", "إدارة الشحنات المحلية داخل المنطقة", "local_market")


@app.route('/customs-management/free-zone/trade-inside-zone')
def customs_free_zone_trade_inside_zone():
    if "user" not in session:
        return redirect("/")
    return render_free_zone_section("الشحنات التداول داخل المنطقة", "إدارة حركة التداول داخل المنطقة الحرة", "within_zone")


@app.route('/customs-management/free-zone/trade-between-zones')
def customs_free_zone_trade_between_zones():
    if "user" not in session:
        return redirect("/")
    return render_free_zone_section("الشحنات التداول بين المناطق", "إدارة الحركة التجارية بين المناطق المختلفة", "between_regions")


@app.route('/customs-management/free-zone/entry-of-detained')
def customs_free_zone_entry_of_detained():
    if "user" not in session:
        return redirect("/")
    return render_free_zone_section("دخول الموقوفات", "إدارة دخول الموقوفات داخل المنطقة الحرة", "stopped_entry")


@app.route('/customs-management/inventory-branch')
def customs_inventory_branch():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT
                i.id,
                i.item_code,
                i.item_name_ar,
                i.item_name_en,
                i.category_id,
                i.current_stock,
                i.qty,
                i.min_qty,
                i.price,
                u.unit_name,
                c.category_name_ar,
                c.category_name_en
            FROM items i
            LEFT JOIN units u ON u.id = i.unit_id
            LEFT JOIN categories c ON c.id = i.category_id
            ORDER BY i.item_name_ar ASC
        """)
        items = cur.fetchall() or []
    finally:
        cur.close()
        conn.close()

    return render_template(
        "customs_inventory_branch.html",
        title="قائمة الجرد",
        subtitle="إدارة قائمة الجرد داخل إدارة الجمارك",
        items=items
    )


@app.route('/customs-management/inventory-branch/movements')
def customs_inventory_movements():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT
                st.id,
                st.item_id,
                st.transaction_type,
                st.qty,
                st.reference_no,
                st.notes,
                st.created_at,
                i.item_code,
                i.item_name_ar,
                i.item_name_en,
                u.unit_name
            FROM stock_transactions st
            LEFT JOIN items i ON i.id = st.item_id
            LEFT JOIN units u ON u.id = i.unit_id
            ORDER BY st.created_at DESC
            LIMIT 200
        """)
        movements = cur.fetchall() or []
    finally:
        cur.close()
        conn.close()

    return render_template(
        "customs_stock_movements.html",
        title="حركات المخزون",
        subtitle="تتبع جميع الحركات المتعلقة بالأصناف والاعتمادات الجمركية",
        movements=movements
    )


@app.route('/customs-management/total-imports-branch')
def customs_total_imports_branch():
    if "user" not in session:
        return redirect("/")
    return render_free_zone_section(
        "قائمة إجمالي الواردات",
        "الواردات التي تم اعتمادها وإضافتها إلى المخزون",
        status="completed"
    )


# -----------------------------
# Invoices list and view
# -----------------------------

@app.route('/customs-management/invoices')
def customs_invoices_list():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, invoice_no, invoice_type, invoice_date, party, total_amount, created_at FROM customs_invoices ORDER BY created_at DESC")
    invoices = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('customs_invoices_list.html', invoices=invoices)


@app.route('/customs-management/invoice/<int:invoice_id>')
def customs_invoice_view(invoice_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customs_invoices WHERE id=%s", (invoice_id,))
    inv = cur.fetchone()
    if not inv:
        cur.close()
        conn.close()
        flash('الفاتورة غير موجودة', 'warning')
        return redirect('/customs-management/invoices')

    cur.execute("SELECT ci.*, i.item_name_ar, u.unit_name FROM customs_invoice_items ci LEFT JOIN items i ON ci.item_id = i.id LEFT JOIN units u ON ci.unit_id = u.id WHERE ci.invoice_id=%s", (invoice_id,))
    items = cur.fetchall() or []

    cur.close()
    conn.close()
    return render_template('customs_invoice_view.html', invoice=inv, items=items)


@app.route('/customs-management/invoice/<int:invoice_id>/print')
def customs_invoice_print(invoice_id):
    if "user" not in session:
        return redirect("/")
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customs_invoices WHERE id=%s", (invoice_id,))
    inv = cur.fetchone()
    if not inv:
        cur.close()
        conn.close()
        flash('الفاتورة غير موجودة', 'warning')
        return redirect('/customs-management/invoices')

    cur.execute("SELECT ci.*, i.item_name_ar, u.unit_name FROM customs_invoice_items ci LEFT JOIN items i ON ci.item_id = i.id LEFT JOIN units u ON ci.unit_id = u.id WHERE ci.invoice_id=%s", (invoice_id,))
    items = cur.fetchall() or []

    cur.close()
    conn.close()
    return render_template('customs_invoice_print.html', invoice=inv, items=items)


# Print declaration (customs/inbound)
@app.route('/customs-management/view/<int:declaration_id>/print')
def customs_declaration_print(declaration_id):
    if "user" not in session:
        return redirect("/")
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customs_declarations WHERE id = %s", (declaration_id,))
    decl = cur.fetchone()
    if not decl:
        cur.close()
        conn.close()
        flash('البيان غير موجود', 'warning')
        return redirect('/customs-management')

    # fetch items
    cur.execute("SELECT ci.*, i.item_name_ar, u.unit_name FROM customs_items ci LEFT JOIN items i ON ci.item_id = i.id LEFT JOIN units u ON ci.unit_id = u.id WHERE ci.declaration_id=%s", (declaration_id,))
    items = cur.fetchall() or []
    cur.close()
    conn.close()
    return render_template('customs_declaration_print.html', customs_item=decl, items=items)

def get_inbound_type_redirect(inbound_type):
    mapping = {
        'external': '/customs-management/free-zone/receiving-foreign-shipments',
        'local_market': '/customs-management/free-zone/local-shipments',
        'within_zone': '/customs-management/free-zone/trade-inside-zone',
        'between_regions': '/customs-management/free-zone/trade-between-zones',
        'stopped_entry': '/customs-management/free-zone/entry-of-detained',
    }
    return mapping.get(inbound_type, '/customs-management')


def get_customs_purchase_departments(inbound_type=None):
    if inbound_type == 'local_market':
        return ['local_purchases']
    if inbound_type in {'external', 'within_zone', 'between_regions', 'stopped_entry'}:
        return ['external_purchases']
    return ['local_purchases', 'external_purchases']


def seed_demo_customs_data():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM customs_declarations WHERE declaration_no = %s LIMIT 1", ('CUS-DEMO-1001',))
        existing = cur.fetchone()
        if existing:
            return existing['id']

        cur.execute("SELECT id FROM units ORDER BY id LIMIT 1")
        unit = cur.fetchone()
        if not unit:
            cur.execute("INSERT INTO units (unit_name, unit_code) VALUES (%s, %s)", ('علبة', 'BOX'))
            conn.commit()
            unit_id = cur.lastrowid
        else:
            unit_id = unit['id']

        cur.execute("SELECT id FROM items ORDER BY id LIMIT 1")
        item = cur.fetchone()
        if not item:
            cur.execute(
                "INSERT INTO items (item_name_ar, item_name_en, unit_id, current_stock, min_stock) VALUES (%s, %s, %s, %s, %s)",
                ('ماء معدني', 'Mineral Water', unit_id, 100, 10)
            )
            conn.commit()
            item_id = cur.lastrowid
        else:
            item_id = item['id']

        username = session.get('user') or 'admin'
        cur.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (username,))
        user = cur.fetchone()
        if not user:
            cur.execute(
                "SELECT id FROM users ORDER BY id LIMIT 1"
            )
            user = cur.fetchone()
        user_id = user['id'] if user else 1

        declaration_date = datetime.now().strftime('%Y-%m-%d')
        approval_date = datetime.now().strftime('%Y-%m-%d')
        now_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cur.execute(
            """
            INSERT INTO customs_declarations (
                declaration_no, declaration_date, inbound_type, importer_name, exporter_name,
                origin_country, destination_country, regime_type, regime_details,
                port_of_loading, port_of_destination, port_of_discharge, shipment_reference,
                acid, total_weight, package_count, currency, tax_card_number,
                commercial_register_number, clearance_officer_name, clearance_officer_location,
                clearance_officer_phone, approval_date, entry_date, shipment_received_at,
                distribution_time, total_value, customs_fee, status, notes, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                'CUS-DEMO-1001', declaration_date, 'external', 'شركة التجربة', 'مصدر تجريبي',
                'تركيا', 'مصر', 'import', 'ميناء', 'ميناء الإسكندرية', 'ميناء بورسعيد',
                'ميناء الأسكندرية', 'REF-DEMO-001', 'ACID-DEMO-1001', 125.50, 12,
                'USD', 'TAX-1001', 'CR-2001', 'أحمد محمد', 'المنطقة الحرة', '01000000000',
                approval_date, declaration_date, now_dt, now_dt, 2500.00, 180.00,
                'completed', 'وارد تجريبي تم إنشاؤه تلقائياً للاختبار', user_id
            )
        )
        declaration_id = cur.lastrowid

        cur.execute(
            "INSERT INTO customs_items (declaration_id, item_id, quantity, unit_price, serial_number, origin_country, unit_id, description) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (declaration_id, item_id, 10, 200.00, 'SER-DEMO-001', 'تركيا', unit_id, 'مياه معدنية')
        )

        conn.commit()
        return declaration_id
    finally:
        cur.close()
        conn.close()


def ensure_customs_declaration_columns():
    try:
        columns = {
            'inbound_type': 'VARCHAR(100) NULL',
            'exporter_name': 'VARCHAR(255) NULL',
            'origin_country': 'VARCHAR(100) NULL',
            'regime_type': 'VARCHAR(100) NULL',
            'regime_details': 'TEXT NULL',
            'port_of_loading': 'VARCHAR(255) NULL',
            'port_of_destination': 'VARCHAR(255) NULL',
            'port_of_discharge': 'VARCHAR(255) NULL',
            'shipment_reference': 'VARCHAR(100) NULL',
            'acid': 'VARCHAR(100) NULL',
            'total_weight': 'DECIMAL(18,2) NULL',
            'package_count': 'INT NULL',
            'currency': 'VARCHAR(20) NULL',
            'tax_card_number': 'VARCHAR(100) NULL',
            'commercial_register_number': 'VARCHAR(100) NULL',
            'clearance_officer_name': 'VARCHAR(255) NULL',
            'clearance_officer_location': 'VARCHAR(255) NULL',
            'clearance_officer_phone': 'VARCHAR(50) NULL',
            'approval_date': 'DATE NULL',
            'entry_date': 'DATE NULL',
            'shipment_received_at': 'DATETIME NULL',
            'distribution_time': 'DATETIME NULL',
            'notes': 'TEXT NULL',
        }
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            for column_name, column_def in columns.items():
                cur.execute(
                    "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=%s AND table_name='customs_declarations' AND column_name=%s",
                    (db_config['database'], column_name)
                )
                if cur.fetchone()[0] == 0:
                    cur.execute(f"ALTER TABLE customs_declarations ADD COLUMN {column_name} {column_def}")
            conn.commit()
        finally:
            cur.close()
            conn.close()
    except Exception as exc:
        print(f"Database warning/error: {exc}")
        pass


def ensure_customs_clearance_columns():
    ensure_customs_declaration_columns()


@app.before_request
def ensure_customs_schema_before_request():
    if request.path.startswith('/customs-management'):
        ensure_customs_declaration_columns()
        ensure_customs_status_enum()


def ensure_customs_status_enum():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COLUMN_TYPE FROM information_schema.columns WHERE table_schema=%s AND table_name='customs_declarations' AND column_name='status'", (db_config['database'],))
            row = cur.fetchone()
            if not row:
                return
            col_type = row[0].upper()
            required_values = ['DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'CLEARED', 'PENDING', 'PROCESSING', 'COMPLETED']
            if not all(value in col_type for value in required_values):
                cur.execute("ALTER TABLE customs_declarations MODIFY COLUMN status ENUM('draft','submitted','under_review','approved','rejected','cleared','pending','processing','completed') NOT NULL DEFAULT 'pending'")
                conn.commit()
        finally:
            cur.close()
            conn.close()
    except Exception as exc:
        print(f"Database warning/error: {exc}")
        pass


    ensure_customs_declaration_columns()
    ensure_customs_status_enum()


@app.route('/customs-management/new', methods=['GET', 'POST'])
def customs_new_entry():
    return customs_new_inbound()


def customs_new_inbound():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        declaration_no = request.form.get('declaration_no', '').strip()
        declaration_date = request.form.get('declaration_date', '').strip()
        inbound_type = request.form.get('inbound_type', '').strip()
        importer_name = request.form.get('importer_name', '').strip()
        exporter_name = request.form.get('exporter_name', '').strip()
        origin_country = request.form.get('origin_country', '').strip()
        destination_country = request.form.get('destination_country', '').strip()
        regime_type = request.form.get('regime_type', '').strip()
        regime_details = request.form.get('regime_details', '').strip()
        port_of_loading = request.form.get('port_of_loading', '').strip()
        port_of_destination = request.form.get('port_of_destination', '').strip()
        port_of_discharge = request.form.get('port_of_discharge', '').strip()
        shipment_reference = request.form.get('shipment_reference', '').strip()
        acid = request.form.get('acid', '').strip()
        total_weight = float(request.form.get('total_weight', 0) or 0)
        package_count = int(request.form.get('package_count', 0) or 0)
        currency = request.form.get('currency', '').strip()
        tax_card_number = request.form.get('tax_card_number', '').strip()
        commercial_register_number = request.form.get('commercial_register_number', '').strip()
        clearance_officer_name = request.form.get('clearance_officer_name', '').strip()
        clearance_officer_location = request.form.get('clearance_officer_location', '').strip()
        clearance_officer_phone = request.form.get('clearance_officer_phone', '').strip()
        approval_date = request.form.get('approval_date', '').strip() or None
        entry_date = request.form.get('entry_date', '').strip() or None
        shipment_received_at = request.form.get('shipment_received_at', '').strip() or None
        distribution_time = request.form.get('distribution_time', '').strip() or None
        total_value = float(request.form.get('total_value', 0) or 0)
        customs_fee = float(request.form.get('customs_fee', 0) or 0)
        notes = request.form.get('notes', '').strip()
        status = request.form.get('status', 'pending').strip() or 'pending'

        try:
            ensure_customs_clearance_columns()
            ensure_customs_status_enum()
            created_by = get_current_user_id(conn)

            cur.execute("""
                INSERT INTO customs_declarations
                (
                    declaration_no,
                    declaration_date,
                    inbound_type,
                    importer_name,
                    exporter_name,
                    origin_country,
                    destination_country,
                    regime_type,
                    regime_details,
                    port_of_loading,
                    port_of_destination,
                    port_of_discharge,
                    shipment_reference,
                    acid,
                    total_weight,
                    package_count,
                    currency,
                    tax_card_number,
                    commercial_register_number,
                    clearance_officer_name,
                    clearance_officer_location,
                    clearance_officer_phone,
                    approval_date,
                    entry_date,
                    shipment_received_at,
                    distribution_time,
                    total_value,
                    customs_fee,
                    status,
                    notes,
                    created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                declaration_no,
                declaration_date,
                inbound_type,
                importer_name,
                exporter_name,
                origin_country,
                destination_country,
                regime_type,
                regime_details,
                port_of_loading,
                port_of_destination,
                port_of_discharge,
                shipment_reference,
                acid,
                total_weight,
                package_count,
                currency,
                tax_card_number,
                commercial_register_number,
                clearance_officer_name,
                clearance_officer_location,
                clearance_officer_phone,
                approval_date,
                entry_date,
                shipment_received_at,
                distribution_time,
                total_value,
                customs_fee,
                status,
                notes,
                created_by
            ))

            declaration_id = cur.lastrowid

            # Handle line items (arrays)
            item_ids = request.form.getlist('item_id[]')
            serials = request.form.getlist('serial_number[]')
            unit_prices = request.form.getlist('unit_price[]')
            origins = request.form.getlist('origin[]')
            quantities = request.form.getlist('qty[]')
            unit_ids = request.form.getlist('unit_id[]')
            descriptions = request.form.getlist('description[]')

            for item_id, serial, up, origin, qty, unit_id, desc in zip(item_ids, serials, unit_prices, origins, quantities, unit_ids, descriptions):
                if not (item_id or desc):
                    continue
                try:
                    qty_val = float(qty or 0)
                except ValueError:
                    qty_val = 0
                try:
                    up_val = float(up or 0)
                except ValueError:
                    up_val = 0

                cur.execute("""
                    INSERT INTO customs_items
                    (declaration_id, item_id, quantity, unit_price, serial_number, origin_country, unit_id, description)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    declaration_id,
                    item_id or None,
                    qty_val,
                    up_val,
                    serial or None,
                    origin or None,
                    unit_id or None,
                    desc or None
                ))

            conn.commit()
            flash("تم إضافة سجل جمركي جديد", "success")
            redirect_target = get_inbound_type_redirect(inbound_type)
            return redirect(redirect_target)
        except Exception as e:
            conn.rollback()
            flash(str(e), "danger")

    # load items and units for the items section
    inbound_type = request.form.get('inbound_type') or request.args.get('inbound_type') or None
    department_list = get_customs_purchase_departments(inbound_type)
    if len(department_list) == 1:
        cur.execute("SELECT id, item_name_ar FROM items WHERE department = %s ORDER BY item_name_ar", (department_list[0],))
    else:
        cur.execute("SELECT id, item_name_ar FROM items WHERE department IN (%s, %s) ORDER BY item_name_ar", (department_list[0], department_list[1]))
    items_list = cur.fetchall()
    cur.execute("SELECT id, unit_name FROM units ORDER BY unit_name")
    units_list = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "customs_management_form.html",
        title="إضافة وارد جديد",
        subtitle="أنشئ سجل وارد جديد مع جميع البيانات الأساسية.",
        customs_item=None,
        submit_label="حفظ",
        items_list=items_list,
        units_list=units_list,
        declaration_items=[]
    )


@app.route('/customs-management/urgent-release', methods=['GET', 'POST'])
def customs_urgent_release():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            declaration_id = request.form.get('declaration_id', '').strip()
            voucher_no = request.form.get('voucher_no', '').strip()
            reference_no = request.form.get('reference_no', '').strip() or None
            service_type = request.form.get('service_type', '').strip()
            rental_company_id = request.form.get('rental_company_id', '').strip() or None
            issue_date = request.form.get('issue_date', '').strip() or datetime.now().date().isoformat()
            recipient_company = request.form.get('recipient_company', '').strip()
            recipient_name = request.form.get('recipient_name', '').strip()
            item_ids = request.form.getlist('item_id[]')
            customs_item_ids = request.form.getlist('customs_item_id[]')
            quantities = request.form.getlist('qty[]')
            unit_prices = request.form.getlist('unit_price[]')
            notes = request.form.getlist('notes[]')

            if not declaration_id:
                raise ValueError('اختر الوارد المراد تنفيذ الإفراج العاجل عليه.')
            if not recipient_company:
                raise ValueError('اكتب اسم الشركة المنصرف إليها.')
            if service_type not in {'rental', 'final_sale', 'service'}:
                raise ValueError('اختر نوع الخدمة.')
            if service_type == 'rental' and not rental_company_id:
                raise ValueError('اختر شركة التأجير.')
            if not customs_item_ids or not quantities:
                raise ValueError('اختر بندًا واحدًا على الأقل وحدد كمية الصرف.')

            cur.execute(
                "SELECT id, declaration_no, acid FROM customs_declarations WHERE id=%s FOR UPDATE",
                (declaration_id,)
            )
            declaration = cur.fetchone()
            if not declaration:
                raise ValueError('الوارد المحدد غير موجود.')

            if not voucher_no:
                voucher_no = f"URG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            reference = f"URGENT_RELEASE-{declaration['id']}"
            declaration_reference = declaration['acid'] or declaration['declaration_no']
            voucher_notes = (
                f"صرف مؤقت للإفراج العاجل للوارد {declaration['declaration_no']}"
                f" ({declaration_reference}) | الشركة المنصرف إليها: {recipient_company}"
                f"{f' | المستلم: {recipient_name}' if recipient_name else ''}"
            )

            cur.execute(
                """
                INSERT INTO issue_vouchers
                (voucher_no, reference_no, service_type, rental_company_id, issue_date, department, receiver_name, notes, created_by, status, approved_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'approved', NOW())
                """,
                (
                    voucher_no,
                    reference_no,
                    service_type,
                    rental_company_id,
                    issue_date,
                    'customs_urgent_release',
                    recipient_company,
                    voucher_notes,
                    session.get('user')
                )
            )
            voucher_id = cur.lastrowid

            for index, customs_item_id in enumerate(customs_item_ids):
                try:
                    requested_qty = float(quantities[index] or 0)
                except (IndexError, TypeError, ValueError):
                    requested_qty = 0
                if requested_qty <= 0:
                    raise ValueError('كميات الصرف يجب أن تكون أكبر من صفر.')

                item_id = item_ids[index] if index < len(item_ids) else None
                cur.execute(
                    """
                    SELECT ci.item_id, ci.quantity, i.current_stock, i.current_balance, i.price
                    FROM customs_items ci
                    JOIN items i ON i.id = ci.item_id
                    WHERE ci.id=%s AND ci.declaration_id=%s AND ci.item_id=%s
                    FOR UPDATE
                    """,
                    (customs_item_id, declaration_id, item_id)
                )
                item = cur.fetchone()
                if not item:
                    raise ValueError('أحد البنود المحددة لا ينتمي إلى الوارد المختار.')
                if requested_qty > float(item['quantity'] or 0):
                    raise ValueError('كمية الصرف أكبر من كمية البند في الوارد.')
                if requested_qty > float(item['current_stock'] or 0):
                    raise ValueError('الرصيد الحالي للصنف غير كافٍ لتنفيذ الإفراج العاجل.')

                try:
                    unit_price = float(unit_prices[index] or 0)
                except (IndexError, TypeError, ValueError):
                    unit_price = float(item['price'] or 0)
                if unit_price < 0:
                    raise ValueError('السعر لا يمكن أن يكون سالبًا.')
                item_note = notes[index].strip() if index < len(notes) else ''
                cur.execute(
                    """
                    INSERT INTO issue_voucher_items
                    (voucher_id, item_id, qty, unit_price, total)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (voucher_id, item['item_id'], requested_qty, unit_price, requested_qty * unit_price)
                )
                cur.execute(
                    """
                    UPDATE items
                    SET current_stock = current_stock - %s,
                        current_balance = COALESCE(current_balance, 0) - %s
                    WHERE id=%s
                    """,
                    (requested_qty, requested_qty, item['item_id'])
                )
                cur.execute(
                    """
                    INSERT INTO stock_movements
                    (item_id, warehouse_id, movement_type, qty, reference_type, reference_id)
                    VALUES (%s, %s, 'OUT', %s, 'URGENT_RELEASE', %s)
                    """,
                    (item['item_id'], 1, requested_qty, voucher_id)
                )
                cur.execute(
                    """
                    INSERT INTO stock_transactions
                    (item_id, warehouse_id, transaction_type, qty, reference_no, notes, created_at)
                    VALUES (%s, %s, 'OUT', %s, %s, %s, NOW())
                    """,
                    (
                        item['item_id'],
                        1,
                        requested_qty,
                        reference,
                        item_note or voucher_notes
                    )
                )

            conn.commit()
            flash(f"تم تنفيذ الإفراج العاجل كصرف مؤقت. رقم الإذن: {voucher_no}", 'success')
            return redirect('/issue-vouchers')

        cur.execute(
            """
            SELECT id, declaration_no, acid, declaration_date, importer_name, status
            FROM customs_declarations
            ORDER BY created_at DESC, id DESC
            """
        )
        declarations_list = cur.fetchall() or []
        cur.execute("SELECT id, company_name FROM companies WHERE status='active' ORDER BY company_name")
        rental_companies = cur.fetchall() or []
        return render_template(
            'customs_urgent_release.html',
            declarations_list=declarations_list,
            rental_companies=rental_companies,
            now_date=datetime.now().date().isoformat()
        )
    except Exception as exc:
        conn.rollback()
        flash(str(exc), 'danger')
        cur.execute(
            """
            SELECT id, declaration_no, acid, declaration_date, importer_name, status
            FROM customs_declarations
            ORDER BY created_at DESC, id DESC
            """
        )
        declarations_list = cur.fetchall() or []
        cur.execute("SELECT id, company_name FROM companies WHERE status='active' ORDER BY company_name")
        rental_companies = cur.fetchall() or []
        return render_template(
            'customs_urgent_release.html',
            declarations_list=declarations_list,
            rental_companies=rental_companies,
            now_date=datetime.now().date().isoformat()
        )
    finally:
        cur.close()
        conn.close()


# -----------------------------
# Sub-pages for Customs section
# -----------------------------

@app.route('/customs-management/create-export-invoice', methods=['GET', 'POST'])
def create_export_invoice():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        invoice_no = request.form.get('invoice_no', '').strip()
        invoice_date = request.form.get('invoice_date') or None
        party = request.form.get('recipient', '').strip()
        notes = request.form.get('notes', '').strip() if request.form.get('notes') else None
        declaration_id = request.form.get('declaration_id') or None

        try:
            created_by = get_current_user_id(conn)
            # insert header (include optional declaration_id)
            cur.execute("""
                INSERT INTO customs_invoices (invoice_no, invoice_type, invoice_date, party, notes, created_by, declaration_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                invoice_no,
                'export_invoice',
                invoice_date,
                party,
                notes,
                created_by,
                declaration_id or None
            ))
            invoice_id = cur.lastrowid

            # if no invoice_no provided, generate one: CUS-YYYY-XXXX
            if not invoice_no:
                import datetime
                year = datetime.datetime.now().year
                gen_no = f"CUS-{year}-{int(invoice_id):04d}"
                cur.execute("UPDATE customs_invoices SET invoice_no=%s WHERE id=%s", (gen_no, invoice_id))
                invoice_no = gen_no

            total = 0
            item_ids = request.form.getlist('item_id[]')
            unit_prices = request.form.getlist('unit_price[]')
            quantities = request.form.getlist('qty[]')
            unit_ids = request.form.getlist('unit_id[]')
            descriptions = request.form.getlist('description[]') if request.form.getlist('description[]') else [''] * len(item_ids)

            for item_id, up, qty, unit_id, desc in zip(item_ids, unit_prices, quantities, unit_ids, descriptions):
                try:
                    qty_val = float(qty or 0)
                except ValueError:
                    qty_val = 0
                try:
                    up_val = float(up or 0)
                except ValueError:
                    up_val = 0
                line_total = qty_val * up_val
                total += line_total
                cur.execute("""
                    INSERT INTO customs_invoice_items (invoice_id, item_id, quantity, unit_price, unit_id, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    invoice_id,
                    item_id or None,
                    qty_val,
                    up_val,
                    unit_id or None,
                    desc or None
                ))

            cur.execute("UPDATE customs_invoices SET total_amount = %s WHERE id = %s", (total, invoice_id))
            conn.commit()
            flash('تم إنشاء فاتورة صادر', 'success')
            cur.close()
            conn.close()
            return redirect('/customs-management/invoices')
        except Exception as e:
            conn.rollback()
            flash(str(e), 'danger')

    # load helper lists
    cur.execute("SELECT id, item_name_ar FROM items ORDER BY item_name_ar")
    items_list = cur.fetchall()
    cur.execute("SELECT id, unit_name FROM units ORDER BY unit_name")
    units_list = cur.fetchall()
    # load declarations for linking by ACID
    cur.execute("SELECT id, declaration_no, acid FROM customs_declarations ORDER BY created_at DESC")
    declarations_list = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('customs_management_create_export_invoice.html', title='انشاء فاتورة صادر', items_list=items_list, units_list=units_list, declarations_list=declarations_list)


# Edit and Delete invoice
@app.route('/customs-management/invoice/<int:invoice_id>/edit', methods=['GET', 'POST'])
def edit_invoice(invoice_id):
    if "user" not in session:
        return redirect("/")
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customs_invoices WHERE id=%s", (invoice_id,))
    inv = cur.fetchone()
    if not inv:
        cur.close()
        conn.close()
        flash('الفاتورة غير موجودة', 'warning')
        return redirect('/customs-management/invoices')

    if request.method == 'POST':
        invoice_no = request.form.get('invoice_no', '').strip()
        invoice_date = request.form.get('invoice_date') or None
        party = request.form.get('recipient') or request.form.get('customer') or request.form.get('from_store') or request.form.get('reason') or ''
        notes = request.form.get('notes', '').strip() if request.form.get('notes') else None
        try:
            cur.execute("UPDATE customs_invoices SET invoice_no=%s, invoice_date=%s, party=%s, notes=%s, updated_at=NOW() WHERE id=%s", (invoice_no, invoice_date, party, notes, invoice_id))

            # delete existing items and re-insert
            cur.execute("DELETE FROM customs_invoice_items WHERE invoice_id=%s", (invoice_id,))

            total = 0
            item_ids = request.form.getlist('item_id[]')
            unit_prices = request.form.getlist('unit_price[]')
            quantities = request.form.getlist('qty[]')
            unit_ids = request.form.getlist('unit_id[]')
            descriptions = request.form.getlist('description[]') if request.form.getlist('description[]') else [''] * len(item_ids)

            for item_id, up, qty, unit_id, desc in zip(item_ids, unit_prices, quantities, unit_ids, descriptions):
                try:
                    qty_val = float(qty or 0)
                except ValueError:
                    qty_val = 0
                try:
                    up_val = float(up or 0)
                except ValueError:
                    up_val = 0
                total += qty_val * up_val
                cur.execute("INSERT INTO customs_invoice_items (invoice_id, item_id, quantity, unit_price, unit_id, description) VALUES (%s,%s,%s,%s,%s,%s)", (invoice_id, item_id or None, qty_val, up_val, unit_id or None, desc or None))

            cur.execute("UPDATE customs_invoices SET total_amount=%s WHERE id=%s", (total, invoice_id))
            conn.commit()
            flash('تم تحديث الفاتورة', 'success')
            cur.close()
            conn.close()
            return redirect(f'/customs-management/invoice/{invoice_id}')
        except Exception as e:
            conn.rollback()
            flash(str(e), 'danger')

    # load items for form
    cur.execute("SELECT id, item_name_ar FROM items ORDER BY item_name_ar")
    items_list = cur.fetchall()
    cur.execute("SELECT id, unit_name FROM units ORDER BY unit_name")
    units_list = cur.fetchall()
    cur.execute("SELECT * FROM customs_invoice_items WHERE invoice_id=%s", (invoice_id,))
    items = cur.fetchall()
    # load declarations for linking by ACID so edit can re-link or show current link
    cur.execute("SELECT id, declaration_no, acid FROM customs_declarations ORDER BY created_at DESC")
    declarations_list = cur.fetchall()

    cur.close()
    conn.close()

    # reuse create template but pass invoice and items
    return render_template('customs_management_create_export_invoice.html', title='تعديل فاتورة', items_list=items_list, units_list=units_list, invoice=inv, existing_items=items, declarations_list=declarations_list)


@app.route('/customs-management/invoice/<int:invoice_id>/delete', methods=['POST'])
def delete_invoice(invoice_id):
    if "user" not in session:
        return redirect("/")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM customs_invoices WHERE id=%s", (invoice_id,))
        conn.commit()
        flash('تم حذف الفاتورة', 'success')
    except Exception as e:
        conn.rollback()
        flash(str(e), 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect('/customs-management/invoices')


@app.route('/customs-management/create-final-sale', methods=['GET', 'POST'])
def create_final_sale():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        invoice_no = request.form.get('invoice_no', '').strip()
        invoice_date = request.form.get('invoice_date') or None
        party = request.form.get('customer', '').strip()
        notes = request.form.get('notes', '').strip() if request.form.get('notes') else None

        try:
            created_by = get_current_user_id(conn)
            cur.execute("""
                INSERT INTO customs_invoices (invoice_no, invoice_type, invoice_date, party, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                invoice_no,
                'final_sale',
                invoice_date,
                party,
                notes,
                created_by
            ))
            invoice_id = cur.lastrowid

            # generate invoice_no if empty
            if not invoice_no:
                import datetime
                year = datetime.datetime.now().year
                gen_no = f"CUS-{year}-{int(invoice_id):04d}"
                cur.execute("UPDATE customs_invoices SET invoice_no=%s WHERE id=%s", (gen_no, invoice_id))
                invoice_no = gen_no

            total = 0
            item_ids = request.form.getlist('item_id[]')
            unit_prices = request.form.getlist('unit_price[]')
            quantities = request.form.getlist('qty[]')
            unit_ids = request.form.getlist('unit_id[]')
            descriptions = request.form.getlist('description[]') if request.form.getlist('description[]') else [''] * len(item_ids)

            for item_id, up, qty, unit_id, desc in zip(item_ids, unit_prices, quantities, unit_ids, descriptions):
                try:
                    qty_val = float(qty or 0)
                except ValueError:
                    qty_val = 0
                try:
                    up_val = float(up or 0)
                except ValueError:
                    up_val = 0
                line_total = qty_val * up_val
                total += line_total
                cur.execute("""
                    INSERT INTO customs_invoice_items (invoice_id, item_id, quantity, unit_price, unit_id, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    invoice_id,
                    item_id or None,
                    qty_val,
                    up_val,
                    unit_id or None,
                    desc or None
                ))

            cur.execute("UPDATE customs_invoices SET total_amount = %s WHERE id = %s", (total, invoice_id))
            conn.commit()
            flash('تم إنشاء فاتورة بيع نهائي', 'success')
            cur.close()
            conn.close()
            return redirect('/customs-management/invoices')
        except Exception as e:
            conn.rollback()
            flash(str(e), 'danger')

    cur.execute("SELECT id, item_name_ar FROM items ORDER BY item_name_ar")
    items_list = cur.fetchall()
    cur.execute("SELECT id, unit_name FROM units ORDER BY unit_name")
    units_list = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('customs_management_create_final_sale.html', title='انشاء فاتورة بيع نهائي', items_list=items_list, units_list=units_list)


@app.route('/customs-management/create-umbrella-transfer', methods=['GET', 'POST'])
def create_umbrella_transfer():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        transfer_no = request.form.get('transfer_no', '').strip()
        transfer_date = request.form.get('transfer_date') or None
        party = request.form.get('from_store', '').strip()
        notes = request.form.get('notes', '').strip() if request.form.get('notes') else None

        try:
            created_by = get_current_user_id(conn)
            cur.execute("""
                INSERT INTO customs_invoices (invoice_no, invoice_type, invoice_date, party, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                transfer_no,
                'umbrella_transfer',
                transfer_date,
                party,
                notes,
                created_by
            ))
            invoice_id = cur.lastrowid

            # generate invoice_no if empty
            if not transfer_no:
                import datetime
                year = datetime.datetime.now().year
                gen_no = f"CUS-{year}-{int(invoice_id):04d}"
                cur.execute("UPDATE customs_invoices SET invoice_no=%s WHERE id=%s", (gen_no, invoice_id))
                transfer_no = gen_no

            total = 0
            item_ids = request.form.getlist('item_id[]')
            unit_prices = request.form.getlist('unit_price[]')
            quantities = request.form.getlist('qty[]')
            unit_ids = request.form.getlist('unit_id[]')
            descriptions = request.form.getlist('description[]') if request.form.getlist('description[]') else [''] * len(item_ids)

            for item_id, up, qty, unit_id, desc in zip(item_ids, unit_prices, quantities, unit_ids, descriptions):
                try:
                    qty_val = float(qty or 0)
                except ValueError:
                    qty_val = 0
                try:
                    up_val = float(up or 0)
                except ValueError:
                    up_val = 0
                line_total = qty_val * up_val
                total += line_total
                cur.execute("""
                    INSERT INTO customs_invoice_items (invoice_id, item_id, quantity, unit_price, unit_id, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    invoice_id,
                    item_id or None,
                    qty_val,
                    up_val,
                    unit_id or None,
                    desc or None
                ))

            cur.execute("UPDATE customs_invoices SET total_amount = %s WHERE id = %s", (total, invoice_id))
            conn.commit()
            flash('تم إنشاء فاتورة تحويل مظلة', 'success')
            cur.close()
            conn.close()
            return redirect('/customs-management/invoices')
        except Exception as e:
            conn.rollback()
            flash(str(e), 'danger')

    cur.execute("SELECT id, item_name_ar FROM items ORDER BY item_name_ar")
    items_list = cur.fetchall()
    cur.execute("SELECT id, unit_name FROM units ORDER BY unit_name")
    units_list = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('customs_management_create_umbrella_transfer.html', title='انشاء فاتورة تحويل مظلة', items_list=items_list, units_list=units_list)


@app.route('/customs-management/create-return-export', methods=['GET', 'POST'])
def create_return_export():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        doc_no = request.form.get('doc_no', '').strip()
        doc_date = request.form.get('doc_date') or None
        party = request.form.get('reason', '').strip()
        notes = request.form.get('notes', '').strip() if request.form.get('notes') else None

        try:
            created_by = get_current_user_id(conn)
            cur.execute("""
                INSERT INTO customs_invoices (invoice_no, invoice_type, invoice_date, party, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                doc_no,
                'return_export',
                doc_date,
                party,
                notes,
                created_by
            ))
            invoice_id = cur.lastrowid

            # generate invoice_no if empty
            if not doc_no:
                import datetime
                year = datetime.datetime.now().year
                gen_no = f"CUS-{year}-{int(invoice_id):04d}"
                cur.execute("UPDATE customs_invoices SET invoice_no=%s WHERE id=%s", (gen_no, invoice_id))
                doc_no = gen_no

            total = 0
            item_ids = request.form.getlist('item_id[]')
            unit_prices = request.form.getlist('unit_price[]')
            quantities = request.form.getlist('qty[]')
            unit_ids = request.form.getlist('unit_id[]')
            descriptions = request.form.getlist('description[]') if request.form.getlist('description[]') else [''] * len(item_ids)

            for item_id, up, qty, unit_id, desc in zip(item_ids, unit_prices, quantities, unit_ids, descriptions):
                try:
                    qty_val = float(qty or 0)
                except ValueError:
                    qty_val = 0
                try:
                    up_val = float(up or 0)
                except ValueError:
                    up_val = 0
                line_total = qty_val * up_val
                total += line_total
                cur.execute("""
                    INSERT INTO customs_invoice_items (invoice_id, item_id, quantity, unit_price, unit_id, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    invoice_id,
                    item_id or None,
                    qty_val,
                    up_val,
                    unit_id or None,
                    desc or None
                ))

            cur.execute("UPDATE customs_invoices SET total_amount = %s WHERE id = %s", (total, invoice_id))
            conn.commit()
            flash('تم إنشاء فاتورة اعادة صادر', 'success')
            cur.close()
            conn.close()
            return redirect('/customs-management/invoices')
        except Exception as e:
            conn.rollback()
            flash(str(e), 'danger')

    cur.execute("SELECT id, item_name_ar FROM items ORDER BY item_name_ar")
    items_list = cur.fetchall()
    cur.execute("SELECT id, unit_name FROM units ORDER BY unit_name")
    units_list = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('customs_management_create_return_export.html', title='انشاء فاتورة اعادة صادر', items_list=items_list, units_list=units_list)

@app.route('/customs-management/declaration/<int:declaration_id>/items')
def declaration_items_api(declaration_id):
    if 'user' not in session:
        return jsonify({'error': 'unauthenticated'}), 401
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT ci.id, ci.item_id, ci.quantity, ci.unit_price, ci.description, i.item_name_ar, i.current_stock, i.current_balance, i.price AS item_price, u.unit_name FROM customs_items ci LEFT JOIN items i ON ci.item_id=i.id LEFT JOIN units u ON ci.unit_id=u.id WHERE ci.declaration_id=%s", (declaration_id,))
        rows = cur.fetchall() or []
        return jsonify({'items': rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/customs-management/<int:declaration_id>/approve', methods=['POST'])
def approve_customs_declaration(declaration_id):
    if "user" not in session:
        return redirect("/")

    approval_date = request.form.get('approval_date', '').strip() or None
    if approval_date is None:
        import datetime
        approval_date = datetime.date.today().isoformat()

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT inbound_type, status, declaration_no FROM customs_declarations WHERE id = %s FOR UPDATE", (declaration_id,))
        declaration = cur.fetchone()
        if not declaration:
            flash('السجل غير موجود.', 'warning')
            return redirect('/customs-management')

        if (declaration.get('status') or '').lower() == 'completed':
            flash('تم اعتماد هذا الوارد وتوزيعه مسبقًا.', 'warning')
            return redirect('/customs-management')

        inbound_type = declaration.get('inbound_type', '') or ''
        expected_departments = set(get_customs_purchase_departments(inbound_type))
        if len(expected_departments) != 1:
            raise ValueError('لا يمكن تحديد إدارة رصيد هذا النوع من الوارد.')

        expected_department = next(iter(expected_departments))
        cur.execute(
            "UPDATE customs_declarations SET status = 'completed', approval_date = %s, distribution_time = NOW(), entry_date = CURDATE(), updated_at = NOW() WHERE id = %s",
            (approval_date, declaration_id)
        )

        cur.execute(
            "SELECT id, item_id, quantity, unit_price, description FROM customs_items WHERE declaration_id = %s",
            (declaration_id,)
        )
        declaration_items = cur.fetchall() or []

        for row in declaration_items:
            item_id = row.get('item_id')
            quantity = float(row.get('quantity') or 0)
            if not item_id or quantity <= 0:
                continue

            cur.execute("SELECT current_stock, current_balance, department FROM items WHERE id = %s FOR UPDATE", (item_id,))
            item_row = cur.fetchone()
            if not item_row:
                raise ValueError(f'الصنف المرتبط بالبند غير موجود: {item_id}')
            if normalize_department_key(item_row.get('department')) != expected_department:
                raise ValueError(
                    f'الصنف رقم {item_id} لا يتبع إدارة {expected_department} المطلوبة لهذا الوارد.'
                )

            new_current_stock = float(item_row.get('current_stock') or 0) + quantity
            new_current_balance = float(item_row.get('current_balance') or 0) + quantity

            cur.execute(
                "UPDATE items SET current_stock = %s, current_balance = %s WHERE id = %s",
                (new_current_stock, new_current_balance, item_id)
            )

            cur.execute(
                "INSERT INTO stock_transactions (item_id, warehouse_id, transaction_type, qty, reference_no, notes, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
                (
                    item_id,
                    None,
                    'IN',
                    quantity,
                    f'customs_{declaration_id}',
                    f'إعتماد وارد جمركي رقم {declaration_id}'
                )
            )
            cur.execute(
                "INSERT INTO stock_movements (item_id, warehouse_id, movement_type, qty, reference_type, reference_id) VALUES (%s, %s, 'IN', %s, 'CUSTOMS_DECLARATION', %s)",
                (item_id, 1, quantity, declaration_id)
            )

        conn.commit()
        flash('تم اعتماد الوارد وتوزيعه بنجاح.', 'success')
        return redirect('/customs-management/total-imports-branch')
    except Exception as e:
        conn.rollback()
        flash(str(e), 'danger')
        return redirect('/customs-management')
    finally:
        cur.close()
        conn.close()


@app.route('/customs-management/delete/<int:declaration_id>', methods=['POST'])
def delete_customs_declaration(declaration_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT id, declaration_no, inbound_type, status FROM customs_declarations WHERE id=%s FOR UPDATE",
            (declaration_id,)
        )
        declaration = cur.fetchone()
        if not declaration:
            flash('الوارد غير موجود.', 'warning')
            return redirect('/customs-management')

        if (declaration.get('status') or '').lower() == 'completed':
            expected_departments = set(get_customs_purchase_departments(declaration.get('inbound_type')))
            if len(expected_departments) != 1:
                raise ValueError('لا يمكن تحديد إدارة رصيد هذا الوارد لعكس التوزيع.')
            expected_department = next(iter(expected_departments))

            cur.execute(
                "SELECT item_id, quantity FROM customs_items WHERE declaration_id=%s",
                (declaration_id,)
            )
            for row in cur.fetchall() or []:
                quantity = float(row.get('quantity') or 0)
                if not row.get('item_id') or quantity <= 0:
                    continue
                cur.execute(
                    "SELECT current_stock, current_balance, department FROM items WHERE id=%s FOR UPDATE",
                    (row['item_id'],)
                )
                item = cur.fetchone()
                if not item or normalize_department_key(item.get('department')) != expected_department:
                    raise ValueError('لا يمكن عكس توزيع أحد بنود الوارد بسبب اختلاف إدارة الرصيد.')
                if float(item.get('current_stock') or 0) < quantity or float(item.get('current_balance') or 0) < quantity:
                    raise ValueError('لا يمكن حذف الوارد لأن رصيده الموزع تم استخدامه بالفعل.')
                cur.execute(
                    "UPDATE items SET current_stock=current_stock-%s, current_balance=current_balance-%s WHERE id=%s",
                    (quantity, quantity, row['item_id'])
                )
                cur.execute(
                    "INSERT INTO stock_transactions (item_id, warehouse_id, transaction_type, qty, reference_no, notes, created_at) VALUES (%s, %s, 'OUT', %s, %s, %s, NOW())",
                    (row['item_id'], 1, quantity, f'customs_delete_{declaration_id}', f'عكس توزيع الوارد المحذوف {declaration_id}')
                )

        cur.execute("DELETE FROM customs_declarations WHERE id=%s", (declaration_id,))
        conn.commit()
        flash(f"تم حذف الوارد {declaration['declaration_no']} وعكس توزيعه من الرصيد.", 'success')
    except Exception as exc:
        conn.rollback()
        flash(str(exc), 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect('/customs-management')


@app.route('/customs-management/view/<int:declaration_id>')
def customs_management_view(declaration_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT cd.*
        FROM customs_declarations cd
        WHERE cd.id = %s
    """, (declaration_id,))
    customs_item = cur.fetchone()

    items = []
    if customs_item and has_column('customs_items', 'declaration_id'):
        try:
            cur.execute("""
                SELECT ci.*, i.item_name_ar
                FROM customs_items ci
                LEFT JOIN items i ON ci.item_id = i.id
                WHERE ci.declaration_id = %s
            """, (declaration_id,))
            items = cur.fetchall() or []
        except Exception:
            items = []

    cur.close()
    conn.close()

    if not customs_item:
        flash("السجل الجمركي غير موجود.", "warning")
        return redirect("/customs-management")

    return render_template(
        "customs_management_view.html",
        customs_item=customs_item,
        items=items
    )

@app.route('/customs-management/edit/<int:declaration_id>', methods=['GET', 'POST'])
def customs_management_edit(declaration_id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customs_declarations WHERE id = %s", (declaration_id,))
    customs_item = cur.fetchone()

    if not customs_item:
        cur.close()
        conn.close()
        flash("السجل الجمركي غير موجود.", "warning")
        return redirect("/customs-management")

    if request.method == 'POST':
        declaration_no = request.form.get('declaration_no', '').strip()
        declaration_date = request.form.get('declaration_date', '').strip()
        inbound_type = request.form.get('inbound_type', '').strip()
        importer_name = request.form.get('importer_name', '').strip()
        exporter_name = request.form.get('exporter_name', '').strip()
        origin_country = request.form.get('origin_country', '').strip()
        destination_country = request.form.get('destination_country', '').strip()
        regime_type = request.form.get('regime_type', '').strip()
        regime_details = request.form.get('regime_details', '').strip()
        port_of_loading = request.form.get('port_of_loading', '').strip()
        port_of_destination = request.form.get('port_of_destination', '').strip()
        port_of_discharge = request.form.get('port_of_discharge', '').strip()
        shipment_reference = request.form.get('shipment_reference', '').strip()
        acid = request.form.get('acid', '').strip()
        total_weight = float(request.form.get('total_weight', 0) or 0)
        package_count = int(request.form.get('package_count', 0) or 0)
        currency = request.form.get('currency', '').strip()
        tax_card_number = request.form.get('tax_card_number', '').strip()
        commercial_register_number = request.form.get('commercial_register_number', '').strip()
        total_value = float(request.form.get('total_value', 0) or 0)
        customs_fee = float(request.form.get('customs_fee', 0) or 0)
        notes = request.form.get('notes', '').strip()
        status = request.form.get('status', 'pending').strip() or 'pending'

        try:
            ensure_customs_status_enum()
            cur.execute("""
                UPDATE customs_declarations
                SET declaration_no = %s,
                    declaration_date = %s,
                    inbound_type = %s,
                    importer_name = %s,
                    exporter_name = %s,
                    origin_country = %s,
                    destination_country = %s,
                    regime_type = %s,
                    regime_details = %s,
                    port_of_loading = %s,
                    port_of_destination = %s,
                    port_of_discharge = %s,
                    shipment_reference = %s,
                    acid = %s,
                    total_weight = %s,
                    package_count = %s,
                    currency = %s,
                    tax_card_number = %s,
                    commercial_register_number = %s,
                    approval_date = %s,
                    entry_date = %s,
                    shipment_received_at = %s,
                    distribution_time = %s,
                    total_value = %s,
                    customs_fee = %s,
                    status = %s,
                    notes = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                declaration_no,
                declaration_date,
                inbound_type,
                importer_name,
                exporter_name,
                origin_country,
                destination_country,
                regime_type,
                regime_details,
                port_of_loading,
                port_of_destination,
                port_of_discharge,
                shipment_reference,
                acid,
                total_weight,
                package_count,
                currency,
                tax_card_number,
                commercial_register_number,
                approval_date,
                entry_date,
                shipment_received_at,
                distribution_time,
                total_value,
                customs_fee,
                status,
                notes,
                declaration_id
            ))

            # Delete existing line items and re-insert from form
            try:
                cur.execute("DELETE FROM customs_items WHERE declaration_id = %s", (declaration_id,))
            except Exception:
                pass

            item_ids = request.form.getlist('item_id[]')
            serials = request.form.getlist('serial_number[]')
            unit_prices = request.form.getlist('unit_price[]')
            origins = request.form.getlist('origin[]')
            quantities = request.form.getlist('qty[]')
            unit_ids = request.form.getlist('unit_id[]')
            descriptions = request.form.getlist('description[]')

            for item_id, serial, up, origin, qty, unit_id, desc in zip(item_ids, serials, unit_prices, origins, quantities, unit_ids, descriptions):
                if not (item_id or desc):
                    continue
                try:
                    qty_val = float(qty or 0)
                except ValueError:
                    qty_val = 0
                try:
                    up_val = float(up or 0)
                except ValueError:
                    up_val = 0

                cur.execute("""
                    INSERT INTO customs_items
                    (declaration_id, item_id, quantity, unit_price, serial_number, origin_country, unit_id, description)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    declaration_id,
                    item_id or None,
                    qty_val,
                    up_val,
                    serial or None,
                    origin or None,
                    unit_id or None,
                    desc or None
                ))

            conn.commit()
            flash("تم تحديث السجل الجمركي.", "success")
            return redirect("/customs-management")
        except Exception as e:
            conn.rollback()
            flash(str(e), "danger")

    # load items and units for the items section
    cur.execute("SELECT id, item_name_ar FROM items ORDER BY item_name_ar")
    items_list = cur.fetchall()
    cur.execute("SELECT id, unit_name FROM units ORDER BY unit_name")
    units_list = cur.fetchall()

    # load existing declaration items
    declaration_items = []
    try:
        cur.execute("""
            SELECT ci.*, i.item_name_ar, u.unit_name AS unit
            FROM customs_items ci
            LEFT JOIN items i ON ci.item_id = i.id
            LEFT JOIN units u ON ci.unit_id = u.id
            WHERE ci.declaration_id = %s
        """, (declaration_id,))
        declaration_items = cur.fetchall() or []
    except Exception:
        declaration_items = []

    cur.close()
    conn.close()

    return render_template(
        "customs_management_form.html",
        title="تعديل العملية الجمركية",
        subtitle="حدث بيانات السجل الجمركي الموجود.",
        customs_item=customs_item,
        submit_label="تحديث",
        items_list=items_list,
        units_list=units_list,
        declaration_items=declaration_items
    )

    cur.close()
    conn.close()

    return render_template(
        "customs_management_form.html",
        title="تعديل العملية الجمركية",
        subtitle="حدث بيانات السجل الجمركي الموجود.",
        customs_item=customs_item,
        submit_label="تحديث"
    )

# تسجيل Blueprints
app.register_blueprint(hr_bp)
app.register_blueprint(issue_vouchers_bp)

# ======================
# تشغيل التطبيق
# ======================
if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app_port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=app_port, debug=debug_mode, use_reloader=False)


# Development helper: show CSRF errors with some debug info
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    try:
        print("[CSRFError] description:", e.description)
        print("[CSRFError] form:", dict(request.form))
        print("[CSRFError] headers:")
        for k, v in request.headers.items():
            print(k, v)
    except Exception:
        pass
    return e.description, 400
