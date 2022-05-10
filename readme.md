# Overview

This is a scraper designed to pull information about Amazon, Home Depot, Lowe's, and Walmart's price competition in digital markets. The data involves power drills. For more information on the scrapped data see the [kaggle page](https://www.kaggle.com/datasets/erichschulman/another-ecommerce-scrape) or the repo with [summary statistics](https://github.com/ericschulman/ecommerce_drills). 


## Scrape methodology


I am collecting the following information using the scraper: prices, shipping prices, shipping times, delivery methods, it’s rank in the search results (sorted by best seller), inventory, store locations, whether or not the product is in stock, whether or not there was a sale (tradepromotion). The scraper does the following steps to gather data:
1. It visits each website, inputs a search query.
2. It then sorts by best sellers.
3. It visits each page in the search results and records pricing information and quantity information if it is available. 
4. It also tries to find each of the products among the best sellers on the competitors websites. This way, it will be possible to compare products across websites.


## Modules

* Each of the websites being scraped has it's own scraper. These scrapers extend the `GenericScraper` class defined in `gen_scraper.py`. 
* `metascrape.py` runs each of the files. Originally, I has it scheduled as a `cron` process that ran twice a day.
* Once the data is scraped it is saved to a `sqlite` database. This database is instantiated by `scrape.sql`.

## Dependencies
The scraper is powered by `selenium`. I found using a browswer ased scrape helpful for by passing Amazon's anti-scraping measures for detecting robots.
`conda install selenium`
`conda install -c conda-forge geckodriver`


-------------------

## Work in progress

## Walmart
* walmart get pick up options
* add store address to db
* add store invetory

## Home Depot
* change location using storeid?
* home depot get pickup options
* home depot - weight and other quantity information






