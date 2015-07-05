__author__ = 'matiasleandrokruk'

from scrapy.crawler import Crawler
from twisted.internet import reactor
from billiard import Process
from scrapy.utils.project import get_project_settings
from scrapy.signals import spider_closed
from spiders.news_spider import *

spiders = [ClarinSpider, PerfilSpider, LaNacionSpider,
           Pagina12Spider, InfoBaeSpider, ElArgentinoSpider]


class CrawlerWrapper(Process):
        def __init__(self, spider):
            Process.__init__(self)
            settings = get_project_settings()
            self.crawler = Crawler(spider, settings)
            self.crawler.signals.connect(reactor.stop, signal=spider_closed)
            self.spider = spider

        def run(self):
            self.crawler.crawl()
            reactor.run()


def run_spider(spider):
    crawler = CrawlerWrapper(spider)
    crawler.start()
    crawler.join()


def run_spiders():
    for spider in spiders:
        run_spider(spider)