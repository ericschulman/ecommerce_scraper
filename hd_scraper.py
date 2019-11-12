from gen_scraper import *

class HomeDepotScraper(GenericScraper):

    def __init__(self, db, main_query='drills'):
        super(HomeDepotScraper, self).__init__(db, main_query=main_query)
        self.base_url = 'https://www.homedepot.com/'
        self.platform = 'HD'


    def get_page(self,url):
        rawpage = super(HomeDepotScraper,self).get_page(url)
        return rawpage.decode()


    def search_url(self, query, page, sort='&Ns=P_Topseller_Sort|1'):
        final_query = self.format_query(query)
        page = (page-1)*24
        url =  self.base_url + 's/%s?isSearch=true&Nao=%s%s'%(final_query,page,sort)
        return url

    def prod_url(self, prod_id):
        url =  self.base_url + 'p/' + prod_id
        return url

    def get_data_results(self, item, prod_id):
        
        manuf = self.search_xpath(item,'pod-plp__brand-name')
        if len(manuf) > 0:
            self.data[prod_id]['manufacturer'] = str(manuf[0].text)

        model = self.search_xpath(item,'plp__model')
        if len(model) > 0:
            model = str(model[0].text)
            model = model[model.find('Model#') +8:]
            model = model[:model.find('\n')]
            self.data[prod_id]['model'] = model

        main_info = self.search_xpath(item,'productlist plp-pod__compare')
        if len(main_info)>0:
            main_info = main_info[0][0][0]
            self.data[prod_id]['product'] = main_info.attrib['data-title']
            if 'data-was-price' in main_info.attrib.keys():
                self.data[prod_id]['list_price'] = float(main_info.attrib['data-was-price'][1:])
                self.data[prod_id]['price'] = float(main_info.attrib['data-price'][1:])
            else:
                self.data['price'] = float(main_info.attrib['data-price'][1:])


    def add_ids(self, num_ids, lookup=False, query=None, page=1):
        if query is None:
            query = [self.main_query]
       
        search_rank = 1
        prod_ids = []
        max_page = 2 if lookup else 5

        while page < max_page and search_rank <= num_ids:

            url = self.search_url(query, page , sort='') if lookup else self.search_url(query, page)
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
                    
                    manuf,model = query[0], query[0]
                    if len(query) >1:
                        manuf,model= query[0],query[1]
                            
                    title = 'title'
                    in_name = model is not None and title.find(model) >= 0  # and title.find(manuf) >= 0

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
                        print(index, items[index],prod_id)
                        self.get_data_results(items[index],prod_id)
                    
                search_rank = search_rank +1
                index = index +1
            page = page+1

        return prod_ids



if __name__ == '__main__':
    scrap = HomeDepotScraper('db/')
    prod_id1 = '207051121'
    print(scrap.add_ids(10))
    scrap.write_data()
