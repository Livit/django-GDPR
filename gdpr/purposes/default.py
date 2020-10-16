from __future__ import absolute_import

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from typing import Any, Dict, KeysView, List, Tuple, Union

from gdpr.enums import LegalReasonState
from gdpr.fields import Fields
from gdpr.loading import anonymizer_register, purpose_register

FieldList = Union[List[unicode], Tuple, KeysView[unicode]]  # List, tuple or return of dict keys() method.
FieldMatrix = Union[unicode, Tuple[Any, ...]]
RelatedMatrix = Dict[unicode, FieldMatrix]


class PurposeMetaclass(type):

    def __new__(mcs, name, bases, attrs):
        from gdpr.loading import purpose_register

        new_class = super(PurposeMetaclass, mcs).__new__(mcs, name, bases, attrs)
        if hasattr(new_class, u'slug') and new_class.slug:
            if new_class.slug in purpose_register:
                raise ImproperlyConfigured(u'More anonymization purposes with slug {}'.format(new_class.slug))

            purpose_register.register(new_class.slug, new_class)
        return new_class

    def __str__(self):
        return unicode(self.name)


class AbstractPurpose(object):
    __metaclass__ = PurposeMetaclass
    u"""

    :param anonymize_legal_reason_related_object_only: If True anonymize only related objects which have links which
    have LegalReasonRelatedObject records.
    """

    name = None
    slug = None
    fields = None
    expiration_timedelta = None
    anonymize_legal_reason_related_objects_only = None

    def get_parsed_fields(self, model):
        return Fields(self.fields or (), model)

    def deanonymize_obj(self, obj, fields = None):
        fields = fields or self.fields or ()
        if len(fields) == 0:
            # If there are no fields to deanonymize do nothing.
            return
        obj_model = obj.__class__
        anonymizer  = anonymizer_register[obj_model]()
        anonymizer.deanonymize_obj(obj, fields)

    def anonymize_obj(self, obj, legal_reason = None,
                      fields = None):
        fields = fields or self.fields or ()
        if len(fields) == 0:
            # If there are no fields to anonymize do nothing.
            return
        from gdpr.models import LegalReason  # noqa

        obj_model = obj.__class__
        anonymizer  = anonymizer_register[obj_model]()

        # MultiLegalReason
        other_legal_reasons = LegalReason.objects.filter_source_instance(obj).filter(state=LegalReasonState.ACTIVE)
        if legal_reason:
            other_legal_reasons = other_legal_reasons.filter(~Q(pk=legal_reason.pk))
        if other_legal_reasons.count() == 0:
            anonymizer.anonymize_obj(obj, legal_reason, self, fields)
            return

        from gdpr.loading import purpose_register

        parsed_fields = self.get_parsed_fields(obj_model)

        # Transform legal_reasons to fields
        for allowed_fields in [purpose_register[slug]().get_parsed_fields(obj_model) for slug in
                               set([i.purpose_slug for i in other_legal_reasons])]:
            parsed_fields -= allowed_fields

        if len(parsed_fields) == 0:
            # If there are no fields to anonymize do nothing.
            return

        anonymizer.anonymize_obj(obj, legal_reason, self, parsed_fields)


purposes_map = purpose_register  # Backwards compatibility
