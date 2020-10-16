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
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from gdpr.mixins import AnonymizationModel
from gdpr.utils import is_reversion_installed
from tests.validators import CZBirthNumberValidator, BankAccountValidator


class Customer(AnonymizationModel):
    # Keys for pseudoanonymization
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    primary_email_address = models.EmailField(blank=True, null=True)

    full_name = models.CharField(max_length=256, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    personal_id = models.CharField(max_length=10, blank=True, null=True, validators=[CZBirthNumberValidator])
    phone_number = models.CharField(max_length=9, blank=True, null=True)
    facebook_id = models.CharField(
        max_length=256, blank=True, null=True,
        verbose_name=_(u"Facebook ID"), help_text=_(u"Facebook ID used for login via Facebook."))
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    def save(self, *args, **kwargs):
        u"""Just helper method for saving full name.

        You can ignore this method.
        """
        self.full_name = u"%s %s" % (self.first_name, self.last_name)
        super(Customer, self).save(*args, **kwargs)

    def __str__(self):
        return u"{} {}".format((self.first_name), (self.last_name))


class Email(AnonymizationModel):
    u"""Example on anonymization on related field."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name=u"emails")
    email = models.EmailField(blank=True, null=True)


class Address(AnonymizationModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name=u"addresses")
    street = models.CharField(max_length=256, blank=True, null=True)
    house_number = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=256, blank=True, null=True)
    post_code = models.CharField(max_length=6, blank=True, null=True)


class Account(AnonymizationModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name=u"accounts")
    number = models.CharField(max_length=256, blank=True, null=True, validators=[BankAccountValidator])
    IBAN = models.CharField(max_length=34, blank=True, null=True)
    swift = models.CharField(max_length=11, blank=True, null=True)
    owner = models.CharField(max_length=256, blank=True, null=True)


class Payment(AnonymizationModel):
    u"""Down the rabbit hole multilevel relations."""
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name=u"payments")
    value = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)
    date = models.DateField(auto_now_add=True)


class ContactForm(AnonymizationModel):
    email = models.EmailField()
    full_name = models.CharField(max_length=256)


class Note(AnonymizationModel):
    note = models.TextField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey(u'content_type', u'object_id')


class Avatar(AnonymizationModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name=u"avatars")
    image = models.FileField()


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
    reversion.register(Email)
    reversion.register(Address)
    reversion.register(Account)
    reversion.register(Payment)
    reversion.register(ContactForm)
    reversion.register(Note)
    reversion.register(TopParentA)
    reversion.register(ParentB, follow=(u'topparenta_ptr',))
    reversion.register(ParentC, follow=(u'parentb_ptr',))
    reversion.register(ExtraParentD)
    reversion.register(ChildE, follow=(u'parentc_ptr', u'extraparentd_ptr'))
