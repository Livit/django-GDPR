from __future__ import absolute_import
from django.test import TestCase

from gdpr.fields import Fields
from tests.anonymizers import CustomerAnonymizer
from tests.models import Customer

LOCAL_FIELDS = (u"first_name", u"last_name")


class TestFields(TestCase):
    def test_local_all(self):
        fields = Fields(u'__ALL__', Customer)
        self.assertListEqual(fields.local_fields, list(CustomerAnonymizer().fields.keys()))

    def test_local(self):
        fields = Fields(LOCAL_FIELDS, Customer)
        self.assertListEqual(fields.local_fields, list(LOCAL_FIELDS))
