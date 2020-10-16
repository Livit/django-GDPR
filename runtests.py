#!/usr/bin/env python
from __future__ import absolute_import
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


if __name__ == u"__main__":
    os.environ[u'DJANGO_SETTINGS_MODULE'] = u'tests.test_settings'
    django.setup()
    failures = TestRunner = get_runner(settings)().run_tests([u"tests", u"gdpr"])
    sys.exit(bool(failures))
