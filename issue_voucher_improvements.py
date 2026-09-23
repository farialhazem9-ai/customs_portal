# ======================
# تحسينات نظام إذن الصرف
# ======================
# هذا الملف يحتوي على 4 حلول رئيسية

from flask import Flask, request, session, flash, redirect, render_template
import mysql.connector
from datetime import datetime


def setup_issue_voucher_improvements(app, db_config, get_db_connection):
    """
    تثبيت جميع تحسينات نظام إذن الصرف
    """
    
    # ============================================
    # 1️⃣ تحديث المخزون عند اعتماد الأذن
    # ============================================
    @app.route("/issue-vouchers/<int:voucher_id>/approve-enhanced", methods=["GET", "POST"])
    def approve_issue_voucher_enhanced(voucher_id):
        """
        اعتماد إذن صرف مع تحديث المخزون والتحقق من الرصيد
        """
        if "user" not in session:
            return redirect("/")

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        try:
            # الحصول على بيانات الإذن
            cur.execute("SELECT * FROM issue_vouchers WHERE id=%s", (voucher_id,))
            voucher = cur.fetchone()

            if not voucher:
                flash("الإذن غير موجود", "danger")
                return redirect("/issue-vouchers")

            if voucher["status"] == "approved":
                flash("تم الاعتماد مسبقاً", "warning")
                return redirect("/issue-vouchers")

            # الحصول على عناصر الإذن
            cur.execute("""
                SELECT ivi.*, i.current_stock, i.current_balance
                FROM issue_voucher_items ivi
                LEFT JOIN items i ON ivi.item_id = i.id
                WHERE ivi.voucher_id=%s
            """, (voucher_id,))
            details = cur.fetchall()

            # 🔍 التحقق من الرصيد الكافي
            insufficient_items = []
            for row in details:
                if row["current_stock"] is None or float(row["current_stock"]) < float(row["qty"]):
                    insufficient_items.append({
                        "item_id": row["item_id"],
                        "required": row["qty"],
                        "available": row["current_stock"] or 0
                    })

            if insufficient_items:
                error_msg = "الرصيد غير كافي للأصناف التالية:\n"
                for item in insufficient_items:
                    error_msg += f"- الصنف #{item['item_id']}: مطلوب {item['required']}, متوفر {item['available']}\n"
                flash(error_msg, "danger")
                return redirect(f"/issue-vouchers/view/{voucher_id}")

            # ✅ تحديث المخزون والإنشاء حركات المخزون
            for row in details:
                # 1. تحديث current_balance و current_stock
                cur.execute("""
                    UPDATE items
                    SET current_balance = current_balance - %s,
                        current_stock = current_stock - %s
                    WHERE id = %s
                """, (
                    float(row["qty"]),
                    float(row["qty"]),
                    row["item_id"]
                ))

                # 2. إنشاء سجل حركة مخزون (OUT)
                cur.execute("""
                    INSERT INTO stock_movements
                    (
                        item_id,
                        warehouse_id,
                        movement_type,
                        qty,
                        reference_type,
                        reference_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    row["item_id"],
                    1,  # المخزن الافتراضي
                    "OUT",
                    float(row["qty"]),
                    "ISSUE_VOUCHER",
                    voucher_id
                ))

                # 3. إنشاء سجل في stock_transactions
                cur.execute("""
                    INSERT INTO stock_transactions
                    (item_id, warehouse_id, transaction_type, qty, reference_no, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    row["item_id"],
                    1,
                    "OUT",
                    float(row["qty"]),
                    f"IV-{voucher_id}",
                    f"صرف من إذن الصرف رقم {voucher['voucher_no']}"
                ))

            # تحديث حالة الإذن
            cur.execute("""
                UPDATE issue_vouchers
                SET status='approved', approved_at=NOW()
                WHERE id=%s
            """, (voucher_id,))

            conn.commit()
            flash("✅ تم اعتماد إذن الصرف وتحديث المخزون بنجاح", "success")

        except Exception as e:
            conn.rollback()
            flash(f"❌ خطأ: {str(e)}", "danger")
            import traceback
            traceback.print_exc()

        finally:
            cur.close()
            conn.close()

        return redirect("/issue-vouchers")

    # ============================================
    # 2️⃣ التحقق من الرصيد قبل الموافقة
    # ============================================
    @app.route("/issue-vouchers/<int:voucher_id>/check-stock", methods=["GET"])
    def check_voucher_stock(voucher_id):
        """
        التحقق من توفر الرصيد قبل الموافقة
        """
        if "user" not in session:
            return redirect("/")

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT ivi.*, i.item_name_ar, i.current_stock
            FROM issue_voucher_items ivi
            LEFT JOIN items i ON ivi.item_id = i.id
            WHERE ivi.voucher_id=%s
        """, (voucher_id,))
        
        items = cur.fetchall()
        cur.close()
        conn.close()

        # فحص كل صنف
        results = []
        for item in items:
            available = float(item["current_stock"] or 0)
            required = float(item["qty"])
            status = "✅ متوفر" if available >= required else "❌ غير متوفر"
            
            results.append({
                "item_name": item["item_name_ar"],
                "required": required,
                "available": available,
                "status": status,
                "shortage": max(0, required - available)
            })

        return render_template(
            "stock_check_report.html",
            voucher_id=voucher_id,
            items=results
        )

    # ============================================
    # 3️⃣ ربط أذون الصرف بأوامر الشراء
    # ============================================
    @app.route("/issue-vouchers/<int:voucher_id>/link-order", methods=["POST"])
    def link_voucher_to_order(voucher_id):
        """
        ربط إذن صرف برقم أمر شراء
        """
        if "user" not in session:
            return redirect("/")

        po_number = request.form.get("po_number")

        if not po_number:
            flash("يرجى إدخال رقم أمر الشراء", "warning")
            return redirect(f"/issue-vouchers/view/{voucher_id}")

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        try:
            # التحقق من وجود أمر الشراء
            cur.execute(
                "SELECT id FROM purchase_orders WHERE po_number=%s",
                (po_number,)
            )
            po = cur.fetchone()

            if not po:
                flash(f"أمر الشراء '{po_number}' غير موجود", "danger")
                return redirect(f"/issue-vouchers/view/{voucher_id}")

            # ربط الإذن بأمر الشراء
            cur.execute("""
                UPDATE issue_vouchers
                SET purchase_order_id=%s
                WHERE id=%s
            """, (po["id"], voucher_id))

            conn.commit()
            flash(f"✅ تم ربط الإذن برقم الأمر: {po_number}", "success")

        except Exception as e:
            conn.rollback()
            flash(f"❌ خطأ: {str(e)}", "danger")

        finally:
            cur.close()
            conn.close()

        return redirect(f"/issue-vouchers/view/{voucher_id}")

    # ============================================
    # 4️⃣ تقارير استهلاك المخزون
    # ============================================
    @app.route("/reports/inventory-consumption", methods=["GET"])
    def inventory_consumption_report():
        """
        تقرير استهلاك المخزون من أذون الصرف
        """
        if "user" not in session:
            return redirect("/")

        from_date = request.args.get("from_date")
        to_date = request.args.get("to_date")
        item_id = request.args.get("item_id")

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # بناء الاستعلام
        query = """
            SELECT
                i.id,
                i.item_code,
                i.item_name_ar,
                COUNT(DISTINCT ivi.voucher_id) as voucher_count,
                SUM(ivi.qty) as total_qty,
                SUM(ivi.qty * ivi.unit_price) as total_value,
                MIN(iv.issue_date) as first_issue,
                MAX(iv.issue_date) as last_issue
            FROM issue_voucher_items ivi
            LEFT JOIN items i ON ivi.item_id = i.id
            LEFT JOIN issue_vouchers iv ON ivi.voucher_id = iv.id
            WHERE iv.status = 'approved'
        """

        params = []

        if from_date:
            query += " AND iv.issue_date >= %s"
            params.append(from_date)

        if to_date:
            query += " AND iv.issue_date <= %s"
            params.append(to_date)

        if item_id:
            query += " AND i.id = %s"
            params.append(item_id)

        query += " GROUP BY i.id ORDER BY total_qty DESC"

        cur.execute(query, params)
        report_data = cur.fetchall()

        # الحصول على قائمة الأصناف
        cur.execute("SELECT id, item_name_ar FROM items ORDER BY item_name_ar")
        items_list = cur.fetchall()

        cur.close()
        conn.close()

        return render_template(
            "inventory_consumption_report.html",
            report_data=report_data,
            items_list=items_list,
            from_date=from_date,
            to_date=to_date,
            selected_item=item_id
        )

    @app.route("/reports/inventory-consumption/export", methods=["GET"])
    def export_consumption_report():
        """
        تصدير تقرير الاستهلاك كـ CSV
        """
        if "user" not in session:
            return redirect("/")

        import csv
        from io import StringIO

        from_date = request.args.get("from_date")
        to_date = request.args.get("to_date")

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        query = """
            SELECT
                i.item_code,
                i.item_name_ar,
                COUNT(DISTINCT ivi.voucher_id) as voucher_count,
                SUM(ivi.qty) as total_qty,
                SUM(ivi.qty * ivi.unit_price) as total_value
            FROM issue_voucher_items ivi
            LEFT JOIN items i ON ivi.item_id = i.id
            LEFT JOIN issue_vouchers iv ON ivi.voucher_id = iv.id
            WHERE iv.status = 'approved'
        """

        params = []
        if from_date:
            query += " AND iv.issue_date >= %s"
            params.append(from_date)
        if to_date:
            query += " AND iv.issue_date <= %s"
            params.append(to_date)

        query += " GROUP BY i.id ORDER BY total_qty DESC"
        cur.execute(query, params)
        data = cur.fetchall()
        cur.close()
        conn.close()

        # إنشاء CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["الكود", "اسم الصنف", "عدد الأذونات", "الكمية الإجمالية", "القيمة الإجمالية"])
        
        for row in data:
            writer.writerow([
                row["item_code"],
                row["item_name_ar"],
                row["voucher_count"],
                row["total_qty"],
                row["total_value"]
            ])

        output.seek(0)
        return output.getvalue(), 200, {
            "Content-Disposition": "attachment;filename=consumption_report.csv",
            "Content-Type": "text/csv"
        }
