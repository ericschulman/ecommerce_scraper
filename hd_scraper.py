from gen_scraper import *
from selenium.common.exceptions import TimeoutException

class HomeDepotScraper(GenericScraper):

    def __init__(self,*args, **kwargs):
        kwargs['url'] = 'https://www.homedepot.com/'
        kwargs['platform'] = 'HD'
        self.store = {'store_address':None, 'store_zip':None}
        super(HomeDepotScraper, self).__init__(*args, **kwargs)


    def get_page(self,url):
        rawpage = super(HomeDepotScraper,self).get_page(url)
        return rawpage

    def set_location(self,driver,retry=20):
        return driver
        if retry <= 0:
            return driver
        try:
            driver.get("https://www.homedepot.com/")
            driver.find_element(By.XPATH, '//*[@class="MyStore__label"]').click()
            driver.find_element(By.XPATH, '//*[@class="MyStore__store"]').click()
            driver.find_element(By.XPATH, '//*[@class="MyStore__label"]').click()
            driver.find_element(By.XPATH, '//*[@class="MyStore__store"]').click()
            time.sleep(5)
            driver.find_element(By.XPATH, '//*[@class="bttn__content" and text()="Find Other Stores"]').click()
            time.sleep(2)
            driver.find_element(By.ID, "txtStoreFinder").click()
            driver.find_element(By.ID, "txtStoreFinder").click()
            driver.find_element(By.ID, "txtStoreFinder").send_keys(self.location)
            driver.find_element(By.CSS_SELECTOR, ".icon-search").click()
            time.sleep(2)
            #get data from store
            self.store['store_address'] = driver.find_element(By.CSS_SELECTOR, ".sfStoreRow:nth-child(1) .street-address").text +', '
            self.store['store_address'] = self.store['store_address'] + driver.find_element(By.CSS_SELECTOR, ".sfStoreRow:nth-child(1) .locality").text +', '
            self.store['store_address'] = self.store['store_address'] + driver.find_element(By.CSS_SELECTOR, ".sfStoreRow:nth-child(1) .region").text
            self.store['store_zip'] = driver.find_element(By.CSS_SELECTOR, ".sfStoreRow:nth-child(1) .postal-code").text
            driver.find_element(By.CSS_SELECTOR, ".sfStoreRow:nth-child(1) .bttn__content").click()
        except Exception as e:
            print(e)
            return self.set_location(driver,retry=retry-1)
        return driver


    def search_url(self, keywords, page, sort='&Ns=P_Topseller_Sort|1'):
        final_query = self.format_query(keywords)
        page = (page-1)*24
        url =  self.base_url + 's/%s?isSearch=true&Nao=%s%s'%(final_query,page,sort)
        return url

    def prod_url(self, prod_id):
        url =  self.base_url + 'p/' + prod_id
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
        #return self.data[prod_id]
        url = self.prod_url(prod_id)
        rawtext =''

        if self.test_file is None:
            rawtext = self.get_page(url)
        else:
            f = open(test_file,'r')
            rawtext = f.read()

        tree = html.fromstring(rawtext)
        #weight
        weight = tree.xpath('//*[@itemprop="weight"]')
        if len(weight) > 0:
            self.data[prod_id]['weight'] = float(weight[0].text[:-2])
        
        return self.data[prod_id]


    def get_shipping(self, item, index, prod_id):
        #shipping
        shipping = item.xpath( '//*[@class="pod-plp__shipping-message__wrapper-boss-bopis "]')
        if len(shipping) > index:
            if str(shipping[index][0][0].text).find('d') < 0:
                self.data[prod_id]['shipping'] = shipping[index][0][0][0].text
            else:
                self.data[prod_id]['shipping'] = shipping[index][0][0].text

        pickup = item.xpath( '//*[@class="pod-plp__fulfillment-message__wrapper-boss-bopis "]')
        store_stock = []
        if len(pickup) > index:
            pickup = etree.fromstring(etree.tostring(pickup[index])) #must be a better way to do this...
            store_stock = pickup.xpath( '//*[@class="Inventory-Stock__wrapper"]' )

            if len(store_stock) > 0:
                store_stock = str(etree.tostring(store_stock[0]))
                store_stock = store_stock[store_stock.find('<span>')+6:store_stock.find('</span>')]
                self.data[prod_id]['quantity1'] = int(store_stock)

            messages = ['Unavailable at your store','Limited stock','Free ship to store for pickup']
            for message in messages:
                message_disp = self.search_xpath(pickup,message)
                if len(message_disp) > 0:
                    self.data[prod_id]["store_stock"] = message_disp[0].text



        
        #limited stock
        #in store pickup

    def get_data_results(self, item, index, prod_id):
        self.data[prod_id]['store_address'] = self.store['store_address']
        self.data[prod_id]['store_zip'] = self.store['store_zip']

        manuf = self.search_xpath(item,'pod-plp__brand-name')
        if len(manuf) > index:
            self.data[prod_id]['manufacturer'] = str(manuf[index].text)


        self.data[prod_id]['model'] = self.get_model(item,index)

        main_info = self.search_xpath(item,'productlist plp-pod__compare')
        if len(main_info)> index:
            main_info = main_info[index][0][0]
            self.data[prod_id]['product'] = main_info.attrib['data-title']
            if 'data-was-price' in main_info.attrib.keys():
                self.data[prod_id]['list_price'] = float(main_info.attrib['data-was-price'][1:])
                self.data[prod_id]['price'] = float(main_info.attrib['data-price'][1:])
            else:
                self.data[prod_id]['price'] = float(main_info.attrib['data-price'][1:])
        
        limited_q = str(etree.tostring(item))

        if limited_q.find(' per order') > 0:
            limited_q = int(limited_q[limited_q.find('Limit ')+6:limited_q.find(' per order')])
            self.data[prod_id]['quantity2'] = limited_q

        ratings = self.search_xpath(item,'out of 5 stars')
        
        if len(ratings) > index:
            self.data[prod_id]['rating'] = float(ratings[index].attrib['rel'])

        reviews = self.search_xpath(item,'#customer_reviews')
        if len(reviews) > 2*index +1:
            reviews = str(reviews[2*index+1].text)
            reviews = reviews[reviews.find('(')+1:reviews.find(')')]
            self.data[prod_id]['reviews'] = int(reviews)



    def add_ids(self, num_ids, lookup=False, keywords=None, page=1):
        if keywords is None:
            keywords = [self.query]
       
        search_rank = 1
        prod_ids = []
        max_page = 2 if lookup else 5

        while page < max_page and search_rank <= num_ids:

            url = self.search_url(keywords, page , sort='') if lookup else self.search_url(keywords, page)
            rawtext =''
            if self.test_file is None:
                rawtext = self.get_page(url)
            else:
                f = open(test_file,'r')
                rawtext = f.read()

            tree = html.fromstring(rawtext)
            items = tree.xpath('//*[@data-component="productpod"]')
            if len(items) == 0:
                return []

            index = 0
            while index < len(items) and  search_rank <= num_ids:

                prod_id = items[index].attrib['data-productid']
                found_product = not lookup

                if not found_product:
                    in_name = True #get the product name
                    
                    manuf,model = keywords[0], keywords[0]
                    if len(keywords) >1:
                        manuf,model= keywords[0],keywords[1]
                    
                    title =  self.get_model(items[index],index)

                    in_name = model is not None and title is not None and title.find(model) >= 0  # and title.find(manuf) >= 0

                    if in_name:
                        found_product = True
                
                
                if found_product:
                    prod_ids.append(prod_id)
                    if prod_id not in self.data.keys():
                        self.create_id(prod_id)
                        self.data[prod_id]['query'] = url
                        self.data[prod_id]['rank'] = 0 if lookup else search_rank
                        self.data[prod_id]['ads'] = 0
                        self.data[prod_id]['page'] = page

                        #seems like all data is on search results
                        self.get_data_results(items[index],index, prod_id)
                        self.get_shipping(items[index], index, prod_id)
                    
                search_rank = search_rank +1
                index = index +1
            page = page+1

        return prod_ids



if __name__ == '__main__':
    test = False
    if test:
        test_file = 'tests/test_hd1.txt'
        scrap = HomeDepotScraper('db/',test_file=test_file)
        #scrap.add_ids(24)
        scrap.get_data(test_file)
        #scrap.write_data()
        #print(scrap.data[ list(scrap.data.keys())[1]])
        

    if not test:   
        scrap = HomeDepotScraper('db/')
        #scrap.add_ids(10)
        #print(scrap.lookup_id(('BLACK+DECKER','LD120VA')))
        #print(scrap.lookup_id(('Hyper Tough','AQ75023G')))
        print(scrap.lookup_id(('DEWALT','DCD777C2')))
        #scrap.write_data()
        #scrap.end_scrape()