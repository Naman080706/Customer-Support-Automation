-- SQLite memory schema for the Customer Support Automation System (Task 7)
-- Recreate the memory database manually with:
--     sqlite3 memory.db < schema.sql

CREATE TABLE IF NOT EXISTS interactions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id   TEXT NOT NULL,
    customer_name TEXT,
    query         TEXT NOT NULL,
    intent        TEXT,
    department    TEXT,
    response      TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customer ON interactions(customer_id);
