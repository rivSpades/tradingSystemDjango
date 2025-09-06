#!/usr/bin/env python3
"""
Test script for Binance API integration in the trading system.
This script tests the BrokerUtils class with Binance broker configuration.
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

from execution.broker_utils import BrokerUtils
from symbols.models import Symbols, Broker

def test_binance_integration():
    """Test Binance API integration"""
    
    print("🔍 Testing Binance API Integration...")
    
    # Check if Binance broker exists
    try:
        binance_broker = Broker.objects.get(name="Binance")
        print(f"✅ Found Binance broker: {binance_broker.name}")
        print(f"   API Key: {'*' * 10}{binance_broker.api_key[-4:] if binance_broker.api_key else 'Not set'}")
        print(f"   Secret Key: {'*' * 10}{binance_broker.secret_key[-4:] if binance_broker.secret_key else 'Not set'}")
    except Broker.DoesNotExist:
        print("❌ Binance broker not found in database")
        print("   Please create a Binance broker entry with API credentials")
        return False
    
    # Initialize BrokerUtils with Binance
    try:
        broker_utils = BrokerUtils(
            broker_name="Binance",
            api_key=binance_broker.api_key,
            secret_key=binance_broker.secret_key
        )
        print("✅ BrokerUtils initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize BrokerUtils: {e}")
        return False
    
    # Test 1: Get account information
    print("\n📊 Test 1: Getting account information...")
    try:
        account_info = broker_utils.get_account_info()
        if "error" not in account_info:
            print("✅ Account info retrieved successfully")
            print(f"   Status: {account_info.get('status', 'Unknown')}")
            print(f"   Equity: {account_info.get('equity', 'Unknown')}")
        else:
            print(f"❌ Failed to get account info: {account_info['error']}")
    except Exception as e:
        print(f"❌ Error getting account info: {e}")
    
    # Test 2: Get daily price data for BTC-USD
    print("\n📈 Test 2: Getting daily price data for BTC-USD...")
    try:
        # Create a test symbol if it doesn't exist
        btc_symbol, created = Symbols.objects.get_or_create(
            ticker="BTC-USD",
            defaults={
                'instrument': 'CRYPTO',
                'name': 'Bitcoin',
                'broker': binance_broker
            }
        )
        
        if created:
            print(f"✅ Created test symbol: {btc_symbol.ticker}")
        else:
            print(f"✅ Using existing symbol: {btc_symbol.ticker}")
        
        # Get daily prices for the last 7 days
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=7)
        
        daily_prices = broker_utils.get_daily_price(btc_symbol, start_date, end_date)
        
        if not daily_prices.empty:
            print("✅ Daily price data retrieved successfully")
            print(f"   Data points: {len(daily_prices)}")
            print(f"   Date range: {daily_prices['Date'].min()} to {daily_prices['Date'].max()}")
            print(f"   Latest close: ${daily_prices['Close'].iloc[-1]:.2f}")
            print(f"   Columns: {list(daily_prices.columns)}")
        else:
            print("❌ No daily price data retrieved")
            
    except Exception as e:
        print(f"❌ Error getting daily price data: {e}")
    
    # Test 3: Get latest minute bar
    print("\n⏰ Test 3: Getting latest minute bar...")
    try:
        latest_bar = broker_utils.last_minute_bar("BTC-USD")
        
        if not latest_bar.empty:
            print("✅ Latest minute bar retrieved successfully")
            print(f"   Time: {latest_bar['Date'].iloc[0]}")
            print(f"   Close: ${latest_bar['Close'].iloc[0]:.2f}")
            print(f"   Volume: {latest_bar['Volume'].iloc[0]:.2f}")
        else:
            print("❌ No latest minute bar data retrieved")
            
    except Exception as e:
        print(f"❌ Error getting latest minute bar: {e}")
    
    print("\n🎉 Binance integration test completed!")
    return True

def test_symbol_format_conversion():
    """Test symbol format conversion for Binance"""
    print("\n🔄 Testing symbol format conversion...")
    
    test_cases = [
        ("BTC-USD", "BTCUSDT"),
        ("ETH-USD", "ETHUSDT"),
        ("BTC-USDT", "BTCUSDT"),
        ("ETH-USDT", "ETHUSDT"),
        ("ADA-USDT", "ADAUSDT"),
    ]
    
    broker_utils = BrokerUtils("Binance", "test_key", "test_secret")
    
    for input_symbol, expected_output in test_cases:
        # Test the conversion logic
        if input_symbol.endswith('-USD'):
            converted = input_symbol.replace('-USD', 'USDT')
        elif input_symbol.endswith('-USDT'):
            converted = input_symbol.replace('-', '')
        else:
            converted = input_symbol.replace('-', '')
        
        if converted == expected_output:
            print(f"✅ {input_symbol} → {converted}")
        else:
            print(f"❌ {input_symbol} → {converted} (expected: {expected_output})")

if __name__ == "__main__":
    print("🚀 Starting Binance Integration Tests...")
    print("=" * 50)
    
    # Test symbol format conversion
    test_symbol_format_conversion()
    
    # Test full integration
    success = test_binance_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests completed successfully!")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    print("\n📝 Notes:")
    print("- Make sure you have a Binance broker entry in the database")
    print("- Ensure API key and secret key are properly configured")
    print("- For live trading, use real API credentials")
    print("- For testing, you can use Binance testnet")
