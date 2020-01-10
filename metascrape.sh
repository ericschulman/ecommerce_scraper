#!/bin/sh

echo "-------starting scrape --------"
cd /home/erichschulman/Documents/9oclock/
/home/erichschulman/anaconda3/bin/python metascrape.py
echo "----------------- backing up files --------------------"
/usr/bin/rclone sync ~/Documents/9oclock/db/scrape.db remote:9oclock/db/
echo "--------- end of scrape---------"
