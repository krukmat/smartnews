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
    for topic in ScrapedTopicGroups.objects.all():
        for topic2 in ScrapedTopicGroups.objects.all():
            if topic != topic2 and len(topic.tags) == len(topic2.tags) \
                    and topic.links == topic2.links:
                # Tags Fusion
                topic.tags.extend(topic2.tags)
                topic.links = topic2.links
                topic.save()
                # Remove one of the topics
                topic2.delete()


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
    tokens = []
    for document in documents:
        similar_items_news = model.nearest_neighbors(document)
        for similarity, sim_document in similar_items_news:
            if sim_document.id not in documents_analyzed:
                tokens.extend([word for word, _ in sim_document.words.iteritems()])
                documents_analyzed.append(sim_document.id)
        # Added is there some document similar
        if document.id not in documents_analyzed:
            tokens.extend([word for word, _ in document.words.iteritems()])
            documents_analyzed.append(document.id)
            # document_cluster.append(list(set(tokens)))
    # complete_text = ".".join([" ".join(document) for document in document_cluster])
    tokens = list(set(tokens))
    for token in tokens:
        links = SiteNewsScrapedData.find_coincidences([token])
        # Filtrar solamente si tiene mas de 3 links
        if len(links) > 3:
            if not ScrapedTopicGroups.contain_tag(token):
                ScrapedTopicGroups.create(tags=[token], links=links, relevance=len(links),
                                   day=today.day, month=today.month, year=today.year)
    reduce_topics()
    return True