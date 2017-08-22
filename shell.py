import sqlalchemy as sqla
from sqlalchemy import inspect

from models import *
from library import *

app.app_context().push()

context = locals()

import argparse
parser = argparse.ArgumentParser(description='Interactive shell preloaded with interesting objects of the app.')
args = parser.parse_args()

from config import sitename_from_readme

appname = sitename_from_readme()
if appname is None:
    appname = 'App'

import code
code.interact(local=context, banner='%s interactive shell.' % appname)
