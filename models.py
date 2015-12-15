import datetime

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship

from database import Base

class Staff(Base):
    __tablename__ = 'staff'

    username = Column(String, primary_key=True)
    password = Column(String)
    f_name = Column(String)
    l_name = Column(String)
    phone = Column(Integer)


class Profile(Base):
    __tablename__ = 'profile'

    username = Column(String, ForeignKey('staff.username'),
                            primary_key=True)
    staff = relationship('Staff', backref=backref('profile', uselist=False))
    bio = Column(Text)


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


def init_models():
    from database import db_session

    rl1 = ReadingList(recdate=datetime.date(2015,10,1),
                      book='ABCs',
                      author='Dr. Suess',
                      comment='best seller',
                      url='http://www.seussville.com/books/book_detail.php?isbn=9780394800301')
    db_session.add(rl1)
    admin = Staff(username='admin', password='admin', f_name='Admin',
                  l_name='User', phone=1111111111)
    admin.readinglist.append(rl1)
    db_session.add(admin)

    fred = Staff(username='fred', password='fred', f_name='Fred', l_name='Fredderson', phone=2222222222)
    rl2 = ReadingList(recdate=datetime.date(2015,10,2), 
                      book='Night Before Christmas',
                      author='Santa',
                      comment='find holday fun',
                      url='https://www.overdrive.com/media/1577310/the-night-before-christmas')
    fred.readinglist.append(rl2)
    db_session.add(fred)

    db_session.add(Profile(staff=admin, bio='Admin bio'))
    db_session.add(Profile(staff=fred, bio='Fred\'s bio'))

    db_session.commit()
