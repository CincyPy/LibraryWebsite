import re
import argparse
import bcrypt
from sqlalchemy.sql import text

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from passwordtype import hashpassword, encode
from library import app, db
from models import Staff

def ishashed(s):
    # Surely no one makes their password look like a bcrypt hash.

    # Assuming this is a good way to detect the hash, didn't find much info on
    # what are valid parts of a hash.

    # https://github.com/fwenzel/python-bcrypt
    # python-bcrypt says the base64 characters in bcrypt are digits,
    # upper/lower-case, dot and backslash.

    return re.match(r'\$[0-9a-z]+\$\d+\$[0-9A-Za-z.\\]+', s)

def update_passwords():
    """
    Update the plain-text passwords to bcrypt. Checks to see if already hashed,
    however admin should check if this needs to be run first.
    """
    with app.app_context():
        conn = db.session.connection()

        for staff in Staff.query.all():
            plaintext = staff.password.hashed

            # Make some attempt not to hash already hashed passwords
            if ishashed(plaintext):
                continue

            hashed = hashpassword(plaintext)

            # Have to sneak around the Staff class to get at the literal database value.
            sql = text('update staff set password = :hashed where username = :username')
            conn.execute(sql, hashed=hashed, username=staff.username)

        db.session.commit()

def main():
    argparser = argparse.ArgumentParser(description=update_passwords.__doc__)
    argparser.add_argument('--echo', action='store_true', help='Echo SQL commands.')
    args = argparser.parse_args()

    if not any((hashpassword, app, db, Staff)):
        argparser.exit(message='Import error, run as:\n$ python -m migration.00_hashpasswords\n')

    if args.echo:
        db.engine.echo = True

    update_passwords()

if __name__ == '__main__':
    main()
