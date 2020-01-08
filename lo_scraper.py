from gen_scraper import *
from selenium.common.exceptions import TimeoutException
import random

class LowesScraper(GenericScraper):

    def __init__(self,*args, **kwargs):
        kwargs['url'] = 'https://www.lowes.com/'
        kwargs['platform'] = 'LOW'
        self.store = {'store_address':None, 'store_zip':None}
        super(LowesScraper, self).__init__(*args, **kwargs)


    def get_page(self,url):
        rawpage = super(LowesScraper,self).get_page(url)
        return rawpage

    def set_location(self,driver,retry=20):
        print('yo')
        if retry <= 0:
            return
        try:
            driver.set_page_load_timeout(10)
            urls = ['https://www.lowes.com/pd/BLACK-DECKER-20-Volt-Max-3-8-in-Cordless-Drill-Charger-Included/999982360',
            'https://www.lowes.com/pd/DEWALT-20-Volt-Max-1-2-in-Brushless-Cordless-Drill-Charger-Included/1000135807',
            'https://www.lowes.com/pd/CRAFTSMAN-V20-20-Volt-Max-1-2-in-Cordless-Drill-Charger-Included/1000552951' ]
            driver.get(urls[random.randint(0,2)])

            if driver.page_source.find('Forbidden') > 0:
                time.sleep(5)
                set_location(self,driver,retry=retry-1)
                return

        except TimeoutException:
            driver.execute_script("window.stop();")

        try:
            driver.find_element(By.CSS_SELECTOR, ".find-store-copy").click()
            time.sleep(5)
            driver.find_element(By.ID, "search-box").click()
            time.sleep(2)
            driver.find_element(By.ID, "search-box").send_keys(self.location)
            driver.find_element(By.CSS_SELECTOR, ".btn-default").click()
            time.sleep(5)
            address = driver.find_element(By.XPATH, '//*[@class="art-fsp-storeAddressBlk0"]').text
            address = str(address).replace('\n', ', ')
            self.store['store_address'] = address
            self.store['store_zip'] = self.location
            driver.find_element(By.CSS_SELECTOR, ".art-fsp-shopThisStoreBtn0").click()

        except TimeoutException:
            driver.execute_script("window.stop();")
            return 

        except Exception as e:
            print(e)
            self.set_location(driver,retry=retry-1)


    def search_url(self, keywords, page, sort='sortBy_bestSellers'):
        final_query = self.format_query(keywords)
        page = (page-1)*36
        url =  self.base_url + 'search?searchTerm=%s&sortMethod=%s'%(final_query,sort)
        if page > 1:
            url = url + '&offset=' + page
        return url

    def prod_url(self, prod_id):
        #look up product name
        prod_name = ''
        url =  self.base_url + 'search?searchTerm=' + prod_id
        return url

    def get_model(self,item,index):
        model = self.search_xpath(item,'plp__model')
        if len(model) > index:
            model = str(model[index].text)
            model = model[model.find('Model#') +8:]
            model = model[:model.find('\n')]
            return model
        return None


    def get_data(self,prod_id):
        url = self.prod_url(prod_id)
        print(url)
        rawtext =''

        if self.test_file is None:
            rawtext = self.get_page(url)
            f= open('tests/test_lo2.txt','w+')
            f.write(rawtext)
            f.close()
        else:
            f = open(test_file,'r')
            rawtext = f.read()
        #print(rawtext)
        tree = html.fromstring(rawtext)


        self.data[prod_id]['manufacturer'] = tree.xpath('//*[@itemprop="brand"]')[0].attrib['content']
        self.data[prod_id]['product'] = tree.xpath('//meta[@itemprop="name"]')[0].attrib['content']
        self.data[prod_id]['model'] = tree.xpath('//span[@class="met-product-model"]')[0].text
        price = tree.xpath('//span[@class="primary-font jumbo strong art-pd-contractPricing"]')[0][0]
        price =  str(etree.tostring(price))
        price = price[price.find('sup>')+4:-1]
        self.data[prod_id]['price'] = float(price)


        try:
            self.data[prod_id]['price'] = float(tree.xpath('//span[@class="secondary-text small-type art-pd-wasPriceLbl"]')[0].text)
        except:
            pass

        store_stock = tree.xpath('//p[@class="gauge-pickup"]')[0]
        store_stock = str(etree.tostring(store_stock)).replace(' ', '')
        store_stock = store_stock[store_stock.find('\\n')+3:]
        print(store_stock)

        store_stock = int(store_stock[:store_stock.find('available')])
        print(store_stock)
        self.data[prod_id]['store_stock'] = store_stock

        #'product':None,
        #'manufacturer':None, 'model':None, 'price':None, 'list_price':None, 'in_stock':None, 
        #'max_qty':None, 'seller':None, 'arrives':None,
        #'shipping':None, 'shipping_price':None, 'shipping_options':None,
        #'store_stock':None,'store_address':None, 'store_zip':None, 'store_price':None,
        #'weight':None, 'reviews':None, 'rating':None,
        #'quantity1':None, 'quantity2':None, 'quantity3':None, 'quantity4':None, 'ads':None}




        return self.data[prod_id]



    def add_ids(self, num_ids, lookup=False, keywords=None, page=1):
        if keywords is None:
            keywords = [self.query]
       
        search_rank = 1
        prod_ids = []
        max_page = 2 if lookup else 5

        while page < max_page and search_rank <= num_ids:

            url = self.search_url(keywords, page , sort='') if lookup else self.search_url(keywords, page)
            print(url)
            rawtext =''
            if self.test_file is None:
                rawtext = self.get_page(url)
                time.sleep(5)
                print(rawtext.find('863707'))
                f= open('tests/test_lo1.txt','w+')
                f.write(rawtext)
                f.close()
            else:
                f = open(test_file,'r')
                rawtext = f.read()
            tree = html.fromstring(rawtext)
            items = tree.xpath('//*[@class="art-pl-itemNum art-sr-itemNum"]')
            models = tree.xpath('//*[@class="art-pl-modelNum art-sr-modelNum"]') 
            
            ratings = tree.xpath('//*[@class="product-rating v-spacing-small"]')  

            if len(items) == 0:
                return []

            index = 0
            while index < len(items) and  search_rank <= num_ids:

                prod_id = items[index].text[1:]
                title =   models[index].text[1:]

                found_product = not lookup

                if not found_product:
                    in_name = True #get the product name
                    
                    manuf,model = keywords[0], keywords[0]
                    if len(keywords) >1:
                        manuf,model= keywords[0],keywords[1]
                    
                    in_name = model is not None and title is not None and title.find(model) >= 0  # and title.find(manuf) >= 0

                    if in_name:
                        found_product = True
                
                
                if found_product:
                    prod_ids.append(prod_id)
                    if prod_id not in self.data.keys():
                        pass
                        self.create_id(prod_id)
                        self.data[prod_id]['query'] = url
                        self.data[prod_id]['rank'] = 0 if lookup else search_rank
                        self.data[prod_id]['ads'] = 0
                        self.data[prod_id]['page'] = page
                        self.data[prod_id]['model'] = title
                        self.data[prod_id]['ratings'] =  ratings[index][0][0][0].attrib['data-rating']
                        self.data[prod_id]['reviews'] = int(ratings[index][0][1].text[1:-1])

                        #seems like all data is on search results
                    
                search_rank = search_rank +1
                index = index +1
            page = page+1

        return prod_ids



if __name__ == '__main__':
    test = True
    if test:
        test_file = 'tests/test_lo2.txt'
        scrap = LowesScraper('db/',test_file=test_file)
        #print(scrap.add_ids(24))
        #print(scrap.data)
        scrap.get_data(test_file)
        print(scrap.data)
        #scrap.write_data()
        #print(scrap.data[ list(scrap.data.keys())[1]])
        

    if not test:   
        scrap = LowesScraper('db/')
        scrap.add_ids(1)

        #scrap.create_id("797394")
        #print(scrap.lookup_id(('BLACK+DECKER','LD120VA')))
        #print(scrap.lookup_id(('Hyper Tough','AQ75023G')))
        #print(scrap.lookup_id(('DEWALT','DCD777C2')))
        #scrap.write_data()
        #scrap.end_scrape()