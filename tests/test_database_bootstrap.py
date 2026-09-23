from pathlib import Path

import app


class FakeCursor:
    def __init__(self):
        self.executed = []
        self._show_tables = False

    def execute(self, sql, params=None, multi=False):
        self.executed.append((sql, params, multi))
        if sql.strip().upper().startswith('SHOW TABLES'):
            self._show_tables = True
            return None
        if sql.strip().upper().startswith('CREATE TABLE'):
            return None
        return None

    def fetchall(self):
        if self._show_tables:
            return [('roles',), ('users',)]
        return []

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def test_bootstrap_database_schema_imports_sql_when_items_table_missing(monkeypatch, tmp_path):
    conn = FakeConnection()
    sql_file = tmp_path / 'customs_portal.sql'
    sql_file.write_text('CREATE TABLE items (id INT);', encoding='utf-8')

    def fake_get_db_connection():
        return conn

    monkeypatch.setattr(app, 'get_db_connection', fake_get_db_connection)

    result = app.bootstrap_database_schema(sql_file)

    assert result is True
    assert conn.committed is True
    assert any('SHOW TABLES' in sql for sql, _, _ in conn.cursor_obj.executed)
    assert any('CREATE TABLE items' in sql for sql, _, _ in conn.cursor_obj.executed)


def test_ensure_database_ready_retries_when_users_table_missing(monkeypatch, tmp_path):
    sql_file = tmp_path / 'customs_portal.sql'
    sql_file.write_text('CREATE TABLE users (id INT); CREATE TABLE items (id INT); CREATE TABLE roles (id INT); CREATE TABLE permissions (id INT);', encoding='utf-8')

    class MissingUsersCursor(FakeCursor):
        def execute(self, sql, params=None, multi=False):
            super().execute(sql, params, multi)
            if str(sql).strip().upper().startswith('SHOW TABLES'):
                return None
            return None

        def fetchall(self):
            return []

    conn = FakeConnection()
    conn.cursor_obj = MissingUsersCursor()

    monkeypatch.setattr(app, 'get_db_connection', lambda: conn)
    monkeypatch.setattr(app, 'bootstrap_database_schema', lambda sql_file=None: True)

    result = app.ensure_database_ready()

    assert result is True
