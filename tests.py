import unittest
import flask

import library
import database
from database import create_engine, scoped_session, sessionmaker
import models
import flask
import db

class LibrarySiteTests(unittest.TestCase):

    def setUp(self):
        engine = create_engine('sqlite:///:memory:', convert_unicode=True)
        db_session = scoped_session(sessionmaker(autocommit=False,
                                                 autoflush=False,
                                                 bind=engine))
        models.Base.query = db_session.query_property()
        models.Base.metadata.create_all(bind=engine)
        models.init_models(db_session)
        library.db_session = db_session
        #get test client
        self.app = library.app.test_client()

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
        self.assertIn("Add a new staff member:",response.data)
        self.assertIn("/edit-profile/admin",response.data)
        self.assertNotIn("/edit-profile/fred",response.data)

        self.logout()
        
        #test normal user
        self.login("fred","fred")
        response = self.app.get("/admin")
        self.assertNotIn("Add a new staff member:",response.data)
        self.assertIn("/edit-profile/fred",response.data)
        self.assertIn("/profile/admin",response.data)
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
        db = library.connect_db()
        cur = db.execute("SELECT * from staff WHERE username='t' AND  password ='t' AND f_name='t' AND l_name='t' AND phone='1112223333' AND email='test@testing.com'")
        rows = cur.fetchall()
        self.assertEqual(len(rows),1)
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
        db = library.connect_db()
        cur = db.execute("SELECT * from staff WHERE username='u' AND  password ='u' AND f_name='u' AND l_name='u' AND phone='1112223333' AND email='test2@testing.com'")
        rows = cur.fetchall()
        self.assertEqual(len(rows),1)

        
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
            URL="t",
            category="t",
            sticky="t"),follow_redirects=True)
        self.assertIn("Book name is required.",response.data)
        #all is well
        response = self.app.post("/addrecread",data=dict(
            book="t",
            author="t",
            comment="t",
            URL="t",
            category="t",
            sticky="t"),follow_redirects=True)
        #db = library.connect_db()
        #XXX: not working with SQLAlchemy models
        cur = library.db_session.execute("SELECT * from readinglist WHERE username='fred' AND book='t' AND author='t' AND comment='t' AND URL='t' AND category='t' AND sticky='t'")
        rows = cur.fetchall()
        self.assertEqual(len(rows),1)
        
    def test_remrecread(self):
        #unknown recread, should not matter
        self.login("fred","fred")
        response = self.app.post("/remrecread/100",data={},follow_redirects=True)
        self.assertIn("Delete recommended reading.",response.data)
        #insert a recread, make sure its removed
        response = self.app.post("/addrecread",data=dict(
            book="t",
            author="t",
            comment="t",
            URL="t",
            category="t",
            sticky="t"),follow_redirects=True)
        db = library.connect_db()
        cur = db.execute("SELECT RLID from readinglist WHERE username='fred' AND book='t'")
        rows = cur.fetchall()
        rlid = rows[0][0]
        response = self.app.post("/remrecread/"+str(rlid),data={},follow_redirects=True)
        cur = db.execute("SELECT RLID from readinglist WHERE username='fred' AND book='t'")
        rows = cur.fetchall()
        self.assertEqual(len(rows),0)

    def test_profile(self):
        response = self.app.get("/profile/fred")
        self.assertIn("Fredderson",response.data)
    
        
        

if __name__ == '__main__':
    unittest.main()

