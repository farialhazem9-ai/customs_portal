import mysql.connector

config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Hazem@2026',
    'database': 'customs_portal',
    'connection_timeout': 10,
}

conn = mysql.connector.connect(**config)
cur = conn.cursor()
cur.execute(
    "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=%s AND table_name='users' AND column_name='last_login_ip'",
    (config['database'],),
)
exists = cur.fetchone()[0]
if exists:
    print('last_login_ip already exists')
else:
    cur.execute("ALTER TABLE users ADD COLUMN last_login_ip VARCHAR(45) NULL AFTER last_login_at")
    conn.commit()
    print('last_login_ip added successfully')
cur.close()
conn.close()
