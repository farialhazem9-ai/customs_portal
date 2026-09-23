from unittest.mock import patch
from app import app


class FakeCursor:
    def __init__(self):
        self._rows = [{'item_count': 2}, {'child_count': 0}]

    def execute(self, query, params=None):
        return None

    def fetchone(self):
        return self._rows.pop(0) if self._rows else {'item_count': 0, 'child_count': 0}

    def close(self):
        return None


class FakeConn:
    def cursor(self, dictionary=True):
        return FakeCursor()

    def commit(self):
        return None

    def rollback(self):
        return None

    def close(self):
        return None


with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user'] = 'admin'

    with patch('app.get_db_connection', return_value=FakeConn()):
        resp = client.post('/categories/delete/1', follow_redirects=True)
        text = resp.get_data(as_text=True)
        print('status=', resp.status_code)
        print('message_present=', 'لا يمكن حذف الفئة لأنه يوجد أصناف أو فئات فرعية مرتبطة بها.' in text)
        print('redirect_ok=', '/categories' in text)
