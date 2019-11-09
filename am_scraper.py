from gen_scraper import *


class AmazonScraper(GenericScraper):
        
    def __init__(self, db):
        super(AmazonScraper, self).__init__(db)
        self.base_url = 'https://www.amazon.com/'
        self.platform = 'AMZN'

    def get_page(self,url):
        rawpage = ''
        for i in range(20):
            rawpage = super(AmazonScraper,self).get_page(url)
            if str(rawpage).find('not a robot. For best results, please make sure your browser is accepting cookies.') < 0:
                rawpage = str(rawpage)
                return str(rawpage)
        return rawpage
        

    def search_url(self, query, page,  sort='salesrank'):
        query = query.replace(' ', '%20')
        url =  self.base_url + 's?k=%s&s=%s&page=%s'%(query,sort,page)
        return url

    def prod_url(self, prod_id):
        return  self.base_url + 'dp/'+prod_id





    def add_ids(self, num_ids, ads=True, sort ='salesrank', query='drills'):
        asin_list = []
        search_rank = 1
        page = 0

        while page < 10 and search_rank <= num_ids:
            
            url = self.search_url(query,page, sort = sort)
            rawtext = self.get_page(url)
            tree = html.fromstring(rawtext)
            search_rows = tree.xpath("//*[@class='s-result-list s-search-results sg-row']")
            row_num = 0
            while row_num < len(search_rows) and search_rank <= num_ids:

                row = search_rows[row_num]
                index = 0
                while index < len(row) and  search_rank <= num_ids:
                    if 'class' in dict(row[index].attrib).keys() and 'data-asin' in dict(row[index].attrib).keys():
                        asin = row[index].attrib['data-asin']

                        if asin not in self.data.keys():
                            self.create_id(asin)
                        self.data[asin]['query'] = query

                        if sort =='':
                            in_name = True
                            #get the product name
                            title = str(etree.tostring(row[index]))
                            space = query.find(' ')
                            manuf,model= query[:space],query[space+1:]
                            print(title)
                            in_name = title.find(model) < 0 or title.find('Cache hit while loading Amazon') > 0
                            #print(title)
                
                            if in_name:
                                #search_rank = search_rank +1
                                return asin_list

                        if not ('AdHolder' in row[index].attrib['class']) and row[index].attrib['data-asin'] !='':
                            self.data[asin]['rank'] = search_rank
                            self.data[asin]['ads'] = 0
                            search_rank = search_rank +1
                            asin_list.append(asin)
                        else:
                            if ads:
                                self.data[asin]['rank'] = 0
                                self.data[asin]['ads'] = 1

                    index = index +1
                row_num = row_num+1
            page = page +1

        return asin_list


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
            self.data[asin]['quantity1']= int(listings[ind1+1:ind2])

        #rank in page


        #only x left in stock


        #shipping description


        #shipping cost
    

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



    def lookup_id_upc(self, upc):
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


if __name__ == '__main__':

    scrap = AmazonScraper('db/')
    #print(scrap.lookup_id(('BLACK+DECKER','LD120VA')))
    print(scrap.lookup_id(('BLACK+DECKER','BCD702C2BWM')))
    #print(scrap.lookup_id('Hyper Tough','AQ75023G'))
    #print(scrap.add_ids(3))
    #print(len(scrap.data))
    #scrap.write_data()
    #scrap.write_data()
