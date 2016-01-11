import unittest
import flask

import library
from database import create_engine, scoped_session, sessionmaker
import flask
import db

class LibrarySiteTests(unittest.TestCase):

    def setUp(self):
        engine = create_engine('sqlite:///:memory:', convert_unicode=True)
        db_session = scoped_session(sessionmaker(autocommit=False,
                                                 autoflush=False,
                                                 bind=engine))
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

if __name__ == '__main__':
    unittest.main()

