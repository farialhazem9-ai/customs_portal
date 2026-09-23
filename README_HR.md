HR module quick start

Files added:
- HR_requirements.md — requirements checklist and Egypt-specific questions
- HR_policies_egypt.md — default policies and calculation examples
- hr_models.py, hr_payroll.py, hr_seed.py, hr_test_payslip.py — models, payroll engine, seed and test
- hr_api.py — simple Flask Blueprint exposing CRUD and payroll run
- migrations/002_hr_egypt_rates.sql — initial config insertion for Egypt rates

Quick run (dev):

```bash
pip install -r requirements.txt
python hr_seed.py
python hr_test_payslip.py
# start app (will register HR Blueprint)
python app.py
```

Next recommended steps:
- Confirm statutory rates/thresholds for Egypt and update `hr_config` via migration.
- Add authentication/authorization for HR endpoints.
- Build admin UI for employee management and payroll runs.
