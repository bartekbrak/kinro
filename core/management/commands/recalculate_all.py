from django.core.management import BaseCommand

from core.models import DayCache


class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)

    def handle(self, *args, **options):
        DayCache.recalculate_all()
