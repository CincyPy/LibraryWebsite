import sqlite3

# create a new database if the database doesn't already exist
with sqlite3.connect("library.db") as connection:
    c = connection.cursor()
    c.execute("""CREATE TABLE staff (f_name TEXT, l_name TEXT, phone INT) """)
