CREATE TABLE IF NOT EXISTS issue_voucher_sequences (
    issue_date DATE NOT NULL,
    sequence_value INT UNSIGNED NOT NULL DEFAULT 0,
    PRIMARY KEY (issue_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
