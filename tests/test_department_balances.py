import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app


def test_normalize_department_key():
    assert app.normalize_department_key('local_purchases') == 'local_purchases'
    assert app.normalize_department_key('المشتريات المحلية') == 'local_purchases'
    assert app.normalize_department_key('external_purchases') == 'external_purchases'
    assert app.normalize_department_key('المشتريات الخارجية') == 'external_purchases'


def test_department_stock_summary_aggregation():
    rows = [
        {'department': 'local_purchases', 'current_stock': 10},
        {'department': 'external_purchases', 'current_stock': 7},
        {'department': 'local_purchases', 'current_stock': 3},
    ]

    summary = app.build_department_stock_summary(rows)

    assert summary['local_purchases'] == 13
    assert summary['external_purchases'] == 7


def test_item_entry_route_for_department():
    assert app.build_item_entry_path('local_purchases') == '/items/add/local_purchases'
    assert app.build_item_entry_path('external_purchases') == '/items/add/external_purchases'
    assert app.build_item_entry_path('المشتريات الخارجية') == '/items/add/external_purchases'


def test_customs_purchase_department_mapping():
    assert app.get_customs_purchase_departments('local_market') == ['local_purchases']
    assert app.get_customs_purchase_departments('external') == ['external_purchases']
    assert app.get_customs_purchase_departments(None) == ['local_purchases', 'external_purchases']
