from django.core.management.base import BaseCommand, CommandError
from symbols.models import Exchange, Symbols
from strategies.models import Strategy
from backtesting.backtest_logic import execute_backtest
from django.db import transaction
import datetime


class Command(BaseCommand):
    help = 'Execute a backtest for a specific exchange and strategy using only active symbols'

    def add_arguments(self, parser):
        parser.add_argument(
            'exchange_name',
            type=str,
            help='Name of the exchange to execute backtest for (e.g., "NYSE", "NASDAQ", "CRYPTO USDT")'
        )
        parser.add_argument(
            'strategy_slug',
            type=str,
            help='Strategy slug to execute (e.g., "mean-reverting", "ma-crossover", "cointegration")'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            default='2013-01-01',
            help='Start date for backtest (default: 2013-01-01)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for backtest (default: today)'
        )
        parser.add_argument(
            '--symbols',
            type=str,
            help='Comma-separated list of specific symbols to backtest (optional)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without executing the backtest'
        )

    def handle(self, *args, **options):
        exchange_name = options['exchange_name']
        strategy_slug = options['strategy_slug']
        start_date = options['start_date']
        end_date = options['end_date']
        symbols_list = options['symbols']
        dry_run = options['dry_run']

        try:
            # Get the exchange
            exchange = Exchange.objects.get(name__iexact=exchange_name)
            self.stdout.write(
                self.style.SUCCESS(f'Found exchange: {exchange.name}')
            )
        except Exchange.DoesNotExist:
            raise CommandError(f'Exchange "{exchange_name}" not found')

        try:
            # Get the strategy
            strategy = Strategy.objects.get(slug=strategy_slug)
            self.stdout.write(
                self.style.SUCCESS(f'Found strategy: {strategy.name} ({strategy.slug})')
            )
        except Strategy.DoesNotExist:
            raise CommandError(f'Strategy "{strategy_slug}" not found')

        # Get symbols for this exchange (only active)
        symbols_query = Symbols.objects.filter(exchange=exchange, active=True)
        self.stdout.write(f'Filtering by active symbols only')

        # Filter by specific symbols if provided
        if symbols_list:
            symbol_tickers = [s.strip().upper() for s in symbols_list.split(',')]
            symbols_query = symbols_query.filter(ticker__in=symbol_tickers)
            self.stdout.write(f'Filtering by symbols: {", ".join(symbol_tickers)}')

        symbols = symbols_query.all()
        
        if not symbols.exists():
            self.stdout.write(
                self.style.WARNING(f'No active symbols found for exchange {exchange.name}')
            )
            return

        # Set default end date if not provided
        if not end_date:
            end_date = datetime.date.today().strftime('%Y-%m-%d')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would execute backtest for {exchange.name}')
            )
            self.stdout.write(f'This would:')
            self.stdout.write(f'  - Execute strategy: {strategy.name} ({strategy.slug})')
            self.stdout.write(f'  - Process {symbols.count()} active symbols')
            self.stdout.write(f'  - Date range: {start_date} to {end_date}')
            self.stdout.write(f'  - Create backtest results in database')
            
            # Show first few symbols
            self.stdout.write(f'\nSymbols that would be processed:')
            for symbol in symbols[:10]:
                self.stdout.write(f'  - {symbol.ticker}')
            if symbols.count() > 10:
                self.stdout.write(f'  ... and {symbols.count() - 10} more')
            return

        # Confirm the action
        confirm = input(f'\nAre you sure you want to execute backtest for {strategy.name} on {symbols.count()} active symbols from {exchange.name}? (y/N): ')
        if confirm.lower() != 'y':
            self.stdout.write('Operation cancelled')
            return

        try:
            self.stdout.write(f'Executing backtest for {strategy.name} on {exchange.name}...')
            
            # Prepare symbol list for backtest
            symbol_tickers = list(symbols.values_list('ticker', flat=True))
            
            # Execute the backtest
            with transaction.atomic():
                result = execute_backtest(
                    strategy_id=strategy_slug,
                    start_date=start_date,
                    end_date=end_date,
                    symbol_list=symbol_tickers,
                    exchange_name=exchange_name
                )
            
            # Show results
            self.stdout.write(
                self.style.SUCCESS(f'\nBacktest completed successfully!')
            )
            
            self.stdout.write(f'\nBacktest Summary:')
            self.stdout.write(f'  📊 Strategy: {strategy.name}')
            self.stdout.write(f'  🏢 Exchange: {exchange.name}')
            self.stdout.write(f'  📅 Date Range: {start_date} to {end_date}')
            self.stdout.write(f'  🎯 Symbols Processed: {len(symbol_tickers)}')
            
            self.stdout.write(f'\nResult: {result}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error executing backtest: {e}')
            )
            raise CommandError(f'Failed to execute backtest: {e}')
