__author__ = 'matiasleandrokruk'
from stop_words import get_stop_words
from pattern.es import parse, split
from collections import defaultdict


def filter_documents(documents):
    documents_filtered = []

    for document in documents:
        document = document.replace(',', ' , ')
        document = document.replace(';', ' ; ')
        document = document.replace('.', ' . ')
        document = document.replace(':', ' : ')
        document = document.replace('"', ' " ')
        document = document.replace("'", " ' ")
        documents_filtered.append(document)

    texts = [get_keywords(document) for document in documents_filtered if document]
    frequency = defaultdict(int)
    for text in texts:
        for token in text:
            frequency[token] += 1
    texts = [[token for token in text if frequency[token] > 4]
             for text in texts]
    words = []
    for sentence in texts:
        for word in sentence:
            words.append(word)
    words = list(set(words))
    return words

# TODO: Test, check, ...
def get_keywords(sentence):
    # if settings.NLTK_DATA_PATH not in nltk.data.path:
    #    nltk.data.path.append(settings.NLTK_DATA_PATH)
    structure = parse(sentence).split()
    # Return only:
    # NN, NNS, NNP, NNPS, FW, JJ, JJR, JJS
    stop_words = get_stop_words('spanish')
    words = []
    for sentence in structure:
        for token in sentence:
            if token[0] not in stop_words and token[1] in [u'NN', u'NNS', u'NNP', u'NNPS', u'FW', u'JJ', u'JJR', u'JJS']:
                words.append(token[0])
    return words