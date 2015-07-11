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
from django.conf import settings

from pattern.es import parse, split


class SiteNewsScrapedData(Model):
        created_at = columns.DateTime(default=datetime.now, index=True)
        id = columns.UUID(primary_key=True, default=uuid.uuid4)
        page = columns.Text(required=True, index=True)
        content = columns.Text()
        map_link = columns.Map(columns.Text, columns.Text)

        def tokens(self):
            # Add spaces between puntuation signals
            document = self.content.split('.')
            document_filtered = []
            for sentence in document:
                sentence_filtered = sentence.replace(',', ' , ')
                sentence_filtered = sentence_filtered.replace(';', ' ; ')
                sentence_filtered = sentence_filtered.replace('.', ' . ')
                sentence_filtered = sentence_filtered.replace(':', ' : ')
                sentence_filtered = sentence_filtered.replace('"', ' " ')
                sentence_filtered = sentence_filtered.replace("'", " ' ")
                document_filtered.append(sentence_filtered)

            # Extract nouns, adjectives
            new_document = []
            for sentence in document_filtered:
                new_sentence = []
                structure = parse(sentence).split()
                if structure:
                    words = structure[0]
                    for token in words:
                        if token[0] not in settings.STOP_WORDS and \
                            token[1] in [u'NN', u'NNS', u'NNP',
                                        u'NNPS', u'FW', u'JJ', u'JJR', u'JJS']:
                            new_sentence.append(token[0])
                    if new_sentence:
                        new_document.append(new_sentence)
            # Remove empty lines and duplicate words from sentence
            texts = [list(set(sentence)) for sentence in new_document if sentence]
            # Reduce the matrix dimension to 2 x 2
            return texts

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

