from flask import Flask, render_template, request, redirect, url_for, flash, g, session
from database import init_db, get_db, close_db, get_db_path, verify_database_structure
from datetime import datetime, date, timedelta
import pandas as pd
from werkzeug.utils import secure_filename

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Define DATABASE path before app creation
DATABASE = get_db_path()

app = Flask(__name__,
            template_folder=resource_path('templates'),
            static_folder=resource_path('static'))

app.secret_key = 'dev'

# Configure upload folder
UPLOAD_FOLDER = resource_path('uploads')
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Error handling
@app.errorhandler(Exception)
def handle_error(e):
    logger.error(f"Unhandled error: {str(e)}", exc_info=True)
    return render_template('error.html', error=str(e)), 500

@app.before_request
def before_request():
    """Establish database connection before each request"""
    try:
        get_db()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}", exc_info=True)
        return render_template('error.html', error="Database connection failed"), 500

app.teardown_appcontext(close_db)

def init_app():
    """Initialize the application"""
    try:
        with app.app_context():
            verify_database_structure()
            init_db()
            sync_inventory_status()
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}", exc_info=True)
        raise


@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()

    # Get search query from URL parameters
    search_query = request.args.get('search', '').strip()

    # First, get the overdue loan green numbers
    cursor.execute('''
        SELECT DISTINCT l.green_number 
        FROM loans l 
        WHERE l.status = 'active' 
        AND CAST((JULIANDAY('now') - JULIANDAY(l.loan_date)) AS INTEGER) > 7
    ''')
    overdue_items = cursor.fetchall()
    overdue_green_numbers = set(str(item['green_number']) for item in overdue_items)

    # Get inventory items with search if provided
    if search_query:
        cursor.execute('''
            SELECT * FROM inventory 
            WHERE name LIKE ? 
            OR green_number LIKE ? 
            OR category LIKE ?
            OR status LIKE ?
            ORDER BY id DESC
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute('SELECT * FROM inventory ORDER BY id DESC')

    # Fetch items and convert to list of dicts
    items = [dict(row) for row in cursor.fetchall()]

    # Add is_overdue flag to each item
    for item in items:
        item['is_overdue'] = str(item['green_number']) in overdue_green_numbers

    return render_template('index.html', items=items, search_query=search_query)


@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        try:
            name = request.form['name']
            quantity = int(request.form['quantity'])
            green_number = int(request.form['green_number'])
            category = request.form['category']
            status = request.form.get('status', 'no')

            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                'INSERT INTO inventory (name, quantity, green_number, category, status) VALUES (?, ?, ?, ?, ?)',
                (name, quantity, green_number, category, status)
            )
            db.commit()
            flash('Item added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding item: {str(e)}', 'error')
            db.rollback()
        return redirect(url_for('index'))

    return render_template('add.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        try:
            name = request.form['name']
            quantity = int(request.form['quantity'])
            green_number = int(request.form['green_number'])
            category = request.form['category']
            status = request.form.get('status', 'no')

            cursor.execute('''
                UPDATE inventory 
                SET name = ?, quantity = ?, green_number = ?, category = ?, status = ?
                WHERE id = ?
            ''', (name, quantity, green_number, category, status, id))
            db.commit()
            flash('Item updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error updating item: {str(e)}', 'error')
            db.rollback()

    cursor.execute('SELECT * FROM inventory WHERE id = ?', (id,))
    item = cursor.fetchone()
    return render_template('edit.html', item=item)


@app.route('/loans')
def loans():
    db = get_db()
    cursor = db.cursor()

    # Get all active loans with calculated days active
    cursor.execute('''
        SELECT *, 
        CAST(
            (JULIANDAY('now') - JULIANDAY(loan_date)) AS INTEGER
        ) as days_active 
        FROM loans 
        WHERE status = 'active' 
        ORDER BY id DESC
    ''')
    loans = cursor.fetchall()

    # Convert loans to a list to modify each row
    loans = [dict(loan) for loan in loans]

    # Add overdue flag
    for loan in loans:
        loan['is_overdue'] = loan['days_active'] > 7

    return render_template('loans.html', loans=loans)


@app.route('/add_loan', methods=['GET', 'POST'])
def add_loan():
    if request.method == 'POST':
        try:
            db = get_db()
            cursor = db.cursor()

            borrower_name = request.form['borrower_name']
            green_numbers = request.form.getlist('green_numbers[]')
            equipment = request.form.getlist('equipment[]')
            equipment_quantities = request.form.getlist('equipment_quantity[]')
            loan_date = request.form['loan_date']
            signature = request.form.get('signature', '')

            if not signature:
                flash('Signature is required!', 'error')
                return render_template('add_loan.html',
                                       form_data=request.form,
                                       available_items=get_available_items())

            if not green_numbers or not any(green_numbers):
                flash('Please select at least one item!', 'error')
                return render_template('add_loan.html',
                                       form_data=request.form,
                                       available_items=get_available_items())

            # Start a transaction
            cursor.execute('BEGIN TRANSACTION')

            try:
                # Process each green number as a separate loan
                for green_number in green_numbers:
                    if not green_number:  # Skip empty selections
                        continue

                    # Check if green number exists and is available
                    cursor.execute('SELECT * FROM inventory WHERE green_number = ?', (green_number,))
                    inventory_item = cursor.fetchone()

                    if inventory_item is None:
                        raise Exception(f'Green number {green_number} does not exist in inventory!')

                    cursor.execute('''
                        SELECT * FROM loans 
                        WHERE green_number = ? 
                        AND status = 'active'
                    ''', (green_number,))
                    existing_loan = cursor.fetchone()

                    if existing_loan:
                        raise Exception(f'Green number {green_number} is currently on loan!')

                    # Create the loan record
                    cursor.execute('''
                        INSERT INTO loans 
                        (borrower_name, item_name, green_number, loan_date, signature, status) 
                        VALUES (?, ?, ?, ?, ?, 'active')
                    ''', (borrower_name, inventory_item['name'], green_number, loan_date, signature))

                    # Update inventory item status to 'yes'
                    cursor.execute('''
                        UPDATE inventory
                        SET status = 'yes'
                        WHERE green_number = ?
                    ''', (green_number,))

                    loan_id = cursor.lastrowid

                    # Add equipment for this loan
                    for equip, qty in zip(equipment, equipment_quantities):
                        if equip:  # Only process if equipment is selected
                            cursor.execute('''
                                INSERT INTO loans_equipment 
                                (loan_id, equipment_type, quantity) 
                                VALUES (?, ?, ?)
                            ''', (loan_id, equip, qty))

                # Commit the transaction
                cursor.execute('COMMIT')
                flash('Loan(s) added successfully!', 'success')
                return redirect(url_for('loans'))

            except Exception as e:
                # If anything goes wrong, rollback the transaction
                cursor.execute('ROLLBACK')
                raise e

        except Exception as e:
            flash(f'Error adding loan: {str(e)}', 'error')
            return render_template('add_loan.html',
                                   form_data=request.form,
                                   available_items=get_available_items())

    return render_template('add_loan.html',
                           available_items=get_available_items())

# Add this helper function to get available items
def get_available_items():
    db = get_db()
    cursor = db.cursor()

    # Get items that are either not loaned or have been returned
    cursor.execute('''
        SELECT DISTINCT i.green_number, i.name 
        FROM inventory i
        LEFT JOIN loans l ON i.green_number = l.green_number AND l.status = 'active'
        WHERE l.id IS NULL
        ORDER BY i.green_number
    ''')

    return cursor.fetchall()

def get_active_loans():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT green_number, item_name, borrower_name, loan_date 
        FROM loans 
        WHERE status = 'active' 
        ORDER BY loan_date DESC
    ''')
    return cursor.fetchall()


