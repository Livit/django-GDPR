# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-19 15:17
from __future__ import absolute_import
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (u'gdpr', u'0003'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name=u'legalreason',
            unique_together=set([(u'purpose_slug', u'source_object_content_type', u'source_object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name=u'legalreasonrelatedobject',
            unique_together=set([(u'legal_reason', u'object_content_type', u'object_id')]),
        ),
    ]
