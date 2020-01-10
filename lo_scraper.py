from gen_scraper import *
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
import random
from selenium import webdriver

class LowesScraper(GenericScraper):

    def __init__(self,*args, **kwargs):
        kwargs['url'] = 'https://www.lowes.com/'
        kwargs['platform'] = 'LOW'
        self.store = {'store_address':None, 'store_zip':None}
        super(LowesScraper, self).__init__(*args, **kwargs)


    def set_location(self,driver,retry=20):
        if retry <= 0:

            return driver
        try:
            driver.set_page_load_timeout(10)
            urls = ['https://www.lowes.com/pd/BLACK-DECKER-20-Volt-Max-3-8-in-Cordless-Drill-Charger-Included/999982360',
                'https://www.lowes.com/pd/DEWALT-20-Volt-Max-1-2-in-Brushless-Cordless-Drill-Charger-Included/1000135807',
                'https://www.lowes.com/pd/Rain-X-Latitude-28-Wiper-Blade/3472541',
                'https://www.lowes.com/pd/Pedigree-17-9-lbs-Healthy-Puppies-Dog-Food/3530418' ] #land on a random page
            index = retry%4
            driver.get(urls[index])

            if driver.page_source.find('Access Denied') > 0:
                print('Access denied')
                driver.close()                 #make a new driver
                opts = Options()
                if self.headless:
                    opts.set_headless()
                driver = webdriver.Firefox(options=opts, executable_path=self.geckodriver_path)
                return self.set_location(driver,retry=retry-1)

        except TimeoutException:
            driver.execute_script("window.stop();")

        try:
            driver.find_element(By.CSS_SELECTOR, ".find-store-copy").click()
            time.sleep(4)
            driver.find_element(By.ID, "search-box").click()
            time.sleep(2)
            driver.find_element(By.ID, "search-box").send_keys(self.location)
            driver.find_element(By.CSS_SELECTOR, ".btn-default").click()

            time.sleep(4)
            try:
                driver.find_element(By.XPATH, '//*[@class="btn-group centered art-fsp-mystoreLbl0"]').click()#.send_keys(Keys.ESCAPE)
                print('already set')
                webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                return driver
            except:
                address = driver.find_element(By.XPATH, '//*[@class="art-fsp-storeAddressBlk0"]').text
                address = str(address).replace('\n', ', ')
                self.store['store_address'] = address
                self.store['store_zip'] = self.location
                driver.find_element(By.CSS_SELECTOR, ".art-fsp-shopThisStoreBtn0").click()

        except TimeoutException:
            driver.execute_script("window.stop();")
            return driver

        except Exception as e:
            print(e)
            return self.set_location(driver,retry=retry-1)

        return driver


    def search_url(self, keywords, page, sort='sortBy_bestSellers'):
        final_query = self.format_query(keywords)
        page = (page-1)*36
        url =  self.base_url + 'search?searchTerm=' + final_query
        if sort !='':
            url = url + '&sortMethod=' + sort
        if page > 1:
            url = url + '&offset=' + str(page)
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
        #print(url)
        rawtext =''
        
        self.data[prod_id]['store_address'] = self.store['store_address']
        self.data[prod_id]['store_zip'] = self.store['store_zip']

        if self.test_file is None:
            rawtext = self.get_page(url)
        else:
            f = open(test_file,'r')
            rawtext = f.read()

        tree = html.fromstring(rawtext)
        redirect = tree.xpath('//*[@class="js-gauge-track-pdp product-title '+\
            'js-product-title met-product-title v-spacing-mini ellipsis-three-line art-plp-itemDescription"]')
        
        if len(redirect) == 0:
            pass
        else:
            #print( self.base_url[:-1]+ redirect[0].attrib['data-producturl'] )
            rawtext = self.get_page(self.base_url[:-1]+ redirect[0].attrib['data-producturl'])
            tree = html.fromstring(rawtext)

        #___________________________ price, listprice, manufacturer, model, product, below retail ___________________________
        try:
            price = tree.xpath('//span[@itemprop="price"]')[0].attrib['content']
            self.data[prod_id]['price'] = float(price)

            self.data[prod_id]['manufacturer'] = tree.xpath('//*[@itemprop="brand"]')[0].attrib['content']
            self.data[prod_id]['product'] = tree.xpath('//meta[@itemprop="name"]')[0].attrib['content']
            self.data[prod_id]['model'] = tree.xpath('//span[@class="met-product-model"]')[0].text

            #quantity2 - below retail
            q2 = self.search_xpath(tree,'View Price In Cart')
            if len(q2) > 0:
                self.data[prod_id]['quantity2'] = 1
            else:
                self.data[prod_id]['quantity2'] = 0
            
            list_price = tree.xpath('//span[@class="secondary-text small-type art-pd-wasPriceLbl"]')[0].text[len(' Was $'):]
            self.data[prod_id]['list_price'] = float(list_price)
        except:
            pass

        #___________________________ shipping information ___________________________
        try:
            stock = tree.xpath('//*[@class="fulfillment-method-body media"]')
            store_stock = stock[0].xpath('//*[@class="gauge-pickup"]') #quantity1 storestock

            if len(store_stock) == 0:
                self.data[prod_id]['quantity1'] = 0

            else:
                store_stock = str(etree.tostring(store_stock[0])).replace(' ', '')
                store_stock = store_stock[store_stock.find('\\n')+2:]
                store_stock = int(store_stock[:store_stock.find('available')])
                self.data[prod_id]['quantity1'] = store_stock

            in_stock = stock[1]
            in_stock = str(etree.tostring(in_stock))

            if in_stock.find('Currently unavailable') > 0:
                self.data[prod_id]['in_stock'] = 0
                self.data[prod_id]['shipping'] = 'Currently unavailable'
            elif in_stock.find('Available!') > 0:
                self.data[prod_id]['in_stock'] = 1
                self.data[prod_id]['shipping'] = 'Available!'

            elif in_stock.find('Delivery available') > 0:
                self.data[prod_id]['in_stock'] = 1
                self.data[prod_id]['shipping'] = 'Delivery available'
        except:
            pass

        #___________________________ weight ___________________________
        try:      
            weight = tree.xpath('//*[@class="table full-width no-borders"]')
            weight = str(etree.tostring(weight[0]))

            if weight.find('Weight (lbs.)') > 0:
                weight = weight[weight.find('Weight (lbs.)') +13:]
                weight = float(weight[weight.find('<span>')+6:weight.find('</span>')])
                self.data[prod_id]['weight'] = weight
        except:
            pass

        #___________________________ ratings, reviews ___________________________
        try:

            ratings = tree.xpath('//*[@class="js-average-rating"]')
            self.data[prod_id]['rating'] = float(ratings[0].text)

            reviews = tree.xpath('//*[@class="reviews-count art-pdp-lblTopRatingSummaryValue"]')[0]
            reviews = int(reviews.text[:-len(' Ratings')])
            self.data[prod_id]['reviews'] = reviews
        except:
            pass

        return self.data[prod_id]



    def add_ids(self, num_ids, lookup=False, keywords=None, page=1):
        if keywords is None:
            keywords = [self.query]
        if lookup:
            keywords = keywords[:-1]

        search_rank = 1
        prod_ids = []
        max_page = 2 if lookup else 5

        while page < max_page and search_rank <= num_ids:

            url = self.search_url(keywords, page , sort='') if lookup else self.search_url(keywords, page)
            #print(url)
            rawtext =''
            if self.test_file is None:
                rawtext = self.get_page(url)
                time.sleep(5)
            else:
                f = open(test_file,'r')
                rawtext = f.read()
            tree = html.fromstring(rawtext)
            items = tree.xpath('//*[@class="art-pl-itemNum art-sr-itemNum"]')
            models = tree.xpath('//*[@class="art-pl-modelNum art-sr-modelNum"]') 
            
            ratings = tree.xpath('//*[@class="product-rating v-spacing-small"]')  

            index = 0
            landed_page = lookup and len(items)==0 and len(self.search_xpath(tree,"t find any results for")) == 0
            while (index < len(items) or landed_page) and  search_rank <= num_ids:
                
                prod_id = ''
                title = ''
                #directly routed to page
                if landed_page:
                    prod_id = tree.xpath('//span[@class="met-product-item-number"]')[0].text
                    title = tree.xpath('//span[@class="met-product-model"]')[0].text
                    landed_page = False

                else:
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
                        #extra data
                        try:
                            self.data[prod_id]['model'] = title
                            self.data[prod_id]['rating'] =  ratings[index][0][0][0].attrib['data-rating']
                            self.data[prod_id]['reviews'] = int(ratings[index][0][1].text[1:-1])
                        except:
                            pass
                    
                search_rank = search_rank +1
                index = index +1
            page = page+1

        return prod_ids



if __name__ == '__main__':
    test = False
    if test:
        test_file = 'tests/test_lo1.txt'
        scrap = LowesScraper('db/',test_file=test_file)
        print(scrap.lookup_id(('BLACK+DECKER','LD120VA')))
        #print(scrap.add_ids(24))
        #print(scrap.data)
        #scrap.get_data(test_file)
        #print(scrap.data)
        #scrap.write_data()
        #print(scrap.data[ list(scrap.data.keys())[1]])
        

    if not test:   
        scrap = LowesScraper('db/',location = '78705')
        #scrap.add_ids(50)

        #scrap.create_id("918748")
        #print(scrap.lookup_id(('BLACK+DECKER','LD120VA')))
        #print(scrap.data)
        #print(scrap.lookup_id(('Hyper Tough','AQ75023G')))
        #print(scrap.lookup_id(('DEWALT','DCD777C2')))
        print(scrap.lookup_id(('DEWALT', 'DCK278C2')))
        #scrap.write_data()
        #scrap.end_scrape()