# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scraper_module.models import SiteNewsData
from scrapy.item import Item


class NewsCrawlerItem(Item):
    page = scrapy.Field()
    content = scrapy.Field()

    def materialize(self):
        try:
            SiteNewsData.sync()
        except:
            pass
        instance = SiteNewsData()
        instance.page = self['page']
        instance.content = self['content']
        instance.save()
