import argparse

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library import app, db

def migrate():
    """
    Add columns 'location', 'org', and 'mult' to patroncontact table.
    """
    with app.app_context():
        conn = db.session.connection()
        with conn.begin() as transaction:
            conn.execute('ALTER TABLE patroncontact ADD COLUMN location TEXT')
            conn.execute('ALTER TABLE patroncontact ADD COLUMN org TEXT')
            conn.execute('ALTER TABLE patroncontact ADD COLUMN mult BOOLEAN CHECK (mult IN (0, 1))')

def main():
    parser = argparse.ArgumentParser(description=migrate.__doc__)
    parser.add_argument('--echo', action='store_true', help='Echo SQL commands.')
    args = parser.parse_args()

    if args.echo:
        db.engine.echo = True

    migrate()

if __name__ == '__main__':
    main()
