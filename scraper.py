import urllib
import lxml
from lxml import etree
from lxml import html
import pandas as pd
import json
import os
import sqlite3
import datetime

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
		self.data = {}
		
		#create the database if it is not there
		if not os.path.isfile(db+'scrape.db') :
			f = open(db+'scrape.sql','r')
			sql = f.read()
			con = sqlite3.connect(db + 'scrape.db') #create the db
			cur = con.cursor()
			cur.executescript(sql)
			con.commit()

	def get_page(self, url):
		try:
			hdr = GenericScraper.hdrs[self.counter%2]
			page = urllib.request.Request(url, headers=hdr)
			response = urllib.request.urlopen(page)
			rawtext = response.read()
			return rawtext
		except urllib.error.HTTPError as err:
			print(err, url)
			empty = b'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css"><script src="script.js"></script></head></html>'
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
		return self.ids[prod_id]

	def write_data(self):
		conn = sqlite3.connect(self.db + 'scrape.db')
		c = conn.cursor()
		for key in self.data.keys():
			query_pt1 = " INSERT INTO prices(website,prod_id"
			query_pt2 = " VALUES ('%s','%s'"%(self.base_url,key)
			for sub_key in self.data[key].keys():
				if self.data[key][sub_key] is not None:
					query_pt1 = query_pt1 + "," + sub_key
					query_pt2 = query_pt2 + ",'%s'"%self.data[key][sub_key]
			query_pt1 = query_pt1 + ")"
			query_pt2 = query_pt2 + ")"
			c.execute(query_pt1 + query_pt2)

		conn.commit()


	def create_id(self,prod_id):
		date = datetime.datetime.now()
		date = date.strftime("%m/%d/%Y")
		self.data[prod_id] = {'date':date, 'upc':None, 'manufacturer':None, 
		'product':None,
		'model':None, 'price':None, 'sale_price':None, 'in_stock':None, 
		'max_qty':None, 'seller':None, 'listings':None, 'arrives':None,
		'weight':None, 'reviews':None, 'rating':None}


	def add_ids(self,num_ids,query='drills'):
		return self.data


class AmazonScraper(GenericScraper):
		
	def __init__(self, db):
		super(AmazonScraper, self).__init__(db)
		self.data = {}
		self.base_url = 'https://www.amazon.com/'

	def get_page(self,url):
		rawpage = super(AmazonScraper,self).get_page(url)
		return str(rawpage)

	def search_url(self, query):
		url =  self.base_url + 's?k=%s&s=%s'%(query,'salesrank')
		return url

	def prod_url(self, prod_id):
		return  self.base_url + 'dp/'+prod_id


	def add_ids(self,num_ids,query='drills'):
		url = self.search_url(query)
		rawtext = self.get_page(url)
		tree = html.fromstring(rawtext)
		search_rows = tree.xpath("//*[@class='s-result-list s-search-results sg-row']")[0]
		asins = []
		i=0
		while( i < len(search_rows) and  len(asins) < num_ids ):
			if not ('AdHolder' in search_rows[i].attrib['class']) and search_rows[i].attrib['data-asin'] !='':
				asins.append(search_rows[i].attrib['data-asin'])
			i=i+1
		for asin in asins:
			if asin not in self.data.keys():
				self.create_id(asin)
		return self.data


	def amazon_table(self, tree,key):
		table =  tree.xpath("//*[@id='%s']"%key)[0]
		table = pd.read_html(etree.tostring(table , encoding='utf8', method='html'))[0]
		table = table.applymap(lambda s: s[3:-2]) #clean things up
		table = table.set_index(0)
		return table
		

	def get_data(self, asin):
		if asin not in self.data.keys():
			self.create_id(asin)

		url =  self.prod_url(asin)
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
		self.data[asin]['model'] = model
		self.data[asin]['manufacturer'] = manuf.text
		return self.data[asin]


	def lookup_upc(self, prod_id):

		data = self.get_data(prod_id)
		brand = data['manufacturer']
		item  = data['model']
		#TODO: write data that i'm getting outside of this...
		#TODO: make this part of the generic class
		url = 'https://www.upcitemdb.com/upc/%s %s'%(brand,item)
		url = url.replace(' ', '%20')
		rawtext = self.get_page(url)
		tree = html.fromstring(rawtext)
		link_cand = tree.xpath("//*[@class='rImage']")
		#TODO: go for top 3 items instead
		if len(link_cand)  == 0 :
			return None
		self.data[prod_id]['upc'] = link_cand[0][0].text
		return link_cand[0][0].text



	def lookup_id(self, upc):
		#TODO: save some of this data since i have it
		#TODO: make an extra query to amazon using the product names?
		url = 'https://www.upcitemdb.com/upc/' + upc
		rawtext = self.get_page(url)
		tree = html.fromstring(rawtext)
		table = tree.xpath("//*[@class='detail-list']")
		if len(table) == 0:
			return None
		table = table[0]
		table = pd.read_html(etree.tostring(table, encoding='utf8', method='html'))[0]
		table = table.set_index(0)
		if  'Amazon ASIN:' in (table.index):
			asin = table.loc['Amazon ASIN:'][1]
			self.create_id(asin)
			self.data[asin]['upc'] = upc
			return asin
		return None



