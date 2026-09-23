from hr_models import make_session, Employee
import hr_seed
from hr_payroll import ConfigLoader, compute_payslip

s = make_session()
cfg = ConfigLoader(s)

emp = s.query(Employee).first()
if not emp:
    raise SystemExit('No employee found after seeding')

p = compute_payslip(s, emp.id, cfg)
print('Payslip generated:')
print('Employee:', emp.first_name, emp.last_name)
print('Gross:', p.gross_salary)
print('Deductions:', p.total_deductions)
print('Net:', p.net_salary)
