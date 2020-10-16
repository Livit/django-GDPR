# -*- coding: future_fstrings -*-
from __future__ import absolute_import

import warnings

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.db.utils import Error

from gdpr.models import AnonymizedData, LegalReason, LegalReasonRelatedObject


class AnonymizationModelMixin(object):

    @property
    def content_type(self):
        u"""Get model ContentType"""
        return ContentType.objects.get_for_model(self.__class__)

    def _anonymize_obj(self, *args, **kwargs):
        from gdpr.loading import anonymizer_register
        if self.__class__ in anonymizer_register:
            anonymizer_register[self.__class__]().anonymize_obj(self, *args, **kwargs)
        else:
            raise ImproperlyConfigured(u'%s does not have registered anonymizer.' % self.__class__)

    def _deanonymize_obj(self, *args, **kwargs):
        from gdpr.loading import anonymizer_register
        if self.__class__ in anonymizer_register:
            anonymizer_register[self.__class__]().deanonymize_obj(self, *args, **kwargs)
        else:
            raise ImproperlyConfigured(u'%s does not have registered anonymizer.' % self.__class__)

    def get_consents(self):
        return LegalReason.objects.filter_source_instance(self)

    def create_consent(self, purpose_slug, *args, **kwargs):
        return LegalReason.objects.create_consent(purpose_slug, self, *args, **kwargs)

    def deactivate_consent(self, purpose_slug):
        LegalReason.objects.deactivate_consent(purpose_slug, self)

    def delete(self, *args, **kwargs):
        u"""Cleanup anonymization metadata"""
        obj_id = unicode(self.pk)
        super(AnonymizationModelMixin, self).delete(*args, **kwargs)
        try:
            AnonymizedData.objects.filter(object_id=obj_id, content_type=self.content_type).delete()
        except Error, e:
            # Better to just have some leftovers then to fail
            warnings.warn('An exception {} occurred during cleanup of {}'.format((unicode(e)), (unicode(self))))
        try:
            LegalReasonRelatedObject.objects.filter(object_id=obj_id, object_content_type=self.content_type).delete()
        except Error, e:
            # Better to just have some leftovers then to fail
            warnings.warn('An exception {} occurred during cleanup of {}'.format((unicode(e)), (unicode(self))))


class AnonymizationModel(AnonymizationModelMixin, Model):
    class Meta(object):
        abstract = True
