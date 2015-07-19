__author__ = 'matiasleandrokruk'
from django.conf import settings

from pattern.es import parse, split


def contains_any(small, big):
    for element in small:
        if element in big:
            return True
    return False


def cleanup(text):
    text = text.replace(',', ' ')
    text = text.replace(';', ' ')
    text = text.replace('.', ' ')
    text = text.replace(':', ' ')
    text = text.replace('"', ' ')
    text = text.replace("'", ' ')

    return text


def only_nouns(sentence):
    new_sentence = []
    structure = parse(sentence).split()
    if structure:
        words = structure[0]
        for token in words:
            if token[0] not in settings.STOP_WORDS and \
                            token[1] in [u'NN', u'NNS', u'NNP',
                                         u'NNPS']:
                new_sentence.append(token[0].lower())
    return new_sentence