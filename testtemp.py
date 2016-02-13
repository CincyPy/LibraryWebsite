import unittest
import flask
import requests
from itertools import chain
from ipaddress import ip_network

import library
import database
from database import create_engine, scoped_session, sessionmaker
from publisher import Publisher
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

