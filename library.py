import sqlite3
import time
from random import shuffle
from functools import wraps

from flask import Flask, render_template, request, session, \
    flash, redirect, url_for, g

# configuration
DATABASE = 'library.db'
SECRET_KEY = '\x00\xb47\xb1\x1b<*tx\x1b2ywW\x86\x01\xfa\xcd\x0b\xeb\x94\x1c\xe5\xaf'

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
        username = request.form['username']
        password = request.form['password']

        g.db = connect_db()
        cur = g.db.execute('SELECT password FROM staff WHERE username=?', [username])
        results = cur.fetchall()
        for row in results:
            if row[0] == password:
                session['logged_in'] = True
                session['logged_in_name'] = username
                if username == 'admin':
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('librarian'))
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
    g.db = connect_db()

    cur = g.db.execute('SELECT username, f_name, l_name, phone FROM staff')
    staff = [dict( username=row[0], f_name=row[1], l_name=row[2], phone=row[3]) for row in cur.fetchall()]

    g.db.close()
    shuffle(staff)
    return render_template('main.html', staff=staff)


@app.route('/admin')
@login_required
def admin():
    g.db = connect_db()
    cur = g.db.execute('SELECT username, f_name, l_name, phone FROM staff')
    staff = [dict(username=row[0], f_name=row[1], l_name=row[2], phone=row[3]) for row in cur.fetchall()]
    g.db.close()
    return render_template('admin.html', staff=staff)


@app.route('/librarian')
@login_required
def librarian():
    g.db = connect_db()
    cur = g.db.execute('SELECT recdate, book, author, comment, url, sticky FROM readinglist')
    readinglist = [dict(recdate=row[0], book=row[1], author=row[2], comment=row[3], url=row[4], sticky=row[5])
                   for row in cur.fetchall()]
    g.db.close()
    return render_template('librarian.html', readinglist=readinglist)


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
    g.db = connect_db()
    g.db.execute('INSERT INTO staff (username, password, f_name, l_name, phone) VALUES (?, ?, ?, ?, ?)',
                 [username, password, f_name, l_name, phone])
    g.db.execute('INSERT INTO profile(username,bio) VALUES (?, ?)', [username, ''])
    g.db.commit()
    g.db.close()
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
    g.db = connect_db()
    g.db.execute('INSERT INTO readinglist (RLID, recdate, username, book, author, comment, url, sticky) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                 [None, time.strftime("%Y-%m-%d"), session['logged_in_name'], book, author, comment, url, sticky])
    g.db.commit()
    g.db.close()
    flash('New recommending reading added.')
    return redirect(url_for('librarian'))


@app.route("/profile/<uname>", methods=['GET'])
def profile(uname):
    g.db = connect_db()

    # get profile data
    cur = g.db.execute("SELECT p.bio, s.f_name, s.l_name, s.phone "
                       "FROM profile p JOIN staff s ON p.username=s.username "
                       "WHERE p.username=?;", [uname])
    rows = cur.fetchall()
    c = dict(zip(["bio", "f_name", "l_name", "phone"], rows[0]))

    # get reading list data
    cur = g.db.execute("SELECT recdate, book, author, comment "
                       "FROM readinglist WHERE username=?", [uname])
    d = [dict(recdate=row[0], book=row[1], author=row[2], comment=row[3]) for row in cur.fetchall()]
    return render_template('viewprofile.html', profile=c, readinglist=d)


@app.route('/edit-profile/<uname>', methods=['GET', 'POST'])
@login_required
def edit_profile(uname):
    if session["logged_in_name"] != uname:
        flash("Access denied: You are not " + uname + ".")
        return redirect(url_for('main'))
    else:
        if request.method == "GET":  # regular get, present the form to user to edit.
            g.db = connect_db()
            cur = g.db.execute("SELECT bio FROM profile WHERE username=?", [uname])
            rows = cur.fetchall()
            try:
                bio = rows[0][0]
            except KeyError:
                flash("No profile found for user.")
                return redirect(url_for('main'))

            return render_template('profile.html', bio=bio)

        elif request.method == "POST":  # form was submitted, update database
            new_bio = request.form['bio']

            g.db = connect_db()
            cur = g.db.execute("UPDATE profile SET bio=? WHERE username=?", [new_bio, uname])
            g.db.commit()
            flash("Profile updated!")
            return render_template('profile.html', bio=new_bio)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
