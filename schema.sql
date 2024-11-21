CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    green_number INTEGER NOT NULL,
    category TEXT NOT NULL,
    status TEXT CHECK(status IN ('yes', 'no')) DEFAULT 'no',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borrower_name TEXT NOT NULL,
    item_name TEXT NOT NULL,
    green_number TEXT NOT NULL,
    loan_date TEXT NOT NULL,
    return_date TEXT,
    signature TEXT,
    status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS loans_equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL,
    equipment_type TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (loan_id) REFERENCES loans (id)
);