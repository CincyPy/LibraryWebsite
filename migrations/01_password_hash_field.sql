
/* Issue #57.
   https://github.com/CincyPy/LibraryWebsite/issues/57

   Change the password field of the staff table from character to binary for
   use with password hashing. */

-- `sqlite3 -init migrations/01_password_hash_field.sql library.db`

BEGIN;
    ALTER TABLE staff RENAME TO old_staff;

    -- old_staff.password VARCHAR -> staff.password VARBINARY. It's really just
    -- BLOB but this is consistent with SQLAlchemy-Utils.

    CREATE TABLE staff (
        username VARCHAR NOT NULL,
        password VARBINARY, 
        f_name VARCHAR,
        l_name VARCHAR,
        phonenumber VARCHAR,
        emailaddress VARCHAR,
        bio TEXT,
        email BOOLEAN,
        phone BOOLEAN,
        chat BOOLEAN,
        irl BOOLEAN,
        interests TEXT,
        PRIMARY KEY (username),
        CHECK (email IN (0, 1)),
        CHECK (phone IN (0, 1)),
        CHECK (chat IN (0, 1)),
        CHECK (irl IN (0, 1))
    );

    INSERT INTO staff(username, password, f_name, l_name, phonenumber,
                      emailaddress, bio, email, phone, chat, irl, interests)
    SELECT username, password, f_name, l_name, phonenumber, emailaddress, bio,
           email, phone, chat, irl, interests
      FROM old_staff;

    DROP TABLE old_staff;
COMMIT;
