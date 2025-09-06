from django.core.management.base import BaseCommand
from backtesting.models import BackTestingStrategy, TradeHistory, StrategyStatistics
from strategies.models import StrategySymbol


class Command(BaseCommand):
    help = 'Debug a specific backtest to understand why statistics calculation might fail'

    def add_arguments(self, parser):
        parser.add_argument('backtest_id', type=int, help='ID of the backtest to debug')

    def handle(self, *args, **options):
        backtest_id = options['backtest_id']
        
        self.stdout.write(f"=== Debugging Backtest ID: {backtest_id} ===")
        
        try:
            # Check if backtest exists
            backtest = BackTestingStrategy.objects.get(id=backtest_id)
            self.stdout.write(f"✅ Backtest found: {backtest.strategy.name}")
            self.stdout.write(f"   Strategy: {backtest.strategy.slug}")
            self.stdout.write(f"   Name: {backtest.name}")
            self.stdout.write(f"   Created: {backtest.created_at}")
            
            # Check trades
            trades = TradeHistory.objects.filter(backtest=backtest)
            self.stdout.write(f"📊 Trades found: {trades.count()}")
            
            if trades.exists():
                self.stdout.write("   Sample trades:")
                for trade in trades[:3]:
                    self.stdout.write(f"     - {trade.symbol.ticker} | {trade.action} | P&L: {trade.profit_loss} | Exit Price: {trade.exit_price}")
                
                # Check trades with exit prices
                completed_trades = trades.filter(exit_price__isnull=False)
                self.stdout.write(f"   Completed trades (with exit price): {completed_trades.count()}")
                
                # Check trades by action
                long_trades = trades.filter(action='LONG')
                short_trades = trades.filter(action='SHORT')
                self.stdout.write(f"   LONG trades: {long_trades.count()}")
                self.stdout.write(f"   SHORT trades: {short_trades.count()}")
            
            # Check strategy symbols
            strategy_symbols = StrategySymbol.objects.filter(strategy=backtest.strategy)
            self.stdout.write(f"🎯 Strategy symbols: {strategy_symbols.count()}")
            
            active_long = strategy_symbols.filter(is_active_long=True).count()
            active_short = strategy_symbols.filter(is_active_short=True).count()
            self.stdout.write(f"   Active LONG: {active_long}")
            self.stdout.write(f"   Active SHORT: {active_short}")
            
            if strategy_symbols.exists():
                self.stdout.write("   Sample strategy symbols:")
                for ss in strategy_symbols[:3]:
                    self.stdout.write(f"     - {ss.symbol.ticker} | LONG: {ss.is_active_long} | SHORT: {ss.is_active_short}")
            
            # Check existing statistics
            existing_stats = StrategyStatistics.objects.filter(backtest=backtest)
            self.stdout.write(f"📈 Existing statistics: {existing_stats.count()}")
            
            if existing_stats.exists():
                self.stdout.write("   Existing stats:")
                for stat in existing_stats:
                    self.stdout.write(f"     - {stat.action}: {stat.total_trades} trades, {stat.win_rate:.2f}% win rate")
            
            # Check trades for active symbols only
            if active_long > 0:
                active_long_symbols = strategy_symbols.filter(is_active_long=True).values_list('symbol', flat=True)
                long_trades_active = trades.filter(action='LONG', symbol__in=active_long_symbols, exit_price__isnull=False)
                self.stdout.write(f"   LONG trades for active symbols: {long_trades_active.count()}")
            
            if active_short > 0:
                active_short_symbols = strategy_symbols.filter(is_active_short=True).values_list('symbol', flat=True)
                short_trades_active = trades.filter(action='SHORT', symbol__in=active_short_symbols, exit_price__isnull=False)
                self.stdout.write(f"   SHORT trades for active symbols: {short_trades_active.count()}")
            
        except BackTestingStrategy.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Backtest with ID {backtest_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(f"Traceback: {traceback.format_exc()}"))
