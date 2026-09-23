import json
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from hr_models import HRConfig, Employee, Payslip


class ConfigLoader:
    def __init__(self, session):
        self.session = session
        self._cache = {}

    def get(self, key, default=None):
        if key in self._cache:
            return self._cache[key]
        cfg = self.session.query(HRConfig).filter_by(config_key=key).first()
        if not cfg:
            return default
        try:
            val = json.loads(cfg.config_value)
        except Exception:
            val = cfg.config_value
        self._cache[key] = val
        return val


def money(v):
    return Decimal(v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def compute_payslip(session, employee_id, config_loader):
    emp = session.query(Employee).get(employee_id)
    if not emp:
        raise ValueError('Employee not found')

    gross = Decimal(emp.salary)
    # Pensions (social insurance)
    pension_ceiling = Decimal(config_loader.get('egypt_social_insurance_ceiling', '0'))
    emp_pension_rate = Decimal(config_loader.get('egypt_social_insurance_employee_rate', '0'))
    employer_pension_rate = Decimal(config_loader.get('egypt_social_insurance_employer_rate', '0'))

    # Health insurance
    emp_health_rate = Decimal(config_loader.get('egypt_health_insurance_employee_rate', '0'))
    employer_health_rate = Decimal(config_loader.get('egypt_health_insurance_employer_rate', '0'))

    # Income tax brackets
    tax_brackets = config_loader.get('egypt_income_tax_brackets', [])

    # Apply ceiling
    pensionable_salary = gross if pension_ceiling == 0 or gross <= pension_ceiling else pension_ceiling
    emp_pension = money(pensionable_salary * emp_pension_rate)
    employer_pension = money(pensionable_salary * employer_pension_rate)

    emp_health = money(gross * emp_health_rate)
    employer_health = money(gross * employer_health_rate)

    # Income tax (progressive)
    taxable_income = gross - emp_pension - emp_health

    income_tax = Decimal('0')
    remaining = taxable_income
    last_limit = Decimal('0')
    for bracket in tax_brackets:
        up_to = Decimal(bracket.get('up_to', 0))
        rate = Decimal(str(bracket.get('rate', 0)))
        if remaining <= 0:
            break
        taxable_chunk = min(remaining, up_to - last_limit) if up_to > last_limit else Decimal('0')
        if taxable_chunk > 0:
            income_tax += taxable_chunk * rate
            remaining -= taxable_chunk
        last_limit = up_to

    income_tax = money(income_tax)

    total_deductions = money(emp_pension + emp_health + income_tax)
    net = money(gross - total_deductions)

    payslip = Payslip(
        employee_id=emp.id,
        gross_salary=gross,
        total_deductions=total_deductions,
        net_salary=net
    )
    session.add(payslip)
    session.commit()
    return payslip
