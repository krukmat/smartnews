# -*- coding: utf-8 -*-

import scrapy
from scraper_module.news_crawler.news_crawler import items


class NewsSiteCrawler(scrapy.Spider):
    name = 'newsite'

    def parse(self, response):
        item = items.NewsCrawlerItem()
        item['page'] = self.name
        item['content'] = u''
        for style in self.styles:
            for element in response.xpath(style):
                item['content'] += "%s." % (element.extract(),)
        item.materialize()
        yield item


class ClarinSpider(NewsSiteCrawler):
    name = "clarin"

    def __init__(self, *args, **kwargs):
        super(ClarinSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.clarin.com"]
        self.styles = ["//a/h3/text()"]


class PerfilSpider(NewsSiteCrawler):
    name = "perfil"

    def __init__(self, *args, **kwargs):
        super(PerfilSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.perfil.com"]
        self.styles = ["//h2/text()", "//h1/a/text()"]

class LaNacionSpider(NewsSiteCrawler):
    name = "lanacion"

    def __init__(self, *args, **kwargs):
        super(LaNacionSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.lanacion.com.ar"]
        self.styles = ["//article/h2/a/text()"]


class Pagina12Spider(NewsSiteCrawler):
    name = "pagina12"

    def __init__(self, *args, **kwargs):
        super(Pagina12Spider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.pagina12.com.ar"]
        self.styles = ["//table/tr/td/h3/a/text()"]

class InfoBaeSpider(NewsSiteCrawler):
    name = "infobae"

    def __init__(self, *args, **kwargs):
        super(InfoBaeSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.infobae.com"]
        self.styles = ['//article/h1/a/text()']


class ElArgentinoSpider(NewsSiteCrawler):
    name = "elargentino"

    def __init__(self, *args, **kwargs):
        super(ElArgentinoSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://elargentino.infonews.com"]
        self.styles = ['//h2/a/text()']
