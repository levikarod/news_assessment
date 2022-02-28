# Libraries to handle the extracted info.
import requests
import feedparser
from dateutil import parser

# Handle text
import markdownify
import re

# Handle dates
import datetime
import time
from dateutil.tz import tzutc


# Enviroment files
from dotenv import load_dotenv
import os



#load_dotenv()
#webhook = os.getenv("ENDPOINT")

webhook = "https://discord.com/api/webhooks/942954284729901107/od8Xeo-igzTxYtsKVJwGAZFwANKe8bNSH6hwvIbHv1TnIX0tKEi16F9XRknKPrTtiHFH"


class NewsObject():
    def __init__(self, new):
        self.title = new["title"]
        self.description = new["description"]
        self.main_image = new["media_content"][0]["url"]
        self.url_article = new["link"]
        self.assets = ""
        self._symbols_regex = r"bitcoin|ethereum|litecoin|cardano|polkadot|stellar|dogecoin|binance coin|Tether|Monero"
        self._symbols = { "bitcoin": "BTC", "ethereum": "ETH", "litecoin": "LTC",  "cardano": "ADA", 
                        "polkadot": "DOT", "stellar": "XLM", "dogecoin": "DOGE", "binance coin": "BNB", "Tether": "USDT", "Monero": "XMR"}
        
    def search_assets(self):
        """
        Function that will be taking into consideration the title in order to get the different symbols. 
        The output will be the assets updated. 
        """
        title = self.title.lower()
        for key in self._symbols:
            title = title.replace(self._symbols[key], key)
        # Getting the symbols  
        assets_found_1 = re.findall(self._symbols_regex, title)
        assets_found_2 = re.findall(r"[A-Z]{3,5}", self.title)
        assets = ""
        
        # Drop repeated symbols
        if assets_found_1 or assets_found_2:
            assets_found_1 = set(assets_found_1)
            assets_found_2 = set(assets_found_2)
            assets_found_2 = (assets_found_1^assets_found_2) & assets_found_2
            # Adding symbols to assets
            for symbol in assets_found_1:
                assets += self._symbols[symbol] + ", "
            for symbol in assets_found_2:
                assets += symbol + ", "
        
            self.assets = assets[:-2] + "."
            
            
    def gen_hook(self):
        # Getting html text.  
        if "<p>" in self.description:
            self.description = re.findall(r"(?<=<p>)[\s\S]+(?=</p)", self.description)[0]
        # Creating the object to generate the push
        data = {
            "embeds" : [{
                    "title" : self.title,
                    "description" : markdownify.markdownify(self.description),
                    "url" : self.url_article,
                    "image": {"url": self.main_image},
                    "footer": { "text": self.assets}
                    }]
            }
        return data

    
while True:
    
    # Data sources
    url_telegraph = "https://cointelegraph.com/rss"
    url_coindesk = "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml"
    
    # Getting the entries.
    news_telegraph = feedparser.parse(url_telegraph)["entries"]
    news_coindesk = feedparser.parse(url_coindesk)["entries"]
    
    all_news = news_coindesk + news_telegraph
    
    # Getting the publish time of the last hour 
    for idx in range(len(all_news)):
        new = all_news[idx]
        publish_time = parser.parse(new["published"])
        actual_time = datetime.datetime.now(tzutc())

        delta_time = actual_time - publish_time
        if delta_time.seconds < 3600 and delta_time.days == 0:
            # Initializing the object and parsing the data. 
            my_new = NewsObject(new)
            my_new.search_assets()
            data = my_new.gen_hook()
            result = requests.post(webhook, json = data)
    print("Running...")
    
    
    time.sleep(3600)