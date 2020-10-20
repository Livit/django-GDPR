# -*- coding: future_fstrings -*-
u"""
Models for test app:

Customer
  - Email
  - Address
  - AccountNumber
    - Payment

"""
from __future__ import absolute_import
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from gdpr.mixins import AnonymizationModel
from gdpr.utils import is_reversion_installed


class Customer(AnonymizationModel):
    # Keys for pseudoanonymization
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    primary_email_address = models.EmailField(blank=True, null=True)

    def save(self, *args, **kwargs):
        u"""Just helper method for saving full name.

        You can ignore this method.
        """
        self.full_name = u"%s %s" % (self.first_name, self.last_name)
        super(Customer, self).save(*args, **kwargs)

    def __str__(self):
        return u"{} {}".format((self.first_name), (self.last_name))


class TopParentA(AnonymizationModel):
    name = models.CharField(max_length=250)


class ParentB(TopParentA):
    birth_date = models.DateField()


class ParentC(ParentB):
    first_name = models.CharField(max_length=250)


class ExtraParentD(AnonymizationModel):
    id_d = models.AutoField(primary_key=True, editable=False)
    note = models.CharField(max_length=250)


class ChildE(ParentC, ExtraParentD):
    last_name = models.CharField(max_length=250)


if is_reversion_installed():
    from reversion import revisions as reversion

    reversion.register(Customer)
    reversion.register(TopParentA)
    reversion.register(ParentB, follow=(u'topparenta_ptr',))
    reversion.register(ParentC, follow=(u'parentb_ptr',))
    reversion.register(ExtraParentD)
    reversion.register(ChildE, follow=(u'parentc_ptr', u'extraparentd_ptr'))
