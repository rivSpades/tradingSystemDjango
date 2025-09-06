from django.core.management.base import BaseCommand
from execution.execution_logic import execute_strategies
from datetime import datetime


class Command(BaseCommand):
    help = 'Execute trading strategies with optional broker and exchange filtering'

    def add_arguments(self, parser):
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for strategy execution (YYYY-MM-DD format, default: today)',
        )
        parser.add_argument(
            '--broker',
            type=str,
            help='Filter by broker name',
        )
        parser.add_argument(
            '--exchange',
            type=str,
            help='Filter by exchange name',
        )
        parser.add_argument(
            '--list-brokers',
            action='store_true',
            help='List available brokers',
        )
        parser.add_argument(
            '--list-exchanges',
            action='store_true',
            help='List available exchanges',
        )

    def handle(self, *args, **options):
        # Import here to avoid circular imports
        from symbols.models import Broker, Exchange
        
        # Handle list options
        if options['list_brokers']:
            brokers = Broker.objects.all()
            if brokers:
                self.stdout.write('Available brokers:')
                for broker in brokers:
                    self.stdout.write(f'  - {broker.name}')
            else:
                self.stdout.write('No brokers found.')
            return
        
        if options['list_exchanges']:
            exchanges = Exchange.objects.all()
            if exchanges:
                self.stdout.write('Available exchanges:')
                for exchange in exchanges:
                    self.stdout.write(f'  - {exchange.name}')
            else:
                self.stdout.write('No exchanges found.')
            return
        
        # Parse end date if provided
        end_date = None
        if options['end_date']:
            try:
                end_date = datetime.strptime(options['end_date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD format.')
                )
                return
        
        # Get broker and exchange names
        broker_name = options['broker']
        exchange_name = options['exchange']
        
        # Show execution parameters
        self.stdout.write('Strategy Execution Parameters:')
        self.stdout.write(f'  End Date: {end_date or "Today"}')
        self.stdout.write(f'  Broker Filter: {broker_name or "All"}')
        self.stdout.write(f'  Exchange Filter: {exchange_name or "All"}')
        self.stdout.write('')
        
        # Execute strategies
        self.stdout.write('Executing strategies...')
        result = execute_strategies(
            end_date=end_date,
            broker_name=broker_name,
            exchange_name=exchange_name
        )
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(result['message'])
            )
        else:
            self.stdout.write(
                self.style.ERROR(result['message'])
            )
