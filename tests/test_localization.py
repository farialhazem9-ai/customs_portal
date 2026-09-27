from pathlib import Path

from translations import ARABIC_TO_ENGLISH


ROOT = Path(__file__).resolve().parents[1]


def test_templates_do_not_force_arabic_direction():
    templates = (ROOT / "templates").glob("*.html")

    assert all(
        '<html lang="ar" dir="rtl">' not in template.read_text(encoding="utf-8")
        for template in templates
    )


def test_core_english_localization_terms_exist():
    expected = {
        "نظام الجمارك والمخازن": "Customs, Local & External Purchases System",
        "إدارة المستخدمين والصلاحيات": "Users and permissions",
        "الإدارات المسموح برؤيتها": "Departments allowed to view",
        "الصلاحيات التشغيلية": "Operational permissions",
        "إدارة الجمارك": "Customs Management",
        "إضافة صنف جديد": "Add new item",
        "تقديم طلب شراء جديد": "New purchase request",
    }

    for arabic, english in expected.items():
        assert ARABIC_TO_ENGLISH[arabic] == english