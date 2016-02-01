import ast
import re
import sqlite3
import time
from random import shuffle
from functools import wraps

from flask import Flask, render_template, request, session, \
    flash, redirect, url_for, g, jsonify
from flask_mail import Mail, Message


# configuration
DATABASE = 'library.db'
SECRET_KEY = '\x00\xb47\xb1\x1b<*tx\x1b2ywW\x86\x01\xfa\xcd\x0b\xeb\x94\x1c\xe5\xaf'
MAIL_SERVER = "smtp.gmail.com"
MAIL_USERNAME = "KentonCountyLibrary@gmail.com"
MAIL_PASSWORD = "CincyPyCoders"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_DEFAULT_SENDER = "KentonCountyLibrary@gmail.com"

app = Flask(__name__)
app.config.from_object(__name__)
mail = Mail(app)


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
    return redirect(url_for('main'))


@app.route('/')
def main():
    g.db = connect_db()

    cur = g.db.execute('SELECT username, f_name, l_name, phone FROM staff WHERE username<>"admin"')
    staff = [dict( username=row[0], f_name=row[1], l_name=row[2], phone=row[3]) for row in cur.fetchall()]
    #import pdb; pdb.set_trace();

    for s in staff:
        cur = g.db.execute("SELECT bio FROM profile WHERE username=?", [s['username']])
        s['bio'] = [ row[0] for row in cur.fetchall()][0]

    g.db.close()
    shuffle(staff)
    return render_template('main.html', staff=staff)


@app.route('/admin')
@login_required
def admin():
    g.db = connect_db()
    cur = g.db.execute('SELECT username, f_name, l_name, phone FROM staff')
    staff = [dict(username=row[0], f_name=row[1], l_name=row[2], phone=row[3]) for row in cur.fetchall()]

    cur = g.db.execute('SELECT RLID, recdate, book, author, comment, url, category, sticky FROM readinglist')
    readinglist = [dict(RLID=row[0], recdate=row[1], book=row[2], author=row[3],
                        comment=row[4], url=row[5], category=row[6], sticky=row[7]) for row in cur.fetchall()]

    g.db.close()
    return render_template('admin.html', staff=staff, readinglist=readinglist)


@app.route('/librarian')
@login_required
def librarian():
    g.db = connect_db()
    cur = g.db.execute('SELECT RLID, recdate, book, author, comment, url, category, sticky FROM readinglist WHERE username=?', [session['logged_in_name']])

    readinglist = [dict(RLID=row[0], recdate=row[1], book=row[2], author=row[3],
                        comment=row[4], url=row[5], category=row[6], sticky=row[7]) for row in cur.fetchall()]
    g.db.close()
    return render_template('librarian.html', readinglist=readinglist)


@app.route('/adduser', methods=['POST'])
@login_required
def adduser():
    if session["logged_in_name"] != "admin":
        flash("You are not authorized to perform this action.")
        return redirect(url_for('main'))
    username = request.form['username']
    password = request.form['password']
    f_name = request.form['f_name']
    l_name = request.form['l_name']
    phone = request.form['phone']
    phone = re.sub(r"\D","",phone) # Remove non-digit characters 
    email = request.form['email']    
    if not f_name or not l_name or not phone or not username or not password or not email:
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
    cur = g.db.execute("SELECT username FROM staff WHERE username=? OR email=?", [username, email])
    rows = cur.fetchall()
    if len(rows) > 0:
        flash('Username or email address is already used.')
        return redirect(url_for('admin'))
    g.db.execute('INSERT INTO staff (username, password, f_name, l_name, phone, email) VALUES (?, ?, ?, ?, ?, ?)',
                 [username, password, f_name, l_name, phone, email])
    g.db.execute('INSERT INTO profile(username,bio) VALUES (?, ?)', [username, ''])
    g.db.commit()
    g.db.close()
    flash('New entry was successfully posted!')
    return redirect(url_for('admin'))


@app.route('/addrecread', methods=['POST'])
@login_required
def addrecread():
    if session["logged_in_name"] == "admin":
        flash("Your are not authorized to perform this action.")
        return redirect(url_for('admin'))
    book = request.form['book']
    author = request.form['author']
    comment = request.form['comment']
    url = request.form['URL']
    category = request.form['category']
    sticky = request.form['sticky']
    if not book:
        flash('Book name is required. Please try again.')
        return redirect(url_for('librarian'))
    g.db = connect_db()
    g.db.execute('INSERT INTO readinglist (RLID, recdate, username, book, author, comment, url, category, sticky) '
                 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                 [None, time.strftime("%Y-%m-%d"), session['logged_in_name'],
                  book, author, comment, url, category, sticky])
    g.db.commit()
    g.db.close()
    flash('New recommending reading added.')
    return redirect(url_for('librarian'))

