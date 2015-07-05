# -*- coding: utf-8 -*-

import scrapy
from scraper_module.news_crawler.news_crawler import items


class ClarinSpider(scrapy.Spider):
    name = "clarin"

    def __init__(self, *args, **kwargs):
        super(ClarinSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.clarin.com"]

    def parse(self, response):
        item = items.NewsCrawlerItem()
        item['page'] = self.name
        item['content'] = u''
        for element in response.xpath("//a/h3/text()"):
            item['content'] += "%s." % (element.extract(),)
        item.materialize()
        yield item


class PerfilSpider(scrapy.Spider):
    name = "perfil"

    def __init__(self, *args, **kwargs):
        super(PerfilSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.perfil.com"]

    def parse(self, response):
        item = items.NewsCrawlerItem()
        item['page'] = self.name
        item['content'] = u''
        for element in response.xpath("//h2/text()"):
            item['content'] += "%s." % (element.extract(),)
        for element in response.xpath("//h1/a/text()"):
            item['content'] += "%s." % (element.extract(),)
        item.materialize()
        yield item


class LaNacionSpider(scrapy.Spider):
    name = "lanacion"

    def __init__(self, *args, **kwargs):
        super(LaNacionSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.lanacion.com.ar"]

    def parse(self, response):
        item = items.NewsCrawlerItem()
        item['page'] = self.name
        item['content'] = u''
        for element in response.xpath("//article/h2/a/text()"):
            item['content'] += "%s." % (element.extract(),)
        item.materialize()
        yield item


class Pagina12Spider(scrapy.Spider):
    name = "pagina12"

    def __init__(self, *args, **kwargs):
        super(Pagina12Spider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.pagina12.com.ar"]

    def parse(self, response):
        item = items.NewsCrawlerItem()
        item['page'] = self.name
        item['content'] = u''
        for element in response.xpath("//table/tr/td/h3/a/text()"):
            item['content'] += "%s." % (element.extract(),)
        item.materialize()
        yield item


class InfoBaeSpider(scrapy.Spider):
    name = "infobae"

    def __init__(self, *args, **kwargs):
        super(InfoBaeSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.infobae.com"]

    def parse(self, response):
        item = items.NewsCrawlerItem()
        item['page'] = self.name
        item['content'] = u''
        for element in response.xpath('//article/h1/a/text()'):
            item['content'] += "%s." % (element.extract(),)
        item.materialize()
        yield item


class ElArgentinoSpider(scrapy.Spider):
    name = "elargentino"

    def __init__(self, *args, **kwargs):
        super(ElArgentinoSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://elargentino.infonews.com"]

    def parse(self, response):
        item = items.NewsCrawlerItem()
        item['page'] = self.name
        item['content'] = u''
        for element in response.xpath('//h2/a/text()'):
            item['content'] += "%s." % (element.extract(),)
        item.materialize()
        yield item