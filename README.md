# Django-GDPR (python 2)

**This is a Python2 fork with extremely cut-down functionality.**  
It is intended for legacy django applications.   
It is confirmed to work with:
- python 2.7.14
- django 1.11.29
- MD5 anonymizer and upstream API in general confirmed to work fine

## Installation:
- add to requirements:
    - `git+ssh://git@github.com/Livit/django-GDPR@0.2.12-python2`
    - `git+ssh://git@github.com/druids/django-chamber.git@0.3.9`
- add to `INSTALLED_APPS`: 
    - `gdpr`
- run `python manage.py migrate`

## Brief user manual for devs:
1. set up venv with python2.7. This can be tricky due to problems with old 
versions of `virtualenv` and general lack of support for python2 in 2020.  
Confirmed to work: 
    1. install desired python2 version with [pyenv](https://github.com/pyenv/pyenv)
    2. using `virtualenv` installed in some other python3 environment, create
    python2 environment: ` ~/.pyenv/versions/3.7.8-system/bin/virtualenv --python="/Users/fred/.pyenv/versions/2.7.14/bin/python" .local_env` 
2. `source .local_env/bin/activate`
3. `pip install -r test_requirements.txt` 
4. `pip install -r requirements.txt` 
5. You should now be able to run tests: `python runtests.py`

## Summary of changes in this fork:
- ran `3to2` utility on entire project
- removed typing instructions that were incompatible with python2
- removed vast majority of functionality except simple hash-based anonymizers 
- especially removed custom **cryptography** utils from upstream project
- added `future-fstrings` libary
- removed `enumfields` that were incompatible with python2. Added `enum34` 
and refactored `LegalReasonState` class to use it. 
- identified `django-chamber==0.3.9` as the last compatible with python2 and us it
instead of current version that is python3-only
- added a few tests for critically needed functionality
- a few minor fixes here and there, that resulted from 3to2 conversion


The rest of the documentation below is **left unchanged**. 

--------------

This library enables you to store user's consent for data retention easily
and to anonymize/deanonymize user's data accordingly.

For brief overview you can check example app in `tests` directory.

# Quickstart

Install django-gdpr with pip:

```bash
pip install django-gdpr
```

Add gdpr to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # Django apps...
    'gdpr',
]
```

Imagine having a customer model:

```python
# app/models.py

from django.db import models

from gdpr.mixins import AnonymizationModel

class Customer(AnonymizationModel):
    # these fields will be used as basic keys for pseudoanonymization
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)

    birth_date = models.DateField(blank=True, null=True)
    personal_id = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=9, blank=True, null=True)
    fb_id = models.CharField(max_length=256, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
```

You may want a consent to store all user's data for two years and consent to store first and last name for 10 years.
For that you can simply add new consent purposes like this.

```python
# app/purposes.py

from dateutil.relativedelta import relativedelta

from gdpr.purposes.default import AbstractPurpose

GENERAL_PURPOSE_SLUG = "general"
FIRST_AND_LAST_NAME_SLUG = "first_and_last"

class GeneralPurpose(AbstractPurpose):
    name = "Retain user data for 2 years"
    slug = GENERAL_PURPOSE_SLUG
    expiration_timedelta = relativedelta(years=2)
    fields = "__ALL__"  # Anonymize all fields defined in anonymizer

class FirstAndLastNamePurpose(AbstractPurpose):
    """Store First & Last name for 10 years."""
    name = "retain due to internet archive"
    slug = FIRST_AND_LAST_NAME_SLUG
    expiration_timedelta = relativedelta(years=10)
    fields = ("first_name", "last_name")
```

The field `fields` specify to which fields this consent applies to.

Some more examples:
```python
fields = ("first_name", "last_name") # Anonymize only two fields

# You can also add nested fields to anonymize fields on related objects.
fields = (
    "primary_email_address",
    ("emails", (
        "email",
    )),
)

# Some more advanced configs may look like this:
fields = (
    "__ALL__",
    ("addresses", "__ALL__"),
    ("accounts", (
        "__ALL__",
        ("payments", (
            "__ALL__",
        ))
    )),
    ("emails", (
        "email",
    )),
)

```

Now when we have the purpose(s) created we also have to make an _anonymizer_ so the library knows which fields to
anonymize and how. This is fairly simple and is quite similar to Django forms.

```python
# app/anonymizers.py

from gdpr import anonymizers
from tests.models import Customer


class CustomerAnonymizer(anonymizers.ModelAnonymizer):
    first_name = anonymizers.MD5TextFieldAnonymizer()
    last_name = anonymizers.MD5TextFieldAnonymizer()
    primary_email_address = anonymizers.EmailFieldAnonymizer()

    birth_date = anonymizers.DateFieldAnonymizer()
    personal_id = anonymizers.PersonalIIDFieldAnonymizer()
    phone_number = anonymizers.PhoneFieldAnonymizer()
    fb_id = anonymizers.CharFieldAnonymizer()
    last_login_ip = anonymizers.IPAddressFieldAnonymizer()

    class Meta:
        model = Customer
```

Now you can fully leverage the system:

You can create/revoke consent:
```python
from gdpr.models import LegalReason

from tests.models import Customer
from tests.purposes import FIRST_AND_LAST_NAME_SLUG


customer = Customer(first_name="John", last_name="Smith")
customer.save()

# Create consent
LegalReason.objects.create_consent(FIRST_AND_LAST_NAME_SLUG, customer)

# And now you can revoke it
LegalReason.objects.deactivate_consent(FIRST_AND_LAST_NAME_SLUG, customer)
```

In case your model uses the `AnonymizationModelMixin` or `AnonymizationModel` you can create and revoke consents even
easier.
```python
from tests.models import Customer
from tests.purposes import FIRST_AND_LAST_NAME_SLUG


customer = Customer(first_name="John", last_name="Smith")
customer.save()

# Create consent
customer.create_consent(FIRST_AND_LAST_NAME_SLUG)

# And now you can revoke it
customer.deactivate_consent(FIRST_AND_LAST_NAME_SLUG)
```


Expired consents are revoked by running the following command. You should invoke it repeatedly, for example by cron.
The invocation interval depends on your circumstances - how fast you want to expire consents after their revocation,
the amount of consents to expire in the interval, server load, and last but not least, legal requirements.

```python
from gdpr.models import LegalReason

LegalReason.objects.expire_old_consents()
```

## FieldAnonymizers

* `FunctionAnonymizer` - in place lambda/function anonymization method (e.g. `secret_code = anonymizers.FunctionFieldAnonymizer(lambda x: x**2)`)
* `DateFieldAnonymizer`
* `CharFieldAnonymizer`
* `DecimalFieldAnonymizer`
* `IPAddressFieldAnonymizer`
* `CzechAccountNumberFieldAnonymizer` - for czech bank account numbers
* `IBANFieldAnonymizer`
* `JSONFieldAnonymizer`
* `EmailFieldAnonymizer`
* `MD5TextFieldAnonymizer`
* `SHA256TextFieldAnonymizer`
* `HashTextFieldAnonymizer` - anonymization using given hash algorithm (e.g. `secret_code = anonymizers.HashTextFieldAnonymizer('sha512')`)
* `StaticValueFieldAnonymizer` - anonymization by replacing with static value (e.g. `secret_code = anonymizers.StaticValueFieldAnonymizer(42)`)
