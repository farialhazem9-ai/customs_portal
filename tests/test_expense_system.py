import pytest

from app import (
    calculate_expense_balance_delta,
    calculate_stock_balance_delta,
    build_stock_review_summary,
    calculate_stock_period_closing,
    is_stock_below_reorder_level,
    format_issue_voucher_number,
    validate_expense_amount,
)


def test_expense_balance_delta_for_expense():
    assert calculate_expense_balance_delta(1250.50, "expense") == -1250.50


def test_expense_balance_delta_for_reversal():
    assert calculate_expense_balance_delta(500, "reversal") == 500.0


def test_validate_expense_amount_rejects_invalid_values():
    with pytest.raises(ValueError):
        validate_expense_amount(-1)

    with pytest.raises(ValueError):
        validate_expense_amount(0)


def test_stock_balance_delta_for_issue_and_review_summary():
    assert calculate_stock_balance_delta(12, "issue") == -12
    assert calculate_stock_balance_delta(5, "purchase") == 5

    rows = [
        {"item_name_ar": "مفك", "current_stock": 20, "current_balance": 15, "item_count": 1},
        {"item_name_ar": "مسمار", "current_stock": 4, "current_balance": 4, "item_count": 1},
    ]
    summary = build_stock_review_summary(rows)
    assert summary["total_stock"] == 24
    assert summary["total_balance"] == 19


def test_stock_period_reconciliation_and_reorder_alert():
    assert calculate_stock_period_closing(10, 8, 3) == 15
    assert is_stock_below_reorder_level(4, 5) is True
    assert is_stock_below_reorder_level(5, 5) is True
    assert is_stock_below_reorder_level(6, 5) is False
    assert is_stock_below_reorder_level(0, 0) is False


def test_issue_voucher_number_uses_date_and_zero_padded_sequence():
    assert format_issue_voucher_number("2026-10-09", 7) == "IV-20261009-00007"
