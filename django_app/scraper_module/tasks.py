from celery.canvas import group
from djcelery.app import app
from news_crawler.news_crawler.utils import run_spider, spiders

@app.task
def scrape_site(spider):
    try:
        run_spider(spider)
    except Exception:
        return False
    return True

@app.task
def scrape_news():
    scraped_news = group(scrape_site.s(spider) for spider in spiders)
    (scraped_news | compute_nlp.s())()
    return True

@app.task
def compute_nlp(results):
    return True