from django.db import models
from django.utils import timezone


class Symbols(models.Model):
    ticker = models.CharField(max_length=32, unique=True)
    instrument = models.CharField(max_length=64)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=False)

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
