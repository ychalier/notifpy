from django.core.management.base import BaseCommand
from notifpy.operator import Operator


class Command(BaseCommand):
    """Trigger scheduled channels update"""
    help = "Trigger scheduled channels update"

    def add_arguments(self, parser):
        parser.add_argument("-p", "--priority", type=int, help="Select priority level for update.")

    def handle(self, *args, **kwargs):
        priority = kwargs["priority"]
        if priority is None:
            priorities = None
        else:
            priorities = [priority]
        operator = Operator("secret.json")
        operator.update_channels(priorities, verbose=True)
