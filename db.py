import sqlite3

# create a new database if the database doesn't already exist
with sqlite3.connect("library.db") as connection:
    c = connection.cursor()
    try:
        c.execute("""CREATE TABLE staff (username TEXT, password TEXT, f_name TEXT, l_name TEXT, phone INT) """)
        c.execute("INSERT INTO staff (username,password,f_name,l_name,phone) VALUES ('admin', 'admin', 'Admin', 'User', 1111111111);")
    except sqlite3.OperationalError as e:
        print "Failure: " + str(e)
        
        
