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


def init_db(app):
    with app.app_context():
        db.create_all()
        db.session.add(Staff(username='admin', password='admin', f_name='Admin',
                             l_name='User', phone=1111111111))
        db.session.add(Staff(username='fred', password='fred', f_name='Fred',
                             l_name='Fredderson', phone=2222222222))

        db.session.add(Profile(username='admin', bio=''))
        db.session.add(Profile(username='fred', bio=''))

        db.session.commit()
