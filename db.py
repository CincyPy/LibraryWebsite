import sqlite3
import sys

# create a new database if the database doesn't already exist

def create_db(dbname):
    with sqlite3.connect(dbname) as connection:
        c = connection.cursor()
        try:
            # STAFF TABLE
            c.execute("""CREATE TABLE staff (username TEXT PRIMARY KEY, password TEXT, f_name TEXT, l_name TEXT, phone INT) """)
            c.execute("INSERT INTO staff (username,password,f_name,l_name,phone) VALUES ('admin', 'admin', 'Admin', 'User', 1111111111);")
            c.execute("INSERT INTO staff (username,password,f_name,l_name,phone) VALUES ('fred', 'fred', 'Fred', 'Fredderson', 2222222222);")
            c.execute("INSERT INTO staff (username,password,f_name,l_name,phone) VALUES ('ernie', 'ernie', 'Ernie', 'Ernieston', 3333333333);")
            c.execute("INSERT INTO staff (username,password,f_name,l_name,phone) VALUES ('bert', 'bert', 'Bert', 'Burterson', 4444444444);")
            c.execute("INSERT INTO staff (username,password,f_name,l_name,phone) VALUES ('bigbird', 'bigbird', 'Big', 'Bird', 5555555555);")
            c.execute("INSERT INTO staff (username,password,f_name,l_name,phone) VALUES ('oscar', 'oscar', 'Oscar', 'Thegrouch', 6666666666);")
            c.execute("INSERT INTO staff (username,password,f_name,l_name,phone) VALUES ('elmo', 'elmo', 'Elmo', 'Elmostein', 7777777777);")


            # PROFILE TABLE
            c.execute("""CREATE TABLE profile (username TEXT, bio TEXT, email INTEGER DEFAULT 1, phone INTEGER DEFAULT 1,
                       chat INTEGER DEFAULT 0, irl INTEGER DEFAULT 1, FOREIGN KEY(username) REFERENCES staff(username))""")
            c.execute("""INSERT INTO profile (username) VALUES('admin')""")
            c.execute("""INSERT INTO profile (username,bio) VALUES('fred','Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.')""")
            c.execute("""INSERT INTO profile (username,bio) VALUES('ernie','Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.')""")
            c.execute("""INSERT INTO profile (username,bio) VALUES('bert','Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.')""")
            c.execute("""INSERT INTO profile (username,bio) VALUES('bigbird','Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.')""")
            c.execute("""INSERT INTO profile (username,bio) VALUES('oscar','Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.')""")
            c.execute("""INSERT INTO profile (username,bio) VALUES('grouch','Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.')""")
            c.execute("""INSERT INTO profile (username,bio) VALUES('elmo','Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.')""")

            # READINGLIST TABLE
            c.execute("""CREATE TABLE readinglist (RLID INTEGER PRIMARY KEY AUTOINCREMENT, recdate TEXT, username TEXT,
                        book TEXT, author TEXT, comment TEXT, url TEXT, sticky INTEGER DEFAULT 0, FOREIGN KEY(username) REFERENCES staff(username))""")
            c.execute("""INSERT INTO readinglist (RLID, recdate, username, book, author, comment, url)
                  VALUES (null,'2015-10-01','fred','ABCs', 'Dr. Suess','best seller','http://www.seussville.com/books/book_detail.php?isbn=9780394800301')""")
            c.execute("""INSERT INTO readinglist (RLID, recdate, username, book, author, comment, url)
                  VALUES (null,'2015-10-02','fred','Night Before Christmas', 'Santa','fine holiday fun','https://www.overdrive.com/media/1577310/the-night-before-christmas')""")
            c.execute("""INSERT INTO readinglist (RLID, recdate, username, book, author, comment, url)
                  VALUES (null,'2015-12-21','elmo','The Invisible Man', 'H. G. Wells','my fav','http://aol.com')""")
            c.execute("""INSERT INTO readinglist (RLID, recdate, username, book, author, comment, url)
                  VALUES (null,'2015-12-21','elmo','Moby Dick', 'Herman Melville','a whale of a tale','http://facebook.com')""")

            # PATRON CONTACT TABLE
            # Likes, dislikes, comment, audience, and format are only used for email contact
            # Times is used for all but email
            c.execute("""CREATE TABLE patroncontact (PCID INTEGER PRIMARY KEY AUTOINCREMENT, reqdate TEXT, username TEXT,
                        name TEXT, email TEXT, contact TEXT, phone TEXT, times TEXT, likes TEXT, dislikes TEXT, comment TEXT,
                        audience TEXT, format_pref TEXT, chat TEXT, handle TEXT, FOREIGN KEY(username) REFERENCES staff(username))""")
            c.execute("""INSERT INTO patroncontact (PCID, reqdate, username, name, email, contact, phone, times, likes, dislikes, comment, audience, format_pref, chat, handle)
                  VALUES (null,'2016-01-07','fred','Joe Johanson', 'jjohanson@bigpimpn.net','phone','5555555555','M-Th 12-2 pm',null,null,null,null,null,null,null)""")

        except sqlite3.OperationalError as e:
            print "Failure: " + str(e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: python db.py <db_filename>"
        sys.exit(1)
    else:
        dbname = sys.argv[1]

    create_db(dbname)
