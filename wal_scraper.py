from gen_scraper import *


class WalmartScraper(GenericScraper):

    def __init__(self, *args, **kwargs):
        kwargs['url'] = 'https://www.walmart.com/'
        kwargs['platform'] = 'WMT'
        super(WalmartScraper, self).__init__(*args, **kwargs)
        
    def set_location(self,driver,retry=20):
        try:
            driver.get("https://www.walmart.com/")
            driver.find_element(By.CSS_SELECTOR, ".i_b:nth-child(3)").click()
            time.sleep(4)
            driver.find_element(By.CSS_SELECTOR, ".ao_c").click()
            driver.find_element(By.CSS_SELECTOR, ".ao_c").send_keys(self.location)
            driver.find_element(By.CSS_SELECTOR, ".o_c:nth-child(3) > .i_a").click()
        except Exception as e:
            print(e)
            self.set_location(driver,retry=retry-1)

    def get_page(self,url):
        rawpage = super(WalmartScraper,self).get_page(url)
        return rawpage


    def search_url(self, keywords, page, sort='best_seller'):
        final_query = self.format_query(keywords)
        url =  self.base_url + 'search/?cat_id=0&query=%s&sort=%s&page=%s&ps=40'%(final_query,sort,page)
        return url

    def prod_url(self, prod_id):
        url =  self.base_url + 'ip/' + prod_id
        return url


    def add_ids(self, num_ids, lookup=False, keywords=None, page=1):
        if keywords is None:
            keywords = [self.query]
       
        search_rank = 1
        prod_ids = []
        max_page = 2 if lookup else 5

        while page < max_page and search_rank <= num_ids:

            url = self.search_url(keywords, page , sort='') if lookup else self.search_url(keywords, page)
            rawtext = self.get_page(url)
            tree = html.fromstring(rawtext)

            link_cand = tree.xpath("//*[@id='searchContent']")
            if len(link_cand) ==0:
                return []

            link_cand = link_cand[0]
            datastore = json.loads(link_cand.text)
            items = datastore['searchContent']['preso']['items']
            index = 0

            while index < len(items) and  search_rank <= num_ids:

                prod_id = items[index]['usItemId']
                found_product = not lookup
                if not found_product:
                    in_name = True
                    #get the product name
                    if 'title' in items[index].keys():
                        manuf,model = keywords[0], keywords[0]
                        if len(keywords) >1:
                            manuf,model= keywords[0],keywords[1]
                            
                        title = items[index]['title']
                        in_name = model is not None and title.find(model) >= 0  # and title.find(manuf) >= 0

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

                        if 'shouldHaveSponsoredItemMargin' in items[index].keys():
                            self.data[prod_id]['ads'] = int(items[index]['shouldHaveSponsoredItemMargin'])
                        if 'shouldHaveSpecialOfferMargin' in items[index].keys():
                            self.data[prod_id]['quantity2'] = int(items[index]['shouldHaveSpecialOfferMargin'])
                    
                        if 'quantity' in items[index].keys():
                            self.data[prod_id]['quantity1'] = items[index]['quantity']

                search_rank = search_rank +1
                index = index +1
            page = page+1

        return prod_ids



    def get_data(self, prod_id):
      
        url = self.prod_url(prod_id)

        rawtext =''

        if self.test_file is None:
            rawtext = self.get_page(url)
        else:
            f = open(test_file,'r')
            rawtext = f.read()

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
            #try for shipping data   
            try:
                self.data[prod_id]['in_stock']  = int(data['shippable'])

                for key in ['earliestDeliverDate','exactDeliveryDate']:
                    if key in data['shippingOptionToDisplay']['fulfillmentDateRange'].keys():
                        ship_date = data['shippingOptionToDisplay']['fulfillmentDateRange'][key]
                        self.data[prod_id]['arrives'] =  int(ship_date)

                    if 'fulfillmentPriceType' in data['shippingOptionToDisplay'].keys():
                        self.data[prod_id]['shipping'] = data['shippingOptionToDisplay']['shipMethod']

                    if 'fulfillmentPrice' in data['shippingOptionToDisplay'].keys():
                        self.data[prod_id]['shipping_price'] = float(data['shippingOptionToDisplay']['fulfillmentPrice']['price'])

            except KeyError:
                print('no shipping ' + prod_id)

            if 'shippingOptions' in data.keys():
                self.data[prod_id]['shipping_options'] = len(data['shippingOptions'])

            
            walmart_names = ['upc','brandName','productName', 'model', 'reviewsCount', 'averageRating',
                             'maxQuantity','sellerDisplayName']
            my_names = ['upc','manufacturer','product','model','reviews','rating','max_qty', 'seller']
             
            for i in range(len(walmart_names)):
                if walmart_names[i] in data.keys():
                    self.data[prod_id][my_names[i]] = data[walmart_names[i]]

            #get store pickup data
            try:
                pickup = data['pickupOptions'][0]
                self.data[prod_id]['store_address'] = pickup['storeAddress'] +', ' +pickup['storeCity'] + ', ' + pickup['storeStateOrProvinceCode']
                self.data[prod_id]['store_zip'] = pickup['storePostalCode']
                if 'urgentQuantity' in pickup:
                    self.data[prod_id]['quantity3'] =  pickup['urgentQuantity']
                if "inStoreStockStatus" in pickup.keys():
                    self.data[prod_id]['store_stock'] = pickup['inStoreStockStatus']
                if  'inStorePackagePrice' in pickup.keys():
                    self.data[prod_id]['store_price'] = pickup['inStorePackagePrice']['price']


            except:
                print('no pickup ' + prod_id)

                    
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


if __name__ == '__main__':

    test = False
    if test:
        test_file = 'tests/test_wal1.txt'
        scrap = WalmartScraper('db/',test_file=test_file)
        scrap.get_data(test_file)
        print(scrap.data)

    if not test:   
        scrap = WalmartScraper('db/')
        scrap.add_ids(10)
        #print(scrap.lookup_id(('BLACK+DECKER','LD120VA')))
        #print(scrap.lookup_id(('Hyper Tough','AQ75023G')))
        #print(scrap.lookup_id(('DEWALT','DCD777C2')))
        scrap.write_data()
        scrap.end_scrape()