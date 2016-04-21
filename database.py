from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker
from config import config

from models import Base

# Enable Foreign Key Support in sqlite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class Database(object):
    """
    An extremely simplified version of Flask-SQLAlchemy
    """

    def __init__(self, app=None):
        self._session = None
        self.engine = None
        self.app = None

        if app is not None:
            self.init_app(app)

    @property
    def session(self):
        # either instantiate class with app or init_app before accessing the session property
        if self._session is not None:
            return self._session
        return self.create_session()

    def create_session(self):
        uri = self.app.config['SQLALCHEMY_DATABASE_URI']
        self.engine = engine = create_engine(uri, convert_unicode=True)
        maker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self._session = scoped_session(maker)
        return self._session

    def init_app(self, app):
        self.app = app
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite://')

        Base.query = self.session.query_property()

        @app.teardown_appcontext
        def shutdown_session(response_or_exc):
            if app.config.get('SQLALCHEMY_COMMIT_ON_TEARDOWN'):
                if response_or_exc is None:
                    self.session.commit()
            self.session.remove()
            return response_or_exc


def init_db():
    import models
    Base.metadata.create_all(bind=engine)
