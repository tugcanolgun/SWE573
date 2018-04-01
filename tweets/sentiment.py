from nltk.sentiment.vader import SentimentIntensityAnalyzer
import sqlite3
import logging
import argparse

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('log_sentiment.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class SentimentAnalysis:
    def __init__(self, currency: str):
        if not isinstance(currency, str):
            return
        logger.info("Sentiment analysis has started. %s", self.currency)
        self.currency = currency
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

    def __get_key(self, time: int) -> int:
        for key in self.tweets.keys():
            if abs(key - time) < 100:
                return key
        self.tweets[time] = []
        self.results[time] = dict(pos_ave=0., neg_ave=0., neu_ave=0., com_ave=0., pos_sum=0., neg_sum=0.,
                                      neu_sum=0., com_sum=0., total_posts=0)
        return time

    def __get_latest_analysis(self) -> int:
        currency_id = self.__get_id(self.currency)
        if not currency_id:
            logger.info("Currency %s exists" % self.currency)
            return
        self.cursor.execute("SELECT Time FROM Analysis WHERE CurrencyId = ? ORDER BY Time DESC LIMIT 1", (currency_id, ))
        time = self.cursor.fetchone()
        if not time:
            logger.error("No analysis exist for the currency: %s", self.currency)
            return 0
        else:
            return time[0]

    def __run_sentiment(self):
        """
            Run each tweet for certain time period and do
            the analysis.
        :return:
        """
        for time, tweets in self.tweets.items():
            # print(time, len(tweets))
            for tweet in tweets:
                _result = self.__do_analysis(tweet)
                # Add the results to self.results
                self.__add_to_results(time, _result)
            # Calculate the mean avarage of the results
            self.__calculate_avarage(time)
            self.__write_to_db(time)

    def __write_to_db(self, time: int) -> None:
        currency_id = self.__get_id(self.currency)
        if not currency_id:
            logger.info("Currency %s exists" % self.currency)
            return
        self.cursor.execute("""INSERT INTO Analysis (CurrencyId, PosAvarage, NegAvarage, \
                                  NeuAvarage, ComAvarage, PosSum, NegSum, NeuSum, ComSum, Time) VALUES \
                                  (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (currency_id,
                                self.results[time]["pos_ave"],
                                self.results[time]["neg_ave"],
                                self.results[time]["neu_ave"],
                                self.results[time]["com_ave"],
                                self.results[time]["pos_sum"],
                                self.results[time]["neg_sum"],
                                self.results[time]["neu_sum"],
                                self.results[time]["com_sum"],
                                time))
        self.conn.commit()

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
            logger.error("This timeframe could not be found in results. __add_to_results")
            return False
        if "pos" not in result \
            or "neg" not in result \
            or "neu" not in result \
            or "compound" not in result:
            logger.error("Sentiment result does not contain the keys")
            return False
        self.results[time]["pos_sum"] += result["pos"]
        self.results[time]["neg_sum"] += result["neg"]
        self.results[time]["neu_sum"] += result["neu"]
        self.results[time]["com_sum"] += result["compound"]
        self.results[time]["total_posts"] += 1
        return True

    def __calculate_avarage(self, time: int) -> None:
        """
            Calculates the mean avarage of the results
        :param time:
        :return:
        """
        if time not in self.results:
            logger.error("This timeframe could not be found in results. __calculate_avarage")
            return
        if self.results[time]["total_posts"] == 0:
            return
        self.results[time]["pos_ave"] = self.results[time]["pos_sum"] / self.results[time]["total_posts"]
        self.results[time]["neg_ave"] = self.results[time]["neg_sum"] / self.results[time]["total_posts"]
        self.results[time]["neu_ave"] = self.results[time]["neu_sum"] / self.results[time]["total_posts"]
        self.results[time]["com_ave"] = self.results[time]["com_sum"] / self.results[time]["total_posts"]

    def run(self) -> None:
        """
            Main runner of the script
            row:
                0: Tweet
                1: UnixTime
        :return:
        """
        time = self.__get_latest_analysis()
        self.cursor.execute("SELECT Tweet, UnixTime FROM Tweets WHERE CurrencyId = ? AND UnixTime > ?", (self.currency, time, ))
        for row in self.cursor.fetchall():
            key = self.__get_key(row[1])
            self.tweets[key].append(row[0])
        self.__run_sentiment()
        logger.info("Sentiment analysis has ended. %s", self.currency)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Do sentiment analysis on a coin')
    parser.add_argument('--coin', type=str, help='Coin (short) name', required=True)

    args = parser.parse_args()
    if "coin" in args:
        if isinstance(args.coin, str):
            SentimentAnalysis(args.coin).run()


