import unittest
import flask
import requests
from itertools import chain
from ipaddress import ip_network

import library
from publisher import Publisher
from database import db_session
from sqlalchemy import or_, and_
import models
import flask
import os
import sys
import datetime

if os.environ.get("LIBRARY_ENV",None) != "test":
    print "You need to set LIBRARY_ENV to test!"
    sys.exit(1)

class LibrarySiteTests(unittest.TestCase):

    def setUp(self):
        models.Base.metadata.create_all(bind=models.engine)
        models.init_models()
        self.app = library.app.test_client()

    def tearDown(self):
        models.Base.metadata.drop_all(bind=models.engine)

    def login(self,u,p):
         response = self.app.post('/login', data=dict(
                username=u,
                password=p,
        ), follow_redirects=True)

    def logout(self):
        self.app.get('/logout',follow_redirects=True)

    def test_main(self):
        response = self.app.get('/')
        self.assertIn("Librarian Recommended",response.data)
    
    def test_login(self):
        #test initial get request
        response = self.app.get('/login')
        self.assertIn("Welcome to the Staff Login",response.data)
        
        #test invalid user
        response = self.app.post('/login', data=dict(
                username="invalid",
                password="invalid",
        ), follow_redirects=True) 
        self.assertIn('Invalid Credentials', response.data)
        
        #test valid user
        with self.app:
            response = self.app.post('/login', data=dict(
                username="fred",
                password="fred",
        ), follow_redirects=True)
            self.assertEquals(flask.session["logged_in_name"],"fred")

        response = self.app.post('/login', data=dict(
                username="fred",
                password="fred",
        ), follow_redirects=True) 

        self.assertIn('Welcome to the Librarian Staff Page', response.data)

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
        response = self.app.post("/adduser", data={}, follow_redirects=True)
        self.assertIn("You are not authorized to perform this action.",response.data)
        #try with missing values
        self.logout()
        self.login("admin","admin")
        response = self.app.post("/adduser",data=dict(
            username="t",
            password="t",
            f_name="",
            l_name="",
            phone="",
            email=""),follow_redirects=True)
        self.assertIn("All fields are required. Please try again.",response.data)
        response = self.app.post("/adduser",data=dict(
            username="",
            password="",
            f_name="t",
            l_name="t",
            phone="",
            email=""),follow_redirects=True)
        self.assertIn("All fields are required. Please try again.",response.data)
        #try with bogus phone number
        response = self.app.post("/adduser",data=dict(
            username="t",
            password="t",
            f_name="t",
            l_name="t",
            phone="1112222",
            email="test@testing.com"),follow_redirects=True)
        self.assertIn("Phone number must include area code.",response.data)
        #all is well, make sure stored in db
        response = self.app.post("/adduser",data=dict(
            username="t",
            password="t",
            f_name="t",
            l_name="t",
            phone="1112223333",
            email="test@testing.com"),follow_redirects=True)
        staff=models.Staff.query.filter(and_(models.Staff.username=='t', models.Staff.password=='t', models.Staff.f_name=='t', models.Staff.l_name=='t', models.Staff.phonenumber==1112223333, models.Staff.emailaddress=='test@testing.com')).first()
        self.assertIsNotNone(staff)
        #try adding an existing username
        response = self.app.post("/adduser",data=dict(
            username="t",
            password="t",
            f_name="t",
            l_name="t",
            phone="1112223333",
            email="test2@testing.com"),follow_redirects=True)
        self.assertIn("Username or email address is already used.",response.data)
        #try adding an existing email address
        response = self.app.post("/adduser",data=dict(
            username="u",
            password="u",
            f_name="u",
            l_name="u",
            phone="1112223333",
            email="test@testing.com"),follow_redirects=True)
        self.assertIn("Username or email address is already used.",response.data)
        #second all is well check with non-digit chars in phone
        response = self.app.post("/adduser",data=dict(
            username="u",
            password="u",
            f_name="u",
            l_name="u",
            phone="111-222-3333",
            email="test2@testing.com"),follow_redirects=True)
        staff=models.Staff.query.filter(and_(models.Staff.username=='u', models.Staff.password=='u', models.Staff.f_name=='u', models.Staff.l_name=='u', models.Staff.phonenumber==1112223333, models.Staff.emailaddress=='test2@testing.com')).first()
        self.assertIsNotNone(staff)
        
    def test_addrecread(self):
        #try with admin
        self.login("admin","admin")
        response = self.app.post("/addrecread", data={}, follow_redirects=True)
        self.assertIn("Your are not authorized to perform this action.",response.data)
        #try without book
        self.logout()
        self.login("fred","fred")
        response = self.app.post("/addrecread",data=dict(
            book="",
            author="t",
            comment="t",
            ISBN="t",
            category="t",
            sticky=1),follow_redirects=True)
        self.assertIn("Book name is required.",response.data)
        #all is well
        response = self.app.post("/addrecread",data=dict(
            book="t",
            author="t",
            comment="t",
            ISBN="t",
            category="t",
            sticky=1),follow_redirects=True)
        recread = models.ReadingList.query.filter(and_(
            models.ReadingList.username=='fred',
            models.ReadingList.book=='t',
            models.ReadingList.author=='t',
            models.ReadingList.comment=='t',
            models.ReadingList.ISBN=='t',
            models.ReadingList.sticky==True)).first()
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
        db_session.commit()
        rlid = readinglist.RLID
        #try another user
        self.logout()
        self.login("elmo","elmo")
        
        response = self.app.post("/remrecread/"+str(rlid),data={},follow_redirects=True)
        self.assertNotIn("Deleted recommended reading.",response.data)
        self.logout()

        #try with fred
        self.login("fred","fred")
        response = self.app.post("/remrecread/"+str(rlid),data={},follow_redirects=True)
        self.assertIn("Deleted recommended reading.",response.data)
        rl = models.ReadingList.query.filter(models.ReadingList.ISBN=="eee").first()
        self.assertIsNone(rl)                 
        
    def test_profile(self):
        response = self.app.get("/profile/fred")
        self.assertIn("Fredderson",response.data)
    
        
    def test_github_ip_check(self):
        publish = Publisher('192.168.0.1', "dontmatter", "")
        self.assertFalse(publish.in_ip_address_range())
        jsonResponse = requests.get("https://api.github.com/meta", auth=("KentonCountyLibrary-Cincypy", "CincyPyCoders2000"))
        ipranges = jsonResponse.json()["hooks"]

        ipranges = [list(ip_network(ip).hosts()) for ip in ipranges]

        flat_range = list(chain.from_iterable(ipranges))

        publish = Publisher(str(flat_range[0]), "dontmatter", "")
        self.assertTrue(publish.in_ip_address_range())

if __name__ == '__main__':
    unittest.main()

