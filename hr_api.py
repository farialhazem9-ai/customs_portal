import os
import uuid
from flask import Blueprint, request, jsonify, render_template, redirect, current_app, send_from_directory, session, url_for
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from hr_models import Employee, HRConfig, EmployeeDocument, Payslip, Department
from hr_db import get_session as make_session
from hr_payroll import ConfigLoader, compute_payslip, build_employee_payroll_summary
from decimal import Decimal

bp = Blueprint('hr', __name__, url_prefix='/hr')

UPLOAD_SUBFOLDER = 'employee_documents'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}

def get_upload_folder():
    base = current_app.config.get('HR_UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads'))
    folder = os.path.join(base, UPLOAD_SUBFOLDER)
    os.makedirs(folder, exist_ok=True)
    return folder


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.before_request
def require_hr_access():
    if 'user' not in session:
        return redirect(url_for('login'))
    role = session.get('role')
    if role and role.lower() not in ('admin', 'hr'):
        return render_template('login.html', error='غير مصرح بالدخول إلى نظام شئون العاملين'), 403


def get_departments(session_obj):
    return session_obj.query(Department).order_by(Department.name.asc()).all()


def emp_to_dict(emp):
    return {
        'id': emp.id,
        'employee_number': emp.employee_number,
        'first_name': emp.first_name,
        'last_name': emp.last_name,
        'national_id': emp.national_id,
        'department_id': emp.department_id,
        'department_name': emp.department.name if getattr(emp, 'department', None) else None,
        'job_title': emp.job_title or 'غير محدد',
        'hire_date': emp.hire_date.isoformat() if emp.hire_date else None,
        'salary': str(emp.salary),
        'phone': emp.phone,
        'email': emp.email,
        'status': emp.status or ('نشط' if emp.active else 'موقوف'),
        'active': bool(emp.active)
    }


@bp.route('/api/employees', methods=['GET'])
def list_employees():
    s = make_session()
    query = s.query(Employee)

    search = (request.args.get('q') or '').strip()
    department_id = request.args.get('department_id', type=int)
    status = (request.args.get('status') or '').strip()

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Employee.employee_number.ilike(like),
                Employee.first_name.ilike(like),
                Employee.last_name.ilike(like),
                Employee.national_id.ilike(like)
            )
        )
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if status:
        query = query.filter(Employee.status == status)

    emps = query.order_by(Employee.id.desc()).all()
    return jsonify([emp_to_dict(e) for e in emps])


@bp.route('/config', methods=['GET'])
def list_config():
    s = make_session()
    configs = s.query(HRConfig).all()
    out = []
    for c in configs:
        out.append({
            'id': c.id,
            'config_key': c.config_key,
            'config_value': c.config_value,
            'description': c.description
        })
    return jsonify(out)


@bp.route('/config/<string:key>', methods=['PUT'])
def update_config(key):
    data = request.json or {}
    s = make_session()
    cfg = s.query(HRConfig).filter_by(config_key=key).first()
    if cfg:
        cfg.config_value = data.get('config_value', cfg.config_value)
        cfg.description = data.get('description', cfg.description)
    else:
        cfg = HRConfig(config_key=key, config_value=data.get('config_value',''), description=data.get('description',''))
        s.add(cfg)
    s.commit()
    return jsonify({'config_key': cfg.config_key, 'config_value': cfg.config_value, 'description': cfg.description})


@bp.route('/api/employees/<int:emp_id>', methods=['GET'])
def get_employee(emp_id):
    s = make_session()
    emp = s.query(Employee).get(emp_id)
    if not emp:
        return jsonify({'error':'not found'}), 404
    return jsonify(emp_to_dict(emp))


@bp.route('/api/employees', methods=['POST'])
def create_employee():
    data = request.json or {}
    s = make_session()
    emp = Employee(
        employee_number=data.get('employee_number'),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        national_id=data.get('national_id'),
        department_id=data.get('department_id') or None,
        job_title=data.get('job_title') or 'غير محدد',
        hire_date=data.get('hire_date'),
        salary=Decimal(str(data.get('salary', '0'))),
        phone=data.get('phone'),
        email=data.get('email'),
        status=data.get('status') or 'Active',
        active=data.get('active', True)
    )
    s.add(emp)
    s.commit()
    return jsonify(emp_to_dict(emp)), 201


