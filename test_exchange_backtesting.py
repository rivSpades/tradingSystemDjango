#!/usr/bin/env python3
"""
Test script for exchange-specific backtesting functionality.
This script demonstrates how to run backtests for the same strategy on different exchanges.
"""

import os
import sys
import django
from datetime import date, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from backtesting.backtest_logic import execute_backtest
from backtesting.models import BackTestingStrategy, StrategyStatistics, SymbolStatistics, TradeHistory
from strategies.models import Strategy
from symbols.models import Symbols, Exchange, Broker

def show_available_exchanges():
    """Show available exchanges in the system"""
    
    print("🔍 Available Exchanges...")
    print("=" * 60)
    
    exchanges = Exchange.objects.all()
    
    if not exchanges.exists():
        print("❌ No exchanges found in database")
        return []
    
    print("📊 Exchanges found:")
    print("-" * 40)
    
    for exchange in exchanges:
        symbol_count = Symbols.objects.filter(exchange=exchange).count()
        print(f"  {exchange.id:2d}. {exchange.name:20s} - {symbol_count:4d} symbols")
    
    return list(exchanges)

def show_available_strategies():
    """Show available strategies in the system"""
    
    print("\n🔍 Available Strategies...")
    print("=" * 60)
    
    strategies = Strategy.objects.all()
    
    if not strategies.exists():
        print("❌ No strategies found in database")
        return []
    
    print("📊 Strategies found:")
    print("-" * 40)
    
    for strategy in strategies:
        print(f"  {strategy.slug:15s} - {strategy.name}")
    
    return list(strategies)

def test_exchange_specific_backtest():
    """Test running a backtest for a specific exchange"""
    
    print("\n🔍 Testing Exchange-Specific Backtest...")
    print("=" * 60)
    
    # Get available exchanges and strategies
    exchanges = show_available_exchanges()
    strategies = show_available_strategies()
    
    if not exchanges or not strategies:
        print("❌ Cannot proceed without exchanges or strategies")
        return False
    
    # Select first exchange and strategy for testing
    test_exchange = exchanges[0]
    test_strategy = strategies[0]
    
    print(f"\n📈 Running backtest for:")
    print(f"   Strategy: {test_strategy.name} ({test_strategy.slug})")
    print(f"   Exchange: {test_exchange.name}")
    print(f"   Date Range: 2024-01-01 to 2024-01-31")
    
    try:
        # Run the backtest
        result = execute_backtest(
            strategy_id=test_strategy.slug,
            start_date='2024-01-01',
            end_date='2024-01-31',
            exchange_id=test_exchange.id
        )
        
        if isinstance(result, BackTestingStrategy):
            print(f"✅ Backtest completed successfully!")
            print(f"   Backtest ID: {result.id}")
            print(f"   Exchange: {result.exchange.name if result.exchange else 'None'}")
            print(f"   Strategy: {result.strategy.name}")
            print(f"   Created: {result.created_at}")
            
            # Show statistics
            show_backtest_statistics(result)
            return True
        else:
            print(f"❌ Backtest failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error running backtest: {e}")
        return False

def show_backtest_statistics(backtest):
    """Show statistics for a specific backtest"""
    
    print(f"\n📊 Backtest Statistics for {backtest}")
    print("=" * 60)
    
    # Get symbol statistics
    symbol_stats = SymbolStatistics.objects.filter(backtest=backtest)
    
    if symbol_stats.exists():
        print(f"📈 Symbol Statistics ({symbol_stats.count()} records):")
        print("-" * 50)
        
        for stat in symbol_stats[:5]:  # Show first 5
            exchange_name = f" [{stat.exchange.name}]" if stat.exchange else ""
            symbol_name = stat.symbol.ticker if stat.symbol else "PAIR_TRADING"
            print(f"  {symbol_name:12s} {stat.action:10s} - Trades: {stat.total_trades:3d}, Win Rate: {stat.win_rate:5.1f}%, ROI: {stat.total_roi:6.2f}%{exchange_name}")
        
        if symbol_stats.count() > 5:
            print(f"  ... and {symbol_stats.count() - 5} more records")
    else:
        print("⚠️ No symbol statistics found")
    
    # Get strategy statistics
    strategy_stats = StrategyStatistics.objects.filter(backtest=backtest)
    
    if strategy_stats.exists():
        print(f"\n📊 Strategy Statistics ({strategy_stats.count()} records):")
        print("-" * 50)
        
        for stat in strategy_stats:
            exchange_name = f" [{stat.exchange.name}]" if stat.exchange else ""
            print(f"  {stat.action:12s} - Trades: {stat.total_trades:3d}, Win Rate: {stat.win_rate:5.1f}%, Total P&L: {stat.total_profit_loss:8.2f}{exchange_name}")
    else:
        print("⚠️ No strategy statistics found")

