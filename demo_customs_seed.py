import mysql.connector
from datetime import date, datetime

conn = mysql.connector.connect(
    host=os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST') or 'localhost',
    user=os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'root',
    password=os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or '',
    database=os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'customs_portal',
    port=int(os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT') or '3306')
)
cur = conn.cursor(dictionary=True)

try:
    cur.execute("SELECT id FROM units ORDER BY id LIMIT 1")
    unit_row = cur.fetchone()
    if unit_row:
        unit_id = unit_row['id']
    else:
        cur.execute("INSERT INTO units (unit_name, unit_code) VALUES (%s, %s)", ('علبة', 'BOX'))
        conn.commit()
        unit_id = cur.lastrowid

    cur.execute("SELECT id FROM items ORDER BY id LIMIT 1")
    item_row = cur.fetchone()
    if item_row:
        item_id = item_row['id']
    else:
        cur.execute("SELECT id FROM categories ORDER BY id LIMIT 1")
        category_row = cur.fetchone()
        category_id = category_row['id'] if category_row else None
        cur.execute(
            "INSERT INTO items (item_name_ar, item_name_en, category_id, unit_id, current_stock, min_stock) VALUES (%s, %s, %s, %s, %s, %s)",
            ('ماء معدني', 'Mineral Water', category_id, unit_id, 100, 10)
        )
        conn.commit()
        item_id = cur.lastrowid

    cur.execute("SELECT id FROM users WHERE username=%s LIMIT 1", ('admin',))
    user_row = cur.fetchone()
    if user_row:
        user_id = user_row['id']
    else:
        cur.execute(
            "INSERT INTO users (username, password, full_name, role, status) VALUES (%s, %s, %s, %s, %s)",
            ('admin', 'admin123', 'Administrator', 'admin', 'active')
        )
        conn.commit()
        user_id = cur.lastrowid

    cur.execute("SHOW COLUMNS FROM customs_declarations")
    columns = [row['Field'] for row in cur.fetchall()]

    payload = {
        'declaration_no': 'CUS-TEST-1001',
        'declaration_date': date.today().isoformat(),
        'inbound_type': 'external',
        'importer_name': 'شركة التجربة',
        'exporter_name': 'مصدر تجريبي',
        'origin_country': 'تركيا',
        'destination_country': 'مصر',
        'regime_type': 'import',
        'regime_details': 'ميناء',
        'port_of_loading': 'ميناء الإسكندرية',
        'port_of_destination': 'ميناء بورسعيد',
        'port_of_discharge': 'ميناء الأسكندرية',
        'shipment_reference': 'REF-001',
        'acid': 'ACID-1001',
        'total_weight': 120.5,
        'package_count': 12,
        'currency': 'USD',
        'tax_card_number': 'TAX-1001',
        'commercial_register_number': 'CR-2001',
        'clearance_officer_name': 'أحمد محمد',
        'clearance_officer_location': 'المنطقة الحرة',
        'clearance_officer_phone': '01000000000',
        'approval_date': date.today().isoformat(),
        'entry_date': date.today().isoformat(),
        'shipment_received_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'distribution_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_value': 2500.00,
        'customs_fee': 180.00,
        'status': 'completed',
        'notes': 'وارد تجريبي تم إنشاؤه للاختبار',
        'created_by': user_id,
    }

    fields = [k for k in payload if k in columns]
    if not fields:
        raise RuntimeError('No matching columns found in customs_declarations')

    cur.execute("SELECT id FROM customs_declarations WHERE declaration_no=%s LIMIT 1", ('CUS-TEST-1001',))
    existing = cur.fetchone()
    if existing:
        print('Demo declaration already exists:', existing['id'])
        declaration_id = existing['id']
    else:
        placeholders = ', '.join(['%s'] * len(fields))
        sql = f"INSERT INTO customs_declarations ({', '.join(fields)}) VALUES ({placeholders})"
        values = [payload[field] for field in fields]
        cur.execute(sql, values)
        conn.commit()
        declaration_id = cur.lastrowid
        print('Inserted demo declaration with id:', declaration_id)

    cur.execute("SHOW COLUMNS FROM customs_items")
    item_columns = [row['Field'] for row in cur.fetchall()]
    item_payload = {
        'declaration_id': declaration_id,
        'item_id': item_id,
        'quantity': 10,
        'unit_price': 200.0,
        'serial_number': 'SER-1001',
        'origin_country': 'تركيا',
        'unit_id': unit_id,
        'description': 'مياه معدنية',
    }
    item_fields = [k for k in item_payload if k in item_columns]
    if item_fields:
        placeholders = ', '.join(['%s'] * len(item_fields))
        sql = f"INSERT INTO customs_items ({', '.join(item_fields)}) VALUES ({placeholders})"
        values = [item_payload[field] for field in item_fields]
        cur.execute(sql, values)
        conn.commit()
        print('Inserted demo item line for declaration id:', declaration_id)

    cur.execute("SELECT declaration_no, importer_name, status, approval_date FROM customs_declarations ORDER BY id DESC LIMIT 3")
    rows = cur.fetchall()
    print('Latest declarations:')
    for row in rows:
        print(row)
finally:
    cur.close()
    conn.close()