class WalmartScraper(GenericScraper):


	def __init__(self, db):
		super(WalmartScraper, self).__init__(db)
		self.base_url = 'https://www.walmart.com/'


	def get_page(self,url):
		rawpage = super(WalmartScraper,self).get_page(url)
		return rawpage.decode()


	def search_url(self, query):
		url =  self.base_url + 'search/?cat_id=0&query=%s&sort=%s'%(query,'best_seller')
		return url

	def prod_url(self, prod_id):
		url =  self.base_url + 'ip/' + prod_id
		return url


	def add_ids(self,num_ids,query='drills'):
		url = self.search_url(query)
		rawtext1 = self.get_page(url)
		tree = html.fromstring(rawtext1)

		link_cand = tree.xpath("//*[@id='searchContent']")
		if len(link_cand) ==0:
			return []
		link_cand = link_cand[0]
		datastore = json.loads(link_cand.text)
		items = datastore['searchContent']['preso']['items']
		i=0
		prod_ids = []
		while i < len(items) and  len(prod_ids) < num_ids:
			prod_ids.append(items[i]['productId'])
			i = i+1
		for prod_id in prod_ids:
			if prod_id not in self.data.keys():
				self.create_id(prod_id)
		return self.data


	def lookup_id(self, upc):
		ids = self.add_ids(1,query=upc)
		for key in self.data.keys():
			if self.data[key]['upc'] == upc:
				return key
		return None


	def lookup_upc(self, prod_id):
		if prod_id not in self.data.keys():
			self.create_id(prod_id)

		url = self.prod_url(prod_id)
		rawtext = self.get_page(url)
		tree = html.fromstring(rawtext)
		upc_data = tree.xpath("//*[@id='item']")
		if len(upc_data) ==0:
			return None

		upc_data = upc_data[0]

		#TODO: write a function to take care of this problem...
		datastore = json.loads(upc_data.text)
		
		#deal with this craziness that is walmart's db
		try:
			keyinfo = datastore['item']['product']['products']
			real_id= list(keyinfo.keys())[0]
			upc =   keyinfo[real_id]['upc']
			self.data[prod_id]['upc'] = upc
			return upc

		except KeyError:
			upc = datastore['item']['product']['buyBox']['products'][0]['upc']
			self.data[prod_id]['upc'] = upc
			return upc

		except KeyError:
			pass

		return None





if __name__ == '__main__':

	am_scrap = AmazonScraper('db/')
	print(am_scrap.lookup_upc('B006V6YAPI'))
	#print(am_scrap.lookup_upc('303303799'))
	#print(am_scrap.lookup_id('889526116651'))
	print(am_scrap.data)
	am_scrap.add_ids(3)
	print(am_scrap.data)
	am_scrap.write_data()
	#wal_scrap = WalmartScraper('db/')
	#print(wal_scrap.lookup_upc('6JIWA4VQNBON'))
