#!/usr/bin/env python
"""
Debug script to test calculate_strategy_statistics_by_id function
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from backtesting.backtest_logic import calculate_strategy_statistics_by_id
from backtesting.models import BackTestingStrategy, TradeHistory, StrategyStatistics
from strategies.models import StrategySymbol


def debug_backtest(backtest_id):
    """Debug a specific backtest"""
    print(f"=== Debugging Backtest ID: {backtest_id} ===")
    
    try:
        # Check if backtest exists
        backtest = BackTestingStrategy.objects.get(id=backtest_id)
        print(f"✅ Backtest found: {backtest.strategy.name}")
        print(f"   Strategy: {backtest.strategy.slug}")
        print(f"   Name: {backtest.name}")
        print(f"   Created: {backtest.created_at}")
        
        # Check trades
        trades = TradeHistory.objects.filter(backtest=backtest)
        print(f"📊 Trades found: {trades.count()}")
        
        if trades.exists():
            print("   Sample trades:")
            for trade in trades[:3]:
                print(f"     - {trade.symbol.ticker} | {trade.action} | P&L: {trade.profit_loss}")
        
        # Check strategy symbols
        strategy_symbols = StrategySymbol.objects.filter(strategy=backtest.strategy)
        print(f"🎯 Strategy symbols: {strategy_symbols.count()}")
        
        active_long = strategy_symbols.filter(is_active_long=True).count()
        active_short = strategy_symbols.filter(is_active_short=True).count()
        print(f"   Active LONG: {active_long}")
        print(f"   Active SHORT: {active_short}")
        
        # Check existing statistics
        existing_stats = StrategyStatistics.objects.filter(backtest=backtest)
        print(f"📈 Existing statistics: {existing_stats.count()}")
        
        if existing_stats.exists():
            print("   Existing stats:")
            for stat in existing_stats:
                print(f"     - {stat.action}: {stat.total_trades} trades, {stat.win_rate:.2f}% win rate")
        
        print("\n=== Running Calculation ===")
        result = calculate_strategy_statistics_by_id(backtest_id)
        
        print(f"Result: {result['success']}")
        print(f"Message: {result['message']}")
        
        if not result['success'] and 'error' in result:
            print(f"Error: {result['error']}")
        
        # Check statistics after calculation
        new_stats = StrategyStatistics.objects.filter(backtest=backtest)
        print(f"📈 Statistics after calculation: {new_stats.count()}")
        
        if new_stats.exists():
            print("   New stats:")
            for stat in new_stats:
                print(f"     - {stat.action}: {stat.total_trades} trades, {stat.win_rate:.2f}% win rate")
        
    except BackTestingStrategy.DoesNotExist:
        print(f"❌ Backtest with ID {backtest_id} not found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


def list_backtests():
    """List all backtests with basic info"""
    print("=== Available Backtests ===")
    backtests = BackTestingStrategy.objects.all().select_related('strategy')
    
    for backtest in backtests:
        trades_count = TradeHistory.objects.filter(backtest=backtest).count()
        stats_count = StrategyStatistics.objects.filter(backtest=backtest).count()
        print(f"ID: {backtest.id:3d} | {backtest.strategy.name:20s} | Trades: {trades_count:3d} | Stats: {stats_count:2d}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        backtest_id = int(sys.argv[1])
        debug_backtest(backtest_id)
    else:
        list_backtests()
        print("\nUsage: python debug_calculate_stats.py <backtest_id>")