def test_multiple_exchanges():
    """Test running the same strategy on multiple exchanges"""
    
    print("\n🔍 Testing Multiple Exchanges for Same Strategy...")
    print("=" * 60)
    
    exchanges = Exchange.objects.all()[:3]  # Test with first 3 exchanges
    strategies = Strategy.objects.all()[:1]  # Test with first strategy
    
    if not exchanges.exists() or not strategies.exists():
        print("❌ Need at least 3 exchanges and 1 strategy for this test")
        return False
    
    test_strategy = strategies[0]
    results = []
    
    print(f"📈 Running '{test_strategy.name}' strategy on {exchanges.count()} exchanges:")
    print("-" * 60)
    
    for exchange in exchanges:
        print(f"\n🔄 Testing on {exchange.name}...")
        
        try:
            # Run backtest for this exchange
            result = execute_backtest(
                strategy_id=test_strategy.slug,
                start_date='2024-01-01',
                end_date='2024-01-31',
                exchange_id=exchange.id
            )
            
            if isinstance(result, BackTestingStrategy):
                print(f"   ✅ Success - Backtest ID: {result.id}")
                results.append(result)
                
                # Show quick stats
                symbol_count = SymbolStatistics.objects.filter(backtest=result).count()
                print(f"   📊 Symbol statistics: {symbol_count}")
            else:
                print(f"   ❌ Failed: {result}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Compare results across exchanges
    if results:
        print(f"\n📊 Comparison Across {len(results)} Exchanges:")
        print("-" * 60)
        
        for backtest in results:
            exchange_name = backtest.exchange.name if backtest.exchange else "Unknown"
            symbol_stats = SymbolStatistics.objects.filter(backtest=backtest)
            total_trades = symbol_stats.aggregate(total=models.Sum('total_trades'))['total'] or 0
            avg_win_rate = symbol_stats.aggregate(avg=models.Avg('win_rate'))['avg'] or 0
            total_pnl = symbol_stats.aggregate(total=models.Sum('profit_loss'))['total'] or 0
            
            print(f"  {exchange_name:15s} - Trades: {total_trades:3d}, Avg Win Rate: {avg_win_rate:5.1f}%, Total P&L: {total_pnl:8.2f}")
    
    return len(results) > 0

def show_exchange_comparison():
    """Show a comparison of backtests across different exchanges"""
    
    print("\n🔍 Exchange Comparison Analysis...")
    print("=" * 60)
    
    # Get all backtests with exchange information
    backtests = BackTestingStrategy.objects.filter(exchange__isnull=False).order_by('strategy', 'exchange')
    
    if not backtests.exists():
        print("❌ No exchange-specific backtests found")
        return
    
    print("📊 Backtests by Exchange:")
    print("-" * 60)
    
    current_strategy = None
    for backtest in backtests:
        if current_strategy != backtest.strategy:
            current_strategy = backtest.strategy
            print(f"\n📈 Strategy: {backtest.strategy.name}")
            print("-" * 40)
        
        exchange_name = backtest.exchange.name if backtest.exchange else "Unknown"
        symbol_stats_count = SymbolStatistics.objects.filter(backtest=backtest).count()
        strategy_stats_count = StrategyStatistics.objects.filter(backtest=backtest).count()
        
        print(f"  {exchange_name:20s} - Symbols: {symbol_stats_count:3d}, Strategy Stats: {strategy_stats_count:3d}")

def test_symbol_filtering_by_exchange():
    """Test symbol filtering by exchange"""
    
    print("\n🔍 Testing Symbol Filtering by Exchange...")
    print("=" * 60)
    
    exchanges = Exchange.objects.all()[:2]  # Test with first 2 exchanges
    
    if not exchanges.exists():
        print("❌ No exchanges found for testing")
        return False
    
    for exchange in exchanges:
        print(f"\n📊 Exchange: {exchange.name}")
        print("-" * 40)
        
        # Count symbols for this exchange
        symbol_count = Symbols.objects.filter(exchange=exchange).count()
        print(f"  Total symbols: {symbol_count}")
        
        # Show some example symbols
        symbols = Symbols.objects.filter(exchange=exchange)[:5]
        for symbol in symbols:
            print(f"    - {symbol.ticker}")
        
        if symbol_count > 5:
            print(f"    ... and {symbol_count - 5} more")

if __name__ == "__main__":
    print("🚀 Starting Exchange-Specific Backtesting Tests...")
    
    # Test 1: Show available exchanges and strategies
    show_available_exchanges()
    show_available_strategies()
    
    # Test 2: Test exchange-specific backtest
    exchange_test_passed = test_exchange_specific_backtest()
    
    # Test 3: Test multiple exchanges
    multiple_exchanges_passed = test_multiple_exchanges()
    
    # Test 4: Show exchange comparison
    show_exchange_comparison()
    
    # Test 5: Test symbol filtering
    symbol_filtering_passed = test_symbol_filtering_by_exchange()
    
    print("\n" + "=" * 60)
    print("📝 Summary:")
    print(f"   Exchange-specific backtest: {'✅ PASSED' if exchange_test_passed else '❌ FAILED'}")
    print(f"   Multiple exchanges test: {'✅ PASSED' if multiple_exchanges_passed else '❌ FAILED'}")
    print(f"   Symbol filtering test: {'✅ PASSED' if symbol_filtering_passed else '❌ FAILED'}")
    
    if exchange_test_passed and multiple_exchanges_passed and symbol_filtering_passed:
        print("\n🎉 All tests completed successfully!")
        print("   Exchange-specific backtesting is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
    
    print("\n📋 Usage Examples:")
    print("   # Run backtest for specific exchange")
    print("   execute_backtest('mean-reverting', '2024-01-01', exchange_id=1)")
    print("   ")
    print("   # Run backtest for exchange by name")
    print("   execute_backtest('ma-crossover', '2024-01-01', exchange_name='CRYPTO USDT')")
    print("   ")
    print("   # Run cointegration strategy on specific exchange")
    print("   execute_backtest('cointegration', '2024-01-01', exchange_id=1)")
