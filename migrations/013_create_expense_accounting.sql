CREATE TABLE IF NOT EXISTS expense_accounts (
    id INT NOT NULL AUTO_INCREMENT,
    account_code VARCHAR(50) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_type ENUM('cash', 'bank', 'petty_cash', 'credit', 'other') NOT NULL DEFAULT 'cash',
    current_balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    notes TEXT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_expense_account_code (account_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS expense_categories (
    id INT NOT NULL AUTO_INCREMENT,
    category_name VARCHAR(255) NOT NULL,
    category_code VARCHAR(50) NULL,
    parent_id INT NULL,
    notes TEXT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_expense_categories_parent (parent_id),
    UNIQUE KEY uq_expense_category_code (category_code),
    CONSTRAINT fk_expense_category_parent FOREIGN KEY (parent_id) REFERENCES expense_categories (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS expenses (
    id INT NOT NULL AUTO_INCREMENT,
    account_id INT NOT NULL,
    category_id INT NULL,
    expense_date DATE NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    reference_no VARCHAR(100) NULL,
    description TEXT NULL,
    payment_method ENUM('cash', 'bank_transfer', 'card', 'check', 'other') NOT NULL DEFAULT 'cash',
    status ENUM('pending', 'approved', 'reversed') NOT NULL DEFAULT 'approved',
    created_by INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_expenses_account (account_id),
    KEY idx_expenses_category (category_id),
    KEY idx_expenses_date (expense_date),
    CONSTRAINT fk_expenses_account FOREIGN KEY (account_id) REFERENCES expense_accounts (id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_expenses_category FOREIGN KEY (category_id) REFERENCES expense_categories (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS expense_account_transactions (
    id BIGINT NOT NULL AUTO_INCREMENT,
    account_id INT NOT NULL,
    related_expense_id INT NULL,
    transaction_type ENUM('opening_balance', 'expense', 'reversal', 'adjustment') NOT NULL,
    amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    note TEXT NULL,
    created_by INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_expense_account_txn_account (account_id),
    KEY idx_expense_account_txn_expense (related_expense_id),
    CONSTRAINT fk_expense_txn_account FOREIGN KEY (account_id) REFERENCES expense_accounts (id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_expense_txn_expense FOREIGN KEY (related_expense_id) REFERENCES expenses (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO expense_accounts (account_code, account_name, account_type, current_balance, notes)
SELECT 'CASH-001', 'الصندوق الرئيسي', 'cash', 0.00, 'الحساب الافتراضي لإدارة المصروفات'
WHERE NOT EXISTS (SELECT 1 FROM expense_accounts WHERE account_code = 'CASH-001');

INSERT INTO expense_categories (category_name, category_code, notes)
SELECT 'مصروفات عامة', 'GEN-001', 'فئة افتراضية للإدارة العامة'
WHERE NOT EXISTS (SELECT 1 FROM expense_categories WHERE category_code = 'GEN-001');
