from __future__ import absolute_import

import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from faker import Faker
from freezegun import freeze_time

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

    def test_object_interface(self):
        """
        Create a consent and deactivate it, using AnonymizationModel mixin interface
        """
        customer = Customer.objects.get(pk=self.customer.pk)
        self.assertEqual(0, len(customer.get_consents()))
        #
        # create a consent
        #
        customer.create_consent(FIRST_AND_LAST_NAME_SLUG)
        self.assertEqual(1, len(customer.get_consents()))
        self.assertEqual(1, LegalReason.objects.count())

        legal = LegalReason.objects.first()

        self.assertEqual(legal.state, LegalReasonState.ACTIVE)

        #
        # deactivate (this equals lega.expire(), just a more handy interface
        #
        customer.deactivate_consent(FIRST_AND_LAST_NAME_SLUG)
        legal = LegalReason.objects.first()
        self.assertEqual(legal.state, LegalReasonState.DEACTIVATED)

        # deactivation should result in anonymization
        customer = Customer.objects.get(pk=self.customer.pk)
        self.assertNotEqual(customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(customer, u"first_name")
        self.assertNotEqual(customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataExists(customer, u"last_name")
        # make sure only data we want were anonymized
        self.assertEqual(customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataNotExists(customer, u"primary_email_address")

    def test_expire_old_consents_positive(self):
        """
        1. Create a consent
        2. Let it get old by mocking time
        3. run LegalReason.objects.expire_old_consents() and make sure it expired
            and data got anonymized.
        """
        customer = Customer.objects.get(pk=self.customer.pk)
        customer.create_consent(FIRST_AND_LAST_NAME_SLUG)

        # some time travel stuff from grandpa's garage
        now = datetime.datetime.now()
        future = now + relativedelta(years=10, days=1)

        with freeze_time(future):
            LegalReason.objects.expire_old_consents()

            # names should be anonymized
            customer = Customer.objects.get(pk=self.customer.pk)
            self.assertNotEqual(customer.first_name, CUSTOMER__FIRST_NAME)
            self.assertAnonymizedDataExists(customer, u"first_name")
            self.assertNotEqual(customer.last_name, CUSTOMER__LAST_NAME)
            self.assertAnonymizedDataExists(customer, u"last_name")
            # make sure only data we want were anonymized
            self.assertEqual(customer.primary_email_address, CUSTOMER__EMAIL)
            self.assertAnonymizedDataNotExists(customer, u"primary_email_address")

    def test_expire_old_consents_too_early(self):
        """
        1. Create a consent
        2. Let it get old by mocking time, by too young to expire
        3. run LegalReason.objects.expire_old_consents() and make sure it DID NOT expire
        """
        customer = Customer.objects.get(pk=self.customer.pk)
        customer.create_consent(FIRST_AND_LAST_NAME_SLUG)

        # some time travel stuff from grandpa's garage
        now = datetime.datetime.now()
        future = now + relativedelta(years=9, days=363)

        with freeze_time(future):
            LegalReason.objects.expire_old_consents()

            # names should be anonymized
            customer = Customer.objects.get(pk=self.customer.pk)
            self.assertEqual(customer.first_name, CUSTOMER__FIRST_NAME)
            self.assertAnonymizedDataNotExists(customer, u"first_name")
            self.assertEqual(customer.last_name, CUSTOMER__LAST_NAME)
            self.assertAnonymizedDataNotExists(customer, u"last_name")
            self.assertEqual(customer.primary_email_address, CUSTOMER__EMAIL)
            self.assertAnonymizedDataNotExists(customer, u"primary_email_address")
