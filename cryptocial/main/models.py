from django.db import models
from django.utils import timezone

import datetime

class Crypto(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20)
    date_added = models.DateTimeField('Date added', auto_now_add=True, blank=True)
    logo = models.CharField(max_length=254)


    def __str__(self):
        return self.name

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.date_added <= now

