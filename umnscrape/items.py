# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Item(scrapy.Item):
    # define the fields for your item here like:
    first_name = scrapy.Field()
    middle_name = scrapy.Field()
    last_name = scrapy.Field()

    email = scrapy.Field()
    campus = scrapy.Field()
    phone = scrapy.Field()
    cell_phone = scrapy.Field()
    major = scrapy.Field()
    semester = scrapy.Field()
    address = scrapy.Field()
    internetid = scrapy.Field()
