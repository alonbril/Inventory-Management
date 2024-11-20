# database.py
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

    # Create tables if they don't exist
    with open('schema.sql', 'r') as f:
        db.executescript(f.read())

    # Check if signature column exists
    try:
        db.execute('SELECT signature FROM loans LIMIT 1')
    except sqlite3.OperationalError:
        # Add signature column if it doesn't exist
        db.execute('ALTER TABLE loans ADD COLUMN signature TEXT')

    db.commit()