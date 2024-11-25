import sqlite3
import os
import sys
from flask import g


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_db_path():
    """Get the database path, ensuring it's in a writable location"""
    if getattr(sys, 'frozen', False):
        # If running as compiled executable
        app_dir = os.path.dirname(sys.executable)
        db_path = os.path.join(app_dir, 'inventory.db')
    else:
        # If running in development
        db_path = 'inventory.db'
    return db_path


def create_tables(connection):
    """Create all necessary tables"""
    cursor = connection.cursor()

    # Create tables with consolidated schema
    cursor.executescript('''
        -- Create inventory table
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            green_number INTEGER NOT NULL,
            category TEXT NOT NULL,
            status TEXT CHECK(status IN ('yes', 'no')) DEFAULT 'no',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create loans table
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            borrower_name TEXT NOT NULL,
            item_name TEXT NOT NULL,
            green_number INTEGER NOT NULL,
            loan_date TEXT NOT NULL,
            return_date TEXT,
            signature TEXT,
            status TEXT DEFAULT 'active'
        );

        -- Create loans_equipment table
        CREATE TABLE IF NOT EXISTS loans_equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL,
            equipment_type TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (loan_id) REFERENCES loans (id)
        );

        -- Create indices for better performance
        CREATE INDEX IF NOT EXISTS idx_inventory_green_number ON inventory(green_number);
        CREATE INDEX IF NOT EXISTS idx_loans_green_number ON loans(green_number);
        CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
    ''')

    connection.commit()


# Create database file if it doesn't exist
DATABASE = get_db_path()
if not os.path.exists(DATABASE):
    conn = sqlite3.connect(DATABASE)
    create_tables(conn)  # Create tables immediately when database is created
    conn.close()
    print(f"Created new database file with tables: {DATABASE}")


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row

        # Verify tables exist, create if they don't
        create_tables(g.db)
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database and create tables if they don't exist"""
    try:
        db = get_db()
        create_tables(db)  # Ensure tables exist
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        if 'db' in g:
            g.db.rollback()
        return False


def verify_database_structure():
    """Verify that all required tables exist"""
    try:
        db = get_db()
        cursor = db.cursor()

        # Check each table
        required_tables = ['inventory', 'loans', 'loans_equipment']
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                print(f"Table {table} is missing, creating tables...")
                create_tables(db)
                return

        print("All required tables exist")
    except Exception as e:
        print(f"Error verifying database structure: {e}")