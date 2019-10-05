proxies = ['118.173.232.215:43186', '49.51.68.122:1080']


for i in range(10):
    print(i)
    url = 'https://www.upcitemdb.com/upc/' +str(i)
    #url = 'https://www.google.com/'
    hdr = hdrs[i%2]
    print(hdr)
    proxy = proxies[i%3]
    proxy = {
        "http": 'http://' + proxy, 
        "https": 'http://' + proxy
    }
    
    response = requests.get(url,proxies=proxy, headers=hdr)
    page = str(response.content)
    #get_page(url,hdr,proxy)


def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

print(get_proxies())
print(get_proxies())