import sqlite3
import os
from flask import g

DATABASE = 'inventory.db'


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()

    # Create or update inventory table
    with open('schema.sql', 'r') as f:
        db.executescript(f.read())

    # Update loans table structure
    try:
        db.execute('SELECT green_number FROM loans LIMIT 1')
    except sqlite3.OperationalError:
        # Column doesn't exist, let's add it
        with open('update_loans.sql', 'r') as f:
            db.executescript(f.read())

    db.commit()