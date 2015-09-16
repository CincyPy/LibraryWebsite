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

@app.route('/admin', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME'] or \
            request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid Credentials.  Please try again.'
        else:
            session['logged_in']=True
            return redirect(url_for('main'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))

@app.route('/')
def main():
    #g.db = connect_db()
    #cur = g.db.execute('SELECT * FROM posts')
    #posts = [dict(title=row[0], post=row[1]) for row in cur.fetchall()]
    #g.db.close()
    return render_template('main.html')

@app.route('/add', methods=['POST'])
@login_required
def add():
    title = request.form['title']
    post = request.form['post']
    if not title or not post:
        flash('All fields are required. Please try agian.')
        return redirect(url_for('main'))
    else:
        #g.db = connect_db()
        #g.db.execute('INSERT INTO posts (title, post) VALUES (?, ?)', \
        #             [request.form['title'], request.form['post']])
        #g.db.commit()
        #g.db.close()
        flash('New entry was successfully posted!')
        return redirect(url_for('main'))


if __name__ == '__main__':
    app.run(debug=True)