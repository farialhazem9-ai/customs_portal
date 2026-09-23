-- Migration: add inventory balance and customs regime fields

ALTER TABLE items
  ADD COLUMN IF NOT EXISTS current_balance DECIMAL(15,2) NOT NULL DEFAULT 0.00;

ALTER TABLE customs_declarations
  ADD COLUMN IF NOT EXISTS regime_type VARCHAR(100) NULL;

UPDATE items
SET current_balance = COALESCE(current_balance, 0.00)
WHERE current_balance IS NULL;