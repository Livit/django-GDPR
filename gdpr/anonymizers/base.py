from __future__ import absolute_import
from typing import Any, Iterable, List, Optional, Union, Type

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model

from gdpr.encryption import numerize_key
from gdpr.utils import get_number_guess_len


class RelationAnonymizer(object):
    u"""
    Base class for Anonymizers defining special relations.
    """

    model = None

    def get_related_objects(self, obj):
        raise NotImplementedError

    def get_related_model(self):
        return self.model


class FieldAnonymizer(object):
    u"""
    Field anonymizer's purpose is to anonymize model field according to defined rule.
    """

    ignore_empty_values= True
    empty_values = [None]
    _encryption_key = None
    is_reversible = True

    class IrreversibleAnonymizationException(Exception):
        pass

    def __init__(self, ignore_empty_values = None, empty_values = None):
        u"""
        Args:
            ignore_empty_values: defines if empty value of a model will be ignored or should be anonymized too
            empty_values: defines list of values which are considered as empty
        """
        self._ignore_empty_values = ignore_empty_values if ignore_empty_values is not None else self.ignore_empty_values
        self._empty_values = empty_values if empty_values is not None else self.empty_values

    def get_is_reversible(self, obj=None, raise_exception = False):
        u"""This method allows for custom implementation."""
        if not self.is_reversible and raise_exception:
            raise self.IrreversibleAnonymizationException
        return self.is_reversible

    def get_ignore_empty_values(self, value):
        return self._ignore_empty_values

    def get_is_value_empty(self, value):
        return self.get_ignore_empty_values(value) and value in self._empty_values

    def _get_anonymized_value_from_value(self, value, encryption_key):
        if self.get_is_value_empty(value):
            return value
        return self.get_encrypted_value(value, encryption_key)

    def _get_deanonymized_value_from_value(self, obj, value, encryption_key):
        if self.get_is_reversible(obj, raise_exception=True):
            if self.get_is_value_empty(value):
                return value
            return self.get_decrypted_value(value, encryption_key)

    def get_value_from_obj(self, obj, name, encryption_key, anonymization = True):
        if anonymization:
            return self._get_anonymized_value_from_value(getattr(obj, name), encryption_key)
        return self._get_deanonymized_value_from_value(obj, getattr(obj, name), encryption_key)

    def get_value_from_version(self, obj, version, name, encryption_key, anonymization = True):
        if anonymization:
            return self._get_anonymized_value_from_value(version.field_dict[name], encryption_key)
        return self._get_deanonymized_value_from_value(obj, version.field_dict[name], encryption_key)

    def get_anonymized_value_from_obj(self, obj, name, encryption_key):
        return self.get_value_from_obj(obj, name, encryption_key, anonymization=True)

    def get_deanonymized_value_from_obj(self, obj, name, encryption_key):
        return self.get_value_from_obj(obj, name, encryption_key, anonymization=False)

    def get_anonymized_value_from_version(self, obj, version, name, encryption_key):
        return self.get_value_from_version(obj, version, name, encryption_key, anonymization=True)

    def get_deanonymized_value_from_version(self, obj, version, name, encryption_key):
        return self.get_value_from_version(obj, version, name, encryption_key, anonymization=False)

    def get_anonymized_value(self, value):
        u"""
        Deprecated
        """
        raise DeprecationWarning()

    def get_encrypted_value(self, value, encryption_key):
        u"""
        There must be defined implementation of rule for anonymization

        :param value: value
        :param encryption_key: The encryption key
        :return: Encrypted value
        """
        raise NotImplementedError

    def get_decrypted_value(self, value, encryption_key):
        u"""
        There must be defined implementation of rule for deanonymization.

        :param value: Encrypted value
        :param encryption_key: The encryption key
        :return: Decrypted value
        """
        if self.get_is_reversible(raise_exception=True):
            raise NotImplementedError


class NumericFieldAnonymizer(FieldAnonymizer):
    max_anonymization_range = None

    def __init__(self, max_anonymization_range = None, ignore_empty_values = None,
                 empty_values = None):
        if max_anonymization_range is not None:
            self.max_anonymization_range = max_anonymization_range
        super(NumericFieldAnonymizer, self).__init__(ignore_empty_values, empty_values)

    def get_numeric_encryption_key(self, encryption_key, value = None):
        u"""
        From `encryption_key` create it's numeric counterpart of appropriate length.

        If value is supplied then the appropriate length is based on it if not the
        parameter `self.max_anonymization_range` is used.

        If the numeric_encryption_key is used the value+key may be one order bigger then the original value.

        e.g. value=5, numeric_encryption_key=8 => len('13') == 2

        :param encryption_key: The encryption key generated by anonymizer.
        :param value: Value to which the result of this function will be used.
        :return: Numeric counterpart of encryption_key
        """
        if value is None:
            if self.max_anonymization_range is None:
                return numerize_key(encryption_key)
            return numerize_key(encryption_key) % self.max_anonymization_range

        return numerize_key(encryption_key) % 10 ** get_number_guess_len(value)
