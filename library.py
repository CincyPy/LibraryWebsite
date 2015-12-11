import datetime
import sqlite3
import tempfile
import time

from random import shuffle
from functools import wraps
from flask import Flask, render_template, request, session, \
    flash, redirect, url_for, g

from database import db_session
from models import Profile, ReadingList, Staff

# configuration
SECRET_KEY = '\x00\xb47\xb1\x1b<*tx\x1b2ywW\x86\x01\xfa\xcd\x0b\xeb\x94\x1c\xe5\xaf'

app = Flask(__name__)
app.config.from_object(__name__)

def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))

    return wrap

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

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


@app.route('/librarian')
@login_required
def librarian():
    logged_in_user = Staff.query.get(session['logged_in_name'])
    return render_template('librarian.html', readinglist=logged_in_user.readinglist)


@app.route('/adduser', methods=['POST'])
@login_required
def adduser():
    if session["logged_in_name"] != "admin":
        return redirect(url_for('librarian'))
    username = request.form['username']
    password = request.form['password']
    f_name = request.form['f_name']
    l_name = request.form['l_name']
    phone = request.form['phone']
    if not f_name or not l_name or not phone or not username or not password:
        flash('All fields are required. Please try again.')
        return redirect(url_for('admin'))
    else:
        try:
            if len(phone) != 10:
                flash('Phone number must include area code. Please try again.')
                return redirect(url_for('admin'))
            int(phone)  # Confirms that phone is an integer
        except:
            flash('Phone number must include area code. Please try again.')
            return redirect(url_for('admin'))
    staff = Staff(username=username, password=password, f_name=f_name,
                         l_name=l_name, phone=phone, profile=Profile(bio=""))
    db_session.add(staff)
    db_session.commit()
    flash('New entry was successfully posted!')
    return redirect(url_for('admin'))


@app.route('/addrecread', methods=['POST'])
@login_required
def addrecread():
    if session["logged_in_name"] == "admin":
        return redirect(url_for('admin'))
    book = request.form['book']
    author = request.form['author']
    comment = request.form['comment']
    url = request.form['URL']
    sticky = request.form['sticky']
    if not book:
        flash('Book name is required. Please try again.')
        return redirect(url_for('librarian'))

    logged_in_user = Staff.query.get(session['logged_in_name'])
    logged_in_user.readinglist.append(ReadingList(recdate=datetime.date.today(),
                                                  book=book,
                                                  author=author,
                                                  comment=comment,
                                                  url=url,
                                                  sticky=sticky))
    db_session.commit()
    flash('New recommending reading added.')
    return redirect(url_for('librarian'))


@app.route("/profile/<uname>", methods=['GET'])
def profile(uname):
    staff = Staff.query.get(uname)
    if staff:
        return render_template('viewprofile.html',profile=staff)
    else:
        flash("Profile not found")
        return redirect(url_for('main'))


@app.route('/edit-profile/<uname>', methods=['GET', 'POST'])
@login_required
def edit_profile(uname):
    if session["logged_in_name"] != uname:
        flash("Access denied: You are not " + uname + ".")
        return redirect(url_for('main'))

    staff = Staff.query.get(uname)

    if request.method == "GET": #regular get, present the form to user to edit.
        if staff:
            return render_template('profile.html', bio=staff.profile.bio)
        else:
            flash("No profile found for user.")
            return redirect(url_for('main'))
    elif request.method == "POST": #form was submitted, update database
        staff.profile.bio = request.form['bio']
        db_session.commit()
        flash("Profile updated!")
        return render_template('profile.html', bio=staff.profile.bio)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