@app.route('/remrecread/<rlid>',methods=['POST'])
@login_required
def remrecread(rlid):
    g.db = connect_db()
    g.db.execute("DELETE FROM readinglist WHERE RLID = ?", [rlid])
    g.db.commit()
    g.db.close()
    flash('Delete recommended reading.')
    if session["logged_in_name"] == "admin":
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('librarian'))


@app.route('/profile/<uname>', methods=['GET'])
def profile(uname):
    g.db = connect_db()

    # get profile data
    cur = g.db.execute("SELECT p.bio, s.f_name, s.l_name, s.phone "
                       "FROM profile p JOIN staff s ON p.username=s.username "
                       "WHERE p.username=?;", [uname])
    rows = cur.fetchall()
    c = dict(zip(["bio", "f_name", "l_name", "phone"], rows[0]))

    # get reading list data
    cur = g.db.execute("SELECT RLID, recdate, book, author, comment, url, sticky "
                       "FROM readinglist WHERE username=?", [uname])
    d = [dict(RLID=row[0], recdate=row[1], book=row[2], author=row[3],
              comment=row[4], url=row[5], sticky=row[6]) for row in cur.fetchall()]
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


@app.route("/contact/<uname>", methods=['GET', 'POST'])
def contact(uname):
    inputs = request.args.get('inputs')
    g.db = connect_db()
    cur = g.db.execute("SELECT email, phone, chat, irl FROM profile WHERE username=?", [uname])
    prefs = [dict(email=row[0], phone=row[1], chat=row[2], irl=row[3]) for row in cur.fetchall()][0]
    
    if request.method == "GET":  # regular get, present the form to user to edit.
        if inputs != None: # Prepopulate with entered data
            inputs = ast.literal_eval(inputs) # Captures any form inputs as a dictionary
        return render_template('contact.html', pref=prefs, staff=uname, inputs=inputs)

    elif request.method == "POST":  # form was submitted, update database
        #if any([value == '' for key, value in request.form.iteritems() if key == 'name' or key == 'email']):
        #    flash("Please enter your name and email address in the contact area.")
        #    return  redirect(url_for('contact', uname=uname))
        #import pdb; pdb.set_trace();
        data = dict([(key, value) for key, value in request.form.iteritems()]) # Creates a dictionary out of the form inputs
        name = request.form['name']
        email = request.form['email']
        phone, likes, dislikes, comment, audience, format_pref, chat, handle, times = None, None, None, None, None, None, None, None, None
        if prefs['phone']:
            phone = request.form['phone']
            phone = re.sub(r"\D","",phone)
            message = "\nPhone: " + phone
        if prefs['email']:
            likes = request.form['likes']
            dislikes = request.form['dislikes']
            comment = request.form['comment']
            audience = ','.join(request.form.getlist('audience'))
            format_pref = ','.join(request.form.getlist('format_pref'))
            message = "\nTell us about a few books or authors you've enjoyed. What made these books great?\n"
            message += likes
            message = "\nDescribe some authors or titles that you DID NOT like and why\n"
            message += dislikes
            message = "\nIs there anything else you'd like to tell us about your interests, reading or otherwise, that would help us make your list?\n"
            message += comment            
            message = "\nAre you interested in books for adults, teens, or children?\n"
            message += audience            
            message = "\nDo you have a preferred format?\n"
            message += format_pref
        if prefs['chat']:
            chat = request.form['chat']
            handle = request.form['handle']
            message = "\nChat service: " + chat
            message = "\nChat handle: " + handle
        if prefs['phone'] or prefs['chat'] or prefs['irl']:
            times = request.form['times']
            message += "\nTimes: " + times
        try:
            contact = request.form['contact']
        except:
            flash("Please select a contact method.")
            return  redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))
        if name == '' or email == '':
            flash("Please enter your name and email address in the contact area.")
            return  redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))
        elif contact == 'phone' and len(phone) < 10:
            if len(phone) == 0:
                flash("Please enter your phone number.")
            elif len(phone) < 10:
                flash("Your phone number must include the area code (10 digits total).")
            return redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))
        elif contact == 'chat' and (chat == '' or handle == ''):
            flash("Please input your preferred chat service and handle.")
            return redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))
        g.db = connect_db()
        g.db.execute("""INSERT INTO patroncontact (PCID, reqdate, username, name, email, contact, phone, times, likes, dislikes, comment, audience, format_pref, chat, handle)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    [None, time.strftime("%Y-%m-%d"), uname, name, email, contact, phone, times, likes, dislikes, comment, audience, format_pref, chat, handle])
        g.db.commit()
        flash("You're contact request was received!")
        # Send email to staff member regarding request
        lib = {}
        g.db = connect_db()
        cur = g.db.execute("SELECT email FROM staff WHERE username=?", [uname])
        lib['email'] = [ row[0] for row in cur.fetchall()][0]
        msg = Message("Request for librarian contact", recipients=[email, lib['email']])
        msg.body = name + " has requested to contact " + uname + "\n\nMethod: " + contact
        msg.body += message
        mail.send(msg)
        return redirect(url_for('profile', uname=uname))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
