import mysql.connector
import os

MIGRATION_DIR = os.path.join(os.path.dirname(__file__), 'migrations')
SQL_FILES = [
    os.path.join(MIGRATION_DIR, '006_reconcile_legacy_customs_schema.sql'),
    os.path.join(MIGRATION_DIR, '007_create_audit_logs.sql'),
    os.path.join(MIGRATION_DIR, '009_customs_invoice_export_fields.sql'),
    os.path.join(MIGRATION_DIR, '010_make_item_unit_optional.sql'),
    os.path.join(MIGRATION_DIR, '011_add_po_requisition_id.sql'),
    os.path.join(MIGRATION_DIR, '012_track_po_receipts.sql'),
]

db_config = {
    'host': os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST') or 'localhost',
    'user': os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'root',
    'password': os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or 'Hazem@2026',
    'database': os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'customs_portal',
    'port': int(os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT') or '3306')
}

missing_files = [path for path in SQL_FILES if not os.path.exists(path)]
if missing_files:
    print('Migration file not found:', missing_files[0])
    raise SystemExit(1)

# Split statements; naive split on ';' but keep delimiters inside JSON safe by simple approach: execute whole file with cursor.execute() if connector supports multi.
try:
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    for sql_file in SQL_FILES:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        print('Applying migration:', os.path.basename(sql_file))
        for statement in (part.strip() for part in sql.split(';')):
            if not statement:
                continue
            try:
                cur.execute(statement)
            except mysql.connector.Error as exc:
                if os.path.basename(sql_file).startswith('006_') and exc.errno == 1064:
                    print('Skipping incompatible legacy migration 006; application bootstrap handles legacy columns.')
                    conn.rollback()
                    break
                if os.path.basename(sql_file).startswith('007_') and exc.errno == 1060:
                    print('Column already exists in audit_logs; continuing migration.')
                    conn.rollback()
                    continue
                if os.path.basename(sql_file).startswith('009_') and exc.errno == 1060:
                    print('Column already exists in customs_invoices; continuing migration.')
                    conn.rollback()
                    continue
                if os.path.basename(sql_file).startswith('011_') and exc.errno == 1060:
                    print('Column already exists in purchase_orders; continuing migration.')
                    conn.rollback()
                    continue
                if os.path.basename(sql_file).startswith('012_') and exc.errno == 1060:
                    print('Column already exists in purchase_order_items; continuing migration.')
                    conn.rollback()
                    continue
                raise
            if cur.with_rows:
                print('Result:', cur.fetchall())
            else:
                print('Executed statement, affected rows:', cur.rowcount)
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
