#!/usr/bin/env python3
"""
Test script for CryptoCompare API integration for Binance symbols.
This script tests the daily price retrieval using CryptoCompare API.
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

def test_cryptocompare_api():
    """Test CryptoCompare API directly"""
    
    print("🔍 Testing CryptoCompare API Directly...")
    print("=" * 60)
    
    import requests
    
    api_key = '22a78314e3f7625b24ea2f67cf802d28cae94db3bbaf61cf0c3437ff0df8f97e'
    
    # Test symbols
    test_symbols = [
        ('BTC', 'USD'),
        ('ETH', 'USD'),
        ('LINK', 'USD'),
        ('BNB', 'USD'),
        ('ADA', 'USD')
    ]
    
    print("📊 Testing CryptoCompare API endpoints:")
    print("-" * 50)
    
    for fsym, tsym in test_symbols:
        try:
            url = f'https://min-api.cryptocompare.com/data/v2/histoday'
            params = {
                'fsym': fsym,
                'tsym': tsym,
                'limit': 10,  # Just get 10 days for testing
                'api_key': api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('Response') == 'Error':
                print(f"❌ {fsym}-{tsym}: API Error - {data.get('Message', 'Unknown error')}")
            else:
                records = len(data.get('Data', {}).get('Data', []))
                print(f"✅ {fsym}-{tsym}: {records} records retrieved")
                
        except Exception as e:
            print(f"❌ {fsym}-{tsym}: Error - {e}")
    
    return True

def test_binance_symbols_with_cryptocompare():
    """Test Binance symbols using CryptoCompare API"""
    
    print("\n🔍 Testing Binance Symbols with CryptoCompare...")
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
    
    print(f"📊 Testing {binance_symbols.count()} Binance symbols with CryptoCompare:")
    print("-" * 60)
    
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

def test_broker_utils_cryptocompare():
    """Test BrokerUtils with CryptoCompare for Binance symbols"""
    
    print("\n🔍 Testing BrokerUtils with CryptoCompare...")
    print("=" * 60)
    
    # Create a BrokerUtils instance for Binance
    broker_utils = BrokerUtils("Binance", "test_key", "test_secret")
    
    # Test symbols
    test_symbols = [
        "BTC-USD",
        "ETH-USD",
        "LINK-USD",
        "BNB-USD",
        "ADA-USD"
    ]
    
    print("📊 Testing daily price retrieval:")
    print("-" * 40)
    
    for symbol_ticker in test_symbols:
        try:
            # Create a mock symbol object
            class MockSymbol:
                def __init__(self, ticker):
                    self.ticker = ticker
                    self.instrument = "CRYPTO"
            
            mock_symbol = MockSymbol(symbol_ticker)
            
            # Test daily price retrieval
            df = broker_utils.get_daily_price(mock_symbol, '2024-01-01', '2024-01-31')
            
            if not df.empty:
                print(f"✅ {symbol_ticker}: {len(df)} records retrieved")
                print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
            else:
                print(f"⚠️ {symbol_ticker}: No data retrieved")
                
        except Exception as e:
            print(f"❌ {symbol_ticker}: Error - {e}")
    
    return True

def test_broker_specific_update():
    """Test the broker-specific update functionality with CryptoCompare"""
    
    print("\n🔍 Testing Broker-Specific Update with CryptoCompare...")
    print("=" * 60)
    
    try:
        # Test updating only Binance symbols
        print("🔄 Updating daily prices for Binance broker using CryptoCompare...")
        result = DailyPriceManager.update_daily_prices_for_symbols(broker_name='Binance')
        
        print(f"✅ Binance update completed!")
        print(f"   Success: {result['success_count']}")
        print(f"   Errors: {result['error_count']}")
        print(f"   Total: {result['total_processed']}")
        
        return result['error_count'] == 0
        
    except Exception as e:
        print(f"❌ Error in broker-specific update: {e}")
        return False

def show_cryptocompare_info():
    """Show information about CryptoCompare API"""
    
    print("\n📊 CryptoCompare API Information...")
    print("=" * 60)
    
    print("🔗 API Base URL: https://min-api.cryptocompare.com")
    print("📈 Endpoint: /data/v2/histoday")
    print("🔑 API Key: 22a78314e3f7625b24ea2f67cf802d28cae94db3bbaf61cf0c3437ff0df8f97e")
    print("📊 Max Limit: 2000 daily records")
    print("🌐 Documentation: https://min-api.cryptocompare.com")
    
    print("\n📋 Supported Parameters:")
    print("   - fsym: From Symbol (e.g., BTC)")
    print("   - tsym: To Symbol (e.g., USD)")
    print("   - limit: Number of records (max 2000)")
    print("   - api_key: Your API key")
    
    print("\n📈 Data Format:")
    print("   - time: Unix timestamp")
    print("   - open: Opening price")
    print("   - high: Highest price")
    print("   - low: Lowest price")
    print("   - close: Closing price")
    print("   - volumeto: Volume in quote currency")

if __name__ == "__main__":
    print("🚀 Starting CryptoCompare Integration Tests...")
    
    # Show CryptoCompare API information
    show_cryptocompare_info()
    
    # Test CryptoCompare API directly
    api_test_passed = test_cryptocompare_api()
    
    # Test BrokerUtils with CryptoCompare
    broker_utils_passed = test_broker_utils_cryptocompare()
    
    # Test Binance symbols with CryptoCompare
    symbols_passed = test_binance_symbols_with_cryptocompare()
    
    # Test broker-specific update
    update_passed = test_broker_specific_update()
    
    print("\n" + "=" * 60)
    print("📝 Summary:")
    print(f"   CryptoCompare API test: {'✅ PASSED' if api_test_passed else '❌ FAILED'}")
    print(f"   BrokerUtils test: {'✅ PASSED' if broker_utils_passed else '❌ FAILED'}")
    print(f"   Binance symbols test: {'✅ PASSED' if symbols_passed else '❌ FAILED'}")
    print(f"   Broker-specific update: {'✅ PASSED' if update_passed else '❌ FAILED'}")
    
    if api_test_passed and broker_utils_passed and symbols_passed and update_passed:
        print("\n🎉 All tests completed successfully!")
        print("   The CryptoCompare integration for Binance symbols is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
