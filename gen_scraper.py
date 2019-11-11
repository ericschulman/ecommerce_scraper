import urllib
import lxml
from lxml import etree
from lxml import html
import pandas as pd
import json
import os
import sqlite3
import datetime
import time

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


    def __init__(self, db, main_query='drills'):
        self.counter = 0
        self.base_url = 'https://'
        self.db = db
        self.data = {}
        self.platform = ''
        self.main_query = main_query
        
        #create the database if it is not there
        if not os.path.isfile(db+'scrape.db') :
            f = open(db+'scrape.sql','r')
            sql = f.read()
            con = sqlite3.connect(db + 'scrape.db') #create the db
            cur = con.cursor()
            cur.executescript(sql)
            con.commit()

    def get_page(self, url):
        print(url)
        for i in range(5):
            try:    
                hdr = GenericScraper.hdrs[self.counter%2]
                page = urllib.request.Request(url, headers=hdr)
                response = urllib.request.urlopen(page)
                rawtext = response.read()
                return rawtext

            except urllib.error.HTTPError as err:
                print(err)
                if (err.code ==429):
                    print(err.headers, url)
                    time.sleep(20)

        empty = b'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css"><script src="script.js"></script></head></html>'
        return empty


    def format_query(self, query):
        formated_string =query[0].replace(' ','%20') if query[0] is not None else ''
        final_query = formated_string
        for s in query[1:]:
            formated_string  = '%20' + s.replace(' ','%20') if s is not None else ''
            final_query = final_query + formated_string
        return final_query

    def search_url(self, query, page, sort=''):
        return ''

    def prod_url(self, prod_id):
        return ''

    def lookup_product(self,prod_id):
        if prod_id not in self.data.keys():
            self.create_id(prod_id)
        return self.data[prod_id]['manufacturer'], self.data[prod_id]['model']

    def set_query(self,main_query):
        self.main_query = main_query

    def lookup_id(self, product):
        manuf, model = product
        prod_ids = self.add_ids(3, query=(manuf,model,self.main_query), lookup =True )
        print('yo2', prod_ids)
        if prod_ids != []:
            self.data[prod_ids[0]]['manufacturer'] = manuf
            self.data[prod_ids[0]]['model'] = model
            return prod_ids[0]
        return None


    def lookup_upc(self, prod_id):
        if prod_id not in self.data.keys():
            self.create_id(prod_id)
        return self.data[prod_id]['upc']

    def lookup_id_upc(self, upc):
        prod_ids = self.add_ids(1,query=(upc), lookup =True )
        if prod_ids != []:
            self.data[prod_ids[0]]['upc'] = upc
            return prod_ids[0]
        return None


    def get_data(self,prod_id):
        return self.data[prod_id]

    def to_epoch_time(self, date):
        epoch =  datetime.datetime.utcfromtimestamp(0)
        date = int((date - epoch).total_seconds() * 1000)
        return date


    def write_data(self):
        conn = sqlite3.connect(self.db + 'scrape.db')
        c = conn.cursor()
        for key in self.data.keys():
            query_pt1 = " INSERT INTO prices(website,prod_id"
            query_pt2 = " VALUES ('%s','%s'"%(self.base_url,key)
            for sub_key in self.data[key].keys():
                if self.data[key][sub_key] is not None:
                    query_pt1 = query_pt1 + "," + sub_key
                    query_pt2 = query_pt2 + ",'%s'"%(str(self.data[key][sub_key])).replace('\\','').replace("'","")
            query_pt1 = query_pt1 + ")"
            query_pt2 = query_pt2 + ")"
            try:
                c.execute(query_pt1 + query_pt2)
            except Exception as err:
                print(query_pt1 + query_pt2)
                print(err)

        conn.commit()


    def search_xpath(self,tree,query):
        return tree.xpath("//*[contains(text(), '%s') or @*[contains(., '%s')]]"%(query,query))


    def create_id(self,prod_id):
        date = datetime.datetime.now()
        date = self.to_epoch_time(date)
        self.data[prod_id] = {'platform':self.platform, 'website':self.base_url, 
        'date':date, 'rank':None ,'page':None ,  'upc':None, 'query':None,'product':None,
        'manufacturer':None, 'model':None, 'price':None, 'list_price':None, 'in_stock':None, 
        'max_qty':None, 'seller':None, 'arrives':None,
        'shipping':None, 'shipping_price':None,
        'weight':None, 'reviews':None, 'rating':None,
        'quantity1':None, 'quantity2':None, 'quantity3':None, 'ads':None}
        self.get_data(prod_id)


    def add_ids(self, num_ids, lookup=True, query=None):
        return []