import re
import scrapy
from w3lib.html import remove_tags
from datetime import datetime
from scrapy.linkextractors import LinkExtractor
from vumc.items import Page, BrokenLink

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

PHONE_REGEX = re.compile(r'(\d{3}[-\.\s]\d{3}[-\.\s]\d{4})')
DOMAIN_REGEX = re.compile(r'https://vumc.org/safety')

class VumcSpider(scrapy.Spider):
    name = "vumc"

    def start_requests(self):
        urls = [
            "https://vumc.org/safety/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_page)


    def parse_page(self, response):
        links = LinkExtractor(deny="#", unique=True, restrict_css="article") \
            .extract_links(response)

        emails = response.css("a[href^=mailto]::text").getall()
        emails = [remove_tags(i) for i in emails]

        phone = PHONE_REGEX.findall(response.text)

        yield Page(
            title=response.css("title::text").get(),
            url=response.url,
            links=links,
            emails=emails,
            phone_numbers=phone,
        )

        site_links = LinkExtractor(allow="vumc.org/safety", deny="#") \
            .extract_links(response)

        outside_links = LinkExtractor(deny=["vumc.org/safety", "#"]) \
            .extract_links(response)

        for link in site_links:
            yield response.follow(link,
                callback=self.parse_page,
                errback=self.errback
            )

        for link in outside_links:
            yield response.follow(link,
                callback=self.do_nothing,
                errback=self.errback,
            )

    def errback(self, failure):
        self.logger.error(repr(failure))

        status = None
        url = None

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            status = response.status
            if response.meta.get('redirect_urls'):
                url = response.meta.get('redirect_urls')[0]
            else:
                url = response.url

        elif failure.check(DNSLookupError):
            status = "DNS"
            url = failure.request.url
        elif failure.check(TimeoutError, TCPTimedOutError):
            status = "TimeOut"
            url = failure.request.url

        return BrokenLink(
            status=status,
            url=url,
        )

    def do_nothing(self, response):
        return


