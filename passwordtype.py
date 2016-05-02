import sys
import bcrypt
from sqlalchemy import types

class Password(object):

    def __init__(self, password):
        self.hashed = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

    def verify(self, password):
        return bcrypt.hashpw(password.encode('utf8'), self.hashed) == self.hashed

    def __eq__(self, password):
        return self.verify(password)

    def __ne__(self, password):
        return not self == password


class PasswordType(types.TypeDecorator):

    impl = types.VARCHAR
    python_type = Password

    def process_bind_param(self, value, dialect):
        if isinstance(value, Password):
            return value.hashed
        elif isinstance(value, basestring):
            #XXX: this is hashing hashes because this method handles in/out.
            #     make this a Mutable class?
            return Password(value).hashed

    def process_result_value(self, value, dialect):
        if value is not None:
            return Password(value)
