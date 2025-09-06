#!/usr/bin/env python3
"""
Test script for broker-specific daily price updates.
This script demonstrates how to update daily prices for specific brokers.
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

from symbols.utils import DailyPriceManager
from symbols.models import Symbols, Broker

def test_broker_specific_updates():
    """Test broker-specific daily price updates"""
    
    print("🔍 Testing Broker-Specific Daily Price Updates...")
    print("=" * 60)
    
    # Check available brokers
    brokers = Broker.objects.all()
    print(f"📊 Available brokers: {[b.name for b in brokers]}")
    
    if not brokers.exists():
        print("❌ No brokers found in database")
        print("   Please create broker entries first")
        return False
    
    # Test 1: Update all symbols (all brokers)
    print("\n🔄 Test 1: Updating daily prices for ALL brokers")
    print("-" * 50)
    try:
        result = DailyPriceManager.update_daily_prices_for_symbols()
        print(f"✅ All brokers update completed!")
        print(f"   Success: {result['success_count']}")
        print(f"   Errors: {result['error_count']}")
        print(f"   Total: {result['total_processed']}")
    except Exception as e:
        print(f"❌ Error updating all brokers: {e}")
    
    # Test 2: Update specific broker (if available)
    for broker in brokers:
        print(f"\n🔄 Test 2: Updating daily prices for {broker.name} broker")
        print("-" * 50)
        
        # Check if broker has symbols
        symbol_count = Symbols.objects.filter(broker=broker).count()
        print(f"   Symbols found for {broker.name}: {symbol_count}")
        
        if symbol_count == 0:
            print(f"   ⚠️ No symbols found for {broker.name}, skipping...")
            continue
        
        try:
            result = DailyPriceManager.update_daily_prices_for_symbols(broker_name=broker.name)
            print(f"✅ {broker.name} broker update completed!")
            print(f"   Success: {result['success_count']}")
            print(f"   Errors: {result['error_count']}")
            print(f"   Total: {result['total_processed']}")
        except Exception as e:
            print(f"❌ Error updating {broker.name}: {e}")
    
    # Test 3: Test convenience method
    print(f"\n🔄 Test 3: Testing convenience method")
    print("-" * 50)
    try:
        first_broker = brokers.first()
        result = DailyPriceManager.update_daily_prices_for_broker(first_broker.name)
        print(f"✅ Convenience method test completed for {first_broker.name}!")
        print(f"   Success: {result['success_count']}")
        print(f"   Errors: {result['error_count']}")
    except Exception as e:
        print(f"❌ Error with convenience method: {e}")
    
    print("\n🎉 Broker-specific daily price update tests completed!")
    return True

def test_individual_symbol_update():
    """Test updating a single symbol"""
    
    print("\n🔍 Testing Individual Symbol Update...")
    print("=" * 60)
    
    # Find a symbol with a broker
    symbol = Symbols.objects.filter(broker__isnull=False).first()
    
    if not symbol:
        print("❌ No symbols with brokers found")
        return False
    
    print(f"📊 Testing symbol: {symbol.ticker} ({symbol.broker.name})")
    
    try:
        # Test individual symbol update
        success = DailyPriceManager.insert_daily_price(symbol, '2024-01-01')
        
        if success:
            print(f"✅ Successfully updated {symbol.ticker}")
        else:
            print(f"⚠️ No new data to insert for {symbol.ticker}")
            
    except Exception as e:
        print(f"❌ Error updating {symbol.ticker}: {e}")
    
    return True

def show_symbol_statistics():
    """Show statistics about symbols and their brokers"""
    
    print("\n📊 Symbol Statistics...")
    print("=" * 60)
    
    total_symbols = Symbols.objects.count()
    symbols_with_brokers = Symbols.objects.filter(broker__isnull=False).count()
    symbols_without_brokers = total_symbols - symbols_with_brokers
    
    print(f"Total symbols: {total_symbols}")
    print(f"Symbols with brokers: {symbols_with_brokers}")
    print(f"Symbols without brokers: {symbols_without_brokers}")
    
    # Show breakdown by broker
    brokers = Broker.objects.all()
    for broker in brokers:
        count = Symbols.objects.filter(broker=broker).count()
        print(f"  {broker.name}: {count} symbols")
    
    # Show symbols without brokers
    if symbols_without_brokers > 0:
        print(f"\nSymbols without brokers:")
        for symbol in Symbols.objects.filter(broker__isnull=True)[:5]:  # Show first 5
            print(f"  - {symbol.ticker}")
        if symbols_without_brokers > 5:
            print(f"  ... and {symbols_without_brokers - 5} more")

if __name__ == "__main__":
    print("🚀 Starting Broker-Specific Daily Price Update Tests...")
    
    # Show statistics first
    show_symbol_statistics()
    
    # Test individual symbol update
    test_individual_symbol_update()
    
    # Test broker-specific updates
    success = test_broker_specific_updates()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    print("\n📝 Usage Examples:")
    print("- Update all brokers: DailyPriceManager.update_daily_prices_for_symbols()")
    print("- Update specific broker: DailyPriceManager.update_daily_prices_for_symbols('Binance')")
    print("- Update single symbol: DailyPriceManager.insert_daily_price(symbol, '2024-01-01')")
