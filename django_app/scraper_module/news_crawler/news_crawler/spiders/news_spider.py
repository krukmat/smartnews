# -*- coding: utf-8 -*-

import scrapy
from scraper_module.news_crawler.news_crawler import items


class NewsSiteCrawler(scrapy.Spider):
    name = 'newsite'

    def parse(self, response):
        item = items.NewsCrawlerItem()
        item['page'] = self.name
        item['content'] = u''
        item['texts'] = []
        item['links'] = []

        for style in self.styles:
            # link extraction
            text = None
            link = None
            for element in response.xpath(style):
                # Last case @title
                link_xpath = '@href'
                text_xpath = 'text()'
                # Text path
                if len(element.xpath(text_xpath)) > 0:
                    text = element.xpath(text_xpath)[0]
                    if len(element.xpath(text_xpath)) > 0:
                        link = element.xpath(link_xpath)[0]
                    else:
                        link = None
                if text and link:
                    item['content'] += "%s ." % (text.extract(),)
                    item['texts'].append(text.extract().encode('utf-8'))
                    item['links'].append(link.extract().encode('utf-8'))
        item.materialize()
        yield item


class ClarinSpider(NewsSiteCrawler):
    name = "clarin"

    def __init__(self, *args, **kwargs):
        super(ClarinSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.clarin.com"]
        self.styles = ["//a/h2", "//a/h3", '//article/a/@title']

    def parse(self, response):
        item = items.NewsCrawlerItem()
        item['page'] = self.name
        item['content'] = u''
        item['texts'] = []
        item['links'] = []

        for style in self.styles:
            # link extraction
            text = None
            link = None
            for element in response.xpath(style):
                # Last case @title
                if '@' in style:
                    text_xpath = style
                    link_xpath = style.replace('@title', '@href')
                else:
                    link_xpath = 'parent::*/@href'
                    text_xpath = 'text()'
                # Text path
                if len(element.xpath(text_xpath)) > 0:
                    text = element.xpath(text_xpath)[0]
                    if len(element.xpath(text_xpath)) > 0:
                        link = element.xpath(link_xpath)[0]
                    else:
                        link = None
                else:
                    text_xpath = 'span/text()'
                    if len(element.xpath(text_xpath)) > 0:
                        text = element.xpath(text_xpath)[0]
                        if len(element.xpath(text_xpath)) > 0:
                            link = element.xpath(link_xpath)[0]
                        else:
                            link = None
                if text and link:
                    item['content'] += "%s ." % (text.extract(),)
                    item['texts'].append(text.extract().encode('utf-8'))
                    item['links'].append(link.extract().encode('utf-8'))
        item.materialize()
        yield item


class PerfilSpider(NewsSiteCrawler):
    name = "perfil"

    def __init__(self, *args, **kwargs):
        super(PerfilSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.perfil.com"]
        self.styles = ["//h3/a", "//h1/a", "//h6/a", "//h5/a"]

class LaNacionSpider(NewsSiteCrawler):
    name = "lanacion"

    def __init__(self, *args, **kwargs):
        super(LaNacionSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.lanacion.com.ar"]
        self.styles = ["//article/h2/a"]


class Pagina12Spider(NewsSiteCrawler):
    name = "pagina12"

    def __init__(self, *args, **kwargs):
        super(Pagina12Spider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.pagina12.com.ar"]
        self.styles = ["//table/tr/td/h3/a", "//table/tr/td/h2/a"]


class InfoBaeSpider(NewsSiteCrawler):
    name = "infobae"

    def __init__(self, *args, **kwargs):
        super(InfoBaeSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://www.infobae.com"]
        self.styles = ['//article/h1/a']


class ElArgentinoSpider(NewsSiteCrawler):
    name = "elargentino"

    def __init__(self, *args, **kwargs):
        super(ElArgentinoSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["http://elargentino.infonews.com"]
        self.styles = ['//h2/a']
