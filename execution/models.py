from django.db import models
from symbols.models import Symbols
from strategies.models import CorrelatedPair
from django.utils import timezone

class TradeHistory(models.Model):
    """ Stores individual trade executions. """
    symbol = models.ForeignKey(Symbols, on_delete=models.CASCADE)  
    correlated_pair = models.ForeignKey(CorrelatedPair, null=True, blank=True, on_delete=models.SET_NULL)  # NEW: Link to correlated pair
    entry_date = models.DateField()  
    exit_date = models.DateField(null=True, blank=True)  
    action = models.CharField(max_length=5, choices=[("LONG", "LONG"), ("SHORT", "SHORT"), ("EXIT", "EXIT")])  
    entry_price = models.FloatField()  
    exit_price = models.FloatField(null=True, blank=True)  
    quantity =models.FloatField()  
    profit_loss = models.FloatField(null=True, blank=True)  
    created_at = models.DateTimeField(default=timezone.now)
   

    def __str__(self):
        return f"{self.symbol.ticker} {self.action} {self.quantity} @ {self.entry_price}"
