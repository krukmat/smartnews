__author__ = 'matiasleandrokruk'
from gensim import corpora, models, similarities
from models import *
from pattern.vector import Document, Model as Model_Comp
from pattern.es import parsetree
from django.conf import settings


def cleanup_topic():
    TopicGroups.sync()
    SiteNewsScrapedData.sync()
    sites = SiteNewsScrapedData.objects.all()
    for site in sites:
        site.delete()
    for topic in TopicGroups.objects.all():
        topic.delete()


def compute_topics():
    # Based on similarity
    # Based on words
    SiteNewsScrapedData.sync()
    TopicGroups.sync()
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
    # TODO: Duplica tokens?
    tokens = list(set(tokens))
    for token in tokens:
        links = SiteNewsScrapedData.find_coincidences([token])
        # Filtrar solamente si tiene mas de 3 links
        if len(links) > 3:
            if not TopicGroups.contain_tag(token):
                TopicGroups.create(tags=[token], links=links, relevance=len(links))
    return True