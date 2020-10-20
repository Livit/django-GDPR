from __future__ import absolute_import

from gdpr.loading import anonymizer_register


class Fields(object):

    def __init__(self, fields, model, anonymizer_instance = None):
        self.model = model
        self.anonymizer = anonymizer_register[self.model]() if anonymizer_instance is None else anonymizer_instance
        self.local_fields = self.parse_local_fields(fields)
        self.related_fields = self.parse_related_fields(fields)

    def parse_local_fields(self, fields):
        u"""Get Iterable of local fields from fields matrix."""
        if fields == u'__ALL__' or (u'__ALL__' in fields and type(fields) not in (unicode, str)):
            return list(self.anonymizer.keys())

        return [field for field in fields if type(field) in (unicode, str)]

    def parse_related_fields(self, fields):
        u"""Get Dictionary of related fields from fields matrix."""
        out_dict = {}
        for name, related_fields in [field_tuple for field_tuple in fields if type(field_tuple) in [list, tuple]]:
            out_dict[name] = Fields(related_fields, self.anonymizer.get_related_model(name))

        return out_dict

    def get_tuple(self):
        l1 = self.local_fields
        l2 = [(name, fields.get_tuple()) for name, fields in self.related_fields.items()]
        return tuple(l1 + l2)

    def __len__(self):
        return len(self.local_fields) + len(self.related_fields)

    def __isub__(self, other):
        self.local_fields = [field for field in self.local_fields if field not in other.local_fields]

        for name, related_fields in self.related_fields.items():
            if name in other.related_fields:
                related_fields -= other.related_fields[name]

        for name in list(self.related_fields.keys()):
            if len(self.related_fields[name]) == 0:
                del self.related_fields[name]

        return self