@bp.route('/api/employees/<int:emp_id>', methods=['PUT'])
def update_employee(emp_id):
    data = request.json or {}
    s = make_session()
    emp = s.query(Employee).get(emp_id)
    if not emp:
        return jsonify({'error':'not found'}), 404
    for k in ('employee_number','first_name','last_name','national_id','hire_date'):
        if k in data:
            setattr(emp, k, data[k])
    if 'department_id' in data:
        emp.department_id = data['department_id'] or None
    if 'job_title' in data:
        emp.job_title = data['job_title'] or 'غير محدد'
    if 'salary' in data:
        emp.salary = Decimal(str(data['salary']))
    if 'phone' in data:
        emp.phone = data['phone']
    if 'email' in data:
        emp.email = data['email']
    if 'status' in data:
        emp.status = data['status'] or 'Active'
    if 'active' in data:
        emp.active = bool(data['active'])
    s.commit()
    return jsonify(emp_to_dict(emp))


@bp.route('/api/employees/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    s = make_session()
    emp = s.query(Employee).get(emp_id)
    if not emp:
        return jsonify({'error':'not found'}), 404
    s.delete(emp)
    s.commit()
    return jsonify({'deleted': emp_id})


@bp.route('/payroll/run/<int:emp_id>', methods=['POST'])
def run_payroll(emp_id):
    s = make_session()
    cfg = ConfigLoader(s)
    payslip = compute_payslip(s, emp_id, cfg)
    return jsonify({
        'payslip_id': payslip.id,
        'gross_salary': str(payslip.gross_salary),
        'total_deductions': str(payslip.total_deductions),
        'net_salary': str(payslip.net_salary)
    })


@bp.route('/employees/<int:emp_id>/documents', methods=['POST'])
def upload_employee_document(emp_id):
    if 'document' not in request.files:
        return jsonify({'error':'no file provided'}), 400
    file = request.files['document']
    if file.filename == '':
        return jsonify({'error':'no file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error':'invalid file type'}), 400
    s = make_session()
    emp = s.query(Employee).get(emp_id)
    if not emp:
        return jsonify({'error':'not found'}), 404
    filename = secure_filename(file.filename)
    stored_filename = f"{uuid.uuid4().hex}_{filename}"
    folder = get_upload_folder()
    file.save(os.path.join(folder, stored_filename))
    from hr_models import EmployeeDocument
    doc = EmployeeDocument(
        employee_id=emp.id,
        filename=filename,
        stored_filename=stored_filename,
        description=request.form.get('description')
    )
    s.add(doc)
    s.commit()
    return jsonify({'id': doc.id, 'filename': filename}), 201


@bp.route('/employees/<int:emp_id>/documents/<int:doc_id>', methods=['GET'])
def download_employee_document(emp_id, doc_id):
    s = make_session()
    from hr_models import EmployeeDocument
    doc = s.query(EmployeeDocument).filter_by(id=doc_id, employee_id=emp_id).first()
    if not doc:
        return jsonify({'error':'not found'}), 404
    folder = get_upload_folder()
    return send_from_directory(folder, doc.stored_filename, as_attachment=True, download_name=doc.filename)


@bp.route('/settings', methods=['GET'])
def settings_page():
    return render_template('hr_settings.html')


# --------------------
# Employee HTML pages (CRUD)
# --------------------
@bp.route('/dashboard', methods=['GET'])
def hr_dashboard():
    s = make_session()
    total_employees = s.query(Employee).count()
    active_employees = s.query(Employee).filter(Employee.active.is_(True)).count()
    departments = get_departments(s)
    return render_template(
        'hr_dashboard.html',
        total_employees=total_employees,
        active_employees=active_employees,
        departments=departments
    )


@bp.route('/attendance', methods=['GET'])
def attendance_page():
    s = make_session()
    employees = s.query(Employee).order_by(Employee.id.desc()).limit(10).all()
    return render_template('hr_attendance.html', employees=employees)


@bp.route('/payroll', methods=['GET'])
def payroll_page():
    s = make_session()
    employees = s.query(Employee).order_by(Employee.id.desc()).all()
    payroll_rows = []
    for emp in employees:
        summary = build_employee_payroll_summary(s, emp.id)
        payroll_rows.append({
            'employee': emp,
            'summary': summary,
        })
    return render_template('hr_payroll.html', payroll_rows=payroll_rows)


@bp.route('/payroll/run/<int:emp_id>', methods=['POST'])
def payroll_run(emp_id):
    s = make_session()
    payslip = compute_payslip(s, emp_id)
    return redirect(f'/hr/payslip/{payslip.id}')


@bp.route('/payslip/<int:payslip_id>', methods=['GET'])
def payslip_view(payslip_id):
    s = make_session()
    payslip = s.query(Payslip).get(payslip_id)
    if not payslip:
        return 'Not found', 404

    employee = s.query(Employee).get(payslip.employee_id)
    summary = build_employee_payroll_summary(s, employee.id)
    return render_template('hr_payslip.html', payslip=payslip, employee=employee, summary=summary)


@bp.route('/leaves', methods=['GET'])
def leaves_page():
    s = make_session()
    employees = s.query(Employee).order_by(Employee.id.desc()).all()
    return render_template('hr_leaves.html', employees=employees)


@bp.route('/', methods=['GET'])
@bp.route('/employees', methods=['GET'])
def employees_page():
    s = make_session()
    query = s.query(Employee).join(Department, Employee.department_id == Department.id, isouter=True)

    search = (request.args.get('q') or '').strip()
    department_id = request.args.get('department_id', type=int)
    status = (request.args.get('status') or '').strip()

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Employee.employee_number.ilike(like),
                Employee.first_name.ilike(like),
                Employee.last_name.ilike(like),
                Employee.national_id.ilike(like)
            )
        )
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if status:
        query = query.filter(Employee.status == status)

    emps = query.order_by(Employee.id.desc()).all()
    departments = get_departments(s)
    return render_template(
        'hr_employees.html',
        employees=emps,
        departments=departments,
        search=search,
        department_id=department_id,
        status=status
    )


