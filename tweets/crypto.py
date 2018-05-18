#/usr/bin/python3.6
import json
import logging
import pickle
import re
import sqlite3
from os import environ, system
from time import sleep

import requests
import tweepy

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('log_crypto.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Globals
CURRENCIES = []

class Cryptocurrency:
    def __init__(self):
        logger.info("Initializing crypto...")
        self.conn = sqlite3.connect("../database/tweets.sqlite3")
        self.cursor = self.conn.cursor()

    def __get_id(self, currency: str) -> int:
        self.cursor.execute("SELECT Id FROM Currencies WHERE ShortName = ?", (currency, ))
        currency_id = self.cursor.fetchone()
        if currency_id:
            return currency_id[0]
        else:
            return False

    def __add_currency(self, currency: str, long_name: str="", logo:str =""):
        if not long_name:
            long_name = currency
        
        self.cursor = self.conn.cursor()
        if self.__get_id(currency):
            return
        self.cursor.execute("INSERT INTO Currencies (ShortName, LongName, Logo) VALUES (?, ?, ?)", (currency, long_name, logo, ))
        self.conn.commit()


    def __add_price(self, currency: str, usd: str, btc: str, volume: str) -> None:
        currency_id = self.__get_id(currency)
        if not currency_id:
            logger.info("Currency %s exists" % currency)
            return
        self.cursor = self.conn.cursor()
        self.cursor.execute("INSERT INTO Prices (CurrencyId, PriceUSD, PriceBTC, Volume) VALUES (?, ?, ?, ?)", (currency_id, usd, btc, volume))
        self.conn.commit()

    def run(self):
        req = requests.get("https://api.coinmarketcap.com/v1/ticker/?limit=50")
        res = json.loads(req.text)
        for coin in res:
            currency = coin["symbol"]
            CURRENCIES.append(currency)
            long_name = coin["name"]
            usd = coin["price_usd"]
            btc = coin["price_btc"]
            volume = coin["24h_volume_usd"]
            self.__add_currency(currency, long_name)
            self.__add_price(currency, usd, btc, volume)
        logger.info("Currencies are added")

class Twitter:
    def __init__(self):
        logger.info("Initializing twitter...")
        self.api = None
        self.conn = sqlite3.connect("../database/tweets.sqlite3")
        self.cursor = self.conn.cursor()


    def __auth(self) -> None:
        consumer_secret = environ.get("consumer_secret")
        access_token = environ.get("access_token")
        access_token_secret = environ.get("access_token_secret")
        consumer_key = environ.get("consumer_key")
        if not consumer_key or not access_token or not access_token_secret or not consumer_secret:
            logger.error("Environmental keys could not be fetched")
            raise Exception("Environmental keys could not be fetched")
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        return auth
    
    def __get_id(self, currency: str) -> int:
        self.cursor.execute("SELECT Id FROM Currencies WHERE ShortName = ?", (currency, ))
        currency_id = self.cursor.fetchone()
        if currency_id:
            return currency_id[0]
        else:
            return False

    def __delete_urls(self, text: str) -> str:
        if not isinstance(text, str):
            logger.error("Given text is not str")
            logger.error(str(text))
            logger.error(str(type(text)))
            raise Exception("Given text is not str")
        return re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text)
    
    def __add_tweets(self, currency: str, text: str) -> None:
        currency_id = self.__get_id(currency)
        if not currency_id:
            return
        if not isinstance(text, str):
            return
        self.cursor.execute("INSERT INTO Tweets (CurrencyId, Tweet) VALUES (?, ?)", (currency, text, ))
        self.conn.commit()
        

    def run(self) -> None:
        global CURRENCIES
        for currency in CURRENCIES:
            try:
                self.api = tweepy.API(self.__auth())
                for tweet in tweepy.Cursor(self.api.search, q="#%s -filter:retweets" % currency, lang="en").items(100):
                    text = self.__delete_urls(tweet.text)
                    self.__add_tweets(currency, text)
            except tweepy.TweepError as err:
                logger.error(str(err))
            except:
                logger.error("Something went wrong")
            system("../venv/bin/python3 sentiment.py --coin %s &" % currency)
            sleep(90)
        logger.info("Tweets are added")
        CURRENCIES = []
        self.conn.close()
