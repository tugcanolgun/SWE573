from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import Http404, HttpResponse
from pathlib import Path
# from django.template import loader
# from django.urls import reverse

from .models import Crypto
import sqlite3

MAIN_DIR = str(Path().resolve().parent)

class IndexView(generic.ListView):
    template_name = 'main/index.html'
    context_object_name = 'cr_list'

    def get_queryset(self):
        return Crypto.objects.order_by('-date_added')[:5]

# def index(request):
#     cr_list = Crypto.objects.order_by('-date_added')[:5]
#     template = loader.get_template('main/index.html')
#     context = {
#         'cr_list': cr_list
#     }
#     # return HttpResponse(template.render(context, request))
#     return render(request, 'main/index.html', context)


# class DetailView(generic.DetailView):
#     model = Crypto
#     template_name = 'polls/detail.html'

def detail(request, crypto_id):
    crypto = get_object_or_404(Crypto, pk=crypto_id)
    conn = sqlite3.connect(MAIN_DIR + "/database/tweets.sqlite3")
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM Currencies WHERE ShortName = ?", (crypto.short_name, ))
    id = cursor.fetchone()
    if not id:
        # Put an error page here
        return HttpResponse("Id could not be found")
    else:
        id = id[0]
    sentiment = []
    pos = []
    neg = []
    neu = []
    com = []
    labels = []
    cursor.execute("SELECT Time, PosAvarage, NegAvarage, NeuAvarage, ComAvarage FROM Analysis WHERE CurrencyId = ? ORDER BY Time DESC LIMIT 15", (id, ))
    for row in cursor.fetchall():
        pos.append(row[1])
        neg.append(row[2])
        neu.append(row[3])
        com.append(row[4])
        sentiment.append(dict(pos=row[1], neg=row[2], neu=row[3], compound=row[4]))
        labels.append(row[0])

    conn.close()
    # req = request.get("https://min-api.cryptocompare.com/data/histohour?fsym=BTC&tsym=USD&limit=15")



    return render(request, 'main/detail.html', {'crypto': crypto, 'result': sentiment, 'labels': labels, 'pos': pos, 'neg': neg, 'neu': neu, 'com': com, 'MAIN_DIR': MAIN_DIR})
