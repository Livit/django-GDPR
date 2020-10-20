from __future__ import absolute_import

from django.test import TestCase

from tests.models import Customer
from .data import (CUSTOMER__FIRST_NAME, CUSTOMER__KWARGS, CUSTOMER__LAST_NAME)
from .utils import AnonymizedDataMixin, NotImplementedMixin


class TestModelAnonymization(AnonymizedDataMixin, NotImplementedMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = Customer(**CUSTOMER__KWARGS)
        cls.customer.save()
        cls.base_encryption_key = u'LoremIpsum'

    def test_anonymize_customer(self):
        self.customer._anonymize_obj()
        anon_customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, u'first_name')
        self.assertNotEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataExists(anon_customer, u'last_name')

    def test_anonymization_of_anonymized_data(self):
        u'''Test that anonymized data are not anonymized again.'''
        self.customer._anonymize_obj()
        anon_customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, u'first_name')

        anon_customer._anonymize_obj()
        anon_customer2 = Customer.objects.get(pk=self.customer.pk)

        self.assertEqual(anon_customer2.first_name, anon_customer.first_name)
        self.assertNotEqual(anon_customer2.first_name, CUSTOMER__FIRST_NAME)

    def test_anonymization_field_matrix(self):
        self.customer._anonymize_obj(fields=(u'first_name',))
        anon_customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, u'first_name')

        self.assertEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, u'last_name')
