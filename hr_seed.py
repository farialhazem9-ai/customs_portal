from hr_models import make_session, Employee, HRConfig
from decimal import Decimal

s = make_session()

# seed config if not present
configs = [
    ('egypt_social_insurance_employee_rate', '0.14', 'Employee pension contribution rate (14%)'),
    ('egypt_social_insurance_employer_rate', '0.18', 'Employer pension contribution rate (18%)'),
    ('egypt_social_insurance_ceiling', '15000', 'Monthly salary ceiling for pension contributions in EGP'),
    ('egypt_health_insurance_employee_rate', '0.02', 'Employee health insurance contribution rate (2%)'),
    ('egypt_health_insurance_employer_rate', '0.04', 'Employer health insurance contribution rate (4%)'),
    ('egypt_income_tax_brackets', '[{"up_to":15000,"rate":0.0},{"up_to":30000,"rate":0.1},{"up_to":45000,"rate":0.15},{"up_to":60000,"rate":0.2},{"up_to":1000000,"rate":0.25}]', 'Progressive monthly tax brackets JSON example')
]

for k,v,d in configs:
    q = s.query(HRConfig).filter_by(config_key=k).first()
    if not q:
        s.add(HRConfig(config_key=k, config_value=v, description=d))

# seed an employee
if not s.query(Employee).first():
    s.add(Employee(employee_number='EMP001', first_name='Ahmed', last_name='Ali', national_id='12345678901234', hire_date='2022-01-01', salary=Decimal('12000.00')))

s.commit()
print('Seeded hr_dev.db with sample data')
