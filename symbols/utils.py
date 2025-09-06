import datetime
import yfinance as yf
import requests
import pandas as pd
from io import StringIO
from django.utils import timezone
from .models import Symbols, DailyPrice,Exchange
from execution.utils import ExecutionUtils
class SymbolsManager:


    @staticmethod
    def get_symbols():
        """Fetch the list of active stock symbols from Alpha Vantage."""
        endpoint = 'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey=demo'
        response = requests.get(endpoint)

        if response.status_code == 200:
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)

            active_stocks = df[(df['status'] == 'Active') & (pd.isna(df['delistingDate']))]
            active_stocks = active_stocks.where(pd.notnull(active_stocks), None)

            return active_stocks

        return pd.DataFrame()

    @staticmethod
    def get_cryptos():
        """Fetch the list of active stock symbols from Alpha Vantage."""
        endpoint = 'https://www.alphavantage.co/digital_currency_list'
        response = requests.get(endpoint)

        if response.status_code == 200:
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)

        

            return df

        return pd.DataFrame()    

    @classmethod
    def insert_symbols(cls):
        """Insert new symbols into the database from Alpha Vantage and ensure exchange is correctly set."""
        symbols = cls.get_symbols()

        for _, row in symbols.iterrows():
            ticker = row['symbol']

            if not ticker:
                continue  # Skip rows with a null ticker

            instrument = row['assetType']
            name = row['name']
            exchange_name = row['exchange']
            created_date = timezone.now()

            # Ensure the exchange exists, or create it if it doesn't
            exchange_obj, _ = Exchange.objects.get_or_create(name=exchange_name)

            # Fetch or create the symbol
            symbol_obj, created = Symbols.objects.get_or_create(
                ticker=ticker,
                defaults={
                    'instrument': instrument,
                    'name': name,
                    'exchange': exchange_obj,  # Assign the ForeignKey object
                    'created_date': created_date
                }
            )

            # If the symbol already exists, update its exchange if it's empty or incorrect
            if not created and symbol_obj.exchange != exchange_obj:
                symbol_obj.exchange = exchange_obj
                symbol_obj.save()  # Save the updated symbol object

    @classmethod
    def insert_cryptos(cls):
        """Insert new symbols into the database from Alpha Vantage and ensure exchange is correctly set."""
        symbols = cls.get_cryptos()

        for _, row in symbols.iterrows():
            ticker = row['currency code']+'-USD'

            if not ticker:
                continue  # Skip rows with a null ticker

            instrument = "crypto"
            name = row['currency name']
            exchange_name = "CRYPTO"
            created_date = timezone.now()

            # Ensure the exchange exists, or create it if it doesn't
            exchange_obj, _ = Exchange.objects.get_or_create(name=exchange_name)

            # Fetch or create the symbol
            symbol_obj, created = Symbols.objects.get_or_create(
                ticker=ticker,
                defaults={
                    'instrument': instrument,
                    'name': name,
                    'exchange': exchange_obj,  # Assign the ForeignKey object
                    'created_date': created_date
                }
            )

            # If the symbol already exists, update its exchange if it's empty or incorrect
            if not created and symbol_obj.exchange != exchange_obj:
                symbol_obj.exchange = exchange_obj
                symbol_obj.save()  # Save the updated symbol object                


