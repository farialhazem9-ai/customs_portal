import mysql.connector
import os

SQL_FILE = os.path.join(os.path.dirname(__file__), 'migrations', '006_reconcile_legacy_customs_schema.sql')

db_config = {
    'host': os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST') or 'localhost',
    'user': os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'root',
    'password': os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or '',
    'database': os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'customs_portal',
    'port': int(os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT') or '3306')
}

if not os.path.exists(SQL_FILE):
    print('Migration file not found:', SQL_FILE)
    raise SystemExit(1)

with open(SQL_FILE, 'r', encoding='utf-8') as f:
    sql = f.read()

# Split statements; naive split on ';' but keep delimiters inside JSON safe by simple approach: execute whole file with cursor.execute() if connector supports multi.
try:
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    # execute as multi
    for result in cur.execute(sql, multi=True):
        if result.with_rows:
            print('Result:', result.fetchall())
        else:
            print('Executed statement, affected rows:', result.rowcount)
    conn.commit()
    cur.close()
    conn.close()
    print('Migration applied successfully.')
except mysql.connector.Error as e:
    print('MySQL error:', e)
    raise
except Exception as e:
    print('Error:', e)
    raise
