from django.db import models



class Symbols(models.Model):
    exchange_id = models.IntegerField(null=True, blank=True, db_index=True)
    ticker = models.CharField(max_length=32, unique=True)
    instrument = models.CharField(max_length=64)
    name = models.CharField(max_length=255, null=True, blank=True)
    sector = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=32, null=True, blank=True)
    created_date = models.DateTimeField()
    last_updated_date = models.DateTimeField()

    def __str__(self):
        return self.ticker

    class Meta:
        verbose_name = "Symbol"  # Singular name for the model
        verbose_name_plural = "Symbols"  # Plural name for the model
        db_table = 'symbol'  # Ensure the database table name is correct