import datetime
import yfinance as yf
import requests
import pandas as pd
from io import StringIO
from django.utils import timezone
from .models import Symbols, DailyPrice,Exchange

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
        """Fetch daily stock price data using Yahoo Finance."""
        if end_date is None:
            end_date = datetime.date.today().strftime('%Y-%m-%d')
        print(symbol)
        stock_data = yf.download(symbol, start=start_date, end=end_date, auto_adjust=False)
        #print(stock_data)
        stock_data.reset_index(inplace=True)
        stock_data.columns = [col[0] if isinstance(col, tuple) else col for col in stock_data.columns]
        stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.strftime('%Y-%m-%d')

        if stock_data.empty:
            print(f"No data available for {symbol}.")
            return pd.DataFrame()

        return stock_data

    @staticmethod
    def insert_daily_price(symbol, start_date, end_date=None):
        """Insert new daily stock prices into the database."""
        last_date = DailyPriceManager.get_last_date(symbol)  # Fixed method call

        if last_date:
            start_date = (last_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        stock_data = DailyPriceManager.get_daily_price(symbol, start_date, end_date)
        if stock_data.empty:
            print(f"No data available for {symbol}.")
            return False

        symbol_obj = Symbols.objects.get(ticker=symbol)

        daily_price_objects = []
        for _, row in stock_data.iterrows():
            price_date = row['Date']
            # Check if the price data for the symbol and date already exists
            if DailyPrice.objects.filter(symbol=symbol_obj, price_date=price_date).exists():
                print(f"Price data for {symbol} on {price_date} already exists. Skipping.")
                continue  # Skip this entry if it already exists
            
            # If not, create a new DailyPrice object
            daily_price_objects.append(
                DailyPrice(
                    symbol=symbol_obj,
                    price_date=price_date,
                    open_price=row['Open'],
                    high_price=row['High'],
                    low_price=row['Low'],
                    close_price=row['Close'],
                    adj_close_price=row['Adj Close'],
                    volume=row['Volume']
                )
            )

        # Insert the valid new price data
        if daily_price_objects:
            DailyPrice.objects.bulk_create(daily_price_objects)
        return True


    @staticmethod
    def update_daily_prices_for_symbols():
        """Updates daily prices for all symbols."""
        symbols = Symbols.objects.all()

        for symbol in symbols:
            # Get the last available date
            last_date = DailyPriceManager.get_last_date(symbol.ticker)
            
            if last_date:
                start_date = last_date + datetime.timedelta(days=1)  # Start from the next day
            else:
                start_date = "2013-01-01"
            #print(start_date)
            # Call the insert_daily_price method to add the new data
            DailyPriceManager.insert_daily_price(symbol.ticker, start_date)

    @staticmethod
    def get_last_date(symbol):
        """Fetch the last available date for a given symbol in the DailyPrice table."""
        last_entry = DailyPrice.objects.filter(symbol__ticker=symbol).order_by('-price_date').first()
        return last_entry.price_date if last_entry else False

