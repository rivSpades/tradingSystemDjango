#!/usr/bin/env python
"""
Quick debugging helper functions for Django
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

def debug_break():
    """Quick breakpoint function"""
    try:
        import ipdb as pdb
    except ImportError:
        import pdb
    pdb.set_trace()

def inspect_backtest(backtest_id):
    """Quick inspection of a backtest"""
    from backtesting.models import BackTestingStrategy, TradeHistory, StrategyStatistics, SymbolStatistics
    from strategies.models import StrategySymbol
    
    try:
        backtest = BackTestingStrategy.objects.get(id=backtest_id)
        print(f"🔍 Backtest {backtest_id}: {backtest.strategy.name}")
        print(f"   Created: {backtest.created_at}")
        print(f"   Broker: {backtest.broker}")
        print(f"   Exchange: {backtest.exchange}")
        
        trades = TradeHistory.objects.filter(backtest=backtest)
        print(f"   Trades: {trades.count()}")
        
        symbol_stats = SymbolStatistics.objects.filter(backtest=backtest)
        print(f"   Symbol Stats: {symbol_stats.count()}")
        
        strategy_stats = StrategyStatistics.objects.filter(backtest=backtest)
        print(f"   Strategy Stats: {strategy_stats.count()}")
        
        strategy_symbols = StrategySymbol.objects.filter(strategy=backtest.strategy)
        active_long = strategy_symbols.filter(is_active_long=True).count()
        active_short = strategy_symbols.filter(is_active_short=True).count()
        print(f"   Active Strategy Symbols: LONG={active_long}, SHORT={active_short}")
        
        return backtest
        
    except BackTestingStrategy.DoesNotExist:
        print(f"❌ Backtest {backtest_id} not found!")
        return None

def debug_portfolio_analysis(backtest_id):
    """Debug portfolio analysis for a specific backtest"""
    from portfolio.portfolio_logic import analyze_and_enable_strategies
    from backtesting.models import BackTestingStrategy
    
    backtest = BackTestingStrategy.objects.get(id=backtest_id)
    print(f"🔍 Debugging portfolio analysis for backtest {backtest_id}")
    
    # Set breakpoint before calling analyze_and_enable_strategies
    debug_break()
    
    # This will stop execution and let you step through the function
    analyze_and_enable_strategies(backtest)

def debug_calculation(backtest_id):
    """Debug strategy statistics calculation"""
    from backtesting.backtest_logic import calculate_strategy_statistics_by_id
    
    print(f"🔍 Debugging calculation for backtest {backtest_id}")
    
    # Set breakpoint before calling calculate_strategy_statistics_by_id
    debug_break()
    
    # This will stop execution and let you step through the function
    result = calculate_strategy_statistics_by_id(backtest_id)
    print(f"📋 Result: {result}")

# Quick access functions
def debug_66():
    """Quick debug for backtest 66"""
    inspect_backtest(66)
    debug_break()

def debug_portfolio_66():
    """Quick debug portfolio analysis for backtest 66"""
    debug_portfolio_analysis(66)

def debug_calc_66():
    """Quick debug calculation for backtest 66"""
    debug_calculation(66)

if __name__ == '__main__':
    print("🐛 Quick Debug Helpers")
    print("=" * 50)
    print("Available functions:")
    print("- inspect_backtest(backtest_id)")
    print("- debug_portfolio_analysis(backtest_id)")
    print("- debug_calculation(backtest_id)")
    print("- debug_66() - Quick debug for backtest 66")
    print("- debug_portfolio_66() - Debug portfolio for backtest 66")
    print("- debug_calc_66() - Debug calculation for backtest 66")
    print("- debug_break() - Set a breakpoint")
    print("=" * 50)
    
    # Example usage
    debug_66()
