import os
import uuid
from flask import Blueprint, request, jsonify, render_template, redirect, current_app, send_from_directory, session, url_for
from werkzeug.utils import secure_filename
from hr_models import Employee, HRConfig, EmployeeDocument, Payslip
from hr_db import get_session as make_session
from hr_payroll import ConfigLoader, compute_payslip
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


def emp_to_dict(emp):
    return {
        'id': emp.id,
        'employee_number': emp.employee_number,
        'first_name': emp.first_name,
        'last_name': emp.last_name,
        'national_id': emp.national_id,
        'hire_date': emp.hire_date.isoformat() if emp.hire_date else None,
        'salary': str(emp.salary),
        'active': bool(emp.active)
    }


@bp.route('/api/employees', methods=['GET'])
def list_employees():
    s = make_session()
    emps = s.query(Employee).all()
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
        hire_date=data.get('hire_date'),
        salary=Decimal(str(data.get('salary', '0'))),
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
    if 'salary' in data:
        emp.salary = Decimal(str(data['salary']))
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
@bp.route('/', methods=['GET'])
@bp.route('/employees', methods=['GET'])
def employees_page():
    s = make_session()
    emps = s.query(Employee).order_by(Employee.id.desc()).all()
    return render_template('hr_employees.html', employees=emps)


@bp.route('/employees/add', methods=['GET','POST'])
def employees_add():
    s = make_session()
    if request.method == 'POST':
        data = request.form
        emp = Employee(
            employee_number=data.get('employee_number'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            national_id=data.get('national_id'),
            hire_date=data.get('hire_date') or None,
            salary=data.get('salary') or 0,
            active=True
        )
        s.add(emp)
        s.commit()
        return redirect('/hr/employees')
    return render_template('hr_employee_form.html', employee=None)


@bp.route('/employees/edit/<int:emp_id>', methods=['GET','POST'])
def employees_edit(emp_id):
    s = make_session()
    emp = s.query(Employee).get(emp_id)
    if not emp:
        return "Not found", 404
    if request.method == 'POST':
        data = request.form
        emp.employee_number = data.get('employee_number')
        emp.first_name = data.get('first_name')
        emp.last_name = data.get('last_name')
        emp.national_id = data.get('national_id')
        emp.hire_date = data.get('hire_date') or None
        emp.salary = data.get('salary') or emp.salary
        emp.active = True if data.get('active') in ('1','true','on') else False
        s.commit()
        return redirect('/hr/employees')
    return render_template('hr_employee_form.html', employee=emp)


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
