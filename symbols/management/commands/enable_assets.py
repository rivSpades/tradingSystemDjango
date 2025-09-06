from django.core.management.base import BaseCommand, CommandError
from symbols.models import Broker
from execution.broker_utils import BrokerUtils
from django.db import transaction


class Command(BaseCommand):
    help = 'Enable assets for a specific broker using broker_utils.enable_assets()'

    def add_arguments(self, parser):
        parser.add_argument(
            'broker_name',
            type=str,
            help='Name of the broker to enable assets for (e.g., "Alpaca", "Binance")'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        broker_name = options['broker_name']
        dry_run = options['dry_run']

        try:
            # Get the broker
            broker = Broker.objects.get(name__iexact=broker_name)
            self.stdout.write(
                self.style.SUCCESS(f'Found broker: {broker.name}')
            )
        except Broker.DoesNotExist:
            raise CommandError(f'Broker "{broker_name}" not found')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would enable assets for {broker.name}')
            )
            self.stdout.write('This would:')
            self.stdout.write('  - Fetch available assets from the broker API')
            self.stdout.write('  - Create or update symbols in the database')
            self.stdout.write('  - Set appropriate trading permissions (long/short)')
            self.stdout.write('  - Associate symbols with the broker')
            return

        # Confirm the action
        confirm = input(f'\nAre you sure you want to enable assets for {broker.name}? (y/N): ')
        if confirm.lower() != 'y':
            self.stdout.write('Operation cancelled')
            return

        try:
            # Create BrokerUtils instance
            broker_utils = BrokerUtils(broker.name, broker.api_key, broker.secret_key)
            
            self.stdout.write(f'Enabling assets for {broker.name}...')
            
            # Execute the enable_assets function
            with transaction.atomic():
                broker_utils.enable_assets()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully enabled assets for {broker.name}')
            )
            
            # Show summary
            from symbols.models import Symbols
            total_symbols = Symbols.objects.filter(broker=broker).count()
            enabled_symbols = Symbols.objects.filter(broker=broker, slot_free=True).count()
            disabled_symbols = Symbols.objects.filter(broker=broker, slot_free=False).count()
            
            self.stdout.write(f'\nSummary for {broker.name}:')
            self.stdout.write(f'  📊 Total symbols: {total_symbols}')
            self.stdout.write(f'  ✅ Enabled: {enabled_symbols}')
            self.stdout.write(f'  ❌ Disabled: {disabled_symbols}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error enabling assets for {broker.name}: {e}')
            )
            raise CommandError(f'Failed to enable assets: {e}')
