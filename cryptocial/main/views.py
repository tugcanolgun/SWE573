from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponse
from pathlib import Path
import logging
import json
import coloredlogs
import requests
import numpy as np
from scipy.stats import linregress

from .models import Crypto
import sqlite3

MAIN_DIR = str(Path().resolve().parent)
LOG = str(Path().resolve() / "logs" / "main.log")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
coloredlogs.install(fmt='%(asctime)s - %(name)s - %(levelname)s \t %(message)s')
handler = logging.FileHandler(LOG, 'a',)
handler.setLevel(logging.DEBUG)

def get_client_ip(request):
    """
    Gets the IP address of the requester.
    :param request:
    :return:
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class IndexView(generic.ListView):
    template_name = 'main/index.html'
    context_object_name = 'cr_list'

    def get_queryset(self):
        return Crypto.objects.order_by('date_added')[:15]

def get_id_from_db(short_name:str) -> int:
    """
    Get currency ID from shortname. Control of it being exist or not
    will be checked on returned function
    :param short_name:
    :return:
    """
    conn = sqlite3.connect(MAIN_DIR + "/database/tweets.sqlite3")
    logger.debug("Connecting to the sqlite database")
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM Currencies WHERE ShortName = ?", (short_name, ))
    logger.debug(f"Returning the id for {short_name}")
    id: int = cursor.fetchone()
    conn.close()
    logger.debug(f"Closing the connection to sqlite database")
    return id

def get_results(id: int, high: list, high_value: float, low: list, low_value: float) -> (list, list):
    """
    Get results from ID, all assigned to variables:
        sentiment
        labels

    Any future API changes must happen in here.
    :param id:
    :return:
    """
    sentiment: list = []
    labels: list = []
    pos_list: list = []
    neg_list: list = []
    conn = sqlite3.connect(MAIN_DIR + "/database/tweets.sqlite3")
    logger.debug("Connecting to the sqlite database")
    cursor = conn.cursor()
    cursor.execute("SELECT Time, PosAvarage, NegAvarage, NeuAvarage, ComAvarage \
                        FROM Analysis WHERE CurrencyId = ? ORDER BY Time DESC LIMIT 15", (id, ))
    raw = []
    s_high = - float("inf")
    s_low = 0
    for row2 in cursor.fetchall():
        if row2[4] > s_high:
            s_high = row2[4]
        raw.append(row2)
    for index, row in enumerate(raw):
        cons = ((high_value - low_value) / (s_high - s_low))
        pos = low_value + cons * row[1]
        neg = low_value + cons * row[2]
        neu = low_value + cons * row[3]
        compound = low_value + cons * row[4]
        sentiment.append(dict(pos=pos, neg=neg, neu=neu, compound=compound, high=high[index], low=low[index]))
        pos_list.append(pos)
        neg_list.append(neg)
        labels.append(row[0])

    conn.close()
    return sentiment, labels, pos_list, neg_list

def get_currency(short_name):
    high_value = - float("inf")
    low_value = float("inf")
    high = []
    low = []

    req = requests.get(f"https://min-api.cryptocompare.com/data/histohour?fsym={short_name}&tsym=USD&limit=14")
    req = json.loads(req.text)
    for value in req["Data"]:
        if value["high"] > high_value:
            high_value = value["high"]
        if value["low"] < low_value:
            low_value = value["low"]
        high.append(value["high"])
        low.append(value["low"])
    return high, high_value, low, low_value

def corr(slope, rsquare) -> str:
    slope = abs(slope)
    if slope > 0.2 and rsquare > 0.2:
        text = "Correlation between data is on par!"
    elif slope > 0.2 or rsquare > 0.2:
        text = "Correlation between data is semi trustable"
    else:
        text = "There is no direct correlation between these data"
    return text

def detail(request, crypto_id:int) -> render:
    """
    Detail page of the site. It gets the id and returns
    necessary information for graph and other related
    calculations.
    :param request:
    :param crypto_id:
    :return:
    """
    ip: str = get_client_ip(request)
    logger.info(f"Request for {crypto_id} from the IP: {ip}")
    crypto = get_object_or_404(Crypto, pk=crypto_id)
    logger.debug(f"Request for {crypto_id} found successfully")

    id: int = get_id_from_db(crypto.short_name)

    if not id:
        # Put an error page here
        logger.error(f"Id could not be found for shortname:{crypto.short_name}")
        logger.error(f"Request for {crypto_id}")
        return HttpResponse("Id could not be found")
    else:
        id = id[0]
        logger.debug(f"Id fetched successfully. Id: {id}")

    high, high_value, low, low_value = get_currency(crypto.short_name)
    result, labels, pos, neg = get_results(id, high, high_value, low, low_value)
    correlation = {}
    if len(high) == len(pos):
        c = linregress(high, pos)
        rsquare = c.rvalue ** 2
        text = corr(c.slope, rsquare)
        correlation["pos"] = {"slope": c.slope,
                "intercept": c.intercept,
                "rvalue": c.rvalue,
                "pvalue": c.pvalue,
                "stderr": c.stderr,
                }
    logger.warning(f"{len(high)} {len(neg)}")
    if len(high) == len(neg):
        c = linregress(high, neg)
        correlation["neg"] = {"slope": c.slope,
                "intercept": c.intercept,
                "rvalue": c.rvalue,
                "pvalue": c.pvalue,
                "stderr": c.stderr,
                }


    return render(request, 'main/detail.html', {
                                            'result': result,
                                            'crypto': crypto,
                                            'low': low_value,
                                            'high': high_value,
                                            'correlation': correlation,
                                            'text': text
                                        })
