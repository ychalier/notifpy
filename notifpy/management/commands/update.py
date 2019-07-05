from django.core.management.base import BaseCommand
from notifpy.core import Manager


class Command(BaseCommand):
    help = "Trigger scheduled channels update"

    def handle(self, *args, **options):
        Manager("secret.json").update()
