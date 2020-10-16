# -*- coding: future_fstrings -*-
from __future__ import absolute_import
from __future__ import with_statement

import hashlib
import random
import string
import warnings

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.db import transaction
from typing import (
    Any, KeysView, List, Tuple, Union
)

from gdpr.anonymizers.base import FieldAnonymizer, RelationAnonymizer
from gdpr.fields import Fields
from gdpr.models import AnonymizedData
from gdpr.utils import get_field_or_none, get_reversion_version_model

FieldList = Union[List, Tuple, KeysView[unicode]]  # List, tuple or return of dict keys() method.
FieldMatrix = Union[unicode, Tuple[Any, ...]]


class ModelAnonymizerMeta(type):
    u"""
    Metaclass for anonymizers. The main purpose of the metaclass is to register anonymizers and find field anonymizers
    defined in the class as attributes and store it to the fields property.
    """

    def __new__(cls, name, bases, attrs):
        from gdpr.loading import anonymizer_register

        new_obj = super(ModelAnonymizerMeta, cls).__new__(cls, name, bases, attrs)

        # Also ensure initialization is only performed for subclasses of ModelAnonymizer
        # (excluding Model class itself).
        parents = [b for b in bases if isinstance(b, ModelAnonymizerMeta)]
        if not parents or not hasattr(new_obj, u'Meta'):
            return new_obj

        fields = getattr(new_obj, u'fields', {})

        for name, obj in attrs.items():
            if isinstance(obj, FieldAnonymizer):
                fields[name] = obj
        new_obj.fields = fields

        if not getattr(new_obj.Meta, u'abstract', False):
            anonymizer_register.register(new_obj.Meta.model, new_obj)

        return new_obj


