-- Add export invoice metadata fields for storage permit and export document numbers
ALTER TABLE customs_invoices
  ADD COLUMN IF NOT EXISTS storage_permit_no VARCHAR(50) NULL,
  ADD COLUMN IF NOT EXISTS export_no VARCHAR(50) NULL;
