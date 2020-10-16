from __future__ import absolute_import
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from gdpr.models import LegalReason


class Command(BaseCommand):

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write(u'Anonymize expired data of expired legal reasons')
        for legal_reason in tqdm(LegalReason.objects.filter_expired_retaining_data_in_last_days(), ncols=100):
            legal_reason.expire()
