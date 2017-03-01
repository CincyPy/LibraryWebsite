import os
import re

def sitename_from_readme():
    """
    Return text after hash on first non-blank line, if found, otherwise None.
    """
    with open('README.md') as f:
        for line in f:
            if not line.strip():
                continue
            m = re.match('#(.*)$', line)
            return m.group(1).strip() if m else None

def splitcamel(s):
    """
    Split string s into CamelCase parts.
    """
    r = re.findall('[A-Z][^A-Z]+', s)
    if r:
        return r
    else:
        return [s]

class Config(object):
    # configuration
    NAME = "DEBUG"
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DEBUG = True
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_USERNAME = "KentonCountyLibrary@gmail.com"
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD",None)
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_DEFAULT_SENDER = "KentonCountyLibrary@gmail.com"

    SQLALCHEMY_DATABASE_URI = "sqlite:///library.db"

    SITENAME = sitename_from_readme()
    if not SITENAME:
        raise RuntimeError("The site's name not found in README.")
    SITENAMEPARTS = splitcamel(SITENAME)

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
