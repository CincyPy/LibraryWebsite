from flask import Flask, render_template, request, session, \
                flash, redirect, url_for, g
import sqlite3
import os
from functools import wraps

# configuration
DATABASE = 'library.db'
USERNAME = 'admin'
PASSWORD = 'admin'
SECRET_KEY = os.urandom(24)

app = Flask(__name__)

app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME'] or \
            request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid Credentials.  Please try again.'
        else:
            session['logged_in']=True
            return redirect(url_for('admin'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))


@app.route('/')
def main():
    g.db = connect_db()
    cur = g.db.execute('SELECT * FROM staff')
    staff = [dict(f_name=row[0], l_name=row[1], phone=row[2]) for row in cur.fetchall()]
    g.db.close()
    return render_template('main.html', staff=staff)


@app.route('/admin')
def admin():
    g.db = connect_db()
    cur = g.db.execute('SELECT * FROM staff')
    staff = [dict(f_name=row[0], l_name=row[1], phone=row[2]) for row in cur.fetchall()]
    g.db.close()
    return render_template('admin.html', staff=staff)


@app.route('/add', methods=['POST'])
@login_required
def add():
    f_name = request.form['f_name']
    l_name = request.form['l_name']
    phone = request.form['phone']
    if not f_name or not l_name or not phone:
        flash('All fields are required. Please try agian.')
        return redirect(url_for('admin'))
    else:
        try:
            if len(phone) != 10:
                flash('Phone number must include area code. Please try agian.')
                return redirect(url_for('admin'))
            int(phone) # Confirms that phone is an integer
        except:
            flash('Phone number must include area code. Please try agian.')
            return redirect(url_for('admin'))
    g.db = connect_db()
    g.db.execute('INSERT INTO staff (f_name, l_name, phone) VALUES (?, ?, ?)', \
                 [f_name, l_name, phone])
    g.db.commit()
    g.db.close()
    flash('New entry was successfully posted!')
    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=True)