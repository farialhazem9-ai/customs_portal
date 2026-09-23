-- Migration: Egypt social & medical insurance, and basic tax config
-- This file inserts configurable rates/thresholds used by the payroll engine.

INSERT INTO hr_config (config_key, config_value, description) VALUES
('egypt_social_insurance_employee_rate', '0.14', 'Employee pension contribution rate (14%)'),
('egypt_social_insurance_employer_rate', '0.18', 'Employer pension contribution rate (18%)'),
('egypt_social_insurance_ceiling', '15000', 'Monthly salary ceiling for pension contributions in EGP'),
('egypt_health_insurance_employee_rate', '0.02', 'Employee health insurance contribution rate (2%)'),
('egypt_health_insurance_employer_rate', '0.04', 'Employer health insurance contribution rate (4%)'),
('egypt_income_tax_brackets', '[{"up_to":15000,"rate":0.0},{"up_to":30000,"rate":0.1},{"up_to":45000,"rate":0.15},{"up_to":60000,"rate":0.2},{"up_to":1000000,"rate":0.25}]', 'Progressive monthly tax brackets JSON example');
