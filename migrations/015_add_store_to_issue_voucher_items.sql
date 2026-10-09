SET @add_issue_store_column = IF(
    EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='issue_voucher_items' AND COLUMN_NAME='store_id'
    ),
    'SELECT 1',
    'ALTER TABLE issue_voucher_items ADD COLUMN store_id INT NULL AFTER item_id'
);
PREPARE issue_store_column_stmt FROM @add_issue_store_column;
EXECUTE issue_store_column_stmt;
DEALLOCATE PREPARE issue_store_column_stmt;

SET @add_issue_store_index = IF(
    EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='issue_voucher_items' AND INDEX_NAME='idx_issue_voucher_items_store'
    ),
    'SELECT 1',
    'ALTER TABLE issue_voucher_items ADD INDEX idx_issue_voucher_items_store (store_id)'
);
PREPARE issue_store_index_stmt FROM @add_issue_store_index;
EXECUTE issue_store_index_stmt;
DEALLOCATE PREPARE issue_store_index_stmt;
