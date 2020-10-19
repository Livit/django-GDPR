from __future__ import absolute_import

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from faker import Faker

from gdpr.enums import LegalReasonState
from gdpr.models import LegalReason
from tests.models import Customer
from tests.purposes import (
    FIRST_AND_LAST_NAME_SLUG)
from tests.tests.data import (
    CUSTOMER__EMAIL,
    CUSTOMER__FIRST_NAME, CUSTOMER__KWARGS,
    CUSTOMER__LAST_NAME)
from tests.tests.utils import AnonymizedDataMixin, NotImplementedMixin


class TestLegalReason(AnonymizedDataMixin, NotImplementedMixin, TestCase):
    def setUp(self):
        self.fake = Faker()

    @classmethod
    def setUpTestData(cls):
        cls.customer = Customer(**CUSTOMER__KWARGS)
        cls.customer.save()

    def test_create_legal_reason_from_slug(self):
        LegalReason.objects.create_consent(FIRST_AND_LAST_NAME_SLUG, self.customer).save()

        self.assertTrue(LegalReason.objects.filter(
            purpose_slug=FIRST_AND_LAST_NAME_SLUG, source_object_id=self.customer.pk,
            source_object_content_type=ContentType.objects.get_for_model(Customer)).exists())

    def test_expirement_legal_reason(self):
        """
        When the Legal Reason expires, respective data gets anonymized
        """
        legal = LegalReason.objects.create_consent(FIRST_AND_LAST_NAME_SLUG, self.customer)
        self.assertEqual(legal.state, LegalReasonState.ACTIVE)
        legal.expire()
        self.assertEqual(legal.state, LegalReasonState.EXPIRED)

        anon_customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, u"first_name")
        self.assertNotEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataExists(anon_customer, u"last_name")
        # make sure only data we want were anonymized
        self.assertEqual(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataNotExists(anon_customer, u"primary_email_address")

    def test_renew_legal_reason(self):
        legal = LegalReason.objects.create_consent(FIRST_AND_LAST_NAME_SLUG, self.customer)
        legal.expire()
        legal.renew()
        self.assertEqual(legal.state, LegalReasonState.ACTIVE)

        anon_customer = Customer.objects.get(pk=self.customer.pk)

        # Non reversible anonymization
        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, u"first_name")
        self.assertNotEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataExists(anon_customer, u"last_name")
