import bcrypt
from sqlalchemy import types

def encode(s):
    return s.encode('utf8')

def hashpassword(password):
    return bcrypt.hashpw(encode(password), bcrypt.gensalt())

class Password(object):

    def __init__(self, hashed):
        self.hashed = hashed

    def verify(self, password):
        password = encode(password)
        hashed = encode(self.hashed)
        return bcrypt.hashpw(password, hashed) == hashed

    def __eq__(self, password):
        return self.verify(password)

    def __ne__(self, password):
        return not self == password


class PasswordType(types.TypeDecorator):

    impl = types.VARCHAR
    python_type = Password

    def process_bind_param(self, value, dialect):
        if isinstance(value, Password):
            r = value.hashed
        elif isinstance(value, basestring):
            r = hashpassword(value)
        else:
            raise RuntimeError('Unable to process bind parameter: %s.' % (value, ))
        return encode(r)

    def process_result_value(self, value, dialect):
        if value is not None:
            return Password(value)
