import tempfile
from flask import Flask, render_template, request, session, \
    flash, redirect, url_for, g
import sqlite3
import os
from random import shuffle
from functools import wraps

from models import db, Staff, Profile

# configuration
SECRET_KEY = '\x00\xb47\xb1\x1b<*tx\x1b2ywW\x86\x01\xfa\xcd\x0b\xeb\x94\x1c\xe5\xaf'

DATABASE = os.path.join(tempfile.gettempdir(), 'test.db')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' +  DATABASE
SQLALCHEMY_ECHO = True

app = Flask(__name__)

app.config.from_object(__name__)

db.init_app(app)

if os.path.exists(DATABASE):
    os.remove(DATABASE)

def init_db():
    with app.app_context():
        db.create_all()
        db.session.add(Staff(username='admin', password='admin', f_name='Admin',
                             l_name='User', phone=1111111111))
        db.session.add(Staff(username='fred', password='fred', f_name='Fred',
                             l_name='Fredderson', phone=2222222222))

        db.session.add(Profile(username='admin', bio=''))
        db.session.add(Profile(username='fred', bio=''))

        db.session.commit()

init_db()

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
        username = request.form['username']
        password = request.form['password']

        user = Staff.query.get(username)

        if user and user.password == password:
            session['logged_in'] = True
            session["logged_in_name"] = username
            return redirect(url_for('admin'))
        else:
            error = 'Invalid Credentials.  Please try again.'
            return render_template('login.html', error=error)
    else:
        return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))


@app.route('/')
def main():
    staff = Staff.query.all()
    shuffle(staff)
    return render_template('main.html', staff=staff)


@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html', staff=Staff.query.all())


@app.route('/add', methods=['POST'])
@login_required
def add():
    if session["logged_in_name"] != "admin":
        return redirect(url_for('admin'))
    username = request.form['username']
    password = request.form['password']
    f_name = request.form['f_name']
    l_name = request.form['l_name']
    phone = request.form['phone']
    if not f_name or not l_name or not phone or not username or not password:
        flash('All fields are required. Please try agian.')
        return redirect(url_for('admin'))
    else:
        try:
            if len(phone) != 10:
                flash('Phone number must include area code. Please try agian.')
                return redirect(url_for('admin'))
            int(phone)  # Confirms that phone is an integer
        except:
            flash('Phone number must include area code. Please try agian.')
            return redirect(url_for('admin'))
    db.session.add(Staff(username=username, password=password, f_name=f_name,
                         l_name=l_name, phone=phone))
    db.session.commit()
    flash('New entry was successfully posted!')
    return redirect(url_for('admin'))

@app.route("/profile/<uname>", methods=['GET'])
def profile(uname):
    c = Profile.query.get(uname)
    return render_template('viewprofile.html',profile=c)

@app.route('/edit-profile/<uname>', methods=['GET', 'POST'])
@login_required
def edit_profile(uname):
    if session["logged_in_name"] != uname:
        flash("Access denied: You are not " + uname + ".")
        return redirect(url_for('main'))
    else:
        if request.method == "GET": #regular get, present the form to user to edit.
            profile = Profile.query.get(uname)
            if profile:
                return render_template('profile.html', bio=bio)
            else:
                flash("No profile found for user.")
                return redirect(url_for('main'))

        elif request.method == "POST": #form was submitted, update database
            new_bio = request.form['bio']

            g.db = connect_db()
            cur = g.db.execute("UPDATE profile SET bio=? WHERE username=?", [new_bio,uname])
            g.db.commit()
            flash("Profile updated!")
            return render_template('profile.html', bio=new_bio)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
