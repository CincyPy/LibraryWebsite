import os

class Config(object):
    # configuration
    NAME = "DEBUG"
    SECRET_KEY = 'shh'
    DEBUG = True
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_USERNAME = "KentonCountyLibrary@gmail.com"
    MAIL_PASSWORD = "CincyPyCoders"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_DEFAULT_SENDER = "KentonCountyLibrary@gmail.com"

    SQLALCHEMY_DATABASE_URI = "sqlite:///library.db"

    def __init__(self):
        print "Config environment is: " + self.NAME
    
class TestConfig(Config):
    NAME = "TEST"
    SQLALCHEMY_DATABASE_URI = "sqlite://"

config = None
if os.environ.get("LIBRARY_ENV",None) == "test":
    config = TestConfig()
else:
    config = Config()
