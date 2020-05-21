# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Page(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    links = scrapy.Field()
    emails = scrapy.Field()
    phone_numbers = scrapy.Field()

class BrokenLink(scrapy.Item):
    url = scrapy.Field()
    status = scrapy.Field()