class ModelAnonymizerBase(object):
    __metaclass__ = ModelAnonymizerMeta
    can_anonymize_qs = None
    fields = None
    _base_encryption_key = None

    class IrreversibleAnonymizerException(Exception):
        pass

    def __init__(self, base_encryption_key = None):
        self._base_encryption_key = base_encryption_key

    @property
    def model(self):
        return self.Meta.model  # type: ignore

    @property
    def content_type(self):
        u"""Get model ContentType"""
        return ContentType.objects.get_for_model(self.model)

    def __getitem__(self, item):
        return self.fields[item]

    def __contains__(self, item):
        return item in self.fields.keys()

    def __iter__(self):
        for i in self.fields:
            yield i

    def keys(self):
        return self.fields.keys()

    def items(self):
        return self.fields.items()

    def values(self):
        return self.fields.values()

    def get(self, *args, **kwargs):
        return self.fields.get(*args, **kwargs)

    def _get_encryption_key(self, obj, field_name):
        u"""Hash encryption key from `get_encryption_key` and append settings.GDPR_KEY or settings.SECRET_KEY."""
        return hashlib.sha256(
            u'{}::{}::'
            u'{}::{}'.format((obj.pk), (self.get_encryption_key(obj)), (settings.GDPR_KEY if hasattr(settings, u"GDPR_KEY") else settings.SECRET_KEY), (field_name)).encode(
                u'utf-8')).hexdigest()

    def is_reversible(self, obj):
        if hasattr(self.Meta, u'reversible_anonymization'):  # type: ignore
            return self.Meta.reversible_anonymization  # type: ignore
        return True

    def anonymize_reversion(self, obj):
        if hasattr(self.Meta, u'anonymize_reversion'):  # type: ignore
            return self.Meta.anonymize_reversion  # type: ignore
        return False

    def get_encryption_key(self, obj):
        if not self.is_reversible(obj):
            return u''.join(random.choices(string.digits + string.ascii_letters, k=128))
        if self._base_encryption_key:
            return self._base_encryption_key
        raise NotImplementedError(
            u'The anonymizer \'{}\' does not have `get_encryption_key` method defined or '
            u'`base_encryption_key` supplied during anonymization or '
            u'reversible_anonymization set to False.'.format((self.__class__.__name__)))

    def set_base_encryption_key(self, base_encryption_key):
        self._base_encryption_key = base_encryption_key

    def is_field_anonymized(self, obj, name):
        u"""Check if field have AnonymizedData record"""
        return AnonymizedData.objects.filter(
            field=name, is_active=True, content_type=self.content_type, object_id=unicode(obj.pk)
        ).exists()

    @staticmethod
    def is_generic_relation(field):
        return isinstance(field, RelationAnonymizer)

    def get_related_model(self, field_name):
        field = get_field_or_none(self.model, field_name)
        if field is None:
            if self.is_generic_relation(getattr(self, field_name, None)):
                return getattr(self, field_name).get_related_model()
            raise RuntimeError(u'Field \'{}\' is not defined on {}'.format((field_name), (unicode(self.model))))
        elif hasattr(field, u"related_model"):
            return field.related_model
        else:
            raise NotImplementedError(u'Relation {} not supported yet.'.format((unicode(field))))

    def get_value_from_obj(self, field, obj, name, anonymization = True):
        return field.get_value_from_obj(obj, name, self._get_encryption_key(obj, name), anonymization=anonymization)

    def get_value_from_version(self, field, obj, version, name,
                               anonymization = True):
        return field.get_value_from_version(
            obj, version, name, self._get_encryption_key(obj, name), anonymization=anonymization
        )

    def update_field_as_anonymized(self, obj, name, legal_reason = None,
                                   anonymization = True):
        if anonymization:
            AnonymizedData.objects.create(object=obj, field=name, expired_reason=legal_reason)
        else:
            AnonymizedData.objects.filter(
                field=name, is_active=True, content_type=self.content_type, object_id=unicode(obj.pk)
            ).delete()

    def mark_field_as_anonymized(self, obj, name, legal_reason = None):
        self.update_field_as_anonymized(obj, name, legal_reason, anonymization=True)

    def unmark_field_as_anonymized(self, obj, name):
        self.update_field_as_anonymized(obj, name, anonymization=False)

    def get_anonymized_value_from_obj(self, field, obj, name):
        u"""Get from field, obj and field name anonymized value."""
        return self.get_value_from_obj(field, obj, name, anonymization=True)

    def get_deanonymized_value_from_obj(self, field, obj, name):
        u"""Get from field, obj and field name deanonymized value."""
        return self.get_value_from_obj(field, obj, name, anonymization=False)

    def get_anonymized_value_from_version(self, field, obj, version, name):
        u"""Get from field, obj and field name anonymized value."""
        return self.get_value_from_version(field, obj, version, name, anonymization=True)

    def get_deanonymized_value_from_version(self, field, obj, version, name):
        u"""Get from field, obj and field name deanonymized value."""
        return self.get_value_from_version(field, obj, version, name, anonymization=False)

    def _perform_update(self, obj, updated_data, legal_reason = None,
                        anonymization = True):
        for field_name, value in updated_data.items():
            setattr(obj, field_name, value)
        obj.save()
        for field_name in updated_data.keys():
            self.update_field_as_anonymized(obj, field_name, legal_reason, anonymization=anonymization)

    def get_parent_models(self, model_or_obj):
        u"""From model get all it's parent models."""
        return model_or_obj._meta.get_parent_list()

    def get_all_parent_objects(self, obj):
        u"""Get all related parent objects."""
        parent_paths = [
            [path_info.join_field.name for path_info in parent_path]
            for parent_path in
            [obj._meta.get_path_to_parent(parent_model) for parent_model in self.get_parent_models(obj)]
        ]

        parent_objects = []
        for parent_path in parent_paths:
            parent_obj = obj
            for path in parent_path:
                parent_obj = getattr(parent_obj, path, None)
            parent_objects.append(parent_obj)

        return [i for i in parent_objects if i is not None]

    def get_reversion_versions(self, obj):
        from gdpr.utils import get_reversion_versions
        versions = [i for i in get_reversion_versions(obj)]  # QuerySet to list
        parent_obj_versions = [get_reversion_versions(i) for i in self.get_all_parent_objects(obj)]
        versions += [item for sublist in parent_obj_versions for item in sublist]
        return versions

    def _perform_anonymization(self, obj, updated_data,
                               legal_reason = None):
        self._perform_update(obj, updated_data, legal_reason, anonymization=True)

    def _perform_deanonymization(self, obj, updated_data):
        self._perform_update(obj, updated_data, anonymization=False)

    def perform_update(self, obj, updated_data, legal_reason = None,
                       anonymization = True):
        with transaction.atomic():
            self._perform_update(obj, updated_data, legal_reason, anonymization=anonymization)

    def perform_anonymization(self, obj, updated_data,
                              legal_reason = None):
        u"""Update data in database and mark them as anonymized."""
        self.perform_update(obj, updated_data, legal_reason, anonymization=True)

    def perform_deanonymization(self, obj, updated_data):
        u"""Update data in database and mark them as anonymized."""
        self.perform_update(obj, updated_data, anonymization=False)

    @staticmethod
    def _perform_version_update(version, update_data):
        from reversion import revisions
        if hasattr(version, u"object_version"):
            local_obj = version.object_version.object
        else:
            local_obj = version._object_version.object
        for field, value in update_data.items():
            setattr(local_obj, field, value)
        if hasattr(revisions, u'_get_options'):
            version_options = revisions._get_options(get_reversion_version_model(version))
            version_format = version_options.format
            version_fields = version_options.fields
        else:
            version_adapter = revisions.get_adapter(get_reversion_version_model(version))
            version_format = version_adapter.get_serialization_format()
            version_fields = list(version_adapter.get_fields_to_serialize())
        version.serialized_data = serializers.serialize(
            version_format,
            (local_obj,),
            fields=version_fields
        )
        version.save()

    def perform_update_with_version(self, obj, updated_data,
                                    updated_version_data,
                                    legal_reason = None,
                                    anonymization = True):
        with transaction.atomic():
            # first we need to update versions
            for version, version_dict in updated_version_data:
                self._perform_version_update(version, version_dict)
            self._perform_update(obj, updated_data, legal_reason, anonymization=anonymization)

    def perform_anonymization_with_version(self, obj, updated_data,
                                           updated_version_data,
                                           legal_reason = None):
        u"""Update data in database and versions and mark them as anonymized."""
        self.perform_update_with_version(obj, updated_data, updated_version_data, legal_reason, anonymization=True)

    def perform_deanonymization_with_version(self, obj, updated_data,
                                             updated_version_data):
        u"""Update data in database and mark them as anonymized."""
        self.perform_update_with_version(obj, updated_data, updated_version_data, anonymization=False)

    def anonymize_qs(self, qs):
        raise NotImplementedError()

    def deanonymize_qs(self, qs):
        raise NotImplementedError()

    def update_related_fields(self, parsed_fields, obj, legal_reason = None,
                              purpose = None, anonymization = True):
        for name, related_fields in parsed_fields.related_fields.items():
            related_attribute = getattr(obj, name, None)
            related_metafield = get_field_or_none(self.model, name)
            if related_attribute is None and related_metafield is None:
                if self.is_generic_relation(getattr(self, name, None)):
                    objs = getattr(self, name).get_related_objects(obj)
                    for related_obj in objs:
                        related_fields.anonymizer.update_obj(
                            related_obj, legal_reason, purpose, related_fields,
                            base_encryption_key=self._get_encryption_key(obj, name),
                            anonymization=anonymization
                        )
            elif related_metafield.one_to_many or related_metafield.many_to_many:
                for related_obj in related_attribute.all():
                    related_fields.anonymizer.update_obj(
                        related_obj, legal_reason, purpose, related_fields,
                        base_encryption_key=self._get_encryption_key(obj, name),
                        anonymization=anonymization
                    )
            elif (related_metafield.many_to_one or related_metafield.one_to_one) and related_attribute is not None:
                related_fields.anonymizer.update_obj(
                    related_attribute, legal_reason, purpose, related_fields,
                    base_encryption_key=self._get_encryption_key(obj, name),
                    anonymization=anonymization
                )
            elif related_attribute is not None:
                warnings.warn(u'Model anonymization discovered unreachable field {} on model'
                              u'{} on obj {} with pk {}'.format((name), (obj.__class__.__name__), (obj), (obj.pk)))

    def update_obj(self, obj, legal_reason = None,
                   purpose = None,
                   fields = u'__ALL__',
                   base_encryption_key = None,
                   anonymization = True):
        if not anonymization and not self.is_reversible(obj):
            raise self.IrreversibleAnonymizerException(u'{} for obj "{}" is not reversible.'.format((self.__class__.__name__), (obj)))

        if base_encryption_key:
            self._base_encryption_key = base_encryption_key

        parsed_fields = Fields(fields, obj.__class__) if not isinstance(fields, Fields) else fields

        if anonymization:
            raw_local_fields = [i for i in parsed_fields.local_fields if not self.is_field_anonymized(obj, i)]
        else:
            raw_local_fields = [i for i in parsed_fields.local_fields if
                                self.is_field_anonymized(obj, i) and self[i].get_is_reversible(obj)]

        if raw_local_fields:
            update_dict = dict((
                name, self.get_value_from_obj(self[name], obj, name, anonymization)) for name in raw_local_fields)
            if self.anonymize_reversion(obj):
                from gdpr.utils import get_reversion_local_field_dict
                versions = self.get_reversion_versions(obj)
                versions_update_dict = [
                    (
                        version,
                        dict((
                            name, self.get_value_from_version(self[name], obj, version, name,
                                                              anonymization=anonymization))
                            for name in raw_local_fields
                            if name in get_reversion_local_field_dict(version))
                    )
                    for version in versions
                ]
                self.perform_update_with_version(
                    obj, update_dict, versions_update_dict, legal_reason,
                    anonymization=anonymization
                )
            else:
                self.perform_update(obj, update_dict, legal_reason, anonymization=anonymization)

        self.update_related_fields(parsed_fields, obj, legal_reason, purpose, anonymization)

    def anonymize_obj(self, obj, legal_reason = None,
                      purpose = None,
                      fields = u'__ALL__', base_encryption_key = None):

        self.update_obj(obj, legal_reason, purpose, fields, base_encryption_key, anonymization=True)

    def deanonymize_obj(self, obj, fields = u'__ALL__',
                        base_encryption_key = None):

        self.update_obj(obj, fields=fields, base_encryption_key=base_encryption_key, anonymization=False)


