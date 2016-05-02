from sqlalchemy import inspect

from models import *
from library import app, db

app.app_context().push()

elmo = Staff.query.get('elmo')
print elmo
print elmo.password == 'elmo'
