from flask import Flask, render_template, request, redirect, url_for, flash, g
from database import init_db, get_db, close_db

app = Flask(__name__)
app.secret_key = 'dev'  # Change this to a random secret key in production

# Register database close function
app.teardown_appcontext(close_db)


@app.before_first_request
def initialize_database():
    init_db()


@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM inventory')
    items = cursor.fetchall()
    return render_template('index.html', items=items)


@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']
        category = request.form['category']

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO inventory (name, quantity, price, category) VALUES (?, ?, ?, ?)',
            (name, quantity, price, category)
        )
        db.commit()
        flash('Item added successfully!')
        return redirect(url_for('index'))

    return render_template('add.html')


if __name__ == '__main__':
    app.run(debug=True)
