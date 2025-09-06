from django.core.management.base import BaseCommand
from backtesting.backtest_logic import calculate_strategy_statistics_by_id
from backtesting.models import BackTestingStrategy


class Command(BaseCommand):
    help = 'Calculate strategy statistics for a specific backtest by ID'

    def add_arguments(self, parser):
        parser.add_argument(
            'backtest_id',
            type=int,
            help='ID of the backtest to calculate statistics for',
        )
        parser.add_argument(
            '--list-backtests',
            action='store_true',
            help='List all available backtests with their IDs',
        )

    def handle(self, *args, **options):
        # Handle list option
        if options['list_backtests']:
            backtests = BackTestingStrategy.objects.all().select_related('strategy')
            
            if backtests:
                self.stdout.write('Available backtests:')
                self.stdout.write('ID  | Strategy Name          | Backtest Name')
                self.stdout.write('----|------------------------|----------------')
                for backtest in backtests:
                    strategy_name = backtest.strategy.name[:20].ljust(20)
                    backtest_name = (backtest.name or 'Unnamed')[:15].ljust(15)
                    self.stdout.write(f'{backtest.id:3d} | {strategy_name} | {backtest_name}')
            else:
                self.stdout.write('No backtests found.')
            return
        
        # Get backtest ID
        backtest_id = options['backtest_id']
        
        # Show backtest info before execution
        try:
            backtest = BackTestingStrategy.objects.get(id=backtest_id)
            self.stdout.write(f'Calculating strategy statistics for:')
            self.stdout.write(f'  Backtest ID: {backtest_id}')
            self.stdout.write(f'  Strategy: {backtest.strategy.name}')
            self.stdout.write(f'  Backtest Name: {backtest.name or "Unnamed"}')
            self.stdout.write('')
        except BackTestingStrategy.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Backtest with ID {backtest_id} not found.')
            )
            return
        
        # Execute the calculation
        self.stdout.write('Calculating strategy statistics...')
        result = calculate_strategy_statistics_by_id(backtest_id)
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(result['message'])
            )
        else:
            self.stdout.write(
                self.style.ERROR(result['message'])
            )