@app.route('/return_loan/<int:id>')
def return_loan(id):
    try:
        db = get_db()
        cursor = db.cursor()

        # Start transaction
        cursor.execute('BEGIN TRANSACTION')

        # Get the green number before updating the loan
        cursor.execute('SELECT green_number FROM loans WHERE id = ?', (id,))
        loan = cursor.fetchone()

        if loan:
            # Update loan status to returned
            cursor.execute('''
                UPDATE loans 
                SET status = 'returned', return_date = ?
                WHERE id = ?
            ''', (date.today().isoformat(), id))

            # Check if this item has any other active loans
            cursor.execute('''
                SELECT COUNT(*) as active_count 
                FROM loans 
                WHERE green_number = ? AND status = 'active' AND id != ?
            ''', (loan['green_number'], id))

            active_count = cursor.fetchone()['active_count']

            # If no other active loans, update inventory status to 'no'
            if active_count == 0:
                cursor.execute('''
                    UPDATE inventory 
                    SET status = 'no'
                    WHERE green_number = ?
                ''', (loan['green_number'],))

        # Commit transaction
        db.commit()
        flash('Loan marked as returned!', 'success')

    except Exception as e:
        flash(f'Error updating loan: {str(e)}', 'error')
        db.rollback()
    return redirect(url_for('loans'))

