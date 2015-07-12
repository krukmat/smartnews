from celery.canvas import group
from djcelery.app import app
from models import SiteNewsScrapedData, TopicGroups
from news_crawler.news_crawler.utils import run_spider, spiders
from nlp import *


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
    scraped_news = group(scrape_site.s(spider) for spider in spiders)
    (scraped_news | compute_nlp.s())()
    return True

@app.task
def compute_nlp(results):
    compute_topics()
    return True