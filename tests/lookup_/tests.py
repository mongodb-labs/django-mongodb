from django.test import TestCase

from .models import Number


class NumericLookupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.objs = Number.objects.bulk_create(Number(num=x) for x in range(5))
        # Null values should be excluded in less than queries.
        Number.objects.create()

    def test_lt(self):
        self.assertQuerySetEqual(Number.objects.filter(num__lt=3), self.objs[:3])

    def test_lte(self):
        self.assertQuerySetEqual(Number.objects.filter(num__lte=3), self.objs[:4])
