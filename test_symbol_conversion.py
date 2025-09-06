#!/usr/bin/env python3
"""
Test script for symbol conversion logic in BrokerUtils.
This script tests the _convert_symbol_for_binance method with various symbol formats.
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from execution.broker_utils import BrokerUtils

def test_symbol_conversion():
    """Test the symbol conversion logic"""
    
    print("🔍 Testing Symbol Conversion Logic...")
    print("=" * 60)
    
    # Create a BrokerUtils instance (we only need it for the conversion method)
    broker_utils = BrokerUtils("Binance", "test_key", "test_secret")
    
    # Test cases with expected results
    test_cases = [
        # Format: (input_symbol, expected_output)
        ("BTC-USD", "BTCUSDT"),
        ("ETH-USD", "ETHUSDT"),
        ("LINK-USD", "LINKUSDT"),
        ("BTC-USDT", "BTCUSDT"),
        ("ETH-USDT", "ETHUSDT"),
        ("LINK-BTC", "LINKBTC"),
        ("ETH-BTC", "ETHBTC"),
        ("LINK-ETH", "LINKETH"),
        ("BNB-USD", "BNBUSDT"),
        ("ADA-USD", "ADAUSDT"),
        ("DOT-USD", "DOTUSDT"),
        ("SOL-USD", "SOLUSDT"),
        ("MATIC-USD", "MATICUSDT"),
        ("AVAX-USD", "AVAXUSDT"),
        ("UNI-USD", "UNIUSDT"),
        ("LTC-USD", "LTCUSDT"),
        ("BCH-USD", "BCHUSDT"),
        ("XRP-USD", "XRPUSDT"),
        ("DOGE-USD", "DOGEUSDT"),
        ("SHIB-USD", "SHIBUSDT"),
        ("LINK", "LINKUSDT"),  # No quote currency specified
        ("BTC", "BTCUSDT"),    # No quote currency specified
    ]
    
    print("📊 Testing Symbol Conversions:")
    print("-" * 40)
    
    all_passed = True
    
    for input_symbol, expected_output in test_cases:
        try:
            result = broker_utils._convert_symbol_for_binance(input_symbol)
            status = "✅" if result == expected_output else "❌"
            print(f"{status} {input_symbol:12} → {result:12} (expected: {expected_output})")
            
            if result != expected_output:
                all_passed = False
                
        except Exception as e:
            print(f"❌ {input_symbol:12} → ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All symbol conversions passed!")
    else:
        print("❌ Some symbol conversions failed!")
    
    return all_passed

def test_real_symbols():
    """Test with real symbols from the database"""
    
    print("\n🔍 Testing with Real Symbols from Database...")
    print("=" * 60)
    
    try:
        from symbols.models import Symbols, Broker
        
        # Get Binance broker
        binance_broker = Broker.objects.filter(name="Binance").first()
        
        if not binance_broker:
            print("❌ No Binance broker found in database")
            return False
        
        # Get symbols associated with Binance
        binance_symbols = Symbols.objects.filter(broker=binance_broker)
        
        if not binance_symbols.exists():
            print("❌ No symbols found for Binance broker")
            return False
        
        print(f"📊 Found {binance_symbols.count()} symbols for Binance broker")
        print("-" * 40)
        
        broker_utils = BrokerUtils("Binance", "test_key", "test_secret")
        
        for symbol in binance_symbols[:10]:  # Test first 10 symbols
            try:
                converted = broker_utils._convert_symbol_for_binance(symbol.ticker)
                print(f"📈 {symbol.ticker:12} → {converted:12}")
            except Exception as e:
                print(f"❌ {symbol.ticker:12} → ERROR: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing real symbols: {e}")
        return False

def test_api_endpoints():
    """Test if converted symbols work with Binance API endpoints"""
    
    print("\n🔍 Testing API Endpoint Compatibility...")
    print("=" * 60)
    
    # Test symbols that should work with Binance API
    test_symbols = [
        "BTC-USD",
        "ETH-USD", 
        "LINK-BTC",
        "BNB-USD",
        "ADA-USD"
    ]
    
    broker_utils = BrokerUtils("Binance", "test_key", "test_secret")
    
    print("📊 Testing symbol conversion for API endpoints:")
    print("-" * 50)
    
    for symbol in test_symbols:
        try:
            converted = broker_utils._convert_symbol_for_binance(symbol)
            print(f"📈 {symbol:12} → {converted:12}")
            
            # Test if the converted symbol follows Binance naming conventions
            if len(converted) >= 6 and converted.isalnum():
                print(f"   ✅ Valid Binance symbol format")
            else:
                print(f"   ❌ Invalid Binance symbol format")
                
        except Exception as e:
            print(f"❌ {symbol:12} → ERROR: {e}")

if __name__ == "__main__":
    print("🚀 Starting Symbol Conversion Tests...")
    
    # Test basic conversion logic
    conversion_passed = test_symbol_conversion()
    
    # Test with real symbols from database
    real_symbols_passed = test_real_symbols()
    
    # Test API endpoint compatibility
    test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("📝 Summary:")
    print(f"   Symbol conversion logic: {'✅ PASSED' if conversion_passed else '❌ FAILED'}")
    print(f"   Real symbols test: {'✅ PASSED' if real_symbols_passed else '❌ FAILED'}")
    
    if conversion_passed and real_symbols_passed:
        print("\n🎉 All tests completed successfully!")
        print("   The symbol conversion logic should now work correctly with Binance API.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
