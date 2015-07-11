# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scraper_module.models import SiteNewsScrapedData
from scrapy.item import Item


class NewsCrawlerItem(Item):
    page = scrapy.Field()
    content = scrapy.Field()
    texts = scrapy.Field()
    links = scrapy.Field()

    def materialize(self):
        try:
            SiteNewsScrapedData.sync()
        except:
            pass
        instance = SiteNewsScrapedData()
        instance.page = self['page']
        instance.content = self['content']
        for index, text in enumerate(self['texts']):
            instance.map_link[text] = self['links'][index]
        instance.save()
