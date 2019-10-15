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
                    print(err.headers)
                    time.sleep(20)

        empty = b'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css"><script src="script.js"></script></head></html>'
        return empty


    def search_url(self, query):
        return ''

    def prod_url(self, prod_id):
        return ''

    def lookup_upc(self, prod_id):
        if prod_id not in self.data.keys():
            self.create_id(prod_id)
        return self.data[prod_id]['upc']

    def lookup_id(self, upc):
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
                    query_pt2 = query_pt2 + ",'%s'"%(self.data[key][sub_key]).replace('\\','')
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
        self.data[prod_id] = {'date':date, 'upc':None, 'manufacturer':None, 
        'product':None,
        'model':None, 'price':None, 'list_price':None, 'in_stock':None, 
        'max_qty':None, 'seller':None, 'listings':None, 'arrives':None,
        'weight':None, 'reviews':None, 'rating':None}
        self.get_data(prod_id)


    def add_ids(self,num_ids,query='drills'):
        return []


class AmazonScraper(GenericScraper):
        
    def __init__(self, db):
        super(AmazonScraper, self).__init__(db)
        self.data = {}
        self.base_url = 'https://www.amazon.com/'

    def get_page(self,url):
        rawpage = ''
        for i in range(20):
            rawpage = super(AmazonScraper,self).get_page(url)
            if str(rawpage).find('not a robot. For best results, please make sure your browser is accepting cookies.') < 0:
                rawpage = str(rawpage)
                return str(rawpage)
        return rawpage
        

    def search_url(self, query,page):
        url =  self.base_url + 's?k=%s&s=%s&page=%s'%(query,'salesrank',page)
        return url

    def prod_url(self, prod_id):
        return  self.base_url + 'dp/'+prod_id


    def add_ids(self,num_ids,query='drills'):
        asins = []
        for page in range(10):
            if len(asins) > num_ids:
                print(num_ids,len(asins))
                break
            
            url = self.search_url(query,page)
            rawtext = self.get_page(url)
            tree = html.fromstring(rawtext)
            search_rows = tree.xpath("//*[@class='s-result-list s-search-results sg-row']")

            for row in search_rows:

                if len(asins) > num_ids:
                    break
                
                i = 0
                while( i < len(row) and  len(asins) < num_ids ):
                    if 'class' in dict(row[i].attrib).keys() and 'data-asin' in dict(row[i].attrib).keys():
                        if not ('AdHolder' in row[i].attrib['class']) and row[i].attrib['data-asin'] !='':
                            asins.append(row[i].attrib['data-asin'])
                    i=i+1

        for asin in asins:
            if asin not in self.data.keys():
                self.create_id(asin)
        return asins


    def amazon_table(self, tree,key):
        table =  tree.xpath("//*[@id='%s']"%key)
        if table == []:
            return None
        table = table[0]
        table = pd.read_html(etree.tostring(table , encoding='utf8', method='html'))[0]
        table = table.applymap(lambda s: s.replace('\\n','').replace('\\t','').replace('  ', '')) #clean things up
        table = table.set_index(0)
        return table
        
        

    def get_data(self, asin):

        url =  self.prod_url(asin)
        rawtext = self.get_page(url)
        tree = html.fromstring(rawtext)

        #'product':None,
        product = tree.xpath("//*[@id='productTitle']")
        if product !=[]:
            product = product[0].text
            product = product.replace('\\n','').replace('  ', '')
            self.data[asin]['product'] = product
        
        #sale price
        list_price = tree.xpath("//*[@class='priceBlockStrikePriceString a-text-strike']")
        if list_price != []:
            self.data[asin]['list_price'] = float(list_price[0].text[2:])
            
        #price
        price = tree.xpath("//*[@id='base-product-price']")
        if price != []:
            self.data[asin]['price'] = float(price[0].attrib['data-base-product-price'][1:])
        if price == []:
            price = tree.xpath("//*[@id='priceblock_ourprice']")
            if price != []:
                self.data[asin]['price'] = float(price[0].text[1:])
        if price == []:    
            price = tree.xpath("//*[@id='priceblock_saleprice']")
            if price != []:
                self.data[asin]['price'] = float(price[0].text[1:])
        
        #'in_stock' 
        stock = tree.xpath("//*[@id='availability']")
        if stock != []:
            stock = str(etree.tostring(stock[0]))
            self.data[asin]['in_stock']= int(stock.find('In Stock.') >= 0 )
      
        #'seller' 
        seller = tree.xpath("//*[@id='comparison_sold_by_row']")
        if seller != []:
            self.data[asin]['seller'] = seller[0][1][0].text
        
        #'listings'
        listings = self.search_xpath(tree,'mbc-upd-olp-link')
        if listings !=[]:
            listings = str(etree.tostring(listings[0]))
            ind1, ind2 = listings.find('('),listings.find(')')
            self.data[asin]['listings']= int(listings[ind1+1:ind2])
    
        #'arrives'
        arrives =  self.search_xpath(tree,'Two-Day Shipping')
        if arrives != []:
            date = datetime.datetime.now() + datetime.timedelta(days=1)
            self.data[asin]['arrives'] = self.to_epoch_time(date)
        
        #'rating'
        ratings = tree.xpath("//*[@id='acrPopover']")
        if ratings !=[]:
            self.data[asin]['rating'] = float(ratings[0].attrib['title'][:3])
        
        #'reviews'
        reviews = tree.xpath("//*[@id='acrCustomerReviewText']")
        if reviews !=[]:
            reviews = reviews[0].text
            reviews = reviews[:reviews.find(' ')]
            reviews = reviews.replace(',','')
            self.data[asin]['reviews'] = int(reviews)
        
        #manufactuer
        manuf = tree.xpath("//*[@id='bylineInfo']")
        if manuf != []:
            self.data[asin]['manufacturer'] = manuf[0].text
        else:
            print('no manuf %s'%asin)
        
        #model number
        table1 =  self.amazon_table(tree,'productDetails_techSpec_section_1')
        if  table1 is not None and ' Part Number' in list(table1.index):
            model = table1.loc[' Part Number'][1]
            self.data[asin]['model'] = model
            
        elif table1 is not None and ' Item model number' in list(table1.index):
            model = table1.loc[' Item model number'][1]
            self.data[asin]['model'] = model
        
        #'weight'
        table2 = self.amazon_table(tree,'productDetails_detailBullets_sections1')
        if table2 is not None and ' Shipping Weight' in list(table2.index):
            weight = table2.loc[' Shipping Weight'][1][1:]
            weight = weight[:weight.find(' ')]
            self.data[asin]['weight'] = float(weight)
            
        #'max_qty'
        dropdowns = tree.xpath("//*[@class='a-dropdown-container']")
        if dropdowns != []:
            for drop in dropdowns:
                if 'for' in drop[0].attrib and drop[0].attrib['for'] == 'quantity':
                    self.data[asin]['max_qty'] = len(drop[1])
        
        return self.data[asin]


    def lookup_upc(self, prod_id):

        data = self.data[prod_id]
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
            prod_ids.append(items[i]['usItemId'])
            i = i+1
        for prod_id in prod_ids:
            if prod_id not in self.data.keys():
                self.create_id(prod_id)
        return prod_ids


    def get_data(self, prod_id):
        url = self.prod_url(prod_id)
        rawtext = self.get_page(url)
        tree = html.fromstring(rawtext)
        upc_data = tree.xpath("//*[@id='item']")
        if len(upc_data) ==0:
            return None

        upc_data = upc_data[0]
        datastore = json.loads(upc_data.text)
        
        #get weight
        try:
            prod_info = list(datastore['item']['product']['idmlMap'].values())[0]
            prod_info = prod_info['modules']['Specifications']['specifications']['values'][0]
            for column in prod_info:
                if 'assembled_product_weight' in column.keys():
                    weight = column['assembled_product_weight']['displayValue']
                    weight = weight[:weight.find(' ')]
                    self.data[prod_id]['weight'] = float(weight)
        except:
            weight = self.search_xpath(tree,' lbs')
            for w in weight:
                try:
                    weight = weight[0]
                    self.data[prod_id]['weight'] = float(weight[:weight.find(' ')])
                except:
                    pass

        
        #get other stuff
        try:
            
            data = datastore['item']['product']['buyBox']['products'][0]
            walmart_names = ['upc','brandName','productName', 'model', 'reviewsCount', 'averageRating',
                             'maxQuantity','sellerDisplayName']
            my_names = ['upc','manufacturer','product','model','reviews','rating','max_qty', 'seller']
                
            try:
                self.data[prod_id]['in_stock']  = int(data['shippable'])
                for key in ['earliestDeliverDate','exactDeliveryDate']:
                    if key in data['shippingOptionToDisplay']['fulfillmentDateRange'].keys():
                        ship_date = data['shippingOptionToDisplay']['fulfillmentDateRange'][key]
                        self.data[prod_id]['arrives'] =  int(ship_date) 
            except KeyError:
                print('no shipping ' + prod_id)
                
                
            for i in range(len(walmart_names)):
                if walmart_names[i] in data.keys():
                    self.data[prod_id][my_names[i]] = data[walmart_names[i]]
                    
            #pricing data
            if 'priceMap' in data.keys():
                for key in ['price','currentPrice']:
                    if key in data['priceMap'].keys():
                        self.data[prod_id]['price'] = data['priceMap'][key]
                for key in ['wasPrice','listPrice']:
                    if key in data['priceMap'].keys():
                        self.data[prod_id]['list_price'] = data['priceMap'][key]
                
            
        except KeyError:
            pass
        return self.data[prod_id]



    def lookup_id(self, upc):
        prod_ids = self.add_ids(1,query=upc)
        if prod_ids != []:
            self.data[prod_ids[0]]['upc'] = upc
            return prod_ids[0]
        return None



if __name__ == '__main__':

    scrap = AmazonScraper('db/')
    for i in range(50):
    
        url = 'https://www.upcitemdb.com/upc/' +str(i) + '%20' + 'cheese'
        page = scrap.get_page(url)
        print(i,str(page)[0:100])

    #scrap.write_data()
