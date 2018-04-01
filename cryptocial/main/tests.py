from django.test import TestCase
from django.utils import timezone

import datetime

from .models import Crypto

class CryptoModelTest(TestCase):
    def test_was_published_recently_with_future_crypto(self):
        time = timezone.now() - datetime.timedelta(days=30)
        future_crypto = Crypto(date_added=time)
        self.assertIs(future_crypto.was_published_recently(), False)
