-- Migration: 001_create_hr_schema.sql
-- Basic HR schema migration (MySQL-compatible)

CREATE TABLE departments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  code VARCHAR(50) DEFAULT NULL
) ENGINE=InnoDB;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE employees (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_code VARCHAR(50) UNIQUE,
  first_name VARCHAR(120) NOT NULL,
  last_name VARCHAR(120) NOT NULL,
  dob DATE DEFAULT NULL,
  national_id VARCHAR(100) DEFAULT NULL,
  gender VARCHAR(10) DEFAULT NULL,
  hire_date DATE DEFAULT NULL,
  end_date DATE DEFAULT NULL,
  department_id INT DEFAULT NULL,
  manager_id INT DEFAULT NULL,
  status VARCHAR(30) DEFAULT 'active',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
  FOREIGN KEY (manager_id) REFERENCES employees(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE contracts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  contract_type VARCHAR(50) NOT NULL,
  start_date DATE,
  end_date DATE,
  base_salary DECIMAL(12,2) DEFAULT 0,
  currency CHAR(3) DEFAULT 'EGP',
  notes TEXT,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE attendance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  date DATE NOT NULL,
  time_in DATETIME DEFAULT NULL,
  time_out DATETIME DEFAULT NULL,
  hours_worked DECIMAL(6,2) DEFAULT 0,
  source VARCHAR(50) DEFAULT 'manual',
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
  UNIQUE KEY ux_attendance_employee_date (employee_id, date)
) ENGINE=InnoDB;

CREATE TABLE leaves (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  leave_type VARCHAR(50) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  days DECIMAL(5,2) DEFAULT 0,
  status VARCHAR(30) DEFAULT 'pending',
  reason TEXT,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE payrolls (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  period_start DATE,
  period_end DATE,
  pay_date DATE,
  gross_salary DECIMAL(12,2) DEFAULT 0,
  total_allowances DECIMAL(12,2) DEFAULT 0,
  total_deductions DECIMAL(12,2) DEFAULT 0,
  net_salary DECIMAL(12,2) DEFAULT 0,
  status VARCHAR(30) DEFAULT 'draft',
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE payroll_lines (
  id INT AUTO_INCREMENT PRIMARY KEY,
  payroll_id INT NOT NULL,
  code VARCHAR(50) DEFAULT NULL,
  description VARCHAR(255) DEFAULT NULL,
  amount DECIMAL(12,2) DEFAULT 0,
  type ENUM('ALLOWANCE','DEDUCTION') NOT NULL,
  FOREIGN KEY (payroll_id) REFERENCES payrolls(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE social_insurance_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  effective_date DATE NOT NULL,
  employer_share DECIMAL(12,2) DEFAULT 0,
  employee_share DECIMAL(12,2) DEFAULT 0,
  total DECIMAL(12,2) DEFAULT 0,
  scheme VARCHAR(100),
  reference_no VARCHAR(100),
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE medical_insurance_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  effective_date DATE NOT NULL,
  provider VARCHAR(150),
  premium DECIMAL(12,2) DEFAULT 0,
  policy_no VARCHAR(100),
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE documents (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  doc_type VARCHAR(100),
  filename VARCHAR(255),
  path VARCHAR(500),
  uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Indexes for performance
CREATE INDEX idx_emp_code ON employees(employee_code);
CREATE INDEX idx_payroll_employee ON payrolls(employee_id);

COMMIT;
