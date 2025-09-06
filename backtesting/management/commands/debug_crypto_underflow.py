from django.core.management.base import BaseCommand
import numpy as np
from symbols.models import Symbols, DailyPrice
from strategies.strategy_logic import MeanRevertingStrategy
from backtesting.models import BackTestingStrategy
from datetime import date
from django.db import models

class Command(BaseCommand):
    help = 'Debug crypto underflow error for PEPE-USDC'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            default='PEPE-USDC',
            help='Symbol to debug (default: PEPE-USDC)'
        )

    def handle(self, *args, **options):
        symbol_ticker = options['symbol']
        self.stdout.write(f"🔍 Debugging crypto underflow error for {symbol_ticker}")
        
        try:
            # Get the symbol
            symbol = Symbols.objects.get(ticker=symbol_ticker)
            self.stdout.write(f"✅ Found symbol: {symbol.ticker}")
            self.stdout.write(f"   Exchange: {symbol.exchange}")
            self.stdout.write(f"   Broker: {symbol.broker}")
            
            # Check daily prices
            daily_prices = DailyPrice.objects.filter(symbol=symbol).order_by('price_date')
            self.stdout.write(f"📊 Daily prices found: {daily_prices.count()}")
            
            if daily_prices.exists():
                # Show sample prices
                self.stdout.write("Sample prices:")
                for price in daily_prices[:10]:
                    self.stdout.write(f"  {price.price_date}: O={price.open_price}, H={price.high_price}, L={price.low_price}, C={price.close_price}, V={price.volume}")
                
                # Check for very small or zero values
                self.stdout.write("\n🔍 Checking for problematic values:")
                
                # Check for zero or negative prices
                zero_prices = daily_prices.filter(
                    models.Q(open_price__lte=0) |
                    models.Q(high_price__lte=0) |
                    models.Q(low_price__lte=0) |
                    models.Q(close_price__lte=0)
                )
                self.stdout.write(f"   Zero/negative prices: {zero_prices.count()}")
                
                # Check for very small prices
                small_prices = daily_prices.filter(close_price__lt=0.0001)
                self.stdout.write(f"   Very small prices (< 0.0001): {small_prices.count()}")
                
                # Check for zero volumes
                zero_volumes = daily_prices.filter(volume__lte=0)
                self.stdout.write(f"   Zero volumes: {zero_volumes.count()}")
                
                # Check for NaN or infinite values
                self.stdout.write("\n🔍 Checking for NaN/Inf values:")
                for price in daily_prices[:20]:  # Check first 20 prices
                    if (np.isnan(price.open_price) or np.isinf(price.open_price) or
                        np.isnan(price.high_price) or np.isinf(price.high_price) or
                        np.isnan(price.low_price) or np.isinf(price.low_price) or
                        np.isnan(price.close_price) or np.isinf(price.close_price) or
                        np.isnan(price.volume) or np.isinf(price.volume)):
                        self.stdout.write(f"   NaN/Inf found in {price.price_date}: O={price.open_price}, H={price.high_price}, L={price.low_price}, C={price.close_price}, V={price.volume}")
            
            # Test the strategy logic
            self.stdout.write("\n🧪 Testing strategy logic:")
            
            # Create a test backtest
            from strategies.models import Strategy
            strategy = Strategy.objects.get(slug='mean-reverting')
            
            backtest = BackTestingStrategy.objects.create(
                strategy=strategy,
                parameters=strategy.parameters,
                exchange=symbol.exchange
            )
            
            self.stdout.write(f"   Created test backtest: {backtest.id}")
            
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
                self.stdout.write(f"   Created test DataFrame with {len(df)} rows")
                self.stdout.write(f"   Price range: {df['Close'].min()} to {df['Close'].max()}")
                self.stdout.write(f"   Volume range: {df['Volume'].min()} to {df['Volume'].max()}")
                
                # Test strategy execution
                strategy_logic = MeanRevertingStrategy(strategy.parameters)
                self.stdout.write("   Testing strategy execution...")
                
                try:
                    # Test the execute method
                    result = strategy_logic.execute(df, buy=False, last_action="")
                    self.stdout.write(f"   Strategy execute result: {result}")
                    
                    # Test the backtest method
                    result = strategy_logic.backtest(backtest, symbol_ticker, date(2023, 1, 1), date(2023, 12, 31))
                    self.stdout.write(f"   Strategy backtest result: {result}")
                    
                except Exception as e:
                    self.stdout.write(f"   ❌ Error in strategy execution: {e}")
                    import traceback
                    self.stdout.write(f"   Traceback: {traceback.format_exc()}")
            
            # Clean up test backtest
            backtest.delete()
            
        except Symbols.DoesNotExist:
            self.stdout.write(f"❌ Symbol {symbol_ticker} not found!")
        except Exception as e:
            self.stdout.write(f"❌ Error: {e}")
            import traceback
            self.stdout.write(f"Traceback: {traceback.format_exc()}")
        
        # Debug strategy parameters
        self.stdout.write("\n🔍 Debugging strategy parameters:")
        
        from strategies.models import Strategy
        strategy = Strategy.objects.get(slug='mean-reverting')
        
        self.stdout.write(f"Strategy: {strategy.name}")
        self.stdout.write(f"Parameters: {strategy.parameters}")
        
        # Check for problematic parameter values
        if strategy.parameters:
            for key, value in strategy.parameters.items():
                self.stdout.write(f"  {key}: {value} (type: {type(value)})")
                
                # Check for very small or large values
                if isinstance(value, (int, float)):
                    if value < 0.0001:
                        self.stdout.write(f"    ⚠️ Very small value: {value}")
                    elif value > 1000000:
                        self.stdout.write(f"    ⚠️ Very large value: {value}")
        
        # Debug numerical issues
        self.stdout.write("\n🔍 Debugging numerical computation issues:")
        
        # Test numpy operations that might cause underflow
        try:
            # Test multiplication with very small numbers
            small_number = 0.0000001
            result = small_number * 0.0000001
            self.stdout.write(f"   Small number multiplication: {small_number} * {small_number} = {result}")
            
            # Test division by very small numbers
            result = 1.0 / small_number
            self.stdout.write(f"   Division by small number: 1.0 / {small_number} = {result}")
            
            # Test log of very small numbers
            result = np.log(small_number)
            self.stdout.write(f"   Log of small number: log({small_number}) = {result}")
            
            # Test exponential of very large negative numbers
            result = np.exp(-1000)
            self.stdout.write(f"   Exp of large negative: exp(-1000) = {result}")
            
        except Exception as e:
            self.stdout.write(f"   ❌ Numerical error: {e}")
        
        self.stdout.write("\n💡 Suggestions to fix underflow:")
        self.stdout.write("1. Check for zero or very small price values")
        self.stdout.write("2. Check for zero volume values")
        self.stdout.write("3. Add data validation in strategy logic")
        self.stdout.write("4. Use np.clip() to limit extreme values")
        self.stdout.write("5. Add try-catch blocks around numerical operations")
