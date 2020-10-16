from __future__ import absolute_import
from typing import Callable

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.test import TestCase

from gdpr.models import AnonymizedData


class NotImplementedMixin(TestCase):
    def assertNotImplemented(self, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except AssertionError, exc:
            print u"NOT IMPLEMENTED:", self.id(), exc
        else:
            raise AssertionError(u"Function Implemented successfully!!")

    def assertNotImplementedNotEqual(self, *args, **kwargs):
        self.assertNotImplemented(self.assertNotEqual, *args, **kwargs)


class AnonymizedDataMixin(TestCase):
    def assertAnonymizedDataExists(self, obj, field):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        self.assertTrue(
            AnonymizedData.objects.filter(content_type=content_type, object_id=unicode(obj.pk), field=field).exists())

    def assertAnonymizedDataNotExists(self, obj, field):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        self.assertFalse(
            AnonymizedData.objects.filter(content_type=content_type, object_id=unicode(obj.pk), field=field).exists())
