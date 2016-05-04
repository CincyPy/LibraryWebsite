from config import config
import datetime
import ast
import re
import time
import os
import urllib

from random import shuffle
from functools import wraps
from flask import Flask, render_template, request, session, \
     flash, redirect, url_for, g, jsonify, abort
from flask_mail import Mail, Message
from publisher import Publisher
from os import environ

from sqlalchemy import or_, and_

from database import Database
from models import PasswordReset, PatronContact, ReadingList, Staff

from upload_form import UploadForm
from flask.ext.bootstrap import Bootstrap

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(config)

if config.NAME != "TEST":
    app.config.from_pyfile('production.py', silent=True)

db = Database(app)
mail = Mail(app)
bootstrap = Bootstrap(app)

def logout_user():
    session.pop('logged_in', None)

def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        app.logger.info(session)
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))

    return wrap

@app.context_processor
def inject_sitename():
    return dict(sitename=config.SITENAME, sitenameparts=config.SITENAMEPARTS)

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
            app.logger.info(session)
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
    logout_user()
    flash('You were logged out')
    return redirect(url_for('main'))


@app.route('/')
def main():
    staff = Staff.query.filter(Staff.username != 'admin').all()
    shuffle(staff)
    return render_template('main.html', staffmembers=staff)

@app.route('/admin')
@login_required
def admin():
    if session["logged_in_name"] != "admin":
        flash("You are not authorized to perform this action.")
        return redirect(url_for('main'))
    return render_template('admin.html', staff=Staff.query.all(), readinglist=ReadingList.query.all(), patron_reqs=PatronContact.query.all())

@app.route('/librarian')
@app.route('/librarian/<rlid>', methods=['GET', 'POST'])
@login_required
def librarian(rlid=None):
    logged_in_user = Staff.query.get(session['logged_in_name'])
    patron_reqs = PatronContact.query.filter(PatronContact.username==logged_in_user.username, PatronContact.status!='closed')
    inputs = request.args.get('inputs')
    if inputs != None: # Prepopulate with entered data
        inputs = ast.literal_eval(inputs) # Captures any form inputs from url as (takes literal value of string)
    if rlid is None:
        if session["logged_in_name"] == 'admin':
            return render_template('librarian.html', readinglist=ReadingList.query.all(), existingValues=inputs, patron_reqs=patron_reqs)
        else:
            return render_template('librarian.html', readinglist=logged_in_user.readinglist, existingValues=inputs, patron_reqs=patron_reqs)
    else:
        book = ReadingList.query.filter_by(RLID=rlid).first()
        if book.username == session["logged_in_name"]:
            return render_template('librarian.html', readinglist=logged_in_user.readinglist, existingValues=book, patron_reqs=patron_reqs, inputs=inputs)
        elif session["logged_in_name"] == 'admin':
            return render_template('librarian.html', readinglist=ReadingList.query.all(), existingValues=book, patron_reqs=patron_reqs, inputs=inputs)
        else:
            flash("Your are not authorized to perform this action.")
            return redirect(url_for('librarian'), existingValues=inputs)

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
    email = request.form['emailaddress']
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

    if Staff.query.filter(or_(Staff.username==username, Staff.emailaddress==email)).all():
        flash('Username or email address is already used.')
        return redirect(url_for('admin'))

    staff = Staff(username=username, password=password, f_name=f_name,
                  l_name=l_name, phonenumber=phone, emailaddress=email)
    db.session.add(staff)
    db.session.commit()
    flash('New entry was successfully posted!')
    return redirect(url_for('admin'))

@app.route('/deleteuser/<username>', methods=['POST'])
@login_required
def deleteuser(username):
    if session["logged_in_name"] != "admin" or username == "admin":
        flash("You are not authorized to perform this action.")
        return redirect(url_for('main'))
    recread = ReadingList.query.filter(ReadingList.username == username).all()
    for rr in recread:
        db.session.delete(rr)
    staff = Staff.query.get(username)
    db.session.delete(staff)
    db.session.commit()
    flash('User was successfully removed!')
    return redirect(url_for('admin'))

@app.route('/addrecread', methods=['POST'])
@login_required
def addrecread():
    if request.method == "POST":  # form was submitted, update database
        data = {}
        for key, values in dict(request.form).items():
            data[key] = ",".join(values)
    if not request.form['book']:
        flash('Book name is required. Please try again.')
        return redirect(url_for('librarian') + '?inputs=' + str(data))
    if not request.form['ISBN']:
        flash('ISBN is required. Please try again.')
        return redirect(url_for('librarian') + '?inputs=' + str(data))
    if not request.form['author']:
        flash('Author is required. Please try again.')
        return redirect(url_for('librarian') + '?inputs=' + str(data))
    if not request.form['category']:
        flash('Category is required. Please try again.')
        return redirect(url_for('librarian') + '?inputs=' + str(data))

    if not request.form['RLID']:    # add a new book
        if session['logged_in_name'] == 'admin':
            flash('Your are not authorized to perform this action.')
            return redirect(url_for('admin'))
        book_user = Staff.query.get(session['logged_in_name'])
        flash('New recommended reading added.')
    else:   # edit a book
        rl = ReadingList.query.get(request.form['RLID'])
        if not rl:
            flash('Book not found.')
            return redirect(url_for('librarian'))
        book_user = Staff.query.get(rl.username)
        db.session.delete(rl)
        db.session.commit()
        flash('Recommended reading edited.')
    ISBN = request.form['ISBN']
    book = request.form['book']
    author = request.form['author']
    comment = request.form['comment']
    category = request.form['category']
    sticky = request.form['sticky']
    if not book:
        flash('Book name is required. Please try again.')
        return redirect(url_for('librarian'))
    book_user.readinglist.append(ReadingList(recdate=datetime.date.today(),
                                             ISBN=ISBN,
                                             book=book,
                                             author=author,
                                             comment=comment,
                                             sticky=sticky,
                                             category=category))
    db.session.commit()
    if session['logged_in_name'] == 'admin':
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('librarian'))


@app.route('/remrecread/<rlid>', methods=['POST'])
@login_required
def remrecread(rlid):
    if session['logged_in_name'] == 'admin':
        rl = ReadingList.query.filter(ReadingList.RLID == rlid).first()
    else:
        username = session['logged_in_name']
        rl = ReadingList.query.filter(ReadingList.RLID == rlid, ReadingList.username == username).first()

    if rl:
        db.session.delete(rl)
        db.session.commit()
        flash('Deleted recommended reading.')
    if session["logged_in_name"] == "admin":
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('librarian'))


@app.route('/changeSticky/<rlid>', methods=['POST'])
@login_required
def changeSticky(rlid):
    rl = ReadingList.query.get(rlid)
    if rl:
        rl.sticky = not(rl.sticky)
        db.session.commit()
        flash('Sticky changed.')
    if session["logged_in_name"] == "admin":
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('librarian'))


@app.route('/profile/<uname>', methods=['GET'])
def profile(uname):
    staff = Staff.query.get(uname)

    selected_categories = request.args.getlist('category')
    if selected_categories:
        readinglist = (ReadingList.query
                       .filter(and_(
                           ReadingList.username==staff.username,
                           ReadingList.category.in_(selected_categories)))
                       .all())
    else:
        readinglist = staff.readinglist

    if staff:
        return render_template('viewprofile.html', staff=staff,
                               readinglist=readinglist,
                               selected_categories=selected_categories)
    else:
        flash("Profile not found")
        return redirect(url_for('main'))


@app.route('/edit-profile/<uname>', methods=['GET', 'POST'])
@login_required
def edit_profile(uname):
    if session["logged_in_name"] != uname and session["logged_in_name"] != 'admin':
        flash("Access denied: You are not " + uname + ".")
        return redirect(url_for('main'))
    inputs = request.args.get('inputs')
    staff = Staff.query.get(uname)
    if request.method == "GET": #regular get, present the form to user to edit.
        if staff:
            if inputs != None: # Prepopulate with entered data
                inputs = ast.literal_eval(inputs) # Captures any form inputs from url as (takes literal value of string)
            return render_template('profile.html', staff=staff, inputs=inputs)
        else:
            flash("No profile found for user.")
            return redirect(url_for('main'))
    elif request.method == "POST": #form was submitted, update database
        data = {}
        for key, values in dict(request.form).items():
            data[key] = ",".join(values)

        try:
            data['phonenumber'] = re.sub(r"\D","",data['phonenumber'])
            if len(data['phonenumber']) == 0: # This shouldn't happen since the HTML has a required field
                flash("Please enter your phone number.")
                return redirect(url_for('edit_profile', uname=uname) + '?inputs=' + str(data))
            elif len(data['phonenumber']) < 10:
                flash("Your phone number must include the area code (10 digits total).")
                return redirect(url_for('edit_profile', uname=uname) + '?inputs=' + str(data))
        except:
            pass

        try:
            if data['chat'] == 'on':
                data['chat'] = True
        except:
            data['chat'] = False
        try:
            if data['email'] == 'on':
                data['email'] = True
        except:
            data['email'] = False
        for key, value in data.iteritems(): # Dynamically update the model values for staff based on inputs
            setattr(staff, key, value)
        db.session.commit()
        flash("Profile updated!")
    return redirect(url_for('edit_profile', uname=uname))

@app.route('/edit-profile/<uname>/upload-picture', methods=['GET', 'POST'])
@login_required
def upload_picture(uname):
    if session["logged_in_name"] != uname and session["logged_in_name"] != 'admin':
        flash("Access denied: You are not " + uname + ".")
        return redirect(url_for('main'))
    staff = Staff.query.get(uname)
    if staff is None:
        flash('User %s not found' % uname)
        return redirect(url_for('main'))
    image = "uploads/" + uname + ".jpg"
    form = UploadForm()
    if request.method == 'POST' and form.validate_on_submit():
        form.image_file.data.save(os.path.join(app.static_folder, image))
        return redirect(url_for('edit_profile', uname=uname))
    return render_template('picture.html', form=form, image=image, staff=staff)

@app.route("/contact/<uname>", methods=['GET', 'POST'])
def contact(uname):
    inputs = request.args.get('inputs')
    formats = [
        ('book','Book'),
        ('lg_print', 'Large Print'),
        ('cd', 'Audiobook on CD'),
        ('eb', 'E-book'),
        ('digital_audio', 'Digital audiobook'),
    ]
    auds = [
        ('adults', 'Adults'),
        ('teens', 'Teens'),
        ('children', 'Children'),
    ]
    staff = Staff.query.get(uname)
    if request.method == "GET":  # regular get, present the form to user to edit.
        if inputs != None: # Prepopulate with entered data
            inputs = ast.literal_eval(inputs) # Captures any form inputs from url as (takes literal value of string)
        return render_template('contact.html', staff=staff, formats=formats, auds=auds, inputs=inputs)

    elif request.method == "POST":  # form was submitted, update database
        data = {}
        for key, values in dict(request.form).items():
            data[key] = ",".join(values)
        lib = Staff.query.get(uname)
        if not lib:
            flash("Librarian not found")
            return redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))
        try:
            data['contact']
        except:
            flash("Please select a contact method.")
            return  redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))

        try: # Input fields are required so this shouldn't be needed
            if data['name'] == '' or data['email'] == '':
                flash("Please enter your name and email address in the contact area.")
                return  redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))
        except:
            flash("Please enter your name and email address in the contact area.")
            return  redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))

        message = ""
        if data['contact'] == 'email':
                message += "\n\nTell us about a few books or authors you've enjoyed. What made these books great?\n" + data['likes']
                message += "\n\nDescribe some authors or titles that you DID NOT like and why.\n" + data['dislikes']
                message += "\n\nIs there anything else you'd like to tell us about your interests, reading or otherwise, that would help us make your list?\n" + data['comment']
                message += "\n\nAre you interested in books for adults, teens, or children?\n" + data['audience']
                message += "\n\nDo you have a preferred format?\n" + data['format_pref']
        elif data['contact'] == 'phone':
            data['phone'] = re.sub(r"\D","",data['phone'])
            if len(data['phone']) == 0:
                flash("Please enter your phone number.")
                return redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))
            elif len(data['phone']) < 10:
                flash("Your phone number must include the area code (10 digits total).")
                return redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))
            message += "\n\nPhone: " + data['phone']
        elif data['contact'] == 'chat':
            if data['chat'] == '' or data['handle'] == '':
                flash("Please input your preferred chat service and handle.")
                return redirect(url_for('contact', uname=uname) + '?inputs=' + str(data))
            else:
                message += "\n\nChat service: " + data['chat']
                message += "\n\nChat handle: " + data['handle']

        if data['contact'] != 'email' and data['times'] != '':
            message += "\n\nTimes: " + data['times']

        try:
            test = request.form['test'] # Check if running tests
            data.pop('test',None) # Remove test from data dictionary prior to database entry
        except: # If not testing, send email to patron and staff member
            msg = Message("Request for librarian contact", recipients=[data['email'], lib.emailaddress])
            msg.body = data['name'] + " has requested to contact " + uname + "\n\nMethod: " + data['contact']
            msg.body += message
            mail.send(msg)
        patroncontact = PatronContact(reqdate=time.strftime("%Y-%m-%d"), username=uname, status='open', **data)
        db.session.add(patroncontact)
        db.session.commit()
        flash("You're contact request was received!")
    return redirect(url_for('profile', uname=uname))

