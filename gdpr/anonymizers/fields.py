# -*- coding: future_fstrings -*-
from __future__ import absolute_import
import json
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.base import ContentFile, File
from django.utils.inspect import func_supports_parameter
from unidecode import unidecode

from gdpr.anonymizers.base import FieldAnonymizer, NumericFieldAnonymizer
from gdpr.encryption import (
    JSON_SAFE_CHARS, decrypt_email_address, decrypt_text, encrypt_email_address, encrypt_text, numerize_key,
    translate_iban, translate_number, translate_text)
from gdpr.utils import get_number_guess_len
from io import open


class FunctionFieldAnonymizer(FieldAnonymizer):
    u"""
    Use this field anonymization for defining in place lambda anonymization method.

    Example:
    ```
    secret_code = FunctionFieldAnonymizer(lambda self, x, key: x**2)
    ```

    If you want to supply anonymization and deanonymization you can do following:
    ```
    secret_code = FunctionFieldAnonymizer(
        func=lambda self, x, key: x**2+self.get_numeric_encryption_key(key),
        deanonymize_func=lambda a, x, key: x**2-a.get_numeric_encryption_key(key)
        )
    ```
    """
    def __init__(self,
                 anon_func,
                 deanonymize_func = None,
                 *args, **kwargs):
        super(FunctionFieldAnonymizer, self).__init__(*args, **kwargs)
        if callable(anon_func):
            self.anon_func = anon_func  # type: ignore
        else:
            raise ImproperlyConfigured(u'Supplied func is not callable.')

        if callable(deanonymize_func):
            self.deanonymize_func = deanonymize_func
        elif deanonymize_func is not None:
            raise ImproperlyConfigured(u'Supplied deanonymize_func is not callable.')

    def get_numeric_encryption_key(self, encryption_key):
        return numerize_key(encryption_key) % self.max_anonymization_range

    def get_encrypted_value(self, value, encryption_key):
        if self.deanonymize_func is None:
            return self.anon_func(value, encryption_key)
        else:
            return self.anon_func(self, value, encryption_key)

    def get_is_reversible(self, obj=None, raise_exception = False):
        is_reversible = self.deanonymize_func is not None
        if not is_reversible:
            raise self.IrreversibleAnonymizationException
        return is_reversible

    def get_decrypted_value(self, value, encryption_key):
        if not self.get_is_reversible():
            raise self.IrreversibleAnonymizationException()
        else:
            return self.deanonymize_func(self, value, encryption_key)  # type: ignore


class DateTimeFieldAnonymizer(NumericFieldAnonymizer):
    u"""
    Anonymization for DateTimeField.

    """

    max_anonymization_range = 365 * 24 * 60 * 60

    def get_encrypted_value(self, value, encryption_key):
        return value - timedelta(seconds=(self.get_numeric_encryption_key(encryption_key) + 1))

    def get_decrypted_value(self, value, encryption_key):
        return value + timedelta(seconds=(self.get_numeric_encryption_key(encryption_key) + 1))


class DateFieldAnonymizer(NumericFieldAnonymizer):
    u"""
    Anonymization for DateField.

    """

    max_anonymization_range = 365

    def get_encrypted_value(self, value, encryption_key):
        return value - timedelta(days=(self.get_numeric_encryption_key(encryption_key) + 1))

    def get_decrypted_value(self, value, encryption_key):
        return value + timedelta(days=(self.get_numeric_encryption_key(encryption_key) + 1))


class CharFieldAnonymizer(FieldAnonymizer):
    u"""
    Anonymization for CharField.

    transliterate - The CharFieldAnonymizer encrypts only ASCII chars and non-ascii chars are left the same e.g.:
    `François` -> `rbTTç]3d` if True the original text is transliterated e.g. `François` -> 'Francois' -> `rbTTQ9Zg`.
    """

    transliterate = False
    empty_values = [None, u'']

    def __init__(self, *args, **kwargs):
        if 'transliterate' in kwargs: transliterate = kwargs['transliterate']; del kwargs['transliterate']
        else: transliterate =  False
        self.transliterate = transliterate
        super(CharFieldAnonymizer, self).__init__(*args, **kwargs)

    def get_encrypted_value(self, value, encryption_key):
        return encrypt_text(encryption_key, value if not self.transliterate else unidecode(value))

    def get_decrypted_value(self, value, encryption_key):
        return decrypt_text(encryption_key, value)


class EmailFieldAnonymizer(FieldAnonymizer):

    empty_values = [None, u'']

    def get_encrypted_value(self, value, encryption_key):
        return encrypt_email_address(encryption_key, value)

    def get_decrypted_value(self, value, encryption_key):
        return decrypt_email_address(encryption_key, value)


class DecimalFieldAnonymizer(NumericFieldAnonymizer):
    u"""
    Anonymization for CharField.
    """

    def get_encrypted_value(self, value, encryption_key):
        return translate_number(unicode(self.get_numeric_encryption_key(encryption_key)), value)

    def get_decrypted_value(self, value, encryption_key):
        return translate_number(unicode(self.get_numeric_encryption_key(encryption_key)), value, encrypt=False)


class IntegerFieldAnonymizer(NumericFieldAnonymizer):
    u"""
    Anonymization for IntegerField.
    """

    def get_encrypted_value(self, value, encryption_key):
        return translate_number(unicode(self.get_numeric_encryption_key(encryption_key)), value)

    def get_decrypted_value(self, value, encryption_key):
        return translate_number(unicode(self.get_numeric_encryption_key(encryption_key)), value, encrypt=False)

