from django.core.management.base import BaseCommand
from backtesting.backtest_logic import calculate_strategy_statistics_by_id
from backtesting.models import BackTestingStrategy, TradeHistory, StrategyStatistics, SymbolStatistics
from strategies.models import StrategySymbol

class Command(BaseCommand):
    help = 'Test strategy statistics calculation for backtest 66'

    def handle(self, *args, **options):
        self.stdout.write("=== Testing Strategy Statistics Calculation for Backtest 66 ===")
        
        try:
            # Check initial state
            backtest = BackTestingStrategy.objects.get(id=66)
            self.stdout.write(f"Backtest: {backtest.strategy.name} (ID: 66)")
            
            # Check trades
            trades = TradeHistory.objects.filter(backtest=backtest)
            self.stdout.write(f"Trades: {trades.count()}")
            
            # Check symbol statistics
            symbol_stats = SymbolStatistics.objects.filter(backtest=backtest)
            self.stdout.write(f"Symbol Statistics: {symbol_stats.count()}")
            
            # Check strategy symbols
            strategy_symbols = StrategySymbol.objects.filter(strategy=backtest.strategy)
            active_long = strategy_symbols.filter(is_active_long=True).count()
            active_short = strategy_symbols.filter(is_active_short=True).count()
            self.stdout.write(f"Strategy Symbols - Active LONG: {active_long}, Active SHORT: {active_short}")
            
            # Check existing strategy statistics
            strategy_stats = StrategyStatistics.objects.filter(backtest=backtest)
            self.stdout.write(f"Existing Strategy Statistics: {strategy_stats.count()}")
            
            self.stdout.write("\n=== Running Calculation ===")
            
            # Run the calculation
            result = calculate_strategy_statistics_by_id(66)
            
            self.stdout.write(f"Result: {result}")
            
            # Check final state
            self.stdout.write("\n=== Final State ===")
            
            # Check symbol statistics after calculation
            symbol_stats_after = SymbolStatistics.objects.filter(backtest=backtest)
            self.stdout.write(f"Symbol Statistics after: {symbol_stats_after.count()}")
            
            # Check strategy symbols after calculation
            strategy_symbols_after = StrategySymbol.objects.filter(strategy=backtest.strategy)
            active_long_after = strategy_symbols_after.filter(is_active_long=True).count()
            active_short_after = strategy_symbols_after.filter(is_active_short=True).count()
            self.stdout.write(f"Strategy Symbols after - Active LONG: {active_long_after}, Active SHORT: {active_short_after}")
            
            # Check strategy statistics after calculation
            strategy_stats_after = StrategyStatistics.objects.filter(backtest=backtest)
            self.stdout.write(f"Strategy Statistics after: {strategy_stats_after.count()}")
            
            if strategy_stats_after.exists():
                for stat in strategy_stats_after:
                    self.stdout.write(f"  {stat.action}: Trades={stat.total_trades}, ROI={stat.total_roi}, Win Rate={stat.win_rate}")
                    
        except BackTestingStrategy.DoesNotExist:
            self.stdout.write(self.style.ERROR("Backtest ID 66 not found!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
