from celery.canvas import group, chord
from djcelery.app import app
from news_crawler.news_crawler.utils import run_spider, spiders
from nlp import *
from datetime import datetime


@app.task
def scrape_site(spider):
    run_spider(spider)
    return True

@app.task
def scrape_news():
    sites = SiteNewsScrapedData.objects.all()
    for site in sites:
        site.delete()
    # TODO: Pasar de alguna manera el transaction_id al spider
    chord((scrape_site.s(spider) for spider in spiders), compute_nlp.s())()
    return True

@app.task
def compute_nlp(results):
    today = datetime.now()
    compute_topics(True, today)
    return True