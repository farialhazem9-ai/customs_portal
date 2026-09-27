-- HR enhancements for employee directory and roster management
-- MySQL-compatible migration

CREATE TABLE IF NOT EXISTS departments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  code VARCHAR(50) NULL UNIQUE
) ENGINE=InnoDB;

ALTER TABLE employees
  ADD COLUMN IF NOT EXISTS department_id INT NULL,
  ADD COLUMN IF NOT EXISTS job_title VARCHAR(128) NULL,
  ADD COLUMN IF NOT EXISTS phone VARCHAR(32) NULL,
  ADD COLUMN IF NOT EXISTS email VARCHAR(128) NULL,
  ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'Active';

ALTER TABLE employees
  ADD CONSTRAINT fk_employees_department
  FOREIGN KEY (department_id) REFERENCES departments(id)
  ON DELETE SET NULL;

CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_employees_status ON employees(status);
