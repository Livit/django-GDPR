from __future__ import absolute_import
from django.test import TestCase

from tests.models import Customer
from .data import (
    CUSTOMER__BIRTH_DATE, CUSTOMER__EMAIL, CUSTOMER__FACEBOOK_ID, CUSTOMER__FIRST_NAME, CUSTOMER__IP, CUSTOMER__KWARGS,
    CUSTOMER__LAST_NAME,
    CUSTOMER__PERSONAL_ID, CUSTOMER__PHONE_NUMBER)
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
        self.assertNotEqual(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_customer, u'primary_email_address')
        self.assertNotEquals(anon_customer.birth_date, CUSTOMER__BIRTH_DATE)
        self.assertAnonymizedDataExists(anon_customer, u'first_name')
        self.assertNotEquals(anon_customer.facebook_id, CUSTOMER__FACEBOOK_ID)
        self.assertAnonymizedDataExists(anon_customer, u'first_name')
        self.assertNotEqual(unicode(anon_customer.last_login_ip), CUSTOMER__IP)
        self.assertAnonymizedDataExists(anon_customer, u'first_name')

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
