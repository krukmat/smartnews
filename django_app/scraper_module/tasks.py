from celery.canvas import group
from djcelery.app import app
from models import SiteNewsScrapedData
from news_crawler.news_crawler.utils import run_spider, spiders

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
    # TODO: Filtrar por transaction_id
    sites = SiteNewsScrapedData.objects.all()
    # TODO: Create word list
    # TODO: Remove stop words
    # TODO: Apply LDA
    # TODO: Return list and call twitter scraper. Check trends? What?
    # TODO: Remove all SiteNewsScrapedData objects
    # TODO: Stats? What?
    return True