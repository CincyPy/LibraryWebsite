#!/bin/bash
gunicorn -w 2 -b 0.0.0.0:5000 --access-logfile=bookus-access.log --error-logfile=bookus-error.log --log-level=info library:app
