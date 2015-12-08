import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Staff(db.Model):

    __tablename__ = 'staff'

    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.String)
    f_name = db.Column(db.String)
    l_name = db.Column(db.String)
    phone = db.Column(db.Integer)


class Profile(db.Model):

    __tablename__ = 'profile'

    username_id = db.Column(db.String, db.ForeignKey('staff.username'),
                            primary_key=True)
    username = db.relationship('Staff', backref=db.backref('profile', uselist=False))
    bio = db.Column(db.Text)


class ReadingList(db.Model):

    __tablename__ = 'readinglist'

    RLID = db.Column(db.Integer, primary_key=True)
    recdate = db.Column(db.Date)

    username_id = db.Column(db.String, db.ForeignKey('staff.username'))
    username = db.relationship('Staff', backref='readinglist')

    book = db.Column(db.Text)
    author = db.Column(db.Text)
    comment = db.Column(db.Text)
    url = db.Column(db.Text)
    sticky = db.Column(db.Boolean, default=False)


def init_db(app):
    with app.app_context():
        db.create_all()

        rl1 = ReadingList(recdate=datetime.date(2015,10,1),
                          book='ABCs',
                          author='Dr. Suess',
                          comment='best seller',
                          url='http://www.seussville.com/books/book_detail.php?isbn=9780394800301')
        db.session.add(rl1)
        admin = Staff(username='admin', password='admin', f_name='Admin',
                      l_name='User', phone=1111111111)
        admin.readinglist = [rl1]
        db.session.add(admin)

        fred = Staff(username='fred', password='fred', f_name='Fred', l_name='Fredderson', phone=2222222222)
        rl2 = ReadingList(recdate=datetime.date(2015,10,2), 
                          book='Night Before Christmas',
                          author='Santa',
                          comment='find holday fun',
                          url='https://www.overdrive.com/media/1577310/the-night-before-christmas')
        fred.readinglist = [rl2]
        db.session.add(fred)

        db.session.add(Profile(username=admin, bio='Admin bio'))
        db.session.add(Profile(username=fred, bio='Fred\'s bio'))

        db.session.commit()
