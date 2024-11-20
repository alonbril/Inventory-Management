import sqlite3


def add_signature_column():
    try:
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()

        # Add signature column to existing loans table
        cursor.execute('''
            ALTER TABLE loans 
            ADD COLUMN signature TEXT
        ''')

        conn.commit()
        print("Successfully added signature column")

    except sqlite3.OperationalError as e:
        print("Error:", str(e))

    finally:
        conn.close()


if __name__ == "__main__":
    add_signature_column()