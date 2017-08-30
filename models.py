import argparse
import datetime as dt
import os
import sys
import urllib
import random
import string
import re

from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import backref, relationship
from sqlalchemy.ext.declarative import declarative_base

from passwordtype import PasswordType

Base = declarative_base()

class Meta(Base):
    """
    The meta table is to store information about the database or application.
    It is set up as a simple key/value store.
    """
    __tablename__ = 'meta'
    key = Column(String, primary_key=True)
    value = Column(String)

class Staff(Base):
    __tablename__ = 'staff'

    username = Column(String, primary_key=True)
    password = Column(PasswordType)
    f_name = Column(String)
    l_name = Column(String)
    phonenumber = Column(String)
    emailaddress = Column(String, unique=True)

    bio = Column(Text, default='')
    email = Column(Boolean, default=True)
    phone = Column(Boolean, default=False)
    chat = Column(Boolean, default=False)
    irl = Column(Boolean, default=False)

    interests = Column(Text, default='')

    patron_contacts = relationship('PatronContact',
                                   cascade='all, delete-orphan',
                                   backref=backref('staff',
                                                   uselist=False))

    def __getitem__(self, attr):
        return getattr(self, attr)

    @property
    def category_list(self):
        return set([item.category for item in self.readinglist])

    def profile_path(self):
        from library import app
        uploadsdir = os.path.join(app.static_folder, 'uploads')

        # uuid4 regex
        # https://stackoverflow.com/a/18359032
        fnre = re.compile(r'(.+)-[\da-f]{8}-[\da-f]{4}-4[\da-f]{3}-[89ab][\da-f]{3}-[\da-f]{12}\.jpg')

        for fn in os.listdir(uploadsdir):
            match = fnre.match(fn)
            if match:
                fnusername = match.groups(1)[0]
            else:
                fnusername, _ = os.path.splitext(fn)
            if fnusername == self.username:
                pic_file_name = 'uploads/%s' % fn
                break
        else:
            pic_file_name = 'uploads/anon.jpg'

        return pic_file_name

    def full_name(self):
        return str(self.f_name) + ' ' + str(self.l_name)

class PasswordReset(Base):
    __tablename__ = 'passwordreset'

    secret = Column(String, primary_key=True)
    created = Column(DateTime, default=dt.datetime.now)

    username = Column(String, ForeignKey('staff.username', ondelete='CASCADE'))
    staff = relationship('Staff', backref='passwordresets')

    def __init__(self, **kwargs):
        super(PasswordReset, self).__init__(**kwargs)
        if 'secret' not in kwargs:
            self.secret = self.gensecret(8)

    @classmethod
    def gensecret(self, n):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.SystemRandom().choice(chars) for _ in range(n))

    @property
    def valid(self):
        # valid if not over an hour old
        return (dt.datetime.now() - self.created).total_seconds() / 60 / 60 < 1


class ReadingList(Base):
    __tablename__ = 'readinglist'

    RLID = Column(Integer, primary_key=True)
    ISBN = Column(Text)
    recdate = Column(Date)

    username = Column(String, ForeignKey('staff.username', ondelete='CASCADE'))
    staff = relationship('Staff', backref='readinglist')

    book = Column(Text)
    author = Column(Text)
    comment = Column(Text)
    sticky = Column(Boolean, default=False)
    category = Column(Text)


class PatronContact(Base):
    __tablename__ = 'patroncontact'

    PCID = Column(Integer, primary_key=True)
    reqdate = Column(Text)
    username = Column(String, ForeignKey('staff.username'))
    name = Column(Text)
    email = Column(Text)
    contact = Column(Text) # Contact methods: phone, email, chat, irl, speak (for booking a speaking engagement)
    phone = Column(Text)
    times = Column(Text)
    likes = Column(Text)
    dislikes = Column(Text)
    comment = Column(Text)
    audience = Column(Text)
    format_pref = Column(Text)
    chat = Column(Text)
    handle = Column(Text)
    location = Column(Text)
    org = Column(Text)
    mult = Column(Boolean, default=False) # Tracks if selecting multiply dates for booking a speaking engagement
    status = Column(Text)

    def __getitem__(self, attr):
        return getattr(self, attr)

def init_models(session):
    version = Meta(key="DB_VERSION", value="0")
    session.add(version)
    session.commit()

