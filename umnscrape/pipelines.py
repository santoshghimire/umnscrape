# -*- coding: utf-8 -*-
from scrapy.exceptions import DropItem

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class UMNPipeline(object):
    """
    Pipeline module to filter out only relevent
    matches of the lost pet.
    """
    def __init__(self):
        self.items_seen = []

    def process_item(self, item, spider):
        """
        Process each item, drop items that are already seen.
        """
        if item not in self.items_seen:
            self.items_seen.append(item)
            return item
        else:
            raise DropItem("Item Dropped")
