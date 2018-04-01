from nltk.sentiment.vader import SentimentIntensityAnalyzer
import sqlite3


class SedimentAnalysis:
    def __init__(self, currency: str):
        if not isinstance(currency, str):
            return
        self.currency = currency
        self.currency_id = None
        self.tweets = {}
        self.results = {}
        self.conn = sqlite3.connect("tweets.sqlite3")
        self.cursor = self.conn.cursor()

    def __get_id(self, currency: str) -> int:
        self.cursor.execute("SELECT Id FROM Currencies WHERE ShortName = ?", (currency, ))
        currency_id = self.cursor.fetchone()
        if currency_id:
            return currency_id[0]
        else:
            return False

    def __get_key(self, unixtime):
        for key in self.tweets.keys():
            if abs(key - unixtime) < 60:
                return key
        self.tweets[unixtime] = []
        self.results[unixtime] = dict(pos_ave=0., neg_ave=0., neu_ave=0., com_ave=0., pos_sum=0., neg_sum=0.,
                                      neu_sum=0., com_sum=0., total_posts=0)
        return unixtime

    def run(self) -> None:
        """
            Main runner of the script
            row:
                0: Tweet
                1: UnixTime
        :return:
        """
        self.currency_id = self.__get_id(self.currency)
        if not self.currency_id:
            return
        self.cursor.execute("SELECT Tweet, UnixTime FROM Tweets WHERE CurrencyId = ?", (self.currency_id, ))
        for row in self.cursor.fetchall():
            key = self.__get_key(row[1])
            self.tweets[key].append(row[0])
        self.__run_sentiment()

    def __run_sentiment(self):
        """
            Run each tweet for certain time period and do
            the analysis.
        :return:
        """
        for time, tweets in self.tweets.items():
            for tweet in tweets:
                _result = self.__do_analysis(tweet)
                self.__add_to_results(time, _result)

    def __do_analysis(self, tweet: str) -> dict:
        """
            Do analysis and return the results
        :param tweet:
        :return:
        """
        __analysis = SentimentIntensityAnalyzer().polarity_scores(tweet)
        return __analysis

    def __add_to_results(self, time: int, result: dict) -> bool:
        """
            Add results to the self.results
        :param time, result:
        :return:
        """
        if time not in self.results:
            logger.error("This timeframe could not be found in results.")
            return
        if "pos" not in result \
            or "neg" not in result \
            or "neu" not in result \
            or "compund" not in result:
            logger.error("Sentiment result does not contain the keys")
            return
        self.results[time]["pos_sum"] += result["pos"]
        self.results[time]["neg_sum"] += result["neg"]
        self.results[time]["neu_sum"] += result["neu"]
        self.results[time]["com_sum"] += result["compund"]
        self.results[time]["total_posts"] += 1

    def __calculate_avarage(self, time: int) -> None:
        """
            Calculates the mean avarage of the results
        :param time:
        :return:
        """


