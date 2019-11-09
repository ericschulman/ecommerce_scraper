from gen_scraper import *


class WalmartScraper(GenericScraper):

    def __init__(self, db):
        super(WalmartScraper, self).__init__(db)
        self.base_url = 'https://www.walmart.com/'
        self.platform = 'WMT'


    def get_page(self,url):
        rawpage = super(WalmartScraper,self).get_page(url)
        return rawpage.decode()


    def search_url(self, query, sort='best_seller'):
        query = query.replace(' ', '%20')
        url =  self.base_url + 'search/?cat_id=0&query=%s&sort=%s'%(query,sort)
        return url

    def prod_url(self, prod_id):
        url =  self.base_url + 'ip/' + prod_id
        return url


    def add_ids(self, num_ids, ads=True, query='drills',sort='best_seller'):
        url = self.search_url(query,sort=sort)
        rawtext1 = self.get_page(url)
        tree = html.fromstring(rawtext1)

        link_cand = tree.xpath("//*[@id='searchContent']")
        if len(link_cand) ==0:
            return []

        link_cand = link_cand[0]
        datastore = json.loads(link_cand.text)
        items = datastore['searchContent']['preso']['items']
        search_rank = 1
        prod_ids = []
        
        while search_rank <= len(items) and  search_rank <= num_ids:
            prod_id = items[search_rank-1]['usItemId']
            if sort =='':
                in_name = True
                #get the product name
                if 'title' in items[search_rank-1].keys():
                    title = items[search_rank-1]['title']
                    space = query.find(' ')
                    manuf,model= query[:space],query[space+1:]
                    in_name = title.find(model) < 0

                if in_name:
                    #search_rank = search_rank +1
                    #continue
                    return prod_ids

            
            prod_ids.append(prod_id)

            if prod_id not in self.data.keys():
                self.create_id(prod_id)

            self.data[prod_id]['query'] = query
            self.data[prod_id]['rank'] = search_rank
            self.data[prod_id]['ads'] = 0
            if 'quantity' in items[search_rank-1].keys():
                self.data[prod_id]['quantity1'] = items[search_rank-1]['quantity']
            search_rank = search_rank +1

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



    def lookup_id_upc(self, upc):
        prod_ids = self.add_ids(1,query=upc)
        if prod_ids != []:
            self.data[prod_ids[0]]['upc'] = upc
            return prod_ids[0]
        return None


if __name__ == '__main__':
    scrap = WalmartScraper('db/')
    print( scrap.add_ids(3) )
    #print(scrap.lookup_id(('BLACK+DECKER','LD120VA')))
    #print(scrap.lookup_id(('DEWALT','DCD777C2')))
    scrap.write_data()
