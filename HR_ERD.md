**HR System ERD (مخطط الكيانات والعلاقات)**

مرحباً — هذا مخطط ERD مبدئي لنظام شؤون عاملين احترافي يغطي الموظفين، العقود، الحضور، الرواتب، والاستحقاقات التأمينية.

```mermaid
erDiagram
    USERS {
        int id PK
        varchar username
        varchar password_hash
        varchar role
        datetime created_at
    }

    EMPLOYEES {
        int id PK
        varchar employee_code
        varchar first_name
        varchar last_name
        date dob
        varchar national_id
        varchar gender
        date hire_date
        date end_date
        int department_id FK
        int manager_id FK
        varchar status
        datetime created_at
    }

    DEPARTMENTS {
        int id PK
        varchar name
        varchar code
    }

    CONTRACTS {
        int id PK
        int employee_id FK
        varchar contract_type
        date start_date
        date end_date
        decimal base_salary
        decimal salary_currency
        text notes
    }

    ATTENDANCE {
        int id PK
        int employee_id FK
        date date
        datetime time_in
        datetime time_out
        decimal hours_worked
        varchar source
    }

    LEAVES {
        int id PK
        int employee_id FK
        varchar leave_type
        date start_date
        date end_date
        decimal days
        varchar status
        text reason
    }

    PAYROLLS {
        int id PK
        int employee_id FK
        date period_start
        date period_end
        date pay_date
        decimal gross_salary
        decimal total_deductions
        decimal total_allowances
        decimal net_salary
        varchar status
    }

    PAYROLL_LINES {
        int id PK
        int payroll_id FK
        varchar code
        varchar description
        decimal amount
        varchar type  "ALLOWANCE|DEDUCTION"
    }

    SOCIAL_INSURANCE_RECORDS {
        int id PK
        int employee_id FK
        date effective_date
        decimal employer_share
        decimal employee_share
        decimal total
        varchar scheme
        varchar reference_no
    }

    MEDICAL_INSURANCE_RECORDS {
        int id PK
        int employee_id FK
        date effective_date
        varchar provider
        decimal premium
        varchar policy_no
    }

    DOCUMENTS {
        int id PK
        int employee_id FK
        varchar doc_type
        varchar filename
        varchar path
        date uploaded_at
    }

    EMPLOYEES ||--o{ CONTRACTS : has
    EMPLOYEES ||--o{ ATTENDANCE : records
    EMPLOYEES ||--o{ LEAVES : "requests"
    EMPLOYEES ||--o{ PAYROLLS : "pays"
    PAYROLLS ||--o{ PAYROLL_LINES : lines
    EMPLOYEES ||--o{ SOCIAL_INSURANCE_RECORDS : "social"
    EMPLOYEES ||--o{ MEDICAL_INSURANCE_RECORDS : "medical"
    EMPLOYEES ||--o{ DOCUMENTS : "files"
    DEPARTMENTS ||--o{ EMPLOYEES : contains
    USERS ||--o{ EMPLOYEES : manages
```

ملاحظات تصميمية سريعة:
- جداول `PAYROLLS` و`PAYROLL_LINES` تسمح بتفصيل أي بند (بدلات/اقتطاعات). هذا يسهل طباعة قسائم الرواتب.
- `SOCIAL_INSURANCE_RECORDS` و`MEDICAL_INSURANCE_RECORDS` تحتفظان بتاريخ التغيرات (effective_date) حتى يمكن حساب الاستقطاعات حسب فترة.
- `CONTRACTS` تفصل بيانات عقد الموظف (может быть multiple contracts per employee).

التالي: أُنشئ ملف ترحيل SQL مبدئي لإنشاء هذه الجداول مع المفاتيح الأساسية والأجنبية، ثم أجربه على قاعدة بيانات محلية إذا رغبت.
