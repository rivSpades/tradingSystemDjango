#!/usr/bin/env python
"""
Debug script for crypto underflow error in mean-reverting strategy
"""

import os
import sys
import django
import numpy as np

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from symbols.models import Symbols, DailyPrice
from strategies.strategy_logic import MeanRevertingStrategy
from backtesting.models import BackTestingStrategy
from datetime import date

def debug_crypto_underflow():
    """Debug the underflow error for PEPE-USDC"""
    print("🔍 Debugging crypto underflow error for PEPE-USDC")
    
    try:
        # Get the symbol
        symbol = Symbols.objects.get(ticker='PEPE-USDC')
        print(f"✅ Found symbol: {symbol.ticker}")
        print(f"   Exchange: {symbol.exchange}")
        print(f"   Broker: {symbol.broker}")
        
        # Check daily prices
        daily_prices = DailyPrice.objects.filter(symbol=symbol).order_by('price_date')
        print(f"📊 Daily prices found: {daily_prices.count()}")
        
        if daily_prices.exists():
            # Show sample prices
            print("Sample prices:")
            for price in daily_prices[:10]:
                print(f"  {price.price_date}: O={price.open_price}, H={price.high_price}, L={price.low_price}, C={price.close_price}, V={price.volume}")
            
            # Check for very small or zero values
            print("\n🔍 Checking for problematic values:")
            
            # Check for zero or negative prices
            zero_prices = daily_prices.filter(
                models.Q(open_price__lte=0) |
                models.Q(high_price__lte=0) |
                models.Q(low_price__lte=0) |
                models.Q(close_price__lte=0)
            )
            print(f"   Zero/negative prices: {zero_prices.count()}")
            
            # Check for very small prices
            small_prices = daily_prices.filter(close_price__lt=0.0001)
            print(f"   Very small prices (< 0.0001): {small_prices.count()}")
            
            # Check for zero volumes
            zero_volumes = daily_prices.filter(volume__lte=0)
            print(f"   Zero volumes: {zero_volumes.count()}")
            
            # Check for NaN or infinite values
            print("\n🔍 Checking for NaN/Inf values:")
            for price in daily_prices[:20]:  # Check first 20 prices
                if (np.isnan(price.open_price) or np.isinf(price.open_price) or
                    np.isnan(price.high_price) or np.isinf(price.high_price) or
                    np.isnan(price.low_price) or np.isinf(price.low_price) or
                    np.isnan(price.close_price) or np.isinf(price.close_price) or
                    np.isnan(price.volume) or np.isinf(price.volume)):
                    print(f"   NaN/Inf found in {price.price_date}: O={price.open_price}, H={price.high_price}, L={price.low_price}, C={price.close_price}, V={price.volume}")
        
        # Test the strategy logic
        print("\n🧪 Testing strategy logic:")
        
        # Create a test backtest
        from strategies.models import Strategy
        strategy = Strategy.objects.get(slug='mean-reverting')
        
        backtest = BackTestingStrategy.objects.create(
            strategy=strategy,
            parameters=strategy.parameters,
            exchange=symbol.exchange
        )
        
        print(f"   Created test backtest: {backtest.id}")
        
        # Test the strategy with a small dataset
        if daily_prices.count() > 50:
            test_prices = daily_prices[:50]  # Use first 50 prices for testing
            
            # Convert to DataFrame format
            import pandas as pd
            df_data = []
            for price in test_prices:
                df_data.append({
                    'Date': price.price_date,
                    'Open': price.open_price,
                    'High': price.high_price,
                    'Low': price.low_price,
                    'Close': price.close_price,
                    'Volume': price.volume
                })
            
            df = pd.DataFrame(df_data)
            print(f"   Created test DataFrame with {len(df)} rows")
            print(f"   Price range: {df['Close'].min()} to {df['Close'].max()}")
            print(f"   Volume range: {df['Volume'].min()} to {df['Volume'].max()}")
            
            # Test strategy execution
            strategy_logic = MeanRevertingStrategy(strategy.parameters)
            print("   Testing strategy execution...")
            
            try:
                # Test the execute method
                result = strategy_logic.execute(df, buy=False, last_action="")
                print(f"   Strategy execute result: {result}")
                
                # Test the backtest method
                result = strategy_logic.backtest(backtest, 'PEPE-USDC', date(2023, 1, 1), date(2023, 12, 31))
                print(f"   Strategy backtest result: {result}")
                
            except Exception as e:
                print(f"   ❌ Error in strategy execution: {e}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
        
        # Clean up test backtest
        backtest.delete()
        
    except Symbols.DoesNotExist:
        print("❌ Symbol PEPE-USDC not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

def debug_strategy_parameters():
    """Debug the strategy parameters that might cause underflow"""
    print("\n🔍 Debugging strategy parameters:")
    
    from strategies.models import Strategy
    strategy = Strategy.objects.get(slug='mean-reverting')
    
    print(f"Strategy: {strategy.name}")
    print(f"Parameters: {strategy.parameters}")
    
    # Check for problematic parameter values
    if strategy.parameters:
        for key, value in strategy.parameters.items():
            print(f"  {key}: {value} (type: {type(value)})")
            
            # Check for very small or large values
            if isinstance(value, (int, float)):
                if value < 0.0001:
                    print(f"    ⚠️ Very small value: {value}")
                elif value > 1000000:
                    print(f"    ⚠️ Very large value: {value}")

def debug_numerical_issues():
    """Debug potential numerical computation issues"""
    print("\n🔍 Debugging numerical computation issues:")
    
    # Test numpy operations that might cause underflow
    try:
        # Test multiplication with very small numbers
        small_number = 0.0000001
        result = small_number * 0.0000001
        print(f"   Small number multiplication: {small_number} * {small_number} = {result}")
        
        # Test division by very small numbers
        result = 1.0 / small_number
        print(f"   Division by small number: 1.0 / {small_number} = {result}")
        
        # Test log of very small numbers
        result = np.log(small_number)
        print(f"   Log of small number: log({small_number}) = {result}")
        
        # Test exponential of very large negative numbers
        result = np.exp(-1000)
        print(f"   Exp of large negative: exp(-1000) = {result}")
        
    except Exception as e:
        print(f"   ❌ Numerical error: {e}")

if __name__ == '__main__':
    print("🐛 Crypto Underflow Debugger")
    print("=" * 50)
    
    debug_crypto_underflow()
    debug_strategy_parameters()
    debug_numerical_issues()
    
    print("\n💡 Suggestions to fix underflow:")
    print("1. Check for zero or very small price values")
    print("2. Check for zero volume values")
    print("3. Add data validation in strategy logic")
    print("4. Use np.clip() to limit extreme values")
    print("5. Add try-catch blocks around numerical operations")
