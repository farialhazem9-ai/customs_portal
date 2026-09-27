CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NULL,
    username VARCHAR(150) NULL,
    action VARCHAR(40) NOT NULL,
    module VARCHAR(100) NOT NULL,
    description TEXT NULL,
    ip_address VARCHAR(45) NULL,
    request_method VARCHAR(10) NULL,
    request_path VARCHAR(255) NULL,
    status_code SMALLINT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_audit_created_at (created_at),
    INDEX idx_audit_username (username),
    INDEX idx_audit_action (action),
    INDEX idx_audit_module (module),
    INDEX idx_audit_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE audit_logs ADD COLUMN username VARCHAR(150) NULL;
ALTER TABLE audit_logs ADD COLUMN action VARCHAR(40) NULL;
ALTER TABLE audit_logs ADD COLUMN module VARCHAR(100) NULL;
ALTER TABLE audit_logs ADD COLUMN description TEXT NULL;
ALTER TABLE audit_logs ADD COLUMN request_method VARCHAR(10) NULL;
ALTER TABLE audit_logs ADD COLUMN request_path VARCHAR(255) NULL;
ALTER TABLE audit_logs ADD COLUMN status_code SMALLINT NULL;
