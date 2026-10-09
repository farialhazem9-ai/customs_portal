-- Add export invoice metadata fields for storage permit and export document numbers
ALTER TABLE customs_invoices
  ADD COLUMN storage_permit_no VARCHAR(50) NULL;

ALTER TABLE customs_invoices
  ADD COLUMN export_no VARCHAR(50) NULL;