@app.route('/delete/<int:id>')
def delete_item(id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM inventory WHERE id = ?', (id,))
        db.commit()
        flash('Item deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting item: {str(e)}', 'error')
        db.rollback()
    return redirect(url_for('index'))

@app.route('/loans_history')
def loans_history():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT * FROM loans 
        WHERE status = 'returned' 
        ORDER BY return_date DESC
    ''')
    history_loans = cursor.fetchall()
    return render_template('loans_history.html', loans=history_loans)


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/import_inventory', methods=['GET', 'POST'])
def import_inventory():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('index'))

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))

        if file and allowed_file(file.filename):
            try:
                # Read Excel file
                df = pd.read_excel(file)

                # Verify required columns
                required_columns = {'name', 'quantity', 'green_number', 'category', 'status'}
                if not required_columns.issubset(df.columns):
                    flash('Excel file must contain columns: name, quantity, green_number, category, status', 'error')
                    return redirect(url_for('index'))

                # Process each row
                db = get_db()
                cursor = db.cursor()
                success_count = 0
                error_count = 0

                for index, row in df.iterrows():
                    try:
                        # Check if item with green_number already exists
                        cursor.execute('SELECT id FROM inventory WHERE green_number = ?', (row['green_number'],))
                        existing_item = cursor.fetchone()

                        if existing_item:
                            # Update existing item
                            cursor.execute('''
                                UPDATE inventory 
                                SET name = ?, quantity = ?, category = ?, status = ?
                                WHERE green_number = ?
                            ''', (row['name'], row['quantity'], row['category'],
                                  row['status'], row['green_number']))
                        else:
                            # Insert new item
                            cursor.execute('''
                                INSERT INTO inventory (name, quantity, green_number, category, status)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (row['name'], row['quantity'], row['green_number'],
                                  row['category'], row['status']))
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        continue

                db.commit()
                flash(f'Successfully imported {success_count} items. {error_count} errors.', 'success')

            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')

            return redirect(url_for('index'))

        flash('Invalid file type. Please upload an Excel file (.xlsx or .xls)', 'error')
        return redirect(url_for('index'))

    return render_template('import_inventory.html')


# Add this function at the end of your app.py, just before the if __name__ == '__main__': line

def sync_inventory_status():
    try:
        db = get_db()
        cursor = db.cursor()

        # Start transaction
        cursor.execute('BEGIN TRANSACTION')

        # First, set all items to 'no'
        cursor.execute('UPDATE inventory SET status = ?', ('no',))

        # Then set items with active loans to 'yes'
        cursor.execute('''
            UPDATE inventory 
            SET status = 'yes'
            WHERE green_number IN (
                SELECT DISTINCT green_number 
                FROM loans 
                WHERE status = 'active'
            )
        ''')

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error syncing inventory status: {str(e)}")
        return False


@app.route('/extend_loan/<int:id>')
def extend_loan(id):
    try:
        db = get_db()
        cursor = db.cursor()

        # Get current loan details
        cursor.execute('''
            SELECT loan_date, 
            CAST((JULIANDAY('now') - JULIANDAY(loan_date)) AS INTEGER) as days_active 
            FROM loans 
            WHERE id = ?
        ''', (id,))
        loan = cursor.fetchone()

        if loan and loan['days_active'] > 7:
            # Calculate new loan date (current loan date + 7 days)
            cursor.execute('''
                UPDATE loans 
                SET loan_date = date(loan_date, '+7 days')
                WHERE id = ?
            ''', (id,))
            db.commit()
            flash('Loan extended for one week!', 'success')
        else:
            flash('Loan cannot be extended!', 'error')

    except Exception as e:
        flash(f'Error extending loan: {str(e)}', 'error')
        db.rollback()
    return redirect(url_for('loans'))


@app.route('/loan/<int:id>')
def loan_details(id):
    try:
        db = get_db()
        cursor = db.cursor()

        # Store the current page in session for the back button
        session['previous_page'] = request.referrer

        # Get loan details
        cursor.execute('''
            SELECT *, 
            CAST((JULIANDAY('now') - JULIANDAY(loan_date)) AS INTEGER) as days_active 
            FROM loans 
            WHERE id = ?
        ''', (id,))
        loan = cursor.fetchone()

        if not loan:
            flash('Loan not found!', 'error')
            return redirect(url_for('loans'))

        # Get equipment details
        cursor.execute('''
            SELECT equipment_type, quantity 
            FROM loans_equipment 
            WHERE loan_id = ?
        ''', (id,))
        equipment = cursor.fetchall()

        return render_template('loan_details.html',
                               loan=loan,
                               equipment=equipment,
                               days_active=loan['days_active'])

    except Exception as e:
        flash(f'Error loading loan details: {str(e)}', 'error')
        return redirect(url_for('loans'))


@app.route('/back')
def back_to_previous():
    previous_page = session.get('previous_page')
    if previous_page:
        return redirect(previous_page)
    return redirect(url_for('loans'))

# Optional: Add the route to manually trigger the sync
@app.route('/sync_inventory_status')
def sync_inventory():
    if sync_inventory_status():
        flash('Inventory status synchronized successfully!', 'success')
    else:
        flash('Error synchronizing inventory status!', 'error')
    return redirect(url_for('index'))

DATABASE = get_db_path()

if __name__ == '__main__':
    try:
        init_app()
        app.run(debug=True, host='0.0.0.0')
    except Exception as e:
        logger.error(f"Startup error: {str(e)}", exc_info=True)
        sys.exit(1)