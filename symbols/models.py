from django.db import models
import requests
import pandas as pd
from io import StringIO
from django.utils import timezone

class Symbols(models.Model):
   
    ticker = models.CharField(max_length=32, unique=True)
    instrument = models.CharField(max_length=64)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.DateTimeField()
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.ticker

    def get_symbols_from_vendor(self):
        endpoint = 'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey=demo'
        response = requests.get(endpoint)

        if response.status_code == 200:
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)

            active_stocks = df[(df['status'] == 'Active') & (pd.isna(df['delistingDate']))]
            active_stocks = active_stocks.where(pd.notnull(active_stocks), None)

            return active_stocks

    def insert_symbols_in_db(self):
        symbols = self.get_symbols_from_vendor()
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
                # If the symbol already exists, optionally update it
                symbol.instrument = instrument
                symbol.name = name
                symbol.created_date = created_date
                symbol.save()

    class Meta:
        verbose_name = "Symbol"
        verbose_name_plural = "Symbols"
        db_table = 'symbol'
