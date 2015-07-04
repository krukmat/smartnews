__author__ = 'matiasleandrokruk'
from djcelery.app import app

@app.task
def task():
    return True