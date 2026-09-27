from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hr_models import Base, Employee, HRConfig
from hr_payroll import build_employee_payroll_summary


def test_build_employee_payroll_summary_uses_salary_and_deductions():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.add(HRConfig(config_key='egypt_social_insurance_ceiling', config_value='0'))
    session.add(HRConfig(config_key='egypt_social_insurance_employee_rate', config_value='0.14'))
    session.add(HRConfig(config_key='egypt_social_insurance_employer_rate', config_value='0.14'))
    session.add(HRConfig(config_key='egypt_health_insurance_employee_rate', config_value='0.02'))
    session.add(HRConfig(config_key='egypt_health_insurance_employer_rate', config_value='0.02'))
    session.add(HRConfig(config_key='egypt_income_tax_brackets', config_value='[{"up_to": 15000, "rate": 0.10}]'))

    emp = Employee(
        employee_number='EMP999',
        first_name='Test',
        last_name='User',
        national_id='12345678901234',
        hire_date=date(2024, 1, 1),
        salary=Decimal('10000.00'),
        active=True,
        job_title='محاسب',
        status='Active',
        phone='01000000000',
        email='test@example.com',
    )
    session.add(emp)
    session.commit()

    summary = build_employee_payroll_summary(session, emp.id)

    assert summary['gross_salary'] == Decimal('10000.00')
    assert summary['total_deductions'] > Decimal('0.00')
    assert summary['net_salary'] < summary['gross_salary']
    assert summary['employee_pension'] > Decimal('0.00')