@bp.route('/employees/add', methods=['GET','POST'])
def employees_add():
    s = make_session()
    departments = get_departments(s)
    if request.method == 'POST':
        data = request.form
        emp = Employee(
            employee_number=data.get('employee_number') or f"EMP{(s.query(Employee).count() + 1):04d}",
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            national_id=data.get('national_id'),
            department_id=data.get('department_id') or None,
            job_title=data.get('job_title') or 'غير محدد',
            hire_date=data.get('hire_date') or None,
            salary=data.get('salary') or 0,
            phone=data.get('phone') or None,
            email=data.get('email') or None,
            status=data.get('status') or 'Active',
            active=data.get('active') in ('1', 'true', 'on', 'yes')
        )
        s.add(emp)
        s.commit()
        return redirect('/hr/employees')
    return render_template('hr_employee_form.html', employee=None, departments=departments)


@bp.route('/employees/edit/<int:emp_id>', methods=['GET','POST'])
def employees_edit(emp_id):
    s = make_session()
    emp = s.query(Employee).get(emp_id)
    if not emp:
        return "Not found", 404
    departments = get_departments(s)
    if request.method == 'POST':
        data = request.form
        emp.employee_number = data.get('employee_number') or emp.employee_number
        emp.first_name = data.get('first_name')
        emp.last_name = data.get('last_name')
        emp.national_id = data.get('national_id')
        emp.department_id = data.get('department_id') or None
        emp.job_title = data.get('job_title') or 'غير محدد'
        emp.hire_date = data.get('hire_date') or None
        emp.salary = data.get('salary') or emp.salary
        emp.phone = data.get('phone') or None
        emp.email = data.get('email') or None
        emp.status = data.get('status') or 'Active'
        emp.active = data.get('active') in ('1', 'true', 'on', 'yes')
        s.commit()
        return redirect('/hr/employees')
    return render_template('hr_employee_form.html', employee=emp, departments=departments)


@bp.route('/employees/<int:emp_id>/documents/view', methods=['GET'])
def employees_documents(emp_id):
    s = make_session()
    emp = s.query(Employee).get(emp_id)
    if not emp:
        return "Not found", 404
    return render_template('hr_employee_docs.html', employee=emp)


@bp.route('/employees/view/<int:emp_id>', methods=['GET','POST'])
def employee_profile(emp_id):
    s = make_session()
    emp = s.query(Employee).get(emp_id)
    if not emp:
        return "Not found", 404
    message = None
    if request.method == 'POST':
        if request.form.get('action') == 'run_payroll':
            cfg = ConfigLoader(s)
            payslip = compute_payslip(s, emp_id, cfg)
            message = f"تم إنشاء قسيمة راتب جديدة: الصافي {payslip.net_salary}"
    payslips = s.query(Payslip).filter_by(employee_id=emp_id).order_by(Payslip.created_at.desc()).limit(5).all()
    return render_template('hr_employee_profile.html', employee=emp, payslips=payslips, message=message)


@bp.route('/employees/delete/<int:emp_id>', methods=['POST'])
def employees_delete(emp_id):
    s = make_session()
    emp = s.query(Employee).get(emp_id)
    if not emp:
        return jsonify({'error':'not found'}), 404
    s.delete(emp)
    s.commit()
    return redirect('/hr/employees')
