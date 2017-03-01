"""
This script is how you can create an interactive shell within the app
context.  It allows you to work on the db using SQLAlchemy commands
instead of raw SQL.  To invoke, use 'python -i shell.py'
"""
from sqlalchemy import inspect

from models import *
from library import *

app.app_context().push()
