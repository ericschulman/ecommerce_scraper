import urllib
import lxml
from lxml import etree
from lxml import html
import pandas as pd
import json


class GenericScraper:

	hdr1 = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
	   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
	   'Accept-Encoding': 'none',
	   'Accept-Language': 'en-US,en;q=0.8',
	   'Connection': 'keep-alive'}

	hdr2 = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
		'Accept-Encoding': 'none',
		'Accept-Language': 'en-US,en;q=0.8',
		'Connection': 'keep-alive'}

	hdrs = [hdr1,hdr2]

	def __init__(self, db):
		self.counter = 0
		self.base_url = 'https://'
		self.db = db


	def get_page(self, url):
		try:
			hdr = GenericScraper.hdrs[self.counter%2]
			page = urllib.request.Request(url, headers=hdr)
			response = urllib.request.urlopen(page)
			rawtext = response.read()
			return str(rawtext)
		except urllib.error.HTTPError as err:
			print(err, url)
			empty = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css"><script src="script.js"></script></head></html>'
			return empty



	def search_url(self, query):
		return ''

	def prod_url(self, prod_id):
		return ''

	def lookup_upc(self, prod_id):
		return None

	def lookup_id(self, upc):
		return None

	def get_data(self,prod_id):
		return None

	def write_data(self):
		pass

	def get_ids(self):
		return []


class AmazonScraper(GenericScraper):
		
	def __init__(self, db):
		super(AmazonScraper, self).__init__(db)
		self.base_url = 'https://www.amazon.com/'


	def search_url(self, query):
		url =  self.base_url + 's?k=%s&s=%s'%(query,'salesrank')
		return url


	def get_ids(self):
		url = self.search_url('drills')
		rawtext = self.get_page(url)
		tree = html.fromstring(rawtext)
		search_rows = tree.xpath("//*[@class='s-result-list s-search-results sg-row']")[0]
		asins = []
		for i in range(10):
			if not ('AdHolder' in search_rows[i].attrib['class']) and search_rows[i].attrib['data-asin'] !='':
				asins.append(search_rows[i].attrib['data-asin'])
		return asins


	def amazon_table(self, tree,key):
		table =  tree.xpath("//*[@id='%s']"%key)[0]
		table = pd.read_html(etree.tostring(table , encoding='utf8', method='html'))[0]
		table = table.applymap(lambda s: s[3:-2]) #clean things up
		table = table.set_index(0)
		return table
		

	def get_data(self, asin):
		url = 'https://www.amazon.com/dp/' + asin
		rawtext = self.get_page(url)
		tree = html.fromstring(rawtext)
		manuf = tree.xpath("//*[@id='bylineInfo']")[0]
		
		table1 =  self.amazon_table(tree,'productDetails_techSpec_section_1')
		#table2 =  self.amazon_table(tree,'productDetails_detailBullets_sections1')
		
		#TODO: get pricing information
		#TODO: get seller information
		model = ''
		if 'Item model number' in list(table1.index):
			model = table1.loc['Item model number'][1]
		if '\\tPart Number\\t' in list(table1.index):
			model = table1.loc['\\tPart Number\\t'][1]
		return manuf.text, model


	def lookup_upc(self, prod_id):
		brand,item = self.get_data(prod_id)
		url = 'https://www.upcitemdb.com/upc/%s %s'%(brand,item)
		rawtext = self.get_page(url)
		tree = html.fromstring(rawtext)
		link_cand = tree.xpath("//*[@class='rImage']")
		#TODO: go for top 3 items instead
		if len(link_cand)  == 0 : 
			return None

		return link_cand[0][0].text


	def lookup_id(self, upc):
		#TODO implement
		return None



class WalmartScraper(GenericScraper):


	def __init__(self, db):
		super(WalmartScraper, self).__init__(db)
		self.base_url = 'https://www.walmart.com/'


	def search_url(self, query):
		url =  self.base_url + 'search/?cat_id=0&query=%s'%(query)
		return url


	def lookup_id(self, upc):

		url = self.search_url(upc)
		rawtext1 = self.get_page(url)
		tree = html.fromstring(rawtext1)

		link_cand = tree.xpath("//*[@id='searchContent']")
		if len(link_cand) ==0:
			return None
		link_cand = link_cand[0]
		rawdata = link_cand.text.replace('\\"','"')
		rawdata = rawdata.replace("\\'","'")
		datastore = json.loads(rawdata)
		for item in datastore['searchContent']['preso']['items']:
			if upc[:-1] in str(item['upc']) :
				brand = item['brand']
				#url = 'https://www.walmart.com/ip/' + 
				return item['productId']
		return None


	def lookup_upc(self, prod_id):
		return None



if __name__ == '__main__':

	am_scrap = AmazonScraper('db/scrape.db')
	wal_scrap = WalmartScraper('db/scrape.db')

	asins = am_scrap.get_ids()
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