__author__ = 'matiasleandrokruk'


def contains(small, big):
    for element in small:
        if element not in big:
            return False
    return True

def cleanup(text):
    text = text.replace(',', ' ')
    text = text.replace(';', ' ')
    text = text.replace('.', ' ')
    text = text.replace(':', ' ')
    text = text.replace('"', ' ')
    text = text.replace("'", ' ')
    return text