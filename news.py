import feedparser, json, requests, re, time
from datetime import datetime
from bs4 import BeautifulSoup

crypto_json = open("cryptos.json", "r")
crypto_dict = json.load(crypto_json)
asset_alert = ["BTC","ETH"]
Feeds = [
    {
        "link":"https://cointelegraph.com/rss",
        "name": "Cointelegraph",
        "last_check": datetime.now(),
        "last_title": "Top 5 cryptocurrencies to watch this week: BTC, LEO, MANA, KLAY, XTZ",
        "type": "rss",

    }, 
    {
        "link":"https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
        "name": "Coindesk",
        "last_check": datetime.now(),
        "last_title": "Bitcoin’s Value Depends on Its Decentralization",
        "type": "rss"
    },
    {
        "link":"https://blockchain.news/MorePost?pageIndex=0&pageSize=8",
        "name": "Blockchain.news",
        "last_check": datetime.now(),
        "last_title": "",
        "type": "blockchainnews_html"
    },
        ]



# News entry checker for RSS only
class Rss_Entry:
    def __init__(self, entries, number):
        """Initialize all that from entry."""
        
        self.data = entries[number]
        self.title = self.data.title
        self.description = self.parse_description()
        self.url = self.data.link
        self.image = self.data.media_content[0]['url']
        self.published = self.data.published_parsed
        self.assets = self.get_assets()
        print(self.title)
    
    def get_assets(self):
        """Scraps assets from title and description"""
        assets = []
        str_to_scrap = (self.title + self.description).upper()
        for ticker in asset_alert:
            if ticker in str_to_scrap or crypto_dict[ticker].upper() in str_to_scrap:
                assets.append(ticker)
        return assets

    def parse_description(self):
        """Removes hmtl tags from description"""
        soup = BeautifulSoup(self.data['description'], 'lxml')
        return soup.text


# News entry object for Blockchain.News only
class Blockchainnews_Entry:
    def __init__(self, entries, number):
        """Initialize all that from entry."""
        self.data = entries[number]
        self.title = self.data.find('h6', class_="entry-title").text
        self.description = ""
        self.url = "https://blockchain.news" + self.data.find('a', href=True)['href']
        self.image = self.data.find('img')['data-src']
        self.published = datetime.now()
        self.assets = self.get_assets()

    def get_assets(self):
        """Scraps assets from title and description"""
        assets = []
        str_to_scrap = (self.title + self.description).upper()
        for ticker in asset_alert:
            if ticker in str_to_scrap or crypto_dict[ticker].upper() in str_to_scrap:
                assets.append(ticker)
        return assets

# Creates and sends discord alert
class Discord_Alert:
    def __init__(self, author, author_url, title, url, description, image, assets):
        """Sets all data needed to create the alert"""
        self.username = "Webhook"
        self.author_name = author
        self.author_url = author_url
        self.title = title
        self.url = url
        self.description = description
        self.image = image
        self.assets = ','.join(assets)
        self.alert_dict = self.create_dict()

    def create_dict(self):
        """Creates alert body from template"""
        alert_dict = {
            "username": self.username,
            "embeds": [
                {
                    "author": {
                        "name": self.author_name,
                        "url": self.author_url
                    },
                    "title": self.title,
                    "url": self.url,
                    "description": self.description,
                    "fields": [
                        {
                            "name": "Assets",
                            "value": self.assets,
                            "inline": True
                        }
                    ],
                    "image":{
                        "url": self.image
                    }
                }
            ]
        }
        return alert_dict

    def send_alert(self):
        """Sends alert POST to the webhook"""
        alert = requests.post("https://discord.com/api/webhooks/942954284729901107/od8Xeo-igzTxYtsKVJwGAZFwANKe8bNSH6hwvIbHv1TnIX0tKEi16F9XRknKPrTtiHFH", json = self.alert_dict)
        return alert
        
def news_check():
    for NewsFeed in Feeds:
        entries = []
        first_title = ""
        # Get entries per type of source.
        if NewsFeed["type"] == "rss":
            entries = feedparser.parse(NewsFeed["link"]).entries
            first_title = entries[0].title
            for entry_number in range(0, len(entries)):
                data = Rss_Entry(entries, entry_number)
                if data.assets:
                    # If the last news title is found all new news were reviewed.
                    if data.title != NewsFeed["last_title"]:
                        print(Discord_Alert(NewsFeed["name"], NewsFeed["link"], data.title, data.url, data.description, data.image, data.assets).send_alert().status_code)
                        time.sleep(1)
                    else:
                        NewsFeed["last_title"] = first_title
                        NewsFeed["last_check"] = datetime.now()
                        break
        elif NewsFeed["type"] == "blockchainnews_html":
            r = requests.get('https://blockchain.news/MorePost?pageIndex=0&pageSize=8')
            soup = BeautifulSoup(r.text, 'lxml')
            entries = soup.find_all('div', attrs={'class': re.compile('^col-md-6 hidden-xs-down.*')})
            for entry_number in range(0, len(entries)):
                data = Blockchainnews_Entry(entries, entry_number)
                if data.assets:
                    # If the last news title is found all new news were reviewed.
                    if data.title != NewsFeed["last_title"]:
                        print(Discord_Alert(NewsFeed["name"], NewsFeed["link"], data.title, data.url, data.description, data.image, data.assets).send_alert().status_code)
                        time.sleep(1)
                    else:
                        NewsFeed["last_title"] = first_title
                        NewsFeed["last_check"] = datetime.now()
                        break
    print(datetime.now())
    return "done reviewing pages"

while True:
    print(news_check())
    time.sleep(300)

crypto_json.close()