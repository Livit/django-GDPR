# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-02-27 14:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import gdpr.mixins
import tests.validators


class Migration(migrations.Migration):
    dependencies = [
        ('tests', '0004_facebook_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Avatar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.FileField(upload_to='')),
            ],
            options={
                'abstract': False,
            },
            bases=(gdpr.mixins.AnonymizationModelMixin, models.Model),
        ),
        migrations.AlterField(
            model_name='account',
            name='number',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='personal_id',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='avatar',
            name='custormer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='avatars',
                                    to='tests.Customer'),
        ),
    ]
