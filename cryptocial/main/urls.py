from django.urls import path

from . import views

app_name = 'main'
urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.IndexView.as_view(), name='index'),
    path('<int:crypto_id>/', views.detail, name='detail'),
]
