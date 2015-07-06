import uuid
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns
from cassandra.cqlengine.management import sync_table
from django.db import connections
from datetime import datetime
from cassandra.cqlengine import connection
from cassandra.cqlengine.connection import (
    cluster as cql_cluster, session as cql_session)
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import NoHostAvailable


class SiteNewsScrapedData(Model):
        created_at = columns.DateTime(default=datetime.now, index=True)
        id = columns.UUID(primary_key=True, default=uuid.uuid4)
        page = columns.Text(required=True, index=True)
        content = columns.Text()

        @classmethod
        def sync(cls):
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
                sync_table(cls)
            except NoHostAvailable:
                pass

