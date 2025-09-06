from django.core.management.base import BaseCommand, CommandError
from symbols.models import Broker
from symbols.utils import DailyPriceManager
from django.db import transaction


class Command(BaseCommand):
    help = 'Insert daily prices for symbols from a specific broker using the existing update_daily_prices_for_symbols function'

    def add_arguments(self, parser):
        parser.add_argument(
            'broker_name',
            type=str,
            help='Name of the broker to insert daily prices for (e.g., "Alpaca", "Binance")'
        )
        parser.add_argument(
            '--exchange',
            type=str,
            help='Name of the exchange to filter symbols (e.g., "NYSE", "NASDAQ", "CRYPTO USDT")'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            default='2013-01-01',
            help='Start date for price data (default: 2013-01-01)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for price data (default: yesterday)'
        )
        parser.add_argument(
            '--symbols',
            type=str,
            help='Comma-separated list of specific symbols to update (optional)'
        )

    def handle(self, *args, **options):
        broker_name = options['broker_name']
        exchange_name = options['exchange']
        dry_run = options['dry_run']
        start_date = options['start_date']
        end_date = options['end_date']
        symbols_list = options['symbols']

        try:
            # Get the broker
            broker = Broker.objects.get(name__iexact=broker_name)
            self.stdout.write(
                self.style.SUCCESS(f'Found broker: {broker.name}')
            )
        except Broker.DoesNotExist:
            raise CommandError(f'Broker "{broker_name}" not found')

        # Get symbols for this broker
        from symbols.models import Symbols, Exchange
        symbols_query = Symbols.objects.filter(broker=broker, active=True)
        self.stdout.write(f'Filtering by active symbols only')

        # Filter by exchange if provided
        if exchange_name:
            try:
                exchange = Exchange.objects.get(name__iexact=exchange_name)
                symbols_query = symbols_query.filter(exchange=exchange)
                self.stdout.write(f'Filtering by exchange: {exchange.name}')
            except Exchange.DoesNotExist:
                raise CommandError(f'Exchange "{exchange_name}" not found')

        # Filter by specific symbols if provided
        if symbols_list:
            symbol_tickers = [s.strip().upper() for s in symbols_list.split(',')]
            symbols_query = symbols_query.filter(ticker__in=symbol_tickers)
            self.stdout.write(f'Filtering by symbols: {", ".join(symbol_tickers)}')

        symbols = symbols_query.all()
        
        if not symbols.exists():
            self.stdout.write(
                self.style.WARNING(f'No symbols found for broker {broker.name}')
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would insert daily prices for {broker.name}')
            )
            self.stdout.write(f'This would:')
            self.stdout.write(f'  - Process {symbols.count()} symbols')
            self.stdout.write(f'  - Fetch price data from {broker.name} API')
            if exchange_name:
                self.stdout.write(f'  - Filter by exchange: {exchange_name}')
            self.stdout.write(f'  - Insert new daily prices into database')
            self.stdout.write(f'  - Start date: {start_date}')
            if end_date:
                self.stdout.write(f'  - End date: {end_date}')
            else:
                self.stdout.write(f'  - End date: yesterday')
            
            # Show first few symbols
            self.stdout.write(f'\nSymbols that would be processed:')
            for symbol in symbols[:10]:
                self.stdout.write(f'  - {symbol.ticker}')
            if symbols.count() > 10:
                self.stdout.write(f'  ... and {symbols.count() - 10} more')
            return

        # Confirm the action
        confirm = input(f'\nAre you sure you want to insert daily prices for {symbols.count()} symbols from {broker.name}? (y/N): ')
        if confirm.lower() != 'y':
            self.stdout.write('Operation cancelled')
            return

        try:
            self.stdout.write(f'Inserting daily prices for {broker.name}...')
            
            # Execute the update_daily_prices_for_symbols function with filtered symbols
            with transaction.atomic():
                result = DailyPriceManager.update_daily_prices_for_symbols(symbols_list=symbols)
            
            # Show results
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully processed daily prices for {broker.name}')
            )
            
            self.stdout.write(f'\nSummary:')
            self.stdout.write(f'  ✅ Successful: {result["success_count"]}')
            self.stdout.write(f'  ❌ Errors: {result["error_count"]}')
            self.stdout.write(f'  📊 Total processed: {result["total_processed"]}')
            
            # Show broker summary
            total_symbols = Symbols.objects.filter(broker=broker).count()
            from symbols.models import DailyPrice
            total_prices = DailyPrice.objects.filter(symbol__broker=broker).count()
            
            self.stdout.write(f'\nBroker Summary for {broker.name}:')
            self.stdout.write(f'  📊 Total symbols: {total_symbols}')
            self.stdout.write(f'  💰 Total price records: {total_prices}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error inserting daily prices for {broker.name}: {e}')
            )
            raise CommandError(f'Failed to insert daily prices: {e}')