class IBANFieldAnonymizer(FieldAnonymizer):
    u"""
    Field anonymizer for International Bank Account Number.
    """

    empty_values = [None, u'']

    def get_decrypted_value(self, value, encryption_key):
        return translate_iban(encryption_key, value)

    def get_encrypted_value(self, value, encryption_key):
        return translate_iban(encryption_key, value, False)


class JSONFieldAnonymizer(FieldAnonymizer):
    u"""
    Anonymization for JSONField.
    """

    empty_values = [None, u'']

    def get_numeric_encryption_key(self, encryption_key, value = None):
        if value is None:
            return numerize_key(encryption_key)
        return numerize_key(encryption_key) % 10 ** get_number_guess_len(value)

    def anonymize_json_value(self, value,
                             encryption_key,
                             anonymize = True):
        if value is None:
            return None
        elif type(value) is unicode:
            return translate_text(encryption_key, value, anonymize, JSON_SAFE_CHARS)  # type: ignore
        elif type(value) is int:
            return translate_number(encryption_key, value, anonymize)  # type: ignore
        elif type(value) is float:
            # We cannot safely anonymize floats
            return value
        elif type(value) is dict:
            return dict((key, self.anonymize_json_value(item, encryption_key, anonymize)) for key, item in
                    value.items())  # type: ignore
        elif type(value) is list:
            return [self.anonymize_json_value(item, encryption_key, anonymize) for item in value]  # type: ignore
        elif type(value) is bool and self.get_numeric_encryption_key(encryption_key) % 2 == 0:
            return not value
        return value

    def get_encrypted_value(self, value, encryption_key):
        if type(value) not in [dict, list, unicode]:
            raise ValidationError(u"JSONFieldAnonymizer encountered unknown type of json. "
                                  u"Only python dict and list are supported.")
        if type(value) == unicode:
            return json.dumps(self.anonymize_json_value(json.loads(value), encryption_key))
        return self.anonymize_json_value(value, encryption_key)

    def get_decrypted_value(self, value, encryption_key):
        if type(value) not in [dict, list, unicode]:
            raise ValidationError(u"JSONFieldAnonymizer encountered unknown type of json. "
                                  u"Only python dict and list are supported.")
        if type(value) == unicode:
            return json.dumps(self.anonymize_json_value(json.loads(value), encryption_key, anonymize=False))
        return self.anonymize_json_value(value, encryption_key, anonymize=False)


class StaticValueFieldAnonymizer(FieldAnonymizer):
    u"""
    Static value anonymizer replaces value with defined static value.
    """

    is_reversible = False
    empty_values = [None, u'']

    def __init__(self, value, *args, **kwargs):
        super(StaticValueFieldAnonymizer, self).__init__(*args, **kwargs)
        self.value = value

    def get_encrypted_value(self, value, encryption_key):
        return self.value


class SiteIDUsernameFieldAnonymizer(FieldAnonymizer):
    u"""
    Encrypts username in format 1:foo@bar.com
    """

    empty_values = [None, u'']

    def get_encrypted_value(self, value, encryption_key):
        split = value.split(u':', 1)
        if len(split) == 2:
            return u'{}:{}'.format((split[0]), (encrypt_email_address(encryption_key, split[1])))
        return encrypt_email_address(encryption_key, value)

    def get_decrypted_value(self, value, encryption_key):
        split = value.split(u':', 1)
        if len(split) == 2:
            return u'{}:{}'.format((split[0]), (decrypt_email_address(encryption_key, split[1])))
        return decrypt_email_address(encryption_key, value)


class FileFieldAnonymizer(FieldAnonymizer):
    u"""
    Base class for all FileFieldAnonymizers.

    Overrides ``get_is_value_empty`` to check for files.
    """

    def get_is_value_empty(self, value):
        return self.get_ignore_empty_values(value) and not bool(value)


class DeleteFileFieldAnonymizer(FileFieldAnonymizer):
    u"""
    One way anonymization of FileField.
    """

    is_reversible = False

    def get_encrypted_value(self, value, encryption_key):
        value.delete(save=False)
        return value


class ReplaceFileFieldAnonymizer(FileFieldAnonymizer):
    u"""
    One way anonymization of FileField.
    """

    is_reversible = False
    replacement_file = None

    def __init__(self, replacement_file = None, *args, **kwargs):
        if replacement_file is not None:
            self.replacement_file = replacement_file
        super(ReplaceFileFieldAnonymizer, self).__init__(*args, **kwargs)

    def get_replacement_file(self):
        if self.replacement_file is not None:
            return File(open(self.replacement_file, u"rb"))
        elif getattr(settings, u"GDPR_REPLACE_FILE_PATH", None) is not None:
            return File(open(getattr(settings, u"GDPR_REPLACE_FILE_PATH"), u"rb"))
        else:
            return ContentFile(u"THIS FILE HAS BEEN ANONYMIZED.")

    def get_encrypted_value(self, value, encryption_key):
        file_name = value.name
        value.delete(save=False)
        file = self.get_replacement_file()

        if func_supports_parameter(value.storage.save, u'max_length'):
            value.name = value.storage.save(file_name, file, max_length=value.field.max_length)
        else:
            #  Backwards compatibility removed in Django 1.10
            value.name = value.storage.save(file_name, file)
        setattr(value.instance, value.field.name, value.name)

        value._size = file.size  # Django 1.8 + 1.9
        value._committed = True
        file.close()

        return value
