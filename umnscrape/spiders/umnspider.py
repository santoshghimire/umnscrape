# -*- coding: utf-8 -*-
import csv
import scrapy
import string
from scrapy.http.request import Request

from umnscrape.items import Item


def get_popular_names():
    with open('namelist.csv') as namefile:
        csvreader = csv.reader(namefile)
        return [i[0].lower().strip() for i in list(csvreader)]


class UMNSpider(scrapy.Spider):
    """
    Scraper to scrape the pet listings for
    a given lost pet description.
    """
    name = "umn"
    base_url = 'http://myaccount.umn.edu/lookup'
    allowed_domains = ["http://myaccount.umn.edu/"]

    def __init__(self, lost_pet=None):
        # read names from csv
        self.all_names = get_popular_names()

    def start_requests(self):
        # construct the results url
        name = self.all_names[0]
        # name = 'emily+b'
        url = self.get_default_url(name)
        yield Request(url, self.parse, meta={'step': 0})

    def get_default_url(self, name):
        name = name.replace(" ", "+")
        return "{}?SET_INSTITUTION=&type=name&CN={}&campus=a&role=stu".format(
            self.base_url, name)

    def get_next_name(self, name):
        """
        Get next name from the namelist
        """
        try:
            index = self.all_names.index(name)
        except:
            index = -1
        return self.all_names[index + 1]

    def get_step_names(self, name, step=1):
        if step == 1:
            return [name + '+' + s for s in list(string.ascii_lowercase)]
        else:
            return [name + s for s in list(string.ascii_lowercase)]

    def get_name_from_url(self, url):
        qs = url.split("?")[-1]
        name_qs = [i for i in qs.split('&') if i.startswith('CN')][0]
        search_name = name_qs.split('=')[-1]
        base_name = search_name.split("+")[0]
        return search_name, base_name

    def split_names(self, full_name):
        name_parts = full_name.split(" ")
        first_name = name_parts[0]
        if len(name_parts) == 1:
            middle_name = ""
            last_name = ""
        elif len(name_parts) == 2:
            middle_name = ""
            last_name = name_parts[-1]
        else:
            last_name = name_parts[-1]
            middle_name = " ".join(name_parts[1:-1])
        return first_name, middle_name, last_name

    def parse(self, response):
        """
        Parse the content.
        """
        step = response.meta.get('step')
        status = response.xpath(
            "//hr[@height='1']/following-sibling::b/text()").extract_first()
        search_name, base_name = self.get_name_from_url(response.url)

        if not status:
            # extract items
            print("{}: Data found".format(search_name))

            trs = response.xpath(
                "//form/following-sibling::table//tr[@align='LEFT']")
            for tr in trs:
                tds = tr.xpath("./td")
                detail_link = tds[0].xpath("./a/@href").extract_first()
                detail_link = response.urljoin(detail_link)
                yield scrapy.Request(
                    detail_link, self.parse_detail, dont_filter=True)
            if not step:
                # SCRAPE NEXT NAME
                next_name = self.get_next_name(base_name)
                next_url = self.get_default_url(next_name)
                yield scrapy.Request(
                    next_url, self.parse, dont_filter=True, meta={'step': 0})
        elif 'no matches found' in status.lower():
            # no matches found, get next name and continue
            print("{}: no matches found".format(search_name))
            if not step:
                pass
                next_name = self.get_next_name(base_name)
                next_url = self.get_default_url(next_name)
                yield scrapy.Request(
                    next_url, self.parse, dont_filter=True, meta={'step': 0})

        elif 'too many entries' in status.lower():
            # refine the search
            print("{}: Too many entries, step {}".format(search_name, step))
            if not step:
                step_names = self.get_step_names(name=search_name, step=1)
            elif step == 1:
                step_names = self.get_step_names(name=search_name, step=2)
            for each_step_name in step_names:
                pass
                step_url = self.get_default_url(each_step_name)
                yield scrapy.Request(
                    step_url, self.parse, dont_filter=True,
                    meta={'step': (step + 1)}
                )
            if not step:
                # Get next base name and crawl
                next_name = self.get_next_name(base_name)
                next_url = self.get_default_url(next_name)
                yield scrapy.Request(
                    next_url, self.parse, dont_filter=True, meta={'step': 0})

    def parse_detail(self, response):
        item = Item()
        full_name = response.xpath(
            "//form/following-sibling::h2/text()").extract_first()
        item['first_name'], item['middle_name'], item['last_name'] = \
            self.split_names(full_name)
        # enrollment
        enrollment = response.xpath(
            "//form/following-sibling::table//th[@align='RIGHT']"
            "[contains(text(), 'Enrollment')]/parent::tr"
        )
        enrollment = enrollment.xpath("./td/text()").extract()
        if len(enrollment) == 3:
            item['major'] = enrollment[0].strip()
            item['campus'] = enrollment[1].strip()
            item['semester'] = enrollment[2].strip()
        elif len(enrollment) == 2:
            item['campus'] = enrollment[0].strip()
            item['semester'] = enrollment[1].strip()
            item['major'] = None
        elif len(enrollment) == 1:
            item['campus'] = enrollment[0].strip()
            item['semester'] = None
            item['major'] = None
        else:
            print("Enrollment parsing error")
            print("URL = {}".format(response.url))
            print("Enrollment = {}".format(enrollment))
            item['campus'] = None
            item['semester'] = None
            item['major'] = None

        email = response.xpath(
            "//form/following-sibling::table//th[@align='RIGHT']"
            "[contains(text(), 'Email')]/parent::tr"
        )
        item['email'] = email.xpath("./td/a/text()").extract_first()

        internetid = response.xpath(
            "//form/following-sibling::table//th[@align='RIGHT']"
            "[contains(text(), 'Internet')]/parent::tr"
        )
        item['internetid'] = internetid.xpath("./td/tt/text()").extract_first()

        mobile = response.xpath(
            "//form/following-sibling::table//th[@align='RIGHT']"
            "[contains(text(), 'Mobile')]/parent::tr"
        )
        item['cell_phone'] = mobile.xpath("./td/text()").extract_first()

        address = response.xpath(
            "//form/following-sibling::table//th[@align='RIGHT']"
            "[contains(text(), 'Address')]/parent::tr"
        )
        address = address.xpath("./td/text()").extract()
        item['address'] = " ".join([i.strip() for i in address if i.strip()])

        phone = response.xpath(
            "//form/following-sibling::table//th[@align='RIGHT']"
            "[contains(text(), 'Phone')]/parent::tr"
        )
        if phone:
            item['phone'] = phone[-1].xpath("./td/text()").extract_first()
            if item['cell_phone'] == item['phone']:
                item['phone'] = None
        else:
            item['phone'] = None
        yield item

if __name__ == '__main__':
    name = get_popular_names()
