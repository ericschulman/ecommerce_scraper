import urllib
import sqlite3
from lxml import etree
#conn = sqlite3.connect('example.db')


########## get list of products for each website#########
#scrape a list of product url's to visit from deal pages etc.

#####amazon
#searchbox amazon
'https://www.amazon.com/s?k=drills'
#searchbox walmart
'https://www.walmart.com/search/?query=drills'


#perhaps vary the header depending on what's going on...
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

#get a list of proxies too
#https://www.scrapehero.com/how-to-rotate-proxies-and-ip-addresses-using-python-3/
#https://free-proxy-list.net/



### Scrape data form an amazon page ####

#given an amazon page get asin, product
#look up manuctuer and part type in amazon page

#### scrape data from walmart page ##########

#### scrape data from home depot page #######



########given manufacturer and part type look up upc/asin ###################
'https://www.upcitemdb.com/upc/Ryobi%20P1810'
#for amazon, look up product's upc using website/other products try to get asin
#first get a list of products from deal pages
#look up upc and try to get comeptitiors listing
#look up competitors listing based on asin/upc

#put into page, and get asin and upc
#from the page get an additional entry with a new asin and upc


###########given upc look up asin##############
'https://www.upcitemdb.com/upc/0033287166039'


#############given upc look up on other vendors ######################


######given asin look up amazon listing############
#to get amazon page given asin is easy
'https://www.amazon.com/dp/'
#given part number and manufacturer search

