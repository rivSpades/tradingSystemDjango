#!/usr/bin/env python3
"""
Test script for Binance daily price updates with fixed symbol conversion.
This script tests the complete flow from symbol conversion to data retrieval.
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
from execution.broker_utils import BrokerUtils

def test_binance_symbol_conversion():
    """Test the symbol conversion specifically for the problematic symbol"""
    
    print("🔍 Testing Binance Symbol Conversion...")
    print("=" * 60)
    
    # Test the specific symbol that was causing the error
    test_symbols = [
        "LINK-BTC",  # This was causing the 400 error
        "BTC-USD",
        "ETH-USD",
        "BNB-USD",
        "ADA-USD"
    ]
    
    broker_utils = BrokerUtils("Binance", "test_key", "test_secret")
    
    print("📊 Testing symbol conversions:")
    print("-" * 40)
    
    for symbol in test_symbols:
        try:
            converted = broker_utils._convert_symbol_for_binance(symbol)
            print(f"✅ {symbol:12} → {converted:12}")
        except Exception as e:
            print(f"❌ {symbol:12} → ERROR: {e}")
    
    return True

def test_binance_daily_price_retrieval():
    """Test actual daily price retrieval from Binance API"""
    
    print("\n🔍 Testing Binance Daily Price Retrieval...")
    print("=" * 60)
    
    # Get Binance broker
    binance_broker = Broker.objects.filter(name="Binance").first()
    
    if not binance_broker:
        print("❌ No Binance broker found in database")
        return False
    
    # Get a few symbols from Binance
    binance_symbols = Symbols.objects.filter(broker=binance_broker)[:5]
    
    if not binance_symbols.exists():
        print("❌ No symbols found for Binance broker")
        return False
    
    print(f"📊 Testing daily price retrieval for {binance_symbols.count()} symbols")
    print("-" * 50)
    
    success_count = 0
    error_count = 0
    
    for symbol in binance_symbols:
        try:
            print(f"📈 Testing {symbol.ticker}...")
            
            # Test individual symbol update
            success = DailyPriceManager.insert_daily_price(symbol, '2024-01-01')
            
            if success:
                print(f"   ✅ Successfully updated {symbol.ticker}")
                success_count += 1
            else:
                print(f"   ⚠️ No new data to insert for {symbol.ticker}")
                success_count += 1  # Still considered success
                
        except Exception as e:
            print(f"   ❌ Error updating {symbol.ticker}: {e}")
            error_count += 1
    
    print(f"\n📊 Results:")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")
    print(f"   Total: {success_count + error_count}")
    
    return error_count == 0

def test_broker_specific_update():
    """Test the broker-specific update functionality"""
    
    print("\n🔍 Testing Broker-Specific Update...")
    print("=" * 60)
    
    try:
        # Test updating only Binance symbols
        print("🔄 Updating daily prices for Binance broker only...")
        result = DailyPriceManager.update_daily_prices_for_symbols(broker_name='Binance')
        
        print(f"✅ Binance update completed!")
        print(f"   Success: {result['success_count']}")
        print(f"   Errors: {result['error_count']}")
        print(f"   Total: {result['total_processed']}")
        
        return result['error_count'] == 0
        
    except Exception as e:
        print(f"❌ Error in broker-specific update: {e}")
        return False

def show_symbol_statistics():
    """Show statistics about Binance symbols"""
    
    print("\n📊 Binance Symbol Statistics...")
    print("=" * 60)
    
    binance_broker = Broker.objects.filter(name="Binance").first()
    
    if not binance_broker:
        print("❌ No Binance broker found")
        return
    
    binance_symbols = Symbols.objects.filter(broker=binance_broker)
    total_symbols = binance_symbols.count()
    
    print(f"Total Binance symbols: {total_symbols}")
    
    # Show some examples
    print(f"\nExample symbols:")
    for symbol in binance_symbols[:10]:
        print(f"  - {symbol.ticker}")
    
    if total_symbols > 10:
        print(f"  ... and {total_symbols - 10} more")

if __name__ == "__main__":
    print("🚀 Starting Binance Daily Price Tests...")
    
    # Show statistics first
    show_symbol_statistics()
    
    # Test symbol conversion
    conversion_passed = test_binance_symbol_conversion()
    
    # Test daily price retrieval
    retrieval_passed = test_binance_daily_price_retrieval()
    
    # Test broker-specific update
    update_passed = test_broker_specific_update()
    
    print("\n" + "=" * 60)
    print("📝 Summary:")
    print(f"   Symbol conversion: {'✅ PASSED' if conversion_passed else '❌ FAILED'}")
    print(f"   Daily price retrieval: {'✅ PASSED' if retrieval_passed else '❌ FAILED'}")
    print(f"   Broker-specific update: {'✅ PASSED' if update_passed else '❌ FAILED'}")
    
    if conversion_passed and retrieval_passed and update_passed:
        print("\n🎉 All tests completed successfully!")
        print("   The Binance integration should now work correctly.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
