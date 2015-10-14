import unittest

import library


class LibrarySiteTests(unittest.TestCase):
    
    def setUp(self):
        self.app = library.app.test_client()
        
    def test_main(self):
        response = self.app.get('/')
        self.assertIn("<h2>Welcome to the Library Site</h2>",response.data)
        

if __name__ == '__main__':
    unittest.main()
       
