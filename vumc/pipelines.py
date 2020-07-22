# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
import re
from scrapy.exporters import JsonItemExporter

NL = "\n"
BUFSIZE = 10
NODE_REGEX = re.compile(r'\/node\/')

class VumcPipeline(object):
    def open_spider(self, spider):
        self.search_results_file = open('search.csv', "w", buffering=BUFSIZE, encoding='utf-8')
        self.broken_links_file = open('broken.csv', "w", buffering=BUFSIZE, encoding='utf-8')

        self.broken_links_file.write("URL, Status, Linked from" + NL)

    def close_spider(self, spider):
        self.search_results_file.close()
        self.broken_links_file.close()

    def process_item(self, item, spider):
        if item.get('status'): #BrokenLink item
            self.broken_links_file.write(
                f"{item['url']}, {item['status']}, {item['referer']}{NL}"
            )

        if item.get('data'): #SearchResult item
            self.search_results_file.write(
                f"{item['url']}, {item['data']}{NL}"
            )

        return item


class PagePipeline(object):
    def open_spider(self, spider):
        self.pages = []
        self.broken_links = set()

        self.pages_node_file = open('pages_node.csv', "w", buffering=BUFSIZE, encoding='utf-8')
        self.pages_broken_file = open('pages_broken.csv', "w", buffering=BUFSIZE, encoding='utf-8')

        self.pages_json = open("pages.json", "wb")
        self.exporter = JsonItemExporter(self.pages_json, encoding='utf-8')
        self.exporter.start_exporting()

    def close_spider(self, spider):
        for page in self.pages:
            links = page.get('links')

            # find links that are broken or contain /node/
            broken_in_page = [link.url for link in links if link.url in self.broken_links]
            node_in_page = [link.url for link in links if NODE_REGEX.search(link.url)]

            if broken_in_page:
                self.pages_broken_file.write(
                    f"{page['url']}, {page['title']}{NL}"
                )
                for link in broken_in_page:
                    self.pages_broken_file.write(f"{link}{NL}")
                self.pages_broken_file.write(NL)

            if node_in_page:
                self.pages_node_file.write(
                    f"{page['url']}, {page['title']}{NL}"
                )
                for link in node_in_page:
                    self.pages_node_file.write(f"{link}{NL}")
                self.pages_node_file.write(NL)

        self.pages_node_file.close()
        self.pages_broken_file.close()

        self.exporter.finish_exporting()
        self.pages_json.close()


    def process_item(self, item, spider):
        if item.get('title'): #Page item
            # store the page for future processing.
            self.pages.append(item)

            # self.pages_file.write(item['url'])
            # for email in item['emails']:
            #     self.pages_file.write(", " + email)
            # self.pages_file.write(NL)

            # self.exporter.export_item(item)

        if item.get('status'): #BrokenLink item
            # store a set of all the broken links.
            self.broken_links.add(item['url'])

        return item