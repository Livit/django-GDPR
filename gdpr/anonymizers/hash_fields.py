# -*- coding: future_fstrings -*-
from __future__ import absolute_import

import hashlib

from gdpr.anonymizers.base import FieldAnonymizer


class BaseHashTextFieldAnonymizer(FieldAnonymizer):
    algorithm = None
    is_reversible = False

    def get_encrypted_value(self, value, encryption_key):
        h = hashlib.new(self.algorithm)
        h.update(value.encode(u'utf-8'))
        return h.hexdigest()[:len(value)] if value else value


class MD5TextFieldAnonymizer(BaseHashTextFieldAnonymizer):
    algorithm = u'md5'


class SHA256TextFieldAnonymizer(BaseHashTextFieldAnonymizer):
    algorithm = u'sha256'


class HashTextFieldAnonymizer(BaseHashTextFieldAnonymizer):

    def __init__(self, algorithm, *args, **kwargs):
        if algorithm not in hashlib.algorithms_guaranteed:
            raise RuntimeError(u'Hash algorithm {} is not supported by python hashlib.'.format((algorithm)))
        self.algorithm = algorithm

        super(HashTextFieldAnonymizer, self).__init__(*args, **kwargs)
