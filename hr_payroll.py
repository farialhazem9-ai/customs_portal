import json
from decimal import Decimal, ROUND_HALF_UP
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
    return Decimal(str(v)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_income_tax(taxable_income, tax_brackets):
    income_tax = Decimal('0')
    remaining = taxable_income
    last_limit = Decimal('0')
    for bracket in tax_brackets:
        up_to = Decimal(str(bracket.get('up_to', 0)))
        rate = Decimal(str(bracket.get('rate', 0)))
        if remaining <= 0:
            break
        taxable_chunk = min(remaining, up_to - last_limit) if up_to > last_limit else Decimal('0')
        if taxable_chunk > 0:
            income_tax += taxable_chunk * rate
            remaining -= taxable_chunk
        last_limit = up_to
    return money(income_tax)


def build_employee_payroll_summary(session, employee_id):
    emp = session.query(Employee).get(employee_id)
    if not emp:
        raise ValueError('Employee not found')

    config_loader = ConfigLoader(session)
    gross = money(emp.salary)
    pension_ceiling = Decimal(str(config_loader.get('egypt_social_insurance_ceiling', '0')))
    emp_pension_rate = Decimal(str(config_loader.get('egypt_social_insurance_employee_rate', '0')))
    emp_health_rate = Decimal(str(config_loader.get('egypt_health_insurance_employee_rate', '0')))
    tax_brackets = config_loader.get('egypt_income_tax_brackets', [])

    pensionable_salary = gross if pension_ceiling == 0 or gross <= pension_ceiling else pension_ceiling
    employee_pension = money(pensionable_salary * emp_pension_rate)
    employee_health = money(gross * emp_health_rate)
    taxable_income = gross - employee_pension - employee_health
    income_tax = calculate_income_tax(taxable_income, tax_brackets)
    total_deductions = money(employee_pension + employee_health + income_tax)
    net_salary = money(gross - total_deductions)

    return {
        'employee_id': emp.id,
        'gross_salary': gross,
        'employee_pension': employee_pension,
        'employee_health': employee_health,
        'income_tax': income_tax,
        'total_deductions': total_deductions,
        'net_salary': net_salary,
        'allowances': Decimal('0.00'),
    }


def compute_payslip(session, employee_id, config_loader=None):
    emp = session.query(Employee).get(employee_id)
    if not emp:
        raise ValueError('Employee not found')

    if config_loader is None:
        config_loader = ConfigLoader(session)

    summary = build_employee_payroll_summary(session, employee_id)
    payslip = Payslip(
        employee_id=emp.id,
        gross_salary=summary['gross_salary'],
        total_deductions=summary['total_deductions'],
        net_salary=summary['net_salary']
    )
    session.add(payslip)
    session.commit()
    return payslip
