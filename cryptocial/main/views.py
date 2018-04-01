from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import Http404
# from django.template import loader
# from django.urls import reverse

from .models import Crypto

class IndexView(generic.ListView):
    template_name = 'main/index.html'
    context_object_name = 'cr_list'

    def get_queryset(self):
        raise Http404
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
    return render(request, 'main/detail.html', {'crypto': crypto})
