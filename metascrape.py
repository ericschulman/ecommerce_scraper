from gen_scraper import *
from wal_scraper import *
from am_scraper import *
from lo_scraper import *
from hd_scraper import *


class MetaScraper():

    def __init__(self, scrapers,size,query):
        self.scrapers = scrapers
        self.query = query
        self.size = size

    def run_scrape(self):

        for i, scraper in enumerate(self.scrapers):
            #get a list of product ids from each website
            scraper.set_query(self.query)
            prod_ids = scraper.add_ids(self.size )
            #print(prod_ids)
            #figure our their upc code
            products = []
            for prod_id in prod_ids:
                product_lookup = scraper.lookup_product(prod_id)
                if product_lookup is not None:
                    products.append(product_lookup)
                    
            #search for the code on the other websites
            other_scrapers = scrapers[:i] + scrapers[i+1:]
            for j, other_scraper in enumerate(other_scrapers):

                other_scraper_ids = []
                for product in products:
                    if product is not None:
                        #create a text file with output from the scrape
                        #print(product, other_scraper.platform, scraper.platform)
                        #print(other_scraper.lookup_id(product))
                        #print('<----->')


    def write_data(self):
        #get the number of observations for each scraper
        for scraper in self.scrapers:
            print('<----->')
            print(scraper.platform, len(scraper.data))
            scraper.write_data()
            print('<----->')



if __name__ == '__main__':
    db = 'db/'
    scrapers = [LowesScraper(db), HomeDepotScraper(db), WalmartScraper(db), AmazonScraper(db)]
    ms  = MetaScraper(scrapers, 20,'drills')
    ms.run_scrape()
    ms.write_data()