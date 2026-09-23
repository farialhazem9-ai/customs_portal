نظام الجمارك والمخازن (موجز تشغيل)

متطلبات سريعة

- Python 3.8+
- MySQL
- للتصدير إلى PDF باستخدام WeasyPrint قد تحتاج تثبيت حزم نظامية (GTK/Cairo) على Windows/Linux.

تثبيت الاعتمادات

```bash
cd c:\Users\RaniaHazem\customs_portal
python -m pip install -r requirements.txt
```

إعداد البيئة

انسخ `.env.example` إلى `.env` ثم املأ كلمة مرور MySQL والمفتاح السري قبل التشغيل:

```powershell
Copy-Item .env.example .env
```

لا ترفع ملف `.env` إلى Git؛ فهو يحتوي على بيانات اتصال حساسة.

ملاحظات عن WeasyPrint

- على Windows: اتبع تعليمات التثبيت من https://weasyprint.org/docs/
- كبديل يمكن استخدام `wkhtmltopdf` وتعديل الكود لإطلاقه كأمر خارجي.

قواعد البيانات

- شغّل سكربت الترحيل قبل التشغيل لضمان وجود الأعمدة الضرورية:

```sql
-- افتح MySQL واجري:
SOURCE migrations/001_add_unitprice_line_total.sql;
```

تشغيل التطبيق

```bash
python app.py
```

نقاط نهائية مفيدة

- `/purchase-orders` لعرض أوامر الشراء
- `/purchase-orders/<id>` لعرض تفاصيل الأمر
- `/purchase-orders/<id>/pdf` لتصدير PDF (إن كانت WeasyPrint مثبتة)
- `/issue-vouchers` لعرض أذونات الصرف
- `/issue/add` لإنشاء إذن صرف
- `/issue-vouchers/<id>/pdf` لتصدير إذن الصرف إلى PDF

إذا أردت أضبط توليد PDF باستخدام wkhtmltopdf بدلاً من WeasyPrint أو أُرَتِّب خطوات CI للتخطيط، أخبرني.