class DailyPriceManager:
    @staticmethod
    def get_daily_price(symbol, start_date, end_date=None):
        """Fetch daily stock price data using the appropriate broker API."""
        if end_date is None:
            end_date = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"Fetching data for {symbol.ticker} from {symbol.broker.name if symbol.broker else 'Unknown'} broker")
        
        # Use ExecutionUtils to get data from the appropriate broker
        stock_data = ExecutionUtils.get_daily_price(symbol, start_date=start_date, end_date=end_date)
        
        # Handle column names (some APIs return tuples)
        if not stock_data.empty:
            stock_data.columns = [col[0] if isinstance(col, tuple) else col for col in stock_data.columns]
            
            # Ensure Date column is in the correct format
            if 'Date' in stock_data.columns:
                stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.strftime('%Y-%m-%d')

        if stock_data.empty or stock_data is None:
            print(f"No data available for {symbol.ticker} from {symbol.broker.name if symbol.broker else 'Unknown'} broker.")
            return pd.DataFrame()
        
        return stock_data

    @staticmethod
    def insert_daily_price(symbol, start_date, end_date=None):
        """Insert new daily stock prices into the database using the appropriate broker API."""
        print(f"Inserting daily prices for {symbol.ticker} from {symbol.broker.name if symbol.broker else 'Unknown'} broker")
        
        # Get the last available date for this symbol
        last_date = DailyPriceManager.get_last_date(symbol)

        if last_date:
            start_date = (last_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"Starting from {start_date} (last date was {last_date})")
        else:
            print(f"No existing data found, starting from {start_date}")

        # Get price data from the appropriate broker
        stock_data = DailyPriceManager.get_daily_price(symbol, start_date, end_date)
        
        if stock_data.empty or stock_data is None:
            print(f"No data available for {symbol.ticker}.")
            return False

        # Create DailyPrice objects for new data
        daily_price_objects = []
        inserted_count = 0
        skipped_count = 0
        
        for _, row in stock_data.iterrows():
            price_date = row['Date']
            
            # Check if the price data for the symbol and date already exists
            if DailyPrice.objects.filter(symbol=symbol, price_date=price_date).exists():
                print(f"Price data for {symbol.ticker} on {price_date} already exists. Skipping.")
                skipped_count += 1
                continue  # Skip this entry if it already exists
            
            # Create a new DailyPrice object
            daily_price_objects.append(
                DailyPrice(
                    symbol=symbol,
                    price_date=price_date,
                    open_price=row['Open'],
                    high_price=row['High'],
                    low_price=row['Low'],
                    close_price=row['Close'],
                    adj_close_price=row.get('Adj Close', row['Close']),  # Use Adj Close if available, otherwise use Close
                    volume=row['Volume']
                )
            )
            inserted_count += 1

        # Insert the valid new price data
        if daily_price_objects:
            DailyPrice.objects.bulk_create(daily_price_objects)
            print(f"✅ Inserted {inserted_count} new price records for {symbol.ticker}")
        else:
            print(f"ℹ️ No new price records to insert for {symbol.ticker}")
            
        if skipped_count > 0:
            print(f"⏭️ Skipped {skipped_count} existing records for {symbol.ticker}")
            
        return True

    @staticmethod
    def update_daily_prices_for_symbols(broker_name=None, symbols_list=None):
        """Updates daily prices for symbols, optionally filtered by broker or specific symbols list."""
        if symbols_list is not None:
            # Use the provided symbols list
            symbols = symbols_list
            print(f"🔄 Updating daily prices for {symbols.count()} symbols from provided list")
        elif broker_name:
            # Filter symbols by broker and active status
            symbols = Symbols.objects.filter(broker__name=broker_name, active=True)
            print(f"🔄 Updating daily prices for {symbols.count()} active symbols from {broker_name} broker")
        else:
            # Get all active symbols
            symbols = Symbols.objects.filter(active=True)
            print(f"🔄 Updating daily prices for {symbols.count()} active symbols from all brokers")

        success_count = 0
        error_count = 0
        
        for symbol in symbols:
            try:
                print(f"\n📊 Processing {symbol.ticker} ({symbol.broker.name if symbol.broker else 'No broker'})")
                
                # Get the last available date
                last_date = DailyPriceManager.get_last_date(symbol)
                
                if last_date:
                    start_date = last_date + datetime.timedelta(days=1)  # Start from the next day
                    print(f"   Last date: {last_date}, starting from: {start_date}")
                else:
                    start_date = "2013-01-01"
                    print(f"   No existing data, starting from: {start_date}")
                
                # Call the insert_daily_price method to add the new data
                success = DailyPriceManager.insert_daily_price(symbol, start_date)
                
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ Error updating {symbol.ticker}: {str(e)}")
                error_count += 1
                continue
        
        print(f"\n🎉 Update completed!")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total processed: {success_count + error_count}")
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'total_processed': success_count + error_count
        }

    @staticmethod
    def update_daily_prices_for_broker(broker_name):
        """Convenience method to update daily prices for a specific broker."""
        return DailyPriceManager.update_daily_prices_for_symbols(broker_name=broker_name)

    @staticmethod
    def get_last_date(symbol):
        """Fetch the last available date for a given symbol in the DailyPrice table."""
        last_entry = DailyPrice.objects.filter(symbol=symbol).order_by('-price_date').first()
        return last_entry.price_date if last_entry else False

