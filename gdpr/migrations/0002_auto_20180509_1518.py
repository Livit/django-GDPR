# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-09 13:18
from __future__ import absolute_import
from __future__ import unicode_literals

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):
    dependencies = [
        (u'gdpr', u'0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name=u'legalreasonrelatedobject',
            old_name=u'content_type',
            new_name=u'object_content_type',
        ),
        migrations.AddField(
            model_name=u'legalreason',
            name=u'issued_at',
            field=models.DateTimeField(default=datetime.datetime(2018, 5, 9, 13, 18, 7, 317147, tzinfo=utc),
                                       verbose_name=u'issued at'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name=u'legalreason',
            name=u'purpose_slug',
            field=models.CharField(choices=[], max_length=100, verbose_name=u'purpose'),
        ),
    ]
