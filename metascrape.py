import urllib
import lxml
from lxml import etree
from lxml import html
import pandas as pd
import json
from scraper import *

class MetaScraper():

    def __init__(self, scrapers):
        self.scrapers = scrapers

    def run_scrape(self):

        for i, scraper in enumerate(self.scrapers):

            #get a list of product ids from each website
            prod_ids = scraper.add_ids(5)
            #print(prod_ids)

            #figure our their upc code
            upcs = []
            for prod_id in prod_ids:
                upc_lookup = scraper.lookup_upc(prod_id)
                if upc_lookup is not None:
                    upcs.append(upc_lookup)

            #print(upcs,scraper.base_url)

            #search for the code on the other websites
            other_scrapers = scrapers[:i] + scrapers[i+1:]
            #print(other_scrapers)
            for j, other_scraper in enumerate(other_scrapers):

                other_scraper_ids = []
                for upc in upcs:
                    if upc is not None:
                        other_scraper.lookup_id(upc)


    def write_data(self):
        for scraper in self.scrapers:
            scraper.write_data()



if __name__ == '__main__':
    db = 'db/'
    scrapers = [WalmartScraper(db), AmazonScraper(db)]
    ms  = MetaScraper(scrapers)
    ms.run_scrape()
    ms.write_data()