import argparse
import datetime
import os
import sys

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Staff(Base):
    __tablename__ = 'staff'

    username = Column(String, primary_key=True)
    password = Column(String)
    f_name = Column(String)
    l_name = Column(String)
    phonenumber = Column(String)
    emailaddress = Column(String)

    bio = Column(Text, default='')
    email = Column(Boolean, default=False)
    phone = Column(Boolean, default=True)
    chat = Column(Boolean, default=False)
    irl = Column(Boolean, default=True)

    interests = Column(Text, default='')

    patron_contacts = relationship('PatronContact', backref=backref('staff', uselist=False))

    def __getitem__(self, attr):
        return getattr(self, attr)

    @property
    def category_list(self):
        return set([item.category for item in self.readinglist])

    def profile_path(self):
        if os.path.isfile('static/uploads/' + self.username + '.jpg'):
            pic_file_name = 'uploads/'+ self.username + '.jpg'
        else:
            pic_file_name = 'uploads/anon.jpg'
        return pic_file_name


class ReadingList(Base):
    __tablename__ = 'readinglist'

    RLID = Column(Integer, primary_key=True)
    ISBN = Column(Text)
    recdate = Column(Date)

    username = Column(String, ForeignKey('staff.username'))
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
    contact = Column(Text)
    phone = Column(Text)
    times = Column(Text)
    likes = Column(Text)
    dislikes = Column(Text)
    comment = Column(Text)
    audience = Column(Text)
    format_pref = Column(Text)
    chat = Column(Text)
    handle = Column(Text)
    status = Column(Text)

    def __getitem__(self, attr):
        return getattr(self, attr)


def init_models(session):
    admin = Staff(username='admin', password='admin', f_name='Admin', emailaddress='KentonCountyLibrary@gmail.com',
                  l_name='User', phonenumber=1111111111, bio='Admin bio')
    session.add(admin)

    fred = Staff(username='fred', password='fred', f_name='Fred', emailaddress='KentonCountyLibrary@gmail.com',
                 l_name='Fredderson', phonenumber=2222222222, bio='I am Fred\'s incomplete bio',
                 patron_contacts=[
                     PatronContact(reqdate='2016-01-07',
                            status='open',
                            name='Joe Johnson',
                            email='jjohanson@bigpimpn.net',
                            contact='phone',
                            phone='5555555555',
                            times='M-Th 12-2 pm'),
                 ])
    rl1 = ReadingList(recdate=datetime.date(2015,10,1),
                      ISBN='9780394800301',
                      book='ABCs',
                      author='Dr. Suess',
                      comment='best seller',
                      category='Mystery')
    rl2 = ReadingList(recdate=datetime.date(2015,10,2),
                      ISBN=' 9781402750656',
                      book='Night Before Christmas',
                      author='Santa',
                      comment='find holday fun',
                      category='Sci-fi')
    fred.readinglist.append(rl1)
    fred.readinglist.append(rl2)
    session.add(fred)

    loremipsum = '''Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'''

    session.add(Staff(username='ernie',
                         password='ernie',
                         f_name='Ernie',
                         l_name='Ernieston',
                         phonenumber=3333333333,
                         emailaddress='KentonCountyLibrary@gmail.com',
                         bio=loremipsum))
    session.add(Staff(username='bert',
                         password='bert',
                         f_name='Bert',
                         l_name='Burterson',
                         phonenumber=4444444444,
                         emailaddress='KentonCountyLibrary@gmail.com',
                         bio=loremipsum))
    session.add(Staff(username='bigbird',
                         password='bigbird',
                         f_name='Big',
                         l_name='Bird',
                         phonenumber=5555555555,
                         emailaddress='KentonCountyLibrary@gmail.com',
                         bio=loremipsum))
    session.add(Staff(username='oscar',
                         password='oscar',
                         f_name='Oscar',
                         l_name='Thegrouch',
                         phonenumber=6666666666,
                         emailaddress='KentonCountyLibrary@gmail.com',
                         bio=loremipsum))
    session.add(Staff(username='elmo',
                         password='elmo',
                         f_name='Elmo',
                         l_name='Elmostein',
                         phonenumber=7777777777,
                         emailaddress='KentonCountyLibrary@gmail.com',
                         bio=loremipsum))

    session.commit()
    session.query(Staff).get('elmo').readinglist = [
        ReadingList(
            recdate=datetime.date(2015,12,21),
            ISBN='9789380028293',
            book='The Invinsible Man',
            author='H. G. Wells',
            comment='my fav',
            category='History'),
        ReadingList(
            recdate=datetime.date(2015,12,21),
            ISBN='9780393972832',
            book='Moby Dick',
            author='Herman Melville',
            comment='a whale of a tale',
            category='Music')
    ]

    session.commit()

def ArgParser():
    parser = argparse.ArgumentParser(description=main.__doc__)
    _a = parser.add_argument
    _a('--echo', action='store_true', help='echo SQL')
    return parser

def main():
    """
    If a sqlite file can be found in the database URI of the app, prompt to
    remove it, if found on the filesystem, and then create it with the database
    structure and initial data.
    """
    from library import app, db

    parser = ArgParser()
    cmdargs = parser.parse_args()

    def raise_unable_to_parse(uri):
        raise RuntimeError('unable to parse URI: %s' % uri)

    def confirm(msg):
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

    db.engine.echo = cmdargs.echo
    Base.metadata.create_all(bind=db.engine)
    init_models(db.session)

if __name__ == '__main__':
    main()
