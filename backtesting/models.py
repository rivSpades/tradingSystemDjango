from django.db import models
from strategies.models import Strategy
from symbols.models import Symbols
from django.utils import timezone

class BackTestingStrategy(models.Model):
    """ Represents a backtest session for a strategy. """
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)  
    created_at = models.DateTimeField(default=timezone.now)
    parameters = models.JSONField()  # Strategy parameters
    def __str__(self):
        return f"{self.strategy.name} Backtest"

class TradeHistory(models.Model):
    """ Stores individual trade executions. """
    symbol = models.ForeignKey(Symbols, on_delete=models.CASCADE)  
    backtest = models.ForeignKey(BackTestingStrategy, on_delete=models.CASCADE, related_name="trades")
    entry_date = models.DateField()  
    exit_date = models.DateField(null=True, blank=True)  
    action = models.CharField(max_length=5, choices=[("LONG", "LONG"), ("SHORT", "SHORT"), ("EXIT", "EXIT")])  
    entry_price = models.FloatField()  
    exit_price = models.FloatField(null=True, blank=True)  
    quantity = models.IntegerField()  
    profit_loss = models.FloatField(null=True, blank=True)  

    def __str__(self):
        return f"{self.symbol.ticker} {self.action} {self.quantity} @ {self.entry_price}"

class StrategyStatistics(models.Model):
    """ Aggregated statistics for a strategy across all symbols. """
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="strategy_statistics")
    backtest = models.ForeignKey(BackTestingStrategy, on_delete=models.CASCADE, related_name="strategy_stats")
    total_trades = models.IntegerField()  
    win_rate = models.FloatField()  
    total_profit_loss = models.FloatField()  
    sharpe_ratio = models.FloatField(null=True, blank=True)  
    max_drawdown = models.FloatField(null=True, blank=True)  
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.strategy.name} Statistics"

class SymbolStatistics(models.Model):
    """ Performance of a specific symbol within a strategy backtest. """
    symbol = models.ForeignKey(Symbols, on_delete=models.CASCADE)  
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)  
    backtest = models.ForeignKey(BackTestingStrategy, on_delete=models.CASCADE, related_name="symbol_stats")
    total_trades = models.IntegerField()  
    win_rate = models.FloatField()  
    profit_loss = models.FloatField()  
    max_drawdown = models.FloatField(null=True, blank=True)  
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.symbol.ticker} ({self.strategy.name}) Stats"
