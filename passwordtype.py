import bcrypt
from sqlalchemy import types

def hashpassword(password):
    return bcrypt.hashpw(password, bcrypt.gensalt())

def checkpassword(password, hashed):
    return bcrypt.hashpw(password, hashed) == hashed

class Password(object):

    def __init__(self, value):
        self.hashed = value

    def __eq__(self, password):
        print '__eq__'
        return checkpassword(password, self.hashed)


class PasswordType(types.TypeDecorator):

    impl = types.VARCHAR
    python_type = Password

    def process_bind_param(self, value, dialect):
        if isinstance(value, Password):
            return value.hashed

            value = Password(value.encode('utf-8'))

        if isinstance(value, (str, unicode)):
            return hashpassword(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return Password(value)
