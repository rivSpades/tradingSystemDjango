from django.core.management.base import BaseCommand
from execution.execution_logic import eliminate_usd_strategy_symbols


class Command(BaseCommand):
    help = 'Eliminate all StrategySymbols where the symbol ticker ends with "USD"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            # Import here to avoid circular imports
            from strategies.models import StrategySymbol
            
            # Count USD StrategySymbols without deleting
            usd_count = StrategySymbol.objects.filter(
                symbol__ticker__endswith='USD'
            ).count()
            
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would eliminate {usd_count} StrategySymbols with USD symbols'
                )
            )
            
            # Show some examples
            usd_examples = StrategySymbol.objects.filter(
                symbol__ticker__endswith='USD'
            )[:5]
            
            if usd_examples:
                self.stdout.write('\nExamples of StrategySymbols that would be eliminated:')
                for ss in usd_examples:
                    self.stdout.write(f'  - {ss.strategy.name} - {ss.symbol.ticker}')
            
            return
        
        # Execute the elimination
        result = eliminate_usd_strategy_symbols()
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(result['message'])
            )
        else:
            self.stdout.write(
                self.style.ERROR(result['message'])
            )
