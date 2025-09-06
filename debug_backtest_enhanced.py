#!/usr/bin/env python
"""
Enhanced debugging script using ipdb for better debugging experience
"""

try:
    import ipdb as pdb
    print("✅ Using ipdb (enhanced debugger)")
except ImportError:
    import pdb
    print("⚠️ Using pdb (basic debugger) - install ipdb for better experience")

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from backtesting.models import BackTestingStrategy, TradeHistory, StrategyStatistics, SymbolStatistics
from strategies.models import StrategySymbol
from backtesting.backtest_logic import calculate_strategy_statistics_by_id

def debug_backtest_66():
    """Debug function for backtest 66 with multiple breakpoints"""
    print("🔍 Starting enhanced debug session for backtest 66...")
    
    # Breakpoint 1: Check if backtest exists
    pdb.set_trace()
    
    try:
        backtest = BackTestingStrategy.objects.get(id=66)
        print(f"✅ Found backtest: {backtest.strategy.name} (ID: 66)")
    except BackTestingStrategy.DoesNotExist:
        print("❌ Backtest 66 not found!")
        return
    
    # Breakpoint 2: Check trades
    pdb.set_trace()
    
    trades = TradeHistory.objects.filter(backtest=backtest)
    print(f"📊 Trades found: {trades.count()}")
    
    if trades.exists():
        print("Sample trades:")
        for trade in trades[:3]:
            print(f"  {trade.symbol.ticker} {trade.action} @ {trade.entry_price}")
    
    # Breakpoint 3: Check symbol statistics
    pdb.set_trace()
    
    symbol_stats = SymbolStatistics.objects.filter(backtest=backtest)
    print(f"📈 Symbol Statistics: {symbol_stats.count()}")
    
    if symbol_stats.exists():
        print("Sample symbol statistics:")
        for stat in symbol_stats[:3]:
            print(f"  {stat.symbol.ticker} {stat.action}: ROI={stat.total_roi}")
    
    # Breakpoint 4: Check strategy symbols
    pdb.set_trace()
    
    strategy_symbols = StrategySymbol.objects.filter(strategy=backtest.strategy)
    active_long = strategy_symbols.filter(is_active_long=True).count()
    active_short = strategy_symbols.filter(is_active_short=True).count()
    
    print(f"🎯 Strategy Symbols - Active LONG: {active_long}, Active SHORT: {active_short}")
    
    # Breakpoint 5: Run calculation
    pdb.set_trace()
    
    print("🚀 Running calculate_strategy_statistics_by_id(66)...")
    result = calculate_strategy_statistics_by_id(66)
    print(f"📋 Result: {result}")
    
    # Breakpoint 6: Check final state
    pdb.set_trace()
    
    strategy_stats_after = StrategyStatistics.objects.filter(backtest=backtest)
    print(f"📊 Final Strategy Statistics: {strategy_stats_after.count()}")
    
    if strategy_stats_after.exists():
        for stat in strategy_stats_after:
            print(f"  {stat.action}: Trades={stat.total_trades}, ROI={stat.total_roi}")

def debug_portfolio_logic():
    """Debug the portfolio logic specifically"""
    print("🔍 Debugging portfolio logic...")
    
    pdb.set_trace()
    
    from portfolio.portfolio_logic import analyze_and_enable_strategies
    from backtesting.models import BackTestingStrategy
    
    backtest = BackTestingStrategy.objects.get(id=66)
    print(f"Testing analyze_and_enable_strategies for backtest: {backtest.strategy.name}")
    
    # This will help you step through the portfolio logic
    analyze_and_enable_strategies(backtest)

if __name__ == '__main__':
    print("🐛 Enhanced Django Debugger")
    print("=" * 50)
    print("Available debug functions:")
    print("1. debug_backtest_66() - Debug backtest 66 step by step")
    print("2. debug_portfolio_logic() - Debug portfolio logic")
    print("=" * 50)
    
    # You can uncomment the function you want to debug
    debug_backtest_66()
    # debug_portfolio_logic()
