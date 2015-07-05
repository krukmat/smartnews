from djcelery.app import app
from news_crawler.news_crawler.utils import run_spiders


@app.task
def scrape_news():
    run_spiders()
    return True