from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Staff(db.Model):

    __tablename__ = 'staffs'

    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.String)
    f_name = db.Column(db.String)
    l_name = db.Column(db.String)
    phone = db.Column(db.Integer)


class Profile(db.Model):

    __tablename__ = 'profiles'

    username = db.Column(db.String, db.ForeignKey('staffs.username'), primary_key=True)
    bio = db.Column(db.Text)
