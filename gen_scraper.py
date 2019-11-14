import urllib
import lxml
from lxml import etree
from lxml import html
import pandas as pd
import json
import os
import sqlite3
import datetime
import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

class GenericScraper:

    def __init__(self, db, url='', platform='', query='drills',location = '78722', headless=False):
        self.counter = 0
        self.base_url = url
        self.db = db
        self.data = {}
        self.platform = platform
        self.query = query
        self.location = location
        self.headless = headless
        self.drivers = []
        for i in range(2):
            self.add_driver()
        
        #create the database if it is not there
        if not os.path.isfile(db+'scrape.db') :
            f = open(db+'scrape.sql','r')
            sql = f.read()
            con = sqlite3.connect(db + 'scrape.db') #create the db
            cur = con.cursor()
            cur.executescript(sql)
            con.commit()

    def end_scrape(self):
        for driver in self.drivers:
            driver.quit()

    def set_location(self,driver):
        pass

    def add_driver(self):
        opts = Options()
        if self.headless:
           opts.set_headless()
        driver = webdriver.Firefox(options=opts)
        self.set_location(driver)
        self.drivers.append(driver)


    def get_page(self, url):
        self.counter = self.counter +1
        driver = self.drivers[self.counter%2]
        driver.get(url)
        rawtext = driver.page_source
        return rawtext

    def format_query(self, keywords):
        assert type(keywords) == list

        formated_string =keywords[0].replace(' ','%20') if keywords[0] is not None else ''
        final_query = formated_string
        for s in keywords[1:]:
            formated_string  = '%20' + s.replace(' ','%20') if s is not None else ''
            final_query = final_query + formated_string
        return final_query

    def search_url(self, keywords, page, sort=''):
        return ''

    def prod_url(self, prod_id):
        return ''

    def lookup_product(self,prod_id):
        if prod_id not in self.data.keys():
            self.create_id(prod_id)
        return self.data[prod_id]['manufacturer'], self.data[prod_id]['model']

    def set_query(self, query):
        self.query = query

    def lookup_id(self, product):
        manuf, model = product
        prod_ids = self.add_ids(4, keywords=[manuf,model,self.query], lookup = True)
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
        prod_ids = self.add_ids(1,keywords=[upc], lookup =True )
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
        self.data[prod_id] = {'platform':self.platform, 'website':self.base_url, 'zipcode':self.location,
        'date':date, 'rank':None ,'page':None ,  'upc':None, 'query':None,'product':None,
        'manufacturer':None, 'model':None, 'price':None, 'list_price':None, 'in_stock':None, 
        'max_qty':None, 'seller':None, 'arrives':None,
        'shipping':None, 'shipping_price':None, 'shipping_options':None,
        'store_pickup':None,'store_address':None, 'store_zip':None, 'store_price':None,
        'weight':None, 'reviews':None, 'rating':None,
        'quantity1':None, 'quantity2':None, 'quantity3':None, 'quantity4':None, 'ads':None}
        self.get_data(prod_id)


    def add_ids(self, num_ids, lookup=True, keywords=None):
        return []