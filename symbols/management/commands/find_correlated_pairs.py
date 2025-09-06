from django.core.management.base import BaseCommand, CommandError
from symbols.models import Exchange
from strategies.utils import StrategyUtils
from django.db import transaction


class Command(BaseCommand):
    help = 'Find highly correlated pairs for a specific exchange using StrategyUtils.find_highly_correlated_pairs()'

    def add_arguments(self, parser):
        parser.add_argument(
            'exchange_name',
            type=str,
            help='Name of the exchange to find correlated pairs for (e.g., "NYSE", "NASDAQ", "CRYPTO USDT")'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without executing the correlation analysis'
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.90,
            help='Correlation threshold (default: 0.90)'
        )
        parser.add_argument(
            '--no-confirm',
            action='store_true',
            help='Skip confirmation prompt (useful for automated scripts)'
        )

    def handle(self, *args, **options):
        exchange_name = options['exchange_name']
        dry_run = options['dry_run']
        threshold = options['threshold']
        no_confirm = options['no_confirm']

        try:
            # Get the exchange
            exchange = Exchange.objects.get(name__iexact=exchange_name)
            self.stdout.write(
                self.style.SUCCESS(f'Found exchange: {exchange.name}')
            )
        except Exchange.DoesNotExist:
            raise CommandError(f'Exchange "{exchange_name}" not found')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would find correlated pairs for {exchange.name}')
            )
            self.stdout.write(f'This would:')
            self.stdout.write(f'  - Process all symbols in {exchange.name}')
            self.stdout.write(f'  - Calculate correlation matrix')
            self.stdout.write(f'  - Find pairs with correlation > {threshold}')
            self.stdout.write(f'  - Save correlated pairs to database')
            self.stdout.write(f'  - Use StrategyUtils.find_highly_correlated_pairs()')
            return

        # Confirm the action (unless --no-confirm is used)
        if not no_confirm:
            confirm = input(f'\nAre you sure you want to find correlated pairs for {exchange.name}? This may take a while. (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled')
                return

        try:
            self.stdout.write(f'Finding correlated pairs for {exchange.name}...')
            
            # Execute the correlation analysis
            with transaction.atomic():
                pairs_found = StrategyUtils.find_highly_correlated_pairs(exchange_name=exchange.name, threshold=threshold)
            
            self.stdout.write(
                self.style.SUCCESS(f'\nCorrelated pairs analysis completed for {exchange.name}!')
            )
            
            # Show summary of results
            from strategies.models import CorrelatedPair
            from symbols.models import Symbols
            
            total_symbols = Symbols.objects.filter(exchange=exchange).count()
            total_pairs_in_db = CorrelatedPair.objects.filter(exchange=exchange).count()
            
            self.stdout.write(f'\nSummary:')
            self.stdout.write(f'  📊 Exchange: {exchange.name}')
            self.stdout.write(f'  🎯 Total Symbols: {total_symbols}')
            self.stdout.write(f'  🔗 Pairs Found in This Run: {pairs_found}')
            self.stdout.write(f'  📈 Total Correlated Pairs in Database: {total_pairs_in_db}')
            self.stdout.write(f'  📈 Note: Database total includes all pairs from previous runs')
            
            if total_pairs_in_db > 0:
                self.stdout.write(f'\nFirst 10 correlated pairs in database:')
                pairs = CorrelatedPair.objects.filter(exchange=exchange)[:10]
                for pair in pairs:
                    self.stdout.write(f'  - {pair.symbol_1.ticker} + {pair.symbol_2.ticker} (Corr: {pair.correlation})')
                
                if total_pairs_in_db > 10:
                    self.stdout.write(f'  ... and {total_pairs_in_db - 10} more')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error finding correlated pairs: {e}')
            )
            raise CommandError(f'Failed to find correlated pairs: {e}')
