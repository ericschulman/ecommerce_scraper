import urllib
import lxml
from lxml import etree
from lxml import html
import pandas as pd
import json


class MetaScraper():

	def __init__(self, db):
		self.counter = 0
		self.base_url = 'https://'
		self.db = db

	def run_scrape():
		am_scrap = WalmartScraper('db/scrape.db') 
		wal_scrap = AmazonScraper('db/scrape.db')

		asins = am_scrap.get_ids(5)
		print(asins)
		upcs = []
		for asin in asins:
			upc_lookup = am_scrap.lookup_upc(asin)
			if upc_lookup is not None:
				upcs.append(upc_lookup)
		print(upcs)

		walmartids = []
		for upc in upcs:
			if upc is not None:
				walmartids.append(wal_scrap.lookup_id(upc) )
		print(walmartids)



if __name__ == '__main__':