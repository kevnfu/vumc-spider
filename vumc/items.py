# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Field, Item


class Page(Item):
    title = Field()
    url = Field()
    links = Field()
    emails = Field()
    phone_numbers = Field()

    def __repr__(self):
        return repr(dict(title=self["title"], url=self["url"]))

class BrokenLink(Item):
    url = Field()
    status = Field()
    referer = Field()

class SearchResult(Item):
    url = Field()
    data = Field()
