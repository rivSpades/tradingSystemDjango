from django.core.management.base import BaseCommand
from execution.execution_logic import execute_strategies

class Command(BaseCommand):
    help = 'Run strategy execution'

    def handle(self, *args, **options):
        self.stdout.write("Starting strategy execution...")
        execute_strategies()
        self.stdout.write("Strategy execution completed.")


