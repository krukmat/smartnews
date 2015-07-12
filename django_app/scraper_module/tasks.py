from celery.canvas import group
from djcelery.app import app
from models import SiteNewsScrapedData, TopicGroups
from news_crawler.news_crawler.utils import run_spider, spiders
from gensim import corpora, models, similarities

@app.task
def scrape_site(spider):
    run_spider(spider)
    return True

@app.task
def scrape_news():
    # TODO: Pasar de alguna manera el transaction_id al spider
    scraped_news = group(scrape_site.s(spider) for spider in spiders)
    (scraped_news | compute_nlp.s())()
    return True

@app.task
def compute_nlp(results):
    SiteNewsScrapedData.sync()
    sites = SiteNewsScrapedData.objects.all()
    documents = [site.tokens() for site in sites]
    # reduce the matrix level
    documents = [sentence for document in documents for sentence in document]
    # Corpora
    dictionary = corpora.Dictionary(documents)
    corpus = [dictionary.doc2bow(text) for text in documents]
    # Apply LSI
    # TODO: Modelo custom (User? Config? BDA?)
    for corp in corpus:
        lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=5)
        index = similarities.MatrixSimilarity(lsi[corpus])
        vec_lsi = lsi[corp]
        sims = index[vec_lsi]
        # Descending ranking with the similar tokens
        sims = sorted(enumerate(sims), key=lambda item: -item[1])
        current_sequence = [dictionary[key] for key, ocurrence in corp]
        # return all sentences and corpus which score > 0.95
        similar_links = []
        tokens = []
        for sentence, similarity in sims:
            if similarity > 0.95:
                corp_sim = corpus[sentence]
                similar_sentence = [dictionary[key] for key, ocurrence in corp_sim]
                similar_news = SiteNewsScrapedData.find_sequence(similar_sentence)
                if similar_news:
                    tokens.extend(similar_sentence)
                    similar_links.append(similar_news)
                #else:
                #    raise IndexError('No news found with %s' % (similar_sentence))
            else:
                break
        # return all similar links in TopicGroup
        similar_news = SiteNewsScrapedData.find_sequence(current_sequence)
        if similar_news:
            similar_links.append(similar_news)
            tokens.extend(current_sequence)
        # TODO: Count the number of similarities
        # TODO: count the relevance of topic
        try:
            TopicGroups.sync()
        except:
            pass
        tokens = list(set(tokens))
        # Save topic group
        if tokens and similar_links:
            TopicGroups.create(tags=tokens, links=similar_links)
            # Remove all corpus linked
            for sentence, similarity in sims:
                try:
                    corp_sim = corpus[sentence]
                    corpus.remove(corp_sim)
                except:
                    pass

    # Remove all SiteNewsScrapedData objects
    for site in sites:
        site.delete()

    return True