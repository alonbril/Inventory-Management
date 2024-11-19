from flask import Flask, render_template, request, redirect, url_for, flash, g
from database import init_db, get_db, close_db
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'dev'

app.teardown_appcontext(close_db)


def init_app():
    with app.app_context():
        init_db()


@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM inventory ORDER BY id DESC')
    items = cursor.fetchall()
    return render_template('index.html', items=items)


@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        try:
            name = request.form['name']
            quantity = int(request.form['quantity'])
            green_number = float(request.form['green_number'])
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
            green_number = float(request.form['green_number'])
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
    cursor.execute('SELECT * FROM loans ORDER BY id DESC')
    loans = cursor.fetchall()
    return render_template('loans.html', loans=loans)


@app.route('/add_loan', methods=['GET', 'POST'])
def add_loan():
    if request.method == 'POST':
        try:
            item_name = request.form['item_name']
            borrower_name = request.form['borrower_name']
            loan_date = request.form['loan_date']

            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                'INSERT INTO loans (item_name, borrower_name, loan_date) VALUES (?, ?, ?)',
                (item_name, borrower_name, loan_date)
            )
            db.commit()
            flash('Loan added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding loan: {str(e)}', 'error')
            db.rollback()
        return redirect(url_for('loans'))

    return render_template('add_loan.html')


@app.route('/return_loan/<int:id>')
def return_loan(id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            UPDATE loans 
            SET status = 'returned', return_date = ?
            WHERE id = ?
        ''', (date.today().isoformat(), id))
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


if __name__ == '__main__':
    init_app()
    app.run(debug=True)