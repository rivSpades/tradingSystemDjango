#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from backtesting.backtest_logic import calculate_strategy_statistics_by_id
from backtesting.models import BackTestingStrategy, TradeHistory, StrategyStatistics, SymbolStatistics
from strategies.models import StrategySymbol

def test_calculation():
    """Test the strategy statistics calculation for backtest 66"""
    print("=== Testing Strategy Statistics Calculation for Backtest 66 ===")
    
    # Check initial state
    backtest = BackTestingStrategy.objects.get(id=66)
    print(f"Backtest: {backtest.strategy.name} (ID: 66)")
    
    # Check trades
    trades = TradeHistory.objects.filter(backtest=backtest)
    print(f"Trades: {trades.count()}")
    
    # Check symbol statistics
    symbol_stats = SymbolStatistics.objects.filter(backtest=backtest)
    print(f"Symbol Statistics: {symbol_stats.count()}")
    
    # Check strategy symbols
    strategy_symbols = StrategySymbol.objects.filter(strategy=backtest.strategy)
    active_long = strategy_symbols.filter(is_active_long=True).count()
    active_short = strategy_symbols.filter(is_active_short=True).count()
    print(f"Strategy Symbols - Active LONG: {active_long}, Active SHORT: {active_short}")
    
    # Check existing strategy statistics
    strategy_stats = StrategyStatistics.objects.filter(backtest=backtest)
    print(f"Existing Strategy Statistics: {strategy_stats.count()}")
    
    print("\n=== Running Calculation ===")
    
    # Run the calculation
    result = calculate_strategy_statistics_by_id(66)
    
    print(f"Result: {result}")
    
    # Check final state
    print("\n=== Final State ===")
    
    # Check symbol statistics after calculation
    symbol_stats_after = SymbolStatistics.objects.filter(backtest=backtest)
    print(f"Symbol Statistics after: {symbol_stats_after.count()}")
    
    # Check strategy symbols after calculation
    strategy_symbols_after = StrategySymbol.objects.filter(strategy=backtest.strategy)
    active_long_after = strategy_symbols_after.filter(is_active_long=True).count()
    active_short_after = strategy_symbols_after.filter(is_active_short=True).count()
    print(f"Strategy Symbols after - Active LONG: {active_long_after}, Active SHORT: {active_short_after}")
    
    # Check strategy statistics after calculation
    strategy_stats_after = StrategyStatistics.objects.filter(backtest=backtest)
    print(f"Strategy Statistics after: {strategy_stats_after.count()}")
    
    if strategy_stats_after.exists():
        for stat in strategy_stats_after:
            print(f"  {stat.action}: Trades={stat.total_trades}, ROI={stat.total_roi}, Win Rate={stat.win_rate}")

if __name__ == '__main__':
    test_calculation()
