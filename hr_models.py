from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (Column, Integer, String, Date, DateTime, Numeric, Boolean, Text, ForeignKey, create_engine)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class HRConfig(Base):
    __tablename__ = 'hr_config'
    id = Column(Integer, primary_key=True)
    config_key = Column(String(128), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    employee_number = Column(String(32), unique=True, nullable=False)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    national_id = Column(String(32), unique=True)
    hire_date = Column(Date, nullable=False)
    salary = Column(Numeric(12,2), nullable=False)
    active = Column(Boolean, default=True)
    contracts = relationship('Contract', back_populates='employee')
    documents = relationship('EmployeeDocument', back_populates='employee', cascade='all, delete-orphan')

class EmployeeDocument(Base):
    __tablename__ = 'employee_documents'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    filename = Column(String(256), nullable=False)
    stored_filename = Column(String(256), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    description = Column(String(256), nullable=True)
    employee = relationship('Employee', back_populates='documents')

class Contract(Base):
    __tablename__ = 'contracts'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    salary = Column(Numeric(12,2), nullable=False)
    job_title = Column(String(128))
    employee = relationship('Employee', back_populates='contracts')

class PayrollRun(Base):
    __tablename__ = 'payroll_runs'
    id = Column(Integer, primary_key=True)
    run_date = Column(DateTime, default=datetime.utcnow)
    period_start = Column(Date)
    period_end = Column(Date)
    notes = Column(Text)

class Payslip(Base):
    __tablename__ = 'payslips'
    id = Column(Integer, primary_key=True)
    payroll_run_id = Column(Integer, ForeignKey('payroll_runs.id'))
    employee_id = Column(Integer, ForeignKey('employees.id'))
    gross_salary = Column(Numeric(12,2))
    total_deductions = Column(Numeric(12,2))
    net_salary = Column(Numeric(12,2))
    created_at = Column(DateTime, default=datetime.utcnow)
    employee = relationship('Employee', backref='payslips')

# Utility: simple engine/session factory for local testing
def make_session(sqlite_url='sqlite:///hr_dev.db'):
    engine = create_engine(sqlite_url, echo=False, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()
