#!/usr/bin/env python3
"""
Test script to verify the backtest execution fix.
"""

import os
import sys
import django
from datetime import date

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from backtesting.backtest_logic import execute_backtest
from strategies.models import Strategy
from symbols.models import Exchange

def test_backtest_execution():
    """Test that backtest execution works without the variable scope error"""
    
    print("🔍 Testing Backtest Execution Fix...")
    print("=" * 60)
    
    # Get available strategies
    strategies = Strategy.objects.all()
    if not strategies.exists():
        print("❌ No strategies found in database")
        return False
    
    # Get available exchanges
    exchanges = Exchange.objects.all()
    if not exchanges.exists():
        print("❌ No exchanges found in database")
        return False
    
    test_strategy = strategies[0]
    test_exchange = exchanges[0]
    
    print(f"📈 Testing strategy: {test_strategy.name} ({test_strategy.slug})")
    print(f"📊 Testing exchange: {test_exchange.name}")
    print(f"📅 Date range: 2024-01-01 to 2024-01-31")
    
    try:
        # Test 1: Basic backtest without exchange
        print("\n🔄 Test 1: Basic backtest without exchange...")
        result1 = execute_backtest(
            strategy_id=test_strategy.slug,
            start_date='2024-01-01',
            end_date='2024-01-31'
        )
        
        if isinstance(result1, str) and "No symbols available" in result1:
            print("   ⚠️ No symbols available (expected if no symbols in database)")
        elif isinstance(result1, str):
            print(f"   ❌ Error: {result1}")
            return False
        else:
            print(f"   ✅ Success - Backtest ID: {result1.id}")
        
        # Test 2: Backtest with exchange
        print("\n🔄 Test 2: Backtest with exchange...")
        result2 = execute_backtest(
            strategy_id=test_strategy.slug,
            start_date='2024-01-01',
            end_date='2024-01-31',
            exchange_id=test_exchange.id
        )
        
        if isinstance(result2, str) and "No symbols available" in result2:
            print("   ⚠️ No symbols available for this exchange (expected if no symbols in exchange)")
        elif isinstance(result2, str):
            print(f"   ❌ Error: {result2}")
            return False
        else:
            print(f"   ✅ Success - Backtest ID: {result2.id}")
            print(f"   📊 Exchange: {result2.exchange.name if result2.exchange else 'None'}")
        
        # Test 3: Backtest with exchange name
        print("\n🔄 Test 3: Backtest with exchange name...")
        result3 = execute_backtest(
            strategy_id=test_strategy.slug,
            start_date='2024-01-01',
            end_date='2024-01-31',
            exchange_name=test_exchange.name
        )
        
        if isinstance(result3, str) and "No symbols available" in result3:
            print("   ⚠️ No symbols available for this exchange (expected if no symbols in exchange)")
        elif isinstance(result3, str):
            print(f"   ❌ Error: {result3}")
            return False
        else:
            print(f"   ✅ Success - Backtest ID: {result3.id}")
            print(f"   📊 Exchange: {result3.exchange.name if result3.exchange else 'None'}")
        
        print("\n🎉 All tests completed successfully!")
        print("   The variable scope error has been fixed.")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_database_info():
    """Show information about the database state"""
    
    print("\n📊 Database Information...")
    print("=" * 60)
    
    from strategies.models import Strategy
    from symbols.models import Exchange, Symbols
    
    strategies = Strategy.objects.all()
    exchanges = Exchange.objects.all()
    symbols = Symbols.objects.all()
    
    print(f"📈 Strategies: {strategies.count()}")
    for strategy in strategies:
        print(f"   - {strategy.name} ({strategy.slug})")
    
    print(f"\n📊 Exchanges: {exchanges.count()}")
    for exchange in exchanges:
        symbol_count = Symbols.objects.filter(exchange=exchange).count()
        print(f"   - {exchange.name} ({symbol_count} symbols)")
    
    print(f"\n💱 Symbols: {symbols.count()}")
    if symbols.exists():
        for symbol in symbols[:5]:  # Show first 5
            exchange_name = symbol.exchange.name if symbol.exchange else "No exchange"
            print(f"   - {symbol.ticker} ({exchange_name})")
        if symbols.count() > 5:
            print(f"   ... and {symbols.count() - 5} more")

if __name__ == "__main__":
    print("🚀 Testing Backtest Execution Fix...")
    
    # Show database information
    show_database_info()
    
    # Test the fix
    success = test_backtest_execution()
    
    if success:
        print("\n✅ All tests passed! The backtest execution is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
