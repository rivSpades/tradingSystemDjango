#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from backtesting.models import BackTestingStrategy, TradeHistory, StrategyStatistics, SymbolStatistics
from strategies.models import StrategySymbol

def check_backtest_66():
    """Check details of backtest ID 66"""
    try:
        backtest = BackTestingStrategy.objects.get(id=66)
        print(f"=== Backtest ID 66 Details ===")
        print(f"Strategy: {backtest.strategy.name} (slug: {backtest.strategy.slug})")
        print(f"Created: {backtest.created_at}")
        print(f"Broker: {backtest.broker}")
        print(f"Exchange: {backtest.exchange}")
        
        # Check trades
        trades = TradeHistory.objects.filter(backtest=backtest)
        print(f"\n=== Trades ===")
        print(f"Total trades: {trades.count()}")
        completed_trades = trades.filter(exit_price__isnull=False)
        print(f"Completed trades: {completed_trades.count()}")
        
        if completed_trades.exists():
            print("Sample completed trades:")
            for trade in completed_trades[:5]:
                print(f"  {trade.symbol.ticker} {trade.action} @ {trade.entry_price} -> {trade.exit_price} (P&L: {trade.profit_loss})")
        
        # Check strategy symbols
        strategy_symbols = StrategySymbol.objects.filter(strategy=backtest.strategy)
        print(f"\n=== Strategy Symbols ===")
        print(f"Total strategy symbols: {strategy_symbols.count()}")
        
        active_long = strategy_symbols.filter(is_active_long=True)
        active_short = strategy_symbols.filter(is_active_short=True)
        print(f"Active LONG: {active_long.count()}")
        print(f"Active SHORT: {active_short.count()}")
        
        if active_long.exists():
            print("Active LONG symbols:")
            for ss in active_long[:5]:
                print(f"  {ss.symbol.ticker}")
        
        if active_short.exists():
            print("Active SHORT symbols:")
            for ss in active_short[:5]:
                print(f"  {ss.symbol.ticker}")
        
        # Check symbol statistics
        symbol_stats = SymbolStatistics.objects.filter(backtest=backtest)
        print(f"\n=== Symbol Statistics ===")
        print(f"Total symbol statistics: {symbol_stats.count()}")
        
        if symbol_stats.exists():
            print("Sample symbol statistics:")
            for stat in symbol_stats[:5]:
                print(f"  {stat.symbol.ticker} {stat.action}: ROI={stat.total_roi}, Win Rate={stat.win_rate}, Trades={stat.total_trades}")
        
        # Check existing strategy statistics
        strategy_stats = StrategyStatistics.objects.filter(backtest=backtest)
        print(f"\n=== Strategy Statistics ===")
        print(f"Existing strategy statistics: {strategy_stats.count()}")
        
        if strategy_stats.exists():
            for stat in strategy_stats:
                print(f"  {stat.action}: Trades={stat.total_trades}, ROI={stat.total_roi}, Win Rate={stat.win_rate}")
        
        return backtest
        
    except BackTestingStrategy.DoesNotExist:
        print("Backtest ID 66 not found!")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == '__main__':
    check_backtest_66()
