import unittest
import os
import sys

import library


class LibrarySiteTests(unittest.TestCase):
    
    def setUp(self):
        
        #create db file
        try:
            os.system("python db.py test_library.db")
        except:
            print "ERROR CREATING DATABASE"
            sys.exit(1)
            
        #change the app config to use test database
        library.app.config["DATABASE"] = "test_library.db"
        
        #get test client
        self.app = library.app.test_client()
        
    def tearDown(self):
        
        #delete the test database
        try:
            os.remove("test_library.db");
        except:
            pass

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
        response = self.app.post('/login', data=dict(
                username="fred",
                password="fred",
        ), follow_redirects=True) 
        self.assertIn('Welcome to the Staff Page for the Library Site', response.data)

if __name__ == '__main__':
    unittest.main()
       
