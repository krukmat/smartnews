from celery.canvas import group
from djcelery.app import app
from models import SiteNewsScrapedData
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
    documents = [site.tokens() for site in SiteNewsScrapedData.objects.all()]
    # reduce the matrix level
    documents = [sentence for document in documents for sentence in document]
    # Corpora
    dictionary = corpora.Dictionary(documents)
    # dictionary.save('deerwester.dict')
    corpus = [dictionary.doc2bow(text) for text in documents]
    # Apply LSI
    lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=2)
    index = similarities.MatrixSimilarity(lsi[corpus])
    for corp in corpus:
        vec_lsi = lsi[corp]
        sims = index[vec_lsi]
        # Descending ranking with the similar tokens
        sims = sorted(enumerate(sims), key=lambda item: -item[1])
        current_sequence = [dictionary[key] for key, ocurrence in corp]
        # TODO: return all sentences and corpus which score < 0.05
        # TODO: Count the number of similarities
        # TODO: Create topic group. count the weight of topic
        # TODO: Remove the similarities
        # TODO: Guardar los topic group en un modelo

    # TODO: Remove all SiteNewsScrapedData objects
    # for site in sites:
    #    site.delete()
    # TODO: Stats? What?

    return True