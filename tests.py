import unittest
import flask
import requests
from itertools import chain
from ipaddress import ip_network

import library
from publisher import Publisher
from sqlalchemy import or_, and_
import models
import flask
import os
import sys
import datetime

from config import config

if os.environ.get("LIBRARY_ENV",None) != "test":
    print "You need to set LIBRARY_ENV to test!"
    sys.exit(1)

class LibrarySiteTests(unittest.TestCase):

    def setUp(self):
        models.Base.metadata.create_all(bind=library.db.engine)
        self.app = library.app.test_client()
        models.init_models(library.db.session)
        models.init_test_models(library.db.session)
        self.session = library.db.session

    def tearDown(self):
        models.Base.metadata.drop_all(bind=library.db.engine)

    def login(self,u,p):
        with self.app as c:
            response = c.get('/login', follow_redirects=True)
            response = self.app.post('/login', data=dict(
                   username=u,
                   password=p,
                   _csrf_token=flask.session['_csrf_token'],
            ), follow_redirects=True)
        return response

    def logout(self):
        self.app.get('/logout',follow_redirects=True)

    def test_main(self):
        response = self.app.get('/')
        self.assertIn(config.SITENAME, response.data)

    def test_login(self):
        with self.app as c:
            #test initial get request
            response = c.get('/login')
            self.assertIn("Welcome to the Staff Login",response.data)

            #test invalid user
            response = c.post('/login', data=dict(
                    username="invalid",
                    password="invalid",
                    _csrf_token=flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn('Invalid Credentials', response.data)

        #test valid user
        def test_login_as_fred(password):
            with self.app as c:
                c.get('/login')
                response = c.post('/login', data=dict(
                    username="fred",
                    password=password,
                    _csrf_token=flask.session['_csrf_token'],
                ), follow_redirects=True)
                self.assertEquals(flask.session["logged_in_name"],"fred")

                response = c.post('/login', data=dict(
                        username="fred",
                        password=password,
                        _csrf_token=flask.session['_csrf_token'],
                ), follow_redirects=True)

                self.assertIn('Welcome to the Librarian Staff Page', response.data)

        test_login_as_fred("fred")

        #test change password
        with self.app as c:
            c.get('/changepassword')
            response = self.app.post('/changepassword',
                                     data=dict(oldpass='fred',
                                               newpass='freddy',
                                               _csrf_token=flask.session['_csrf_token']),
                                     follow_redirects=True)
            self.assertIn('Welcome to the Staff Login', response.data)
        test_login_as_fred('freddy')

    def test_logout(self):
        with self.app:
            response = self.app.get('/logout',follow_redirects=True)
            self.assertIn('You were logged out',response.data)
            self.assertNotIn("logged_in",flask.session)

    def test_admin(self):
        self.login("admin","admin")
        #test admin
        response = self.app.get("/admin")
        self.assertIn("Add a new staff member",response.data)
        self.assertIn("/edit-profile/admin",response.data)
        self.assertIn("/edit-profile/fred",response.data)

        self.logout()

        #test normal user
        self.login("fred","fred")
        response = self.app.get("/admin", follow_redirects=True)
        self.logout()


    def test_librarian(self):
        self.login("fred","fred")
        response = self.app.get("/librarian")
        self.assertIn("ABCs",response.data)
        self.assertIn("Night Before Christmas",response.data)
        self.assertNotIn("The Invisible Man",response.data)
        self.assertNotIn("Moby Dick",response.data)

    def test_adduser(self):
        #try with non admin
        self.login("fred","fred")
        response = self.app.get('/admin', follow_redirects=True)
        #response = c.post("/adduser", data={}, follow_redirects=True)
        self.assertIn("You are not authorized to perform this action.",response.data)
        #try with missing values
        self.logout()

        self.login("admin","admin")
        with self.app as c:
            c.get('/admin', follow_redirects=True)
            response = c.post("/adduser",data=dict(
                username="t",
                password="t",
                f_name="",
                l_name="",
                phone="",
                _csrf_token = flask.session['_csrf_token'],
                emailaddress=""),follow_redirects=True)
            self.assertIn("All fields are required. Please try again.",response.data)
            response = c.post("/adduser",data=dict(
                username="",
                password="",
                f_name="t",
                l_name="t",
                phone="",
                _csrf_token = flask.session['_csrf_token'],
                emailaddress=""),follow_redirects=True)
            self.assertIn("All fields are required. Please try again.",response.data)
            #try with bogus phone number
            response = c.post("/adduser",data=dict(
                username="t",
                password="t",
                f_name="t",
                l_name="t",
                phone="1112222",
                _csrf_token = flask.session['_csrf_token'],
                emailaddress="test@testing.com"),follow_redirects=True)
            self.assertIn("Phone number must include area code.",response.data)
            #all is well, make sure stored in db
            response = c.post("/adduser",data=dict(
                username="t",
                password="t",
                f_name="t",
                l_name="t",
                phone="1112223333",
                _csrf_token = flask.session['_csrf_token'],
                emailaddress="test@testing.com"),follow_redirects=True)
            staff=models.Staff.query.filter(
                and_(models.Staff.username=='t', models.Staff.f_name=='t',
                     models.Staff.l_name=='t',
                     models.Staff.phonenumber==1112223333,
                     models.Staff.emailaddress=='test@testing.com')).first()
            #NOTE: password must be verified on the Python side now
            self.assertIsNotNone(staff)
            self.assertTrue(staff.password=='t')
            #try adding an existing username
            response = c.post("/adduser",data=dict(
                username="t",
                password="t",
                f_name="t",
                l_name="t",
                _csrf_token = flask.session['_csrf_token'],
                phone="1112223333",
                emailaddress="test2@testing.com"),follow_redirects=True)
            self.assertIn("Username or email address is already used.",response.data)
            #try adding an existing email address
            response = c.post("/adduser",data=dict(
                username="u",
                password="u",
                f_name="u",
                l_name="u",
                _csrf_token = flask.session['_csrf_token'],
                phone="1112223333",
                emailaddress="test@testing.com"),follow_redirects=True)
            self.assertIn("Username or email address is already used.",response.data)
            #second all is well check with non-digit chars in phone
            response = c.post("/adduser",data=dict(
                username="u",
                password="u",
                f_name="u",
                l_name="u",
                _csrf_token = flask.session['_csrf_token'],
                phone="111-222-3333",
                emailaddress="test2@testing.com"),follow_redirects=True)
            staff=models.Staff.query.filter(
                and_(models.Staff.username=='u', models.Staff.f_name=='u',
                     models.Staff.l_name=='u',
                     models.Staff.phonenumber==1112223333,
                     models.Staff.emailaddress=='test2@testing.com')).first()
            self.assertIsNotNone(staff)
            self.assertTrue(staff.password=='u')

    def test_deleteuser(self):
        # ALL posts without csrf should fail
        #
        # # non-admin can't delete users
        # self.login("fred", "fred")
        # response = self.app.post("/deleteuser/elmo", data={}, follow_redirects=True)
        # self.assertIn("You are not authorized to perform this action.", response.data)
        # self.logout()

        self.login("admin", "admin")
        with self.app as c:
            # can't delete admin
            c.get('/admin', follow_redirects=True)
            response = c.post("/deleteuser/admin",
                              data={'_csrf_token': flask.session['_csrf_token']},
                              follow_redirects=True)
            self.assertIn("You are not authorized to perform this action.", response.data)
            # deleting user removed recommended readings and user
            c.get('/admin', follow_redirects=True)
            response = c.post("/deleteuser/elmo",
                              data={'_csrf_token': flask.session['_csrf_token']},
                              follow_redirects=True)
            self.assertIn("User was successfully removed!", response.data)
            rl = models.ReadingList.query.filter(models.ReadingList.username=="elmo").first()
            self.assertIsNone(rl)
            s = models.Staff.query.filter(models.Staff.username=="elmo").first()
            self.assertIsNone(s)
            # confirm delete user with patron contacts
            c.get('/admin', follow_redirects=True)
            response = c.post("/deleteuser/fred",
                              data={'_csrf_token': flask.session['_csrf_token']},
                              follow_redirects=True)
            self.assertIn("User was successfully removed!", response.data)
            rl = models.PatronContact.query.filter(models.PatronContact.username=="fred").first()
            self.assertIsNone(rl)
            s = models.Staff.query.filter(models.Staff.username=="elmo").first()
            self.assertIsNone(s)

    def test_edituser(self):
        #try with admin
        self.logout()
        self.login("admin","admin")
        response = self.app.get("/edit-profile/admin")
        self.assertIn("Staff Profile for admin",response.data)
        #try with non admin
        self.login("fred","fred")
        response = self.app.get("/edit-profile/fred")
        self.assertIn("2222222222",response.data) # Verify that correct phone number is retrieved for fred

        #try name change
        self.login("fred","fred")
        with self.app as c:
            c.get('/edit-profile/fred')
            response = c.post("/edit-profile/fred",data=dict(
                f_name = 'Freddy',
                l_name = 'Fredderson',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Profile updated",response.data)
            staff=models.Staff.query.filter(and_(models.Staff.username=='fred',
                models.Staff.f_name=='Freddy', models.Staff.l_name=='Fredderson',
                models.Staff.emailaddress=='KentonCountyLibrary@gmail.com',
                models.Staff.phonenumber=='2222222222',
                models.Staff.bio=="I am Fred's incomplete bio",
                models.Staff.phone==0, models.Staff.irl==0,
                models.Staff.email==1, models.Staff.chat==0)).first()
            self.assertIsNotNone(staff)

        #try adding interests (and change name back to Fred)
        self.login("fred","fred")
        with self.app as c:
            c.get('/edit-profile/fred')
            response = c.post("/edit-profile/fred",data=dict(
                f_name = 'Fred',
                l_name = 'Fredderson',
                interests = 'books',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Profile updated",response.data)
            staff=models.Staff.query.filter(and_(models.Staff.username=='fred', models.Staff.interests=='books')).first()
            self.assertIsNotNone(staff)

        #try changing with incorrect phone number
        self.login("fred","fred")
        with self.app as c:
            c.get('/edit-profile/fred')
            response = c.post("/edit-profile/fred",data=dict(
                emailaddress = 'test@test.net',
                phonenumber = '111-1111',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Your phone number must include the area code",response.data)
            self.assertIn("test@test.net",response.data) # Verify that input data was retained
            staff=models.Staff.query.filter(and_(models.Staff.username=='fred', models.Staff.emailaddress=='test@test.net', models.Staff.phonenumber=='1111111')).first()
            self.assertIsNone(staff)

        #try changing to an existing email
        self.login("fred","fred")
        with self.app as c:
            c.get('/edit-profile/fred')
            response = c.post("/edit-profile/fred",data=dict(
                emailaddress = 'ernie@test.com',
                phonenumber = '111-111-1111',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Email address used by another user.",response.data)
            staff=models.Staff.query.filter(and_(models.Staff.username=='fred', models.Staff.emailaddress=='ernie@test.com', models.Staff.phonenumber=='1111111111')).first()
            self.assertIsNone(staff)

        #try changing email and phone number
        self.login("fred","fred")
        with self.app as c:
            c.get('/edit-profile/fred')
            response = c.post("/edit-profile/fred",data=dict(
                emailaddress = 'test@test.net',
                phonenumber = '111-111-1111',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Profile updated",response.data)
            staff=models.Staff.query.filter(and_(models.Staff.username=='fred', models.Staff.emailaddress=='test@test.net', models.Staff.phonenumber=='1111111111')).first()
            self.assertIsNotNone(staff)

        #try adding email and chat contact pref (change email and phone number back)
        self.login("fred","fred")
        with self.app as c:
            c.get('/edit-profile/fred')
            response = c.post("/edit-profile/fred",data=dict(
                emailaddress = 'KentonCountyLibrary@gmail.com',
                phonenumber = '222-222-2222',
                interests = 'I like tests',
                bio = 'test',
                phone = 'on',
                chat = 'on',
                irl = 'on',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Profile updated",response.data)
            staff=models.Staff.query.filter(and_(models.Staff.username=='fred', models.Staff.emailaddress=='KentonCountyLibrary@gmail.com', models.Staff.phonenumber=='2222222222', models.Staff.bio=="test", models.Staff.phone==1, models.Staff.irl==1, models.Staff.email==1, models.Staff.chat==1)).first()
            self.assertIsNotNone(staff)

        #Change Password
        #try incorrect old password
        self.login("fred","fred")
        with self.app as c:
            c.get('/edit-profile/fred')
            response = c.post("/changepassword",data=dict(
                oldpass = 'garbage',
                newpass = 'password',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Password verification failed",response.data)
            staff=models.Staff.query.filter(
                and_(models.Staff.username=='fred',
                     models.Staff.emailaddress=='KentonCountyLibrary@gmail.com')).first()
            #NOTE: password must be verified on the Python side now
            self.assertIsNotNone(staff)
            self.assertTrue(staff.password=='fred')

        #try changing password (then change back)
        self.login("fred","fred")
        with self.app as c:
            c.get('/edit-profile/fred')
            response = c.post("/changepassword",data=dict(
                oldpass = 'fred',
                newpass = 'password',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Password changed",response.data)
            staff=models.Staff.query.filter(
                and_(models.Staff.username=='fred',
                     models.Staff.emailaddress=='KentonCountyLibrary@gmail.com')).first()
            #NOTE: password must be verified on the Python side now
            self.assertIsNotNone(staff)
            self.assertTrue(staff.password=='password')

        self.login("fred","password")
        with self.app as c:
            c.get('/changepassword')
            response = c.post("/changepassword",data=dict(
                oldpass = 'fred',
                newpass = 'fred',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)

    def test_addrecread(self):
        # admin can edit, but book name must exist.
        self.login("admin", "admin")
        with self.app as c:
            c.get('/admin')
            # admin EDIT - no book name
            response = c.post("/addrecread", data=dict(
                RLID="1",
                book="",
                author="t",
                comment="t",
                ISBN="t",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("Book name is required.", response.data)
            # admin EDIT - no ISBN
            response = c.post("/addrecread", data=dict(
                RLID="1",
                book="t",
                author="t",
                comment="t",
                ISBN="",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("ISBN is required.", response.data)
            # admin EDIT - no author
            response = c.post("/addrecread", data=dict(
                RLID="1",
                book="t",
                author="",
                comment="t",
                ISBN="t",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("Author is required.", response.data)
            # admin EDIT - no category
            response = c.post("/addrecread", data=dict(
                RLID="1",
                book="t",
                author="t",
                comment="t",
                ISBN="t",
                category="",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("Category is required.", response.data)
        # admin EDIT - with book name
        self.login("admin", "admin")
        with self.app as c:
            c.get('/admin')
            response = c.post("/addrecread", data=dict(
                RLID="1",
                book="t",
                author="t",
                comment="t",
                ISBN="t",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            recread = models.ReadingList.query.filter(and_(
                models.ReadingList.book == 't',
                models.ReadingList.author == 't',
                models.ReadingList.comment == 't',
                models.ReadingList.ISBN == 't',
                models.ReadingList.sticky == True)).first()
            self.assertIsNotNone(recread)
            self.logout()

        # fred can edit and can add
        self.login("fred", "fred")
        with self.app as c:
            c.get('/librarian')
            # fred ADD - no book name
            response = c.post("/addrecread", data=dict(
                book="",
                author="t",
                comment="t",
                ISBN="t",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("Book name is required.", response.data)
            # fred ADD - no ISBN
            response = c.post("/addrecread", data=dict(
                book="t",
                author="t",
                comment="t",
                ISBN="",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("ISBN is required.", response.data)
            # fred ADD - no author
            response = c.post("/addrecread", data=dict(
                book="t",
                author="",
                comment="t",
                ISBN="t",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("Author is required.", response.data)
            # fred ADD - no Cateogry
            response = c.post("/addrecread", data=dict(
                book="t",
                author="t",
                comment="t",
                ISBN="t",
                category="",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("Category is required.", response.data)
            # fred ADD - with book name
            response = c.post("/addrecread", data=dict(
                book="t",
                author="t",
                comment="t",
                ISBN="t",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            recread = models.ReadingList.query.filter(and_(
                models.ReadingList.username == 'fred',
                models.ReadingList.book == 't',
                models.ReadingList.author == 't',
                models.ReadingList.comment == 't',
                models.ReadingList.ISBN == 't',
                models.ReadingList.sticky == True)).first()
            self.assertIsNotNone(recread)
            # fred EDIT - no book name
            c.get('/librarian')
            response = c.post("/addrecread", data=dict(
                RLID="1",
                book="",
                author="t",
                comment="t",
                ISBN="t",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("Book name is required.", response.data)
            # fred EDIT - no ISBN name
            response = c.post("/addrecread", data=dict(
                RLID="1",
                book="t",
                author="t",
                comment="t",
                ISBN="",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("ISBN is required.", response.data)
            # fred EDIT - no author
            response = c.post("/addrecread", data=dict(
                RLID="1",
                book="t",
                author="",
                comment="t",
                ISBN="t",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("Author is required.", response.data)
            # fred EDIT - no cateogry
            response = c.post("/addrecread", data=dict(
                RLID="1",
                book="t",
                author="t",
                comment="t",
                ISBN="t",
                category="",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            self.assertIn("Category is required.", response.data)
            # fred EDIT - with book name
            response = c.post("/addrecread", data=dict(
                RLID="1",
                book="t",
                author="t",
                comment="t",
                ISBN="t",
                category="t",
                _csrf_token = flask.session['_csrf_token'],
                sticky=1), follow_redirects=True)
            recread = models.ReadingList.query.filter(and_(
                models.ReadingList.username == 'fred',
                models.ReadingList.book == 't',
                models.ReadingList.author == 't',
                models.ReadingList.comment == 't',
                models.ReadingList.ISBN == 't',
                models.ReadingList.sticky == True)).first()
            self.assertIsNotNone(recread)

    def test_remrecread(self):
        #unknown recread, should not matter
        self.login("fred","fred")
        response = self.app.post("/remrecread/100",data={},follow_redirects=True)
        self.assertNotIn("Deleted recommended reading.",response.data)
        #insert a recread, make sure its removed
        fred = models.Staff.query.filter(models.Staff.username=='fred').first()

        readinglist = models.ReadingList(
            recdate=datetime.date.today(),
            ISBN="eee",
            book="book",
            author="author",
            comment="comment",
            sticky=0,
            category="category")
        fred.readinglist.append(readinglist)
        self.session.commit()
        rlid = readinglist.RLID
        #try another user
        self.logout()
        self.login("elmo","elmo")

        response = self.app.post("/remrecread/"+str(rlid),data={},follow_redirects=True)
        self.assertNotIn("Deleted recommended reading.",response.data)
        self.logout()

        #try with fred
        self.login("fred","fred")
        with self.app as c:
            c.get('/admin')
            response = c.post("/remrecread/"+str(rlid),
                              data=dict(_csrf_token=flask.session['_csrf_token']),
                              follow_redirects=True)
            self.assertIn("Deleted recommended reading.",response.data)
            rl = models.ReadingList.query.filter(models.ReadingList.ISBN=="eee").first()
            self.assertIsNone(rl)

    def test_profile(self):
        response = self.app.get("/profile/fred")
        self.assertIn("Fredderson",response.data)

    def test_add_patroncontact(self):
        with self.app as c:
            response = c.get("/contact/fred")
            self.assertIn("Contact Fred", response.data)
            #confirm that default contact preference is/not present
            self.assertIn("In Person", response.data)
            self.assertNotIn("Online Chat", response.data)

            #add In Person contact request
            response = c.post("/contact/fred",data=dict(
                test = True,
                name = 'Jeff Johnson',
                email = 'test@test.net',
                contact = 'irl',
                times = 'Anytime',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("contact request was received",response.data)
            patroncontact=models.PatronContact.query.filter(and_(
                models.PatronContact.username=='fred',
                models.PatronContact.name=='Jeff Johnson',
                models.PatronContact.email=='test@test.net',
                models.PatronContact.contact=='irl',
                models.PatronContact.times=='Anytime')).first()
            self.assertIsNotNone(patroncontact)

            #test contact page exists
            response = self.app.get("/contact/fred")
            self.assertIn("Contact Fred",response.data)
            #confirm that default contact preference is/not present
            self.assertIn("In Person",response.data)
            self.assertNotIn("Online Chat",response.data)

            #add In Person contact request
            response = c.post("/contact/fred",data=dict(
                test = True,
                name = 'Jeff Johnson',
                email = 'test@test.net',
                contact = 'irl',
                times = 'Anytime',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("contact request was received",response.data)
            patroncontact=models.PatronContact.query.filter(and_(
                models.PatronContact.username=='fred',
                models.PatronContact.name=='Jeff Johnson',
                models.PatronContact.email=='test@test.net',
                models.PatronContact.contact=='irl',
                models.PatronContact.times=='Anytime')).first()
            self.assertIsNotNone(patroncontact)

            #test missing email
            response = c.post("/contact/fred",data=dict(
                test = True,
                name = 'Jeff Johnson',
                email = '',
                contact = 'phone',
                phone = '',
                times = 'Anytime',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Please enter your name and email address in the contact area",response.data)
            self.assertIn("Jeff Johnson",response.data) # Verify that input data was retained
            patroncontact=models.PatronContact.query.filter(and_(models.PatronContact.username=='fred', models.PatronContact.name=='Jeff Johnson', models.PatronContact.contact=='phone', models.PatronContact.times=='Anytime')).first()
            self.assertIsNone(patroncontact)

            #test missing contact preference
            response = c.post("/contact/fred",data=dict(
                test = True,
                name = 'Jeff Johnson',
                email = 'test@test.net',
                phone = '555-555-5555',
                times = 'Anytime',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Please select a contact method",response.data)
            patroncontact=models.PatronContact.query.filter(and_(models.PatronContact.username=='fred', models.PatronContact.name=='Jeff Johnson', models.PatronContact.email=='test@test.net', models.PatronContact.phone=='555-555-5555', models.PatronContact.times=='Anytime')).first()
            self.assertIsNone(patroncontact)

            #test missing phone number
            response = c.post("/contact/fred",data=dict(
                test = True,
                name = 'Jeff Johnson',
                email = 'test@test.net',
                contact = 'phone',
                phone = '',
                times = 'Anytime',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Please enter your phone number",response.data)
            patroncontact=models.PatronContact.query.filter(and_(models.PatronContact.username=='fred', models.PatronContact.name=='Jeff Johnson', models.PatronContact.email=='test@test.net', models.PatronContact.contact=='phone', models.PatronContact.times=='Anytime')).first()
            self.assertIsNone(patroncontact)

            #test incomplete phone number
            response = c.post("/contact/fred",data=dict(
                test = True,
                name = 'Jeff Johnson',
                email = 'test@test.net',
                contact = 'phone',
                phone = '555-5555',
                times = 'Anytime',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Your phone number must include the area code",response.data)

            #Add chat and email options to fred's contact preferences
            staff = models.Staff.query.get('fred')
            staff.chat, staff.email = True, True
            self.session.add(staff)
            self.session.commit()
            response = self.app.get("/contact/fred")
            self.assertIn("Online Chat",response.data)

            #Test missing chat request info
            response = c.post("/contact/fred",data=dict(
                test = True,
                name = 'Jeff Johnson',
                email = 'test@test.net',
                contact = 'chat',
                chat = '',
                handle = 'bigDog',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Please input your preferred chat service and handle",response.data)

            #test email entry
            response = c.post("/contact/fred",data=dict(
                test = True,
                name = 'Jeff Johnson',
                email = 'test@test.net',
                contact = 'phone',
                phone = '555-5555',
                times = 'Anytime',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Your phone number must include the area code",response.data)

            #test email entry
            response = c.post("/contact/fred",data=dict(
                test = True,
                name = 'Jeff Johnson',
                email = 'test@test.net',
                contact = 'email',
                phone = '555-555-5555',
                times = 'Anytime',
                likes = 'I like books',
                dislikes = 'Sans books',
                comment = 'No comment',
                audience = 'adults,children',
                format_pref = 'book,eb',
                chat = 'Skype',
                handle = 'bigDog',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("contact request was received",response.data)
            patroncontact=models.PatronContact.query.filter(and_(models.PatronContact.username=='fred', models.PatronContact.name=='Jeff Johnson', models.PatronContact.email=='test@test.net', models.PatronContact.contact=='email', \
                                                                 models.PatronContact.likes=='I like books', models.PatronContact.dislikes=='Sans books', models.PatronContact.comment=='No comment', models.PatronContact.format_pref=='book,eb', models.PatronContact.audience=='adults,children')).first()
            self.assertIsNotNone(patroncontact)

            #test incomplete location info on book to speak request
            response = c.post("/contact/fred?speak=True",data=dict(
                test = True,
                contact = 'speak',
                name = 'Jeff Johnson',
                email = 'test@test.net',
                location = '',
                comment = 'anything',
                org = 'CincyPy',
                mult = False,
                times = '05/04/2016 2:30 PM',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Please provide the address for where you would",response.data)

            #test incomplete location info on book to speak request
            response = c.post("/contact/fred?speak=True",data=dict(
                test = True,
                contact = 'speak',
                name = 'Jeff Johnson',
                email = 'test@test.net',
                location = 'My house',
                comment = 'anything',
                org = 'CincyPy',
                mult = False,
                times = '05/04/2016 2:30 PM',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("contact request was received",response.data)
            patroncontact=models.PatronContact.query.filter(and_(models.PatronContact.username=='fred', models.PatronContact.name=='Jeff Johnson', models.PatronContact.email=='test@test.net', models.PatronContact.contact=='speak', \
                                                                 models.PatronContact.location=='My house', models.PatronContact.comment=='anything', models.PatronContact.org=='CincyPy', models.PatronContact.times=='05/04/2016 2:30 PM')).first()
            self.assertIsNotNone(patroncontact)

    def test_edit_patroncontact(self):
        #test patron contact exists on librarian page
        self.login("fred", "fred")

        with self.app as c:
            response = c.get("/librarian")
            self.assertIn("Joe Johnson",response.data) # Test that patron contact request is shown

            #confirm status can be changed
            response = self.app.post("/contact_status/1",data=dict(
                status = 'pending',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertIn("Joe Johnson Patron request status has been updated",response.data)
            self.assertIn("2016-01-07",response.data)
            patroncontact=models.PatronContact.query.filter(and_(models.PatronContact.username=='fred',
                models.PatronContact.name=='Joe Johnson',
                models.PatronContact.email=='jjohanson@bigpimpn.net',
                models.PatronContact.contact=='phone',
                models.PatronContact.phone=='5555555555',
                models.PatronContact.times=='M-Th 12-2 pm',
                models.PatronContact.status=='pending')).first()
            self.assertIsNotNone(patroncontact)
            #confirm closed contact requests are not shown
            response = self.app.post("/contact_status/1",data=dict(
                status = 'closed',
                _csrf_token = flask.session['_csrf_token'],
            ), follow_redirects=True)
            self.assertNotIn("2016-01-07",response.data)
            patroncontact=models.PatronContact.query.filter(and_(models.PatronContact.username=='fred',
                models.PatronContact.name=='Joe Johnson',
                models.PatronContact.email=='jjohanson@bigpimpn.net',
                models.PatronContact.contact=='phone',
                models.PatronContact.phone=='5555555555',
                models.PatronContact.times=='M-Th 12-2 pm',
                models.PatronContact.status=='closed')).first()
            self.assertIsNotNone(patroncontact)

if __name__ == '__main__':
    unittest.main()
