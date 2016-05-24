import re
import argparse
from sqlalchemy.sql import text

try:
    from library import app, db
    from models import PasswordReset
except ImportError:
    app, db, PasswordReset = None, None, None

def create_passwordreset():
    """
    Create the passwordreset table in the database.
    """
    with app.app_context():
        conn = db.session.connection()
        table = PasswordReset.metadata.tables['passwordreset']
        table.create(bind=db.engine)

def main():
    argparser = argparse.ArgumentParser(description=create_passwordreset.__doc__)
    argparser.parse_args()

    if not any((app, db, PasswordReset)):
        argparser.exit(message='Import error, run as:\n$ python -m migration.01_create_passwordreset\n')

    create_passwordreset()

if __name__ == '__main__':
    main()
