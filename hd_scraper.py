from gen_scraper import *

class HomeDepotScraper(GenericScraper):

    def __init__(self,*args, **kwargs):
        kwargs['url'] = 'https://www.homedepot.com/'
        kwargs['platform'] = 'HD'
        super(HomeDepotScraper, self).__init__(*args, **kwargs)


    def get_page(self,url):
        rawpage = super(HomeDepotScraper,self).get_page(url)
        return rawpage


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


    def get_data_results(self, item, index, prod_id):

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
            rawtext = self.get_page(url)
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
                        self.get_data_results(items[index],index, prod_id)
                    
                search_rank = search_rank +1
                index = index +1
            page = page+1

        return prod_ids



if __name__ == '__main__':
    scrap = HomeDepotScraper('db/')
    prod_id1 = '207051121'
    print(scrap.lookup_id(('BLACK+DECKER','LDX220C')))
    print(scrap.add_ids(10))
    scrap.write_data()
    scrap.end_scrape()