from gen_scraper import *
from selenium.common.exceptions import TimeoutException

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
        if retry <= 0:
            return
        try:
            driver.set_page_load_timeout(10)
            driver.get("https://www.lowes.com/pd/DEWALT-20-Volt-Max-1-2-in-Brushless-Cordless-Drill-Charger-Included/1000135807")

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
        print('yo')
        url = self.prod_url(prod_id)
        rawtext =''

        if self.test_file is None:
            rawtext = self.get_page(url)
        else:
            f = open(test_file,'r')
            rawtext = f.read()
        print(rawtext)
        tree = html.fromstring(rawtext)
        return self.data[prod_id]
        #weight
        weight = rawtext.xpath('//*[@itemprop="weight"]')
        if len(weight) > 0:
            print(etree.tostring(weight))
            print(weight.text[:-2] )
            self.data[prod_id] = weight.text[:-2] 
        
        return self.data[prod_id]


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

            return
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
                        pass
                        self.create_id(prod_id)
                        self.data[prod_id]['query'] = url
                        self.data[prod_id]['rank'] = 0 if lookup else search_rank
                        self.data[prod_id]['ads'] = 0
                        self.data[prod_id]['page'] = page

                        #seems like all data is on search results
                    
                search_rank = search_rank +1
                index = index +1
            page = page+1

        return prod_ids



if __name__ == '__main__':
    test = False
    if test:
        test_file = 'tests/test_hd1.txt'
        scrap = LowesScraper('db/',test_file=test_file)
        #scrap.add_ids(24)
        #scrap.get_data(test_file)
        #scrap.write_data()
        #print(scrap.data[ list(scrap.data.keys())[1]])
        

    if not test:   
        scrap = LowesScraper('db/')
        #scrap.add_ids(10)
        scrap.create_id("797394")
        scrap.get_data("797394")
        #print(scrap.lookup_id(('BLACK+DECKER','LD120VA')))
        #print(scrap.lookup_id(('Hyper Tough','AQ75023G')))
        #print(scrap.lookup_id(('DEWALT','DCD777C2')))
        #scrap.write_data()
        #scrap.end_scrape()