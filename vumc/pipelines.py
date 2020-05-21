# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
NL = "\n"
BUFSIZE = 1

class VumcPipeline(object):
    def open_spider(self, spider):
        self.pages_file = open('pages.txt', "w", buffering=BUFSIZE)
        self.broken_links = open('broken.txt', "w", buffering=BUFSIZE)

    def close_spider(self, spider):
        self.pages_file.close()
        self.broken_links.close()

    def process_item(self, item, spider):
        if item.get('title'): #Page item
            links = item.get('links')
            self.pages_file.write(
                f"{item['title']} ({item['url']}){NL}{NL.join(item['phone_numbers'] + item['emails'])}{NL}"
            )
            for link in links:
                self.pages_file.write(
                    f"{link.url} {link.text}{NL}"
                )
            self.pages_file.write("\n")

        if item.get('status'): #BrokenLink item
            self.broken_links.write(
                f"{item['url']} ({item['status']}){NL}"
            )


        return item
