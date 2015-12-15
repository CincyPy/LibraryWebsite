import unittest
import flask

import library
from database import create_engine, scoped_session, sessionmaker

class LibrarySiteTests(unittest.TestCase):
    
    def setUp(self):
        engine = create_engine('sqlite:///:memory:', convert_unicode=True)
        db_session = scoped_session(sessionmaker(autocommit=False,
                                                 autoflush=False,
                                                 bind=engine))
        library.db_session = db_session
        #get test client
        self.app = library.app.test_client()
        
    def test_main(self):
        response = self.app.get('/')
        self.assertIn("<h2>Welcome to the Library Site</h2>",response.data)
        
    def test_login(self):
        #test initial get request
        response = self.app.get('/login')
        self.assertIn("Welcome to the Staff Login for the Library Site",response.data)
        
        #test invalid user
        response = self.app.post('/login', data=dict(
                username="invalid",
                password="invalid",
        ), follow_redirects=True) 
        self.assertIn('Invalid Credentials.  Please try again.', response.data)
        
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
        self.assertIn('Welcome to the Staff Page for the Library Site', response.data)

        

    def test_logout(self):
        with self.app:
            response = self.app.get('/logout',follow_redirects=True)
            self.assertIn('You were logged out',response.data)  
            self.assertNotIn("logged_in",flask.session)
        

if __name__ == '__main__':
    unittest.main()
       
