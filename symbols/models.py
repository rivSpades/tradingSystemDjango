from django.db import models
from django.utils import timezone


class Exchange(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Exchange"
        verbose_name_plural = "Exchanges"
        db_table = 'exchange'


class Symbols(models.Model):
    ticker = models.CharField(max_length=32, unique=True)
    exchange = models.ForeignKey(Exchange, on_delete=models.SET_NULL, null=True, blank=True)  # Updated field
    instrument = models.CharField(max_length=64)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=False)
    slot_free = models.BooleanField(default=True)
    def __str__(self):
        return self.ticker

    class Meta:
        verbose_name = "Symbol"
        verbose_name_plural = "Symbols"
        db_table = 'symbol'


class DailyPrice(models.Model):
    symbol = models.ForeignKey(Symbols, on_delete=models.CASCADE)
    price_date = models.DateField()
    open_price = models.FloatField()
    high_price = models.FloatField()
    low_price = models.FloatField()
    close_price = models.FloatField()
    adj_close_price = models.FloatField()
    volume = models.BigIntegerField()
    created_date = models.DateTimeField(default=timezone.now)
    last_updated_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('symbol', 'price_date')
        db_table = 'daily_price'

    def __str__(self):
        return self.symbol.ticker+' '+str(self.price_date)