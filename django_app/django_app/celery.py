from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import NoHostAvailable
from celery.signals import worker_process_init, beat_init
from cassandra.cqlengine import connection
from cassandra.cqlengine.connection import (
    cluster as cql_cluster, session as cql_session)
from django.db import connections


def cassandra_init(sender=None, signal=None):
    """ Issue reported in ADDNOW-483: Based on suggestions in
        http://stackoverflow.com/questions/24785299/python-cassandra-driver-operationtimeout-on-every-query-in-celery-task.
    """
    try:
        cassandra_host = connections['default'].settings_dict['HOST'].split(',')
        keyspace = connections['default'].settings_dict['NAME']
        user = connections['default'].settings_dict['USER']
        password = connections['default'].settings_dict['PASSWORD']
        auth_provider = PlainTextAuthProvider(username=user, password=password)

        if cql_cluster is not None:
            cql_cluster.shutdown()
        if cql_session is not None:
            cql_session.shutdown()
        connection.setup(cassandra_host, keyspace, auth_provider=auth_provider)
    except NoHostAvailable:
        pass

# Initialize worker context for both standard and periodic tasks, just in the
# case the 'default' connection is defined
# set the default Django settings module for the 'celery' program.
worker_process_init.connect(cassandra_init)
beat_init.connect(cassandra_init)



app = Celery('scraper_module')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)