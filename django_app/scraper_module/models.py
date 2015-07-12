import uuid
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns
from cassandra.cqlengine.management import sync_table
from django.db import connections
from datetime import datetime
from cassandra.cqlengine import connection
from cassandra.cqlengine.connection import (
    cluster as cql_cluster, session as cql_session, execute)
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import NoHostAvailable
from django.conf import settings

from pattern.es import parse, split
from utils import contains, cleanup


class SyncClass(object):
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


class TopicGroups(Model, SyncClass):
    created_at = columns.DateTime(default=datetime.now, index=True)
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    tags = columns.List(columns.Text, index=True)
    links = columns.List(columns.Text, index=True)
    relevance = columns.Integer(default=0, index=True)


    @classmethod
    def all_tags(cls, tags):
        cls.sync()
        for tag in tags:
            result = execute("SELECT count(*) FROM smartnews_dev.topic_groups WHERE tags CONTAINS '%s'" % (
                tag.encode('utf-8'),))
            if result[0]['count'] == 0:
                return False
        return True


class SiteNewsScrapedData(Model, SyncClass):
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
            # TODO: Reduce the matrix dimension to 2 x 2
            return texts

        @classmethod
        def find_sequence(cls, tokens):
            # search for the site object which contains all sequence of tokens
            sites = cls.objects.all()
            for site in sites:
                map = site.map_link
                for key, link in map.iteritems():
                    key = cleanup(key) # remving all not necessary chars
                    if contains(tokens, key.split()):
                        return link
            return None