def init_test_models(session):
    admin = Staff(username='admin', password='admin', f_name='Admin', emailaddress='admin@test.com',
                  l_name='User', phonenumber=1111111111, bio='Admin bio')
    session.add(admin)

    fred = Staff(username='fred', password='fred', f_name='Fred', emailaddress='KentonCountyLibrary@gmail.com',
                 l_name='Fredderson', phonenumber=2222222222, bio='I am Fred\'s incomplete bio',
                 interests='long walks, hobbies, interests, model cars', irl=True,
                 patron_contacts=[
                     PatronContact(reqdate='2016-01-07',
                            status='open',
                            name='Joe Johnson',
                            email='jjohanson@bigpimpn.net',
                            contact='phone',
                            phone='5555555555',
                            times='M-Th 12-2 pm'),
                 ])
    rl1 = ReadingList(recdate=dt.date(2015,10,1),
                      ISBN='9780394800301',
                      book='ABCs',
                      author='Dr. Suess',
                      comment='best seller',
                      category='Mystery')
    rl2 = ReadingList(recdate=dt.date(2015,10,2),
                      ISBN=' 9781402750656',
                      book='Night Before Christmas',
                      author='Santa',
                      comment='find holday fun',
                      category='Sci-fi')
    fred.readinglist.append(rl1)
    fred.readinglist.append(rl2)
    session.add(fred)

    loremipsum = '''Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'''
    loreminterests = 'long walks on the beach, hobbies, interests, model cars, real python, meatballs, 80s jock jams, hangin with mr cooper, drawing with chalk, bird watching, trying to make long interests lists, trying not to run out of ideas and failing'

    session.add(Staff(username='ernie',
                         password='ernie',
                         f_name='Ernie',
                         l_name='Ernieston',
                         phonenumber=3333333333,
                         emailaddress='ernie@test.com',
                         bio=loremipsum,
                         interests = loreminterests))
    session.add(Staff(username='bert',
                         password='bert',
                         f_name='Bert',
                         l_name='Burterson',
                         phonenumber=4444444444,
                         emailaddress='bert@test.com',
                         bio=loremipsum,
                         interests = loreminterests))
    session.add(Staff(username='bigbird',
                         password='bigbird',
                         f_name='Big',
                         l_name='Bird',
                         phonenumber=5555555555,
                         emailaddress='bigbird@test.com',
                         bio=loremipsum,
                         interests = loreminterests))
    session.add(Staff(username='oscar',
                         password='oscar',
                         f_name='Oscar',
                         l_name='Thegrouch',
                         phonenumber=6666666666,
                         emailaddress='oscar@test.com',
                         bio=loremipsum,
                         interests = loreminterests))
    elmo = Staff(username='elmo',
                         password='elmo',
                         f_name='Elmo',
                         l_name='Elmostein',
                         phonenumber=7777777777,
                         emailaddress='elmo@test.com',
                         bio=loremipsum,
                         interests = loreminterests)
    session.add(elmo)
    session.add(PasswordReset(staff=elmo))

    session.commit()
    session.query(Staff).get('elmo').readinglist = [
        ReadingList(
            recdate=dt.date(2015,12,21),
            ISBN='9789380028293',
            book='The Invinsible Man',
            author='H. G. Wells',
            comment='my fav',
            category='History'),
        ReadingList(
            recdate=dt.date(2015,12,21),
            ISBN='9780393972832',
            book='Moby Dick',
            author='Herman Melville',
            comment='a whale of a tale',
            category='Music')
    ]

    session.add(Staff(username='elmoo',
                      password='elmoo',
                      f_name='Elmo',
                      l_name='Ornstein',
                      phonenumber=8888888888,
                      emailaddress='elmoo@sesamestreet.com',
                      bio=loremipsum,
                      interests=loreminterests))

    session.commit()

def createdb(args):
    """
    Create database.
    If a sqlite file can be found in the database URI of the app, prompt to
    remove it, if found on the filesystem, and then create it with the database
    structure and initial data.
    """
    from library import app, db

    def raise_unable_to_parse(uri):
        raise RuntimeError('unable to parse URI: %s' % uri)

    def confirm(msg):
        if args.noconfirm:
            return True
        return raw_input(msg).lower().startswith('y')

    def abort():
        sys.exit('aborted')

    uri = db.engine.url

    if 'sqlite' not in db.engine.driver:
        raise_unable_to_parse(uri)

    dbargs = db.engine.url.translate_connect_args()
    path = os.path.abspath(dbargs['database'])

    if os.path.exists(path):
        if confirm('Remove database file "%s"? ' % path):
            os.remove(path)
        else:
            abort()
    else:
        if not confirm('Create database file "%s"? ' % os.path.abspath(path)):
            abort()

    db.engine.echo = args.echo
    Base.metadata.create_all(bind=db.engine)
    init_models(db.session)
    if args.test_models:
        init_test_models(db.session)

def dumpschema(args):
    """
    Show the database schema produced by the ORM metadata.
    """
    from library import db
    from sqlalchemy.schema import CreateTable
    for class_ in (Staff, PasswordReset, ReadingList, PatronContact):
        print CreateTable(class_.__table__).compile(db.engine)

def main():
    """
    ORM related command line utility.
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    subparsers = parser.add_subparsers()

    subparser = subparsers.add_parser('createdb', help=createdb.__doc__)
    subparser.add_argument('--noconfirm', action='store_true', help='do not ask for confirmation')
    subparser.add_argument('--echo', action='store_true', help='echo SQL')
    subparser.add_argument('--test-models', action="store_true", help="Insert test data.")
    subparser.set_defaults(func=createdb)

    subparser = subparsers.add_parser('dumpschema', help=dumpschema.__doc__)
    subparser.set_defaults(func=dumpschema)

    args = parser.parse_args()
    func = args.func
    delattr(args, 'func')
    func(args)

if __name__ == '__main__':
    main()
