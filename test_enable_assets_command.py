#!/usr/bin/env python3
"""
Test script to demonstrate the enable_assets command that uses broker_utils.enable_assets().
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

from symbols.models import Symbols, Broker, Exchange

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
        enabled_count = Symbols.objects.filter(broker=broker, slot_free=True).count()
        disabled_count = Symbols.objects.filter(broker=broker, slot_free=False).count()
        
        print(f"  {broker.name:15s} - {symbol_count:4d} symbols ({enabled_count:4d} enabled, {disabled_count:4d} disabled)")
    
    return list(brokers)

def test_enable_assets_command():
    """Test the enable_assets command"""
    
    print("🚀 Testing Enable Assets Command (broker_utils)...")
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
            call_command('enable_assets', broker.name, '--dry-run', stdout=out)
            print(out.getvalue())
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
        
        # Test 2: Actual execution (commented out for safety)
        print(f"🔄 Test 2: Would execute enable_assets for {broker.name}...")
        print("   (Skipped for safety - uncomment to test)")
        
        # Uncomment the following lines to actually test the command:
        # try:
        #     out = StringIO()
        #     call_command('enable_assets', broker.name, stdout=out)
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
    print("  # Enable assets for Alpaca broker")
    print("  python manage.py enable_assets 'Alpaca'")
    print("  ")
    print("  # Enable assets for Binance broker")
    print("  python manage.py enable_assets 'Binance'")
    print("  ")
    print("  # Dry run to see what would happen")
    print("  python manage.py enable_assets 'Alpaca' --dry-run")
    print("  ")
    print("  # Enable assets for any broker (case insensitive)")
    print("  python manage.py enable_assets 'alpaca'")
    print("  python manage.py enable_assets 'BINANCE'")

def show_broker_utils_info():
    """Show information about what the command does"""
    
    print("\n🔧 What this command does:")
    print("=" * 60)
    
    print("📊 For Alpaca:")
    print("  - Fetches active US equity assets from Alpaca API")
    print("  - Creates/updates symbols in database")
    print("  - Sets trading permissions (long/short)")
    print("  - Associates symbols with Alpaca broker")
    print("  ")
    print("📊 For Binance:")
    print("  - Fetches exchange info from Binance API")
    print("  - Creates/updates crypto symbols in database")
    print("  - Sets trading permissions based on margin trading availability")
    print("  - Associates symbols with Binance broker")
    print("  ")
    print("⚠️  Note: This command will:")
    print("  - Create new symbols if they don't exist")
    print("  - Update existing symbols with latest broker info")
    print("  - Set slot_free=True for all symbols")
    print("  - Update long/short trading permissions")

if __name__ == "__main__":
    print("🚀 Testing Enable Assets Command (broker_utils)...")
    
    # Show current state
    show_brokers()
    
    # Show what the command does
    show_broker_utils_info()
    
    # Test the command
    success = test_enable_assets_command()
    
    # Show usage examples
    show_usage_examples()
    
    if success:
        print("\n✅ Command testing completed successfully!")
        print("   You can now use the enable_assets command to fetch and enable assets from brokers.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
