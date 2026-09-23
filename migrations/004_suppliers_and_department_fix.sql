-- Migration: ensure suppliers table and items.department column exist

CREATE TABLE IF NOT EXISTS suppliers (
  id INT NOT NULL AUTO_INCREMENT,
  supplier_name VARCHAR(255) NOT NULL,
  supplier_code VARCHAR(100) NULL,
  phone VARCHAR(100) NULL,
  email VARCHAR(255) NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_suppliers_code (supplier_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE items
  ADD COLUMN IF NOT EXISTS department VARCHAR(255) NOT NULL DEFAULT 'local_purchases';

UPDATE items
SET department = COALESCE(department, 'local_purchases')
WHERE department IS NULL;
