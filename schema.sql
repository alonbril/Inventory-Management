CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    green_number REAL NOT NULL,
    category TEXT NOT NULL,
    status TEXT CHECK(status IN ('yes', 'no')) DEFAULT 'no',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    borrower_name TEXT NOT NULL,
    loan_date DATE NOT NULL,
    return_date DATE,
    status TEXT CHECK(status IN ('active', 'returned')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
