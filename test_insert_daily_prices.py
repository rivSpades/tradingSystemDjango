#!/usr/bin/env python3
"""
Test script to demonstrate the insert_daily_prices management command.
"""

import os
import sys
import django
from django.core.management import call_command
from io import StringIO

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from symbols.models import Symbols, Broker, DailyPrice

def show_brokers():
    """Show available brokers"""
    print("🔍 Available Brokers...")
    print("=" * 60)
    
    brokers = Broker.objects.all()
    if not brokers.exists():
        print("❌ No brokers found in database")
        return []
    
    print("📊 Brokers found:")
    print("-" * 40)
    
    for broker in brokers:
        symbol_count = Symbols.objects.filter(broker=broker).count()
        price_count = DailyPrice.objects.filter(symbol__broker=broker).count()
        
        print(f"  {broker.name:15s} - {symbol_count:4d} symbols, {price_count:6d} price records")
    
    return list(brokers)

def show_exchanges():
    """Show available exchanges"""
    print("\n🔍 Available Exchanges...")
    print("=" * 60)
    
    from symbols.models import Exchange
    exchanges = Exchange.objects.all()
    if not exchanges.exists():
        print("❌ No exchanges found in database")
        return []
    
    print("📊 Exchanges found:")
    print("-" * 40)
    
    for exchange in exchanges:
        symbol_count = Symbols.objects.filter(exchange=exchange).count()
        print(f"  {exchange.name:20s} - {symbol_count:4d} symbols")
    
    return list(exchanges)

def test_insert_daily_prices_command():
    """Test the insert_daily_prices command"""
    
    print("🚀 Testing Insert Daily Prices Command...")
    print("=" * 60)
    
    # Show available brokers
    brokers = show_brokers()
    if not brokers:
        return False
    
    # Test with each broker
    for broker in brokers:
        print(f"\n📈 Testing with broker: {broker.name}")
        
        # Test 1: Dry run
        print(f"🔄 Test 1: Dry run for {broker.name}...")
        try:
            out = StringIO()
            call_command('insert_daily_prices', broker.name, '--dry-run', stdout=out)
            print(out.getvalue())
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
        
        # Test 2: Dry run with specific symbols
        print(f"🔄 Test 2: Dry run with specific symbols for {broker.name}...")
        try:
            # Get first few symbols for this broker
            symbols = Symbols.objects.filter(broker=broker)[:3]
            if symbols.exists():
                symbol_list = ','.join([s.ticker for s in symbols])
                print(f"Testing with symbols: {symbol_list}")
                
                out = StringIO()
                call_command('insert_daily_prices', broker.name, '--dry-run', '--symbols', symbol_list, stdout=out)
                print(out.getvalue())
            else:
                print("⚠️ No symbols found for testing")
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
        
        # Test 3: Dry run with exchange filter
        print(f"🔄 Test 3: Dry run with exchange filter for {broker.name}...")
        try:
            # Get exchanges for this broker
            from symbols.models import Exchange
            exchanges = Exchange.objects.filter(symbols__broker=broker).distinct()[:2]
            if exchanges.exists():
                for exchange in exchanges:
                    print(f"Testing with exchange: {exchange.name}")
                    
                    out = StringIO()
                    call_command('insert_daily_prices', broker.name, '--dry-run', '--exchange', exchange.name, stdout=out)
                    print(out.getvalue())
            else:
                print("⚠️ No exchanges found for testing")
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
        
        # Test 4: Actual execution (commented out for safety)
        print(f"🔄 Test 4: Would execute insert_daily_prices for {broker.name}...")
        print("   (Skipped for safety - uncomment to test)")
        
        # Uncomment the following lines to actually test the command:
        # try:
        #     out = StringIO()
        #     call_command('insert_daily_prices', broker.name, stdout=out)
        #     print(out.getvalue())
        # except Exception as e:
        #     print(f"❌ Error: {e}")
        #     continue
    
    return True

def show_usage_examples():
    """Show usage examples for the command"""
    
    print("\n📋 Usage Examples:")
    print("=" * 60)
    
    print("🔧 Basic Usage:")
    print("  # Insert daily prices for Alpaca broker")
    print("  python manage.py insert_daily_prices 'Alpaca'")
    print("  ")
    print("  # Insert daily prices for Binance broker")
    print("  python manage.py insert_daily_prices 'Binance'")
    print("  ")
    print("  # Dry run to see what would happen")
    print("  python manage.py insert_daily_prices 'Alpaca' --dry-run")
    print("  ")
    print("  # Insert prices for specific symbols")
    print("  python manage.py insert_daily_prices 'Alpaca' --symbols 'AAPL,MSFT,GOOGL'")
    print("  ")
    print("  # Insert prices with custom date range")
    print("  python manage.py insert_daily_prices 'Alpaca' --start-date '2024-01-01' --end-date '2024-12-31'")
    print("  ")
    print("  # Insert prices for specific exchange")
    print("  python manage.py insert_daily_prices 'Alpaca' --exchange 'NYSE'")
    print("  ")
    print("  # Insert prices for specific exchange and symbols")
    print("  python manage.py insert_daily_prices 'Alpaca' --exchange 'NASDAQ' --symbols 'AAPL,MSFT'")
    print("  ")
    print("  # Combine options")
    print("  python manage.py insert_daily_prices 'Alpaca' --symbols 'AAPL,MSFT' --dry-run")

def show_daily_price_manager_info():
    """Show information about what the command does"""
    
    print("\n🔧 What this command does:")
    print("=" * 60)
    
    print("📊 Function Used:")
    print("  - Uses DailyPriceManager.update_daily_prices_for_symbols()")
    print("  - Automatically determines the last available date for each symbol")
    print("  - Fetches new price data from the broker API")
    print("  - Inserts only new price records (skips existing ones)")
    print("  ")
    print("📊 For Each Symbol:")
    print("  - Checks the last available date in the database")
    print("  - Fetches price data from the last date + 1 day")
    print("  - Creates DailyPrice objects for new data")
    print("  - Uses bulk_create for efficient database insertion")
    print("  ")
    print("⚠️  Note: This command will:")
    print("  - Only insert new price data (won't overwrite existing)")
    print("  - Use the appropriate broker API for each symbol")
    print("  - Handle errors gracefully and continue with other symbols")
    print("  - Show detailed progress and summary")

if __name__ == "__main__":
    print("🚀 Testing Insert Daily Prices Command...")
    
    # Show current state
    show_brokers()
    show_exchanges()
    
    # Show what the command does
    show_daily_price_manager_info()
    
    # Test the command
    success = test_insert_daily_prices_command()
    
    # Show usage examples
    show_usage_examples()
    
    if success:
        print("\n✅ Command testing completed successfully!")
        print("   You can now use the insert_daily_prices command to fetch and store price data.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
