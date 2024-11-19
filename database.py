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
    # Create new tables if they don't exist
    with open('schema.sql', 'r') as f:
        db.executescript(f.read())

    # Check if we need to update existing database
    try:
        db.execute('SELECT status FROM inventory LIMIT 1')
    except sqlite3.OperationalError:
        # Column doesn't exist, perform update
        with open('schema_update.sql', 'r') as f:
            db.executescript(f.read())
    db.commit()