-- Migration: Add unit_price and line_total to purchase_order_items
-- Run on testing DB first

ALTER TABLE purchase_order_items
  ADD COLUMN IF NOT EXISTS unit_price DECIMAL(10,2) NULL,
  ADD COLUMN IF NOT EXISTS line_total DECIMAL(12,2) NULL;

UPDATE purchase_order_items SET unit_price = 0.00 WHERE unit_price IS NULL;
UPDATE purchase_order_items SET line_total = 0.00 WHERE line_total IS NULL;

ALTER TABLE purchase_order_items
  MODIFY unit_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  MODIFY line_total DECIMAL(12,2) NOT NULL DEFAULT 0.00;

-- Optional: add department and receiver_name to issue_vouchers if missing
ALTER TABLE issue_vouchers
  ADD COLUMN IF NOT EXISTS department VARCHAR(255) NULL,
  ADD COLUMN IF NOT EXISTS receiver_name VARCHAR(255) NULL;

-- Fill defaults
UPDATE issue_vouchers SET department = COALESCE(department, 'غير محدد') WHERE department IS NULL;
UPDATE issue_vouchers SET receiver_name = COALESCE(receiver_name, '') WHERE receiver_name IS NULL;
