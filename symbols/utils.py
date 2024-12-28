from .models import Symbols, DailyPrice
import datetime
import yfinance as yf
import requests
import pandas as pd
from io import StringIO
from django.utils import timezone

def get_last_date(symbol):
    last_entry = DailyPrice.objects.filter(symbol__ticker=symbol).order_by('-price_date').first()
    if last_entry:
        return last_entry.price_date
    return None

def get_daily_price(symbol, start_date, end_date=None):
    if end_date is None:
        end_date = datetime.date.today().strftime('%Y-%m-%d')

    stock_data = yf.download(symbol, start=start_date, end=end_date)
    stock_data.reset_index(inplace=True)
    stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.strftime('%Y-%m-%d')

    if stock_data.empty:
        print(f"No data available for {symbol}.")
        return pd.DataFrame()

    return stock_data

def insert_daily_price(symbol, start_date, end_date=None):
    last_date = get_last_date(symbol)

    if last_date:
        start_date = (last_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    stock_data = get_daily_price(symbol, start_date, end_date)

    if stock_data.empty:
        print(f"No data available for {symbol}.")
        return False

    symbol_obj = Symbols.objects.get(ticker=symbol)

    daily_price_objects = []
    for index, row in stock_data.iterrows():
        price_date = row['Date']
        open_price = row['Open']
        high_price = row['High']
        low_price = row['Low']
        close_price = row['Close']
        adj_close_price = row['Adj Close']
        volume = row['Volume']

        daily_price = DailyPrice(
            symbol=symbol_obj,
            price_date=price_date,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            adj_close_price=adj_close_price,
            volume=volume
        )
        daily_price_objects.append(daily_price)

    DailyPrice.objects.bulk_create(daily_price_objects)

def get_symbols():
    endpoint = 'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey=demo'
    response = requests.get(endpoint)

    if response.status_code == 200:
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)

        active_stocks = df[(df['status'] == 'Active') & (pd.isna(df['delistingDate']))]
        active_stocks = active_stocks.where(pd.notnull(active_stocks), None)

        return active_stocks

def insert_symbols():
    symbols = get_symbols()
    for index, row in symbols.iterrows():
        ticker = row['symbol']

        if ticker is None:
            continue  # Skip rows with a null ticker

        instrument = row['assetType']
        name = row['name']
        created_date = timezone.now()

        # Use get_or_create with defaults
        symbol, created = Symbols.objects.get_or_create(
            ticker=ticker,
            defaults={
                'instrument': instrument,
                'name': name,
                'created_date': created_date
            }
        )

        if not created:
            symbol.save()
