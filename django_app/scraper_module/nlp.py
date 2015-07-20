from collections import defaultdict

__author__ = 'matiasleandrokruk'
from gensim import corpora, models, similarities
from models import *
from pattern.vector import Document, Model as Model_Comp
from pattern.es import parsetree
from django.conf import settings
from datetime import datetime


def cleanup_topic(day, month, year):
    ScrapedTopicGroups.sync()
    SiteNewsScrapedData.sync()
    for topic in ScrapedTopicGroups.objects.allow_filtering().filter(year=year).filter(month=month).filter(day=day):
        topic.delete()


def reduce_topics():
    # Check links are similar to any other topic. If it so => add the tag to that
    # Do the links similarity checking
    # TODO: Reduce based on common words.
    pass

def compute_topics():
    # Based on similarity
    # Based on words
    today = datetime.now()
    cleanup_topic(today.day, today.month, today.year)
    ScrapedTopicGroups.sync()
    sites = SiteNewsScrapedData.objects.all()
    documents = []
    for site in sites:
        for sentence in site.content.split('.'):
            if sentence:
                tree = parsetree(sentence, lemmata=True)
                if len(tree) > 0:
                    documents.append(tree[0])

    documents = [[w.lemma for w in document if
                  w.tag.startswith((u'NN', u'NNS', u'NNP', u'NNPS')) and w.lemma not in settings.STOP_WORDS] for
                 document in documents]

    documents = [Document(" ".join(document) + '.') for document in documents if len(document) > 1]
    model = Model_Comp(documents=documents)

    # format: (distribution, Document)
    documents_analyzed = []
    for document in documents:
        tokens = []
        similar_items_news = model.nearest_neighbors(document)
        for similarity, sim_document in similar_items_news:
            if similarity > 0.95 and sim_document.id not in documents_analyzed:
                tokens.extend([word for word, _ in sim_document.words.iteritems()])
                documents_analyzed.append(sim_document.id)
        # Added is there some document similar
        if document.id not in documents_analyzed:
            tokens.extend([word for word, _ in document.words.iteritems()])
            documents_analyzed.append(document.id)
        # filter the most relevant words (based on count)
        counter = defaultdict(int)
        for token in tokens:
            counter[token] += 1
        # Order counter desc
        tokens_org = sorted(counter.items(), key=lambda element: element[1], reverse=True)
        tokens = [token for token, count in tokens_org[:3]]
        if tokens and len(tokens) > 0:
            links = SiteNewsScrapedData.find_coincidences(tokens)
            # Filtrar solamente si tiene mas de 3 links
            if len(links) > 3:
                ScrapedTopicGroups.create(tags=tokens, links=links, relevance=len(links),
                                        day=today.day, month=today.month, year=today.year)
    #reduce_topics()
    return True