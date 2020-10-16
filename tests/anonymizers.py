# -*- coding: future_fstrings -*-
from __future__ import absolute_import
from gdpr import anonymizers
from tests.models import Customer, Note


class CustomerAnonymizer(anonymizers.ModelAnonymizer):
    first_name = anonymizers.MD5TextFieldAnonymizer()
    last_name = anonymizers.MD5TextFieldAnonymizer()
    notes = anonymizers.ReverseGenericRelationAnonymizer(u'tests', u'Note')

    def get_encryption_key(self, obj):
        return (u"{}::{}::"
                u"{}".format(((obj.first_name or u'').strip()), ((obj.last_name or u'').strip()), ((obj.primary_email_address or u'').strip())))

    class Meta(object):
        model = Customer
