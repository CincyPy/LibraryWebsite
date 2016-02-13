import argparse
import datetime
import os

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship

from database import Base, SQLITE_DATABASE_PATH, engine, init_db

class Staff(Base):
    __tablename__ = 'staff'

    username = Column(String, primary_key=True)
    password = Column(String)
    f_name = Column(String)
    l_name = Column(String)
    phone = Column(Integer)
    email = Column(String)

    patron_contacts = relationship('PatronContact', backref=backref('staff', uselist=False))


class Profile(Base):
    __tablename__ = 'profile'

    username = Column(String, ForeignKey('staff.username'),
                      primary_key=True)
    staff = relationship('Staff', backref=backref('profile', uselist=False))
    bio = Column(Text)

    email = Column(Boolean, default=False)
    phone = Column(Boolean, default=True)
    chat = Column(Boolean, default=False)
    irl = Column(Boolean, default=True)

    def __getitem__(self, attr):
        return getattr(self, attr)


class ReadingList(Base):
    __tablename__ = 'readinglist'

    RLID = Column(Integer, primary_key=True)
    recdate = Column(Date)

    username = Column(String, ForeignKey('staff.username'))
    staff = relationship('Staff', backref='readinglist')

    book = Column(Text)
    author = Column(Text)
    comment = Column(Text)
    url = Column(Text)
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

    def __getitem__(self, attr):
        return getattr(self, attr)


def init_models(db_session=None):
    if db_session is None:
        from database import db_session

    admin = Staff(username='admin', password='admin', f_name='Admin',
                  l_name='User', phone=1111111111)
    db_session.add(admin)

    fred = Staff(username='fred', password='fred', f_name='Fred',
                 l_name='Fredderson', phone=2222222222,
                 patron_contacts=[
                     PatronContact(reqdate='2016-01-07',
                            name='Joe Johnson',
                            email='jjohanson@bigpimpn.net',
                            contact='phone',
                            phone='5555555555',
                            times='M-Th 12-2 pm'),
                 ])
    rl1 = ReadingList(recdate=datetime.date(2015,10,1),
                      book='ABCs',
                      author='Dr. Suess',
                      comment='best seller',
                      url='http://www.seussville.com/books/book_detail.php?isbn=9780394800301',
                      category='Mystery')
    rl2 = ReadingList(recdate=datetime.date(2015,10,2),
                      book='Night Before Christmas',
                      author='Santa',
                      comment='find holday fun',
                      url='https://www.overdrive.com/media/1577310/the-night-before-christmas',
                      category='Sci-fi')
    fred.readinglist.append(rl1)
    fred.readinglist.append(rl2)
    db_session.add(fred)

    db_session.add(Profile(staff=admin, bio='Admin bio'))
    db_session.add(Profile(staff=fred, bio='Fred\'s bio'))

    loremipsum = '''Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'''

    db_session.add(Staff(username='ernie',
                         password='ernie',
                         f_name='Ernie',
                         l_name='Ernieston',
                         phone=3333333333,
                         email='KentonCountyLibrary@gmail.com',
                         profile=Profile(bio=loremipsum)))
    db_session.add(Staff(username='bert',
                         password='bert',
                         f_name='Bert',
                         l_name='Burterson',
                         phone=4444444444,
                         email='KentonCountyLibrary@gmail.com',
                         profile=Profile(bio=loremipsum)))
    db_session.add(Staff(username='bigbird',
                         password='bigbird',
                         f_name='Big',
                         l_name='Bird',
                         phone=5555555555,
                         email='KentonCountyLibrary@gmail.com',
                         profile=Profile(bio=loremipsum)))
    db_session.add(Staff(username='oscar',
                         password='oscar',
                         f_name='Oscar',
                         l_name='Thegrouch',
                         phone=6666666666,
                         email='KentonCountyLibrary@gmail.com',
                         profile=Profile(bio=loremipsum)))
    db_session.add(Staff(username='elmo',
                         password='elmo',
                         f_name='Elmo',
                         l_name='Elmostein',
                         phone=7777777777,
                         email='KentonCountyLibrary@gmail.com',
                         profile=Profile(bio=loremipsum)))

    db_session.commit()
    db_session.query(Staff).get('elmo').readinglist = [
        ReadingList(
            recdate=datetime.date(2015,12,21),
            book='The Invinsible Man',
            author='H. G. Wells',
            comment='my fav',
            url='http://aol.com',
            category='History'),
        ReadingList(
            recdate=datetime.date(2015,12,21),
            book='Moby Dick',
            author='Herman Melville',
            comment='a whale of a tale',
            url='http://facebook.com',
            category='Music')
    ]

    db_session.commit()

def ArgParser():
    parser = argparse.ArgumentParser(
        description=('create and initialize with data a new database for the'
                     ' library web app'))
    _a = parser.add_argument
    _a('--echo', action='store_true', help='echo SQL')
    return parser

if __name__ == '__main__':
    parser = ArgParser()
    args = parser.parse_args()

    if os.path.exists(SQLITE_DATABASE_PATH):
        if raw_input('Remove "%s" ?' % SQLITE_DATABASE_PATH).lower().startswith('y'):
            os.remove(SQLITE_DATABASE_PATH)
        else:
            raise RuntimeError('"%s" exists.' % SQLITE_DATABASE_PATH)

    engine.echo = args.echo

    Base.metadata.create_all(bind=engine)
    init_models()