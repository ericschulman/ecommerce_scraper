from gen_scraper import *
from wal_scraper import *
from am_scraper import *
from lo_scraper import *
from hd_scraper import *
import traceback

class MetaScraper():

    def __init__(self, scrapers,size,query):
        self.scrapers = scrapers
        self.query = query
        self.size = size

    def run_scrape(self):

        for i, scraper in enumerate(self.scrapers):
            print('------ starting %s scrape'%scraper.platform)
            #get a list of product ids from each website
            scraper.set_query(self.query)
            prod_ids = []
            try:
                prod_ids = scraper.add_ids(self.size)
            except:
                print("<< error getting ids", scraper.platform, ' >>')
                traceback.print_exc()

            #figure our their upc code
            print('------ getting name/brand %s scrape'%scraper.platform)
            products = []
            for prod_id in prod_ids:
                try:
                    product_lookup = scraper.lookup_product(prod_id)
                    if product_lookup is not None:
                        products.append(product_lookup)
                except:
                    print("<<error getting name/brand", scraper.platform, prod_id ,' >>')
                    traceback.print_exc()

            #search for the code on the other websites
            print('------ searching %s scrape'%scraper.platform)
            other_scrapers = scrapers[:i] + scrapers[i+1:]
            for j, other_scraper in enumerate(other_scrapers):
                other_scraper_ids = []
                for product in products:
                    if product is not None:
                        try:
                            other_scraper.lookup_id(product)
                        except:
                            print("<< error during searching", other_scraper.platform, scraper.platform, product ,' >>')
                            traceback.print_exc()
            print('------ ending %s scrape'%scraper.platform)

    def write_data(self):
        #get the number of observations for each scraper
        for scraper in self.scrapers:
            try:
                print('------ writing data ', scraper.platform)
                print('obs:', len(scraper.data))
                scraper.write_data()
                scraper.end_scrape()
            except:
                print('<< error writing data >>')
                traceback.print_exc()


if __name__ == '__main__':

    db = 'db/'
    scrapers = [LowesScraper(db), HomeDepotScraper(db), WalmartScraper(db), AmazonScraper(db)]
    print('------ scrapers initialized')
    ms  = MetaScraper(scrapers, 20,'drills')
    try:
        ms.run_scrape()
    except:
        traceback.print_exc()
    ms.write_data()
    print('------ data written')
