import datetime
import ast
import re
import time

from random import shuffle
from functools import wraps
from flask import Flask, render_template, request, session, \
     flash, redirect, url_for, g, jsonify
from flask_mail import Mail, Message

from sqlalchemy import or_

from database import db_session
from models import Profile, ReadingList, Staff, PatronContact

# configuration
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
            if user.username == 'admin':
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

    if Staff.query.filter(or_(Staff.username==username, Staff.email==email)).all():
        flash('Username or email address is already used.')
        return redirect(url_for('admin'))

    staff = Staff(username=username, password=password, f_name=f_name,
                  l_name=l_name, phone=phone, email=email, profile=Profile(bio=""))
    db_session.add(staff)
    db_session.commit()
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

    logged_in_user = Staff.query.get(session['logged_in_name'])
    logged_in_user.readinglist.append(ReadingList(recdate=datetime.date.today(),
                                                  book=book,
                                                  author=author,
                                                  comment=comment,
                                                  url=url,
                                                  sticky=sticky,
                                                  category=category))
    db_session.commit()
    flash('New recommending reading added.')
    return redirect(url_for('librarian'))


@app.route('/remrecread/<rlid>', methods=['POST'])
@login_required
def remrecread(rlid):
    rl = ReadingList.query.get(rlid)
    if rl:
        try:
            db_session.delete(rl)
            db_session.commit()
            flash('Delete recommended reading.')
        except:
            flash('Nope..')
    if session["logged_in_name"] == "admin":
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('librarian'))


@app.route('/changeSticky/<rlid>', methods=['POST'])
@login_required
def changeSticky(rlid):
    g.db = connect_db()
    g.db.execute("UPDATE readinglist SET sticky = not sticky WHERE RLID = ?", [rlid])
    g.db.commit()
    g.db.close()
    flash('Sticky changed.')
    if session["logged_in_name"] == "admin":
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('librarian'))


@app.route('/profile/<uname>', methods=['GET'])
def profile(uname):
    staff = Staff.query.get(uname)
    if staff:
        return render_template('viewprofile.html', profile=staff,
                               readinglist=staff.readinglist)
    else:
        flash("Profile not found")
        return redirect(url_for('main'))


@app.route('/edit-profile/<uname>', methods=['GET', 'POST'])
@login_required
def edit_profile(uname):
    if session["logged_in_name"] != uname and session["logged_in_name"] != 'admin':
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


@app.route("/contact/<uname>", methods=['GET', 'POST'])
def contact(uname):
    inputs = request.args.get('inputs')
    prefs = Profile.query.get(uname)
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
        patroncontact = PatronContact(reqdate=time.strftime("%Y-%m-%d"),
                                      username=uname,
                                      name=name,
                                      email=email,
                                      contact=contact,
                                      phone=phone,
                                      times=times,
                                      likes=likes,
                                      dislikes=dislikes,
                                      comment=comment,
                                      audience=audience,
                                      format_pref=format_pref,
                                      chat=chat,
                                      handle=handle)
        db_session.add(patroncontact)
        db_session.commit()
        flash("You're contact request was received!")
        # Send email to staff member regarding request
        lib = Staff.query.get(uname)
        if not lib:
            flash("Librarian not found")
            return redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))
        msg = Message("Request for librarian contact", recipients=[email, lib.email])
        msg.body = name + " has requested to contact " + uname + "\n\nMethod: " + contact
        msg.body += message
        mail.send(msg)
        return redirect(url_for('profile', uname=uname))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
