import re
import scrapy
from w3lib.html import remove_tags
from datetime import datetime
from scrapy.linkextractors import LinkExtractor, IGNORED_EXTENSIONS
from vumc.items import Page, BrokenLink, SearchResult

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

from collections import Counter

PHONE_REGEX = re.compile(r'(\d{3}[-\.\s]\d{3}[-\.\s]\d{4})')
ALLOW_PDF =[x for x in IGNORED_EXTENSIONS if x != "pdf"]

SEARCH_REGEX = re.compile(r'robin\.trundy@vumc\.org', flags=re.IGNORECASE)

class VumcSpider(scrapy.Spider):
    name = "vumc"

    page_link_extractor = LinkExtractor(deny="#", unique=True, restrict_css="article", deny_extensions=ALLOW_PDF)
    site_link_extractor = LinkExtractor(allow="vumc.org/safety", deny="#")
    external_link_extractor = LinkExtractor(deny=["vumc.org/safety", "#"])
    pdf_link_extractor = LinkExtractor(allow=".pdf$", deny_extensions=ALLOW_PDF)

    def start_requests(self):
        urls = [
            "https://vumc.org/safety/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):
        yield self.parse_page(response)

        result = self.search(response)
        if result:
            yield result

        site_links = self.site_link_extractor.extract_links(response)
        outside_links = self.external_link_extractor.extract_links(response)
        pdf_links = self.pdf_link_extractor.extract_links(response)

        # parse /safety links
        for link in site_links:
            yield response.follow(link,
                callback=self.parse,
                errback=self.errback,
                meta={"from_page": response.url}
            )

        # only check for errors for outside and pdf links
        for link in outside_links + pdf_links:
            yield response.follow(link,
                callback=self.do_nothing, # if no errors, don't do anything
                errback=self.errback, # otherwise log the error
                meta={"from_page": response.url}
            )

    def parse_page(self, response):
        # get links from the <article> sections of the page. This is where the main content of the page is.
        links = self.page_link_extractor.extract_links(response)

        emails = response.css("a[href^=mailto]::attr(href)").getall()
        emails = [remove_tags(i) for i in emails]

        phone = PHONE_REGEX.findall(response.text)

        return Page(
            title=response.css("title::text").get(),
            url=response.url,
            links=links,
            emails=emails,
            phone_numbers=phone,
        )


    # perform an arbitrary search, passing data to the item
    def search(self, response):
        # data = SEARCH_REGEX.findall(response.css('article').get())
        data = SEARCH_REGEX.findall(response.text)

        if data:
            # count occurances of matches and return as a csv string
            data = Counter(data)
            data = [k+':'+str(v) for k,v in data.most_common()]

            return SearchResult(
                url=response.url,
                data= ', '.join(data)
            )
        else:
            return None

    # returns information about a failed request
    def errback(self, failure):
        self.logger.error(repr(failure))

        status = None
        url = None

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            status = response.status

            if status == 401:

                return response.follow(
                    url=response.url,
                )

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
        else:
            status = "Other"
            url = failure.request.url

        return BrokenLink(
            status=status,
            url=url,
            referer=failure.request.meta.get('from_page')
        )

    # do nothing with a successful response
    def do_nothing(self, response):
        return