import os

class Config(object):
    # configuration
    NAME = "PRODUCTION"
    SECRET_KEY = '\x00\xb47\xb1\x1b<*tx\x1b2ywW\x86\x01\xfa\xcd\x0b\xeb\x94\x1c\xe5\xaf'
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_USERNAME = "KentonCountyLibrary@gmail.com"
    MAIL_PASSWORD = "CincyPyCoders"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_DEFAULT_SENDER = "KentonCountyLibrary@gmail.com"

    DBPATH = "sqlite:///library.db"

    def __init__(self):
        print "Config environment is: " + self.NAME
    
class TestConfig(Config):
    NAME = "TEST"
    DBPATH = "sqlite://"

config = None
if os.environ["LIBRARY_ENV"] == "test":
    config = TestConfig()
else:
    config = Config()
