import re
import argparse
from sqlalchemy.sql import text

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library import app, db
from models import PasswordReset

def create_passwordreset():
    """
    Create the passwordreset table in the database.
    """
    #commented out because this is done in models.py
    #with app.app_context():
    #    conn = db.session.connection()
    #    table = PasswordReset.metadata.tables['passwordreset']
    #    table.create(bind=db.engine)
    pass

def main():
    argparser = argparse.ArgumentParser(description=create_passwordreset.__doc__)
    argparser.add_argument('--echo', action='store_true', help='Echo SQL commands.')
    args = argparser.parse_args()

    if not any((app, db, PasswordReset)):
        argparser.exit(message='Import error, run as:\n$ python -m migration.01_create_passwordreset\n')

    if args.echo:
        db.engine.echo = True

    create_passwordreset()

if __name__ == '__main__':
    main()
