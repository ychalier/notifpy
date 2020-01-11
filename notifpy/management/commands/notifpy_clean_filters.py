import re
from django.core.management.base import BaseCommand
from notifpy import models


class Command(BaseCommand):
    """Clean filters (v0.5 fix)"""
    help = "Clean filters (v0.5 fix)"

    def handle(self, *args, **kwargs):
        for filters in models.Filter.objects.all():
            filters.regex = re.sub("\r", "", filters.regex)
            filters.save()