@app.route("/contact_status/<PCID>", methods=['POST'])
def contact_status(PCID):
    contact_req = PatronContact.query.get(PCID)
    if not contact_req:
        flash("Patron request not found")
        return redirect(url_for('librarian'))
    contact_req.status = request.form['status']
    db.session.commit()
    flash(contact_req.name + " Patron request status has been updated")
    if session['logged_in_name'] == 'admin':
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('librarian'))


def is_valid_password(s):
    #XXX: password requirements?
    return len(s) >= 3


@app.route('/changepassword', methods=['GET', 'POST'])
@login_required
def changepassword():
    if request.method == 'POST':
        user = Staff.query.get(session['logged_in_name'])
        if user is None:
            flash("Server error")
            return redirect(url_for('main'))

        if user.password != request.form.get('oldpass'):
            flash("Password verification failed")
        else:
            newpass = request.form.get('newpass', '').strip()
            if not is_valid_password(newpass):
                flash("Bad new password")
            else:
                user.password = newpass
                db.session.commit()
                flash("Password changed")
                logout_user()
                return redirect(url_for('login'))

    return render_template('changepassword.html', username=session['logged_in_name'])


@app.route('/reset/request', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        emailaddress = request.form.get('emailaddress')
        staff = Staff.query.filter(Staff.emailaddress==emailaddress).one_or_none()
        if staff is not None:
            pwreset = PasswordReset(staff=staff)
            db.session.add(pwreset)
            db.session.commit()
            msg = Message('Password Reset', recipients=[staff.emailaddress])
            msg.html = '<a href="%s">Click to reset your password</a>' % (
                url_for('reset_password', secret=pwreset.secret,
                        emailaddress=urllib.quote(staff.emailaddress),
                        _external=True), )
            mail.send(msg)
            flash('Password reset sent')
            return redirect(url_for('main'))
        else:
            flash('Invalid request')

    return render_template('reset_request.html')


@app.route('/reset/password', methods=['GET', 'POST'])
def reset_password():
    emailaddress = request.args.get('emailaddress')
    secret = request.args.get('secret')

    if emailaddress is None or secret is None:
        return redirect(url_for('main'))

    emailaddress = urllib.unquote(emailaddress)
    pwreset = (PasswordReset.query
                            .join(Staff)
                            .filter(PasswordReset.secret==secret,
                                    Staff.emailaddress==emailaddress)).one_or_none()

    if not (pwreset and pwreset.valid):
        return redirect(url_for('main'))

    if request.method == 'POST':
        newpass = request.form.get('newpass')
        if not is_valid_password(newpass):
            flash('Bad password')
        else:
            pwreset.staff.password = newpass
            db.session.delete(pwreset)
            db.session.commit()
            logout_user()
            flash('Password reset')
            return redirect(url_for('login'))

    return render_template('reset_password.html')


@app.route('/publish', methods=['POST'])
def publish():
    ip = request.remote_addr
    publish = Publisher(ip, "publisher", request.json)
    if publish.in_ip_address_range():
        return "Yup"
    abort(403)

if __name__ == '__main__':
    if environ.get('PORT'):
        port = int(environ.get('PORT'))
    else:
        port = 5000
    if environ.get('HOST'):
        host = environ.get('HOST')
    else:
        host = '127.0.0.1'

    app.run(port=port, host=host)