class ModelAnonymizer(ModelAnonymizerBase):
    u"""
    Default model anonymizer that supports anonymization per object.
    Child must define Meta class with model (like factoryboy)
    """

    can_anonymize_qs = False
    chunk_size = 10000


class DeleteModelAnonymizer(ModelAnonymizer):
    u"""
    The simpliest anonymization class that is used for removing whole input queryset.

    For anonymization add `__SELF__` to the FieldMatrix.
    """

    can_anonymize_qs = True

    DELETE_FIELD_NAME = u'__SELF__'

    def update_obj(self, obj, legal_reason = None,
                   purpose = None,
                   fields = u'__ALL__',
                   base_encryption_key = None,
                   anonymization = True):
        parsed_fields = Fields(fields, obj.__class__) if not isinstance(fields, Fields) else fields

        if self.DELETE_FIELD_NAME in parsed_fields.local_fields and anonymization is True:
            self.update_related_fields(parsed_fields, obj, legal_reason, purpose, anonymization)

            obj.__class__.objects.filter(pk=obj.pk).delete()

            if self.anonymize_reversion(obj):
                from gdpr.utils import get_reversion_versions
                get_reversion_versions(obj).delete()

        elif self.DELETE_FIELD_NAME in parsed_fields.local_fields:
            parsed_fields.local_fields = [i for i in parsed_fields.local_fields if i != self.DELETE_FIELD_NAME]
            super(DeleteModelAnonymizer, self).update_obj(obj, legal_reason, purpose, parsed_fields, base_encryption_key, anonymization)
        else:
            super(DeleteModelAnonymizer, self).update_obj(obj, legal_reason, purpose, parsed_fields, base_encryption_key, anonymization)

    def anonymize_qs(self, qs):
        qs.delete()
