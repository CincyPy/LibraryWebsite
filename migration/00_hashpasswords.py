import re
import argparse
from sqlalchemy.sql import text

try:
    from passwordtype import hashpassword
    from library import app, db
    from models import Staff
except ImportError:
    hashpassword, app, db, Staff = None, None, None, None

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

            # Have to sneak around the Staff class to get at the literal database value.
            conn.execute(text('update staff set password = :hashed'),
                         hashed=hashpassword(plaintext))

        db.session.commit()

def main():
    argparser = argparse.ArgumentParser(description=update_passwords.__doc__)
    argparser.parse_args()

    if not any((hashpassword, app, db, Staff)):
        argparser.exit(message='Import error, run as:\n$ python -m migration.00_hashpasswords\n')

    update_passwords()

if __name__ == '__main__':
    main()