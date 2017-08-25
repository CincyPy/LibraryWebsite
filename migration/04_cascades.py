import argparse

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library import app, db

def migrate():
    """
    Add database-level cascading deletes on foreign keys.
    """
    with app.app_context():
        conn = db.session.connection()
        with conn.begin() as transaction:
            # add ON DELETE to table `passwordreset`
            conn.execute('CREATE TEMP TABLE passwordreset_backup('
                         'secret VARCHAR NOT NULL,created DATETIME,username VARCHAR);')
            conn.execute('INSERT INTO passwordreset_backup'
                         ' SELECT secret, created, username FROM passwordreset;')
            conn.execute('DROP TABLE passwordreset;')
            conn.execute('CREATE TABLE passwordreset ('
                         'secret VARCHAR NOT NULL,created DATETIME,username VARCHAR,'
                         'PRIMARY KEY (secret),'
                         'FOREIGN KEY(username) REFERENCES staff (username) ON DELETE CASCADE);')
            conn.execute('INSERT INTO passwordreset'
                         ' SELECT secret, created, username FROM passwordreset_backup;')
            conn.execute('DROP TABLE passwordreset_backup;')
            # add ON DELETE to table `readinglist`
            conn.execute('CREATE TEMP TABLE readinglist_backup('
                         '"RLID" INTEGER NOT NULL,"ISBN" TEXT,recdate DATE,'
                         'username VARCHAR,book TEXT,author TEXT,comment TEXT,'
                         'sticky BOOLEAN,category TEXT);')
            conn.execute('INSERT INTO readinglist_backup'
                         ' SELECT "RLID", "ISBN", recdate, username, book'
                         ' ,author, comment, sticky, category FROM readinglist;')
            conn.execute('DROP TABLE readinglist;')
            conn.execute('CREATE TABLE readinglist('
                         '"RLID" INTEGER NOT NULL,"ISBN" TEXT,recdate DATE,'
                         'username VARCHAR,book TEXT,author TEXT,comment TEXT, '
                         'sticky BOOLEAN,category TEXT,'
                         'PRIMARY KEY ("RLID"), '
                         'FOREIGN KEY(username) REFERENCES staff (username) ON DELETE CASCADE, '
                         'CHECK (sticky IN (0, 1)));')
            conn.execute('INSERT INTO readinglist'
                         ' SELECT "RLID", "ISBN", recdate, username, book,'
                         ' author, comment, sticky, category FROM readinglist_backup;')
            conn.execute('DROP TABLE readinglist_backup;')
            # add ON DELETE to table `patroncontact`
            conn.execute('CREATE TEMP TABLE patroncontact_backup('
                         '"PCID" INTEGER NOT NULL,reqdate TEXT,username VARCHAR,'
                         'name TEXT,email TEXT,contact TEXT,phone TEXT,'
                         'times TEXT,likes TEXT,dislikes TEXT,comment TEXT,'
                         'audience TEXT,format_pref TEXT,chat TEXT,handle TEXT,'
                         'location TEXT,org TEXT,mult BOOLEAN,status TEXT);')
            conn.execute('INSERT INTO patroncontact_backup'
                         ' SELECT "PCID", reqdate, username, name, email, contact, phone'
                         ', times, likes, dislikes, comment, audience, format_pref, chat'
                         ', handle, location, org, mult, status FROM patroncontact;')
            conn.execute('DROP TABLE patroncontact;')
            conn.execute('CREATE TABLE patroncontact ('
                         '"PCID" INTEGER NOT NULL, reqdate TEXT, username VARCHAR, '
                         'name TEXT, email TEXT, contact TEXT, phone TEXT, '
                         'times TEXT, likes TEXT, dislikes TEXT, comment TEXT, '
                         'audience TEXT, format_pref TEXT, chat TEXT, handle TEXT, '
                         'location TEXT, org TEXT, mult BOOLEAN, status TEXT, '
                         'PRIMARY KEY ("PCID"), '
                         'FOREIGN KEY(username) REFERENCES staff (username) ON DELETE CASCADE, '
                         'CHECK (mult IN (0, 1)));')
            conn.execute('INSERT INTO patroncontact'
                         ' SELECT "PCID", reqdate, username, name, email, contact, phone'
                         ' ,times, likes, dislikes, comment, audience, format_pref, chat'
                         ' ,handle, location, org, mult, status'
                         ' FROM patroncontact_backup;')
            conn.execute('DROP TABLE patroncontact_backup;')


def main():
    parser = argparse.ArgumentParser(description=migrate.__doc__)
    parser.add_argument('--echo', action='store_true', help='Echo SQL commands.')
    args = parser.parse_args()

    if args.echo:
        db.engine.echo = True

    migrate()

if __name__ == '__main__':
    main()
