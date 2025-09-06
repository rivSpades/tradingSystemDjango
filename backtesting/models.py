from django.db import models
from strategies.models import Strategy,CorrelatedPair
from symbols.models import Symbols,Broker
from django.utils import timezone

class BackTestingStrategy(models.Model):
    """Represents a backtest session for a strategy."""
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    parameters = models.JSONField(null=True, blank=True)  # Strategy parameters
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, null=True, blank=True, related_name="broker")
    exchange = models.ForeignKey('symbols.Exchange', on_delete=models.CASCADE, null=True, blank=True, related_name="exchange_backtests")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['strategy','name', 'broker', 'exchange'], name='unique_strategy_broker_exchange')
        ]

    def __str__(self):
        exchange_name = f" ({self.exchange.name})" if self.exchange else ""
        broker_name = f" [{self.broker.name}]" if self.broker else ""
        return f"{self.strategy.name} Backtest{exchange_name}{broker_name}"

class TradeHistory(models.Model):
    """ Stores individual trade executions. """
    symbol = models.ForeignKey(Symbols, on_delete=models.CASCADE)  
    correlated_pair = models.ForeignKey(CorrelatedPair, null=True, blank=True, on_delete=models.SET_NULL)  # NEW: Link to correlated pair
    backtest = models.ForeignKey(BackTestingStrategy, on_delete=models.CASCADE, related_name="trades")
    entry_date = models.DateField()  
    exit_date = models.DateField(null=True, blank=True)  
    action = models.CharField(max_length=5, choices=[("LONG", "LONG"), ("SHORT", "SHORT"), ("EXIT", "EXIT")])  
    entry_price = models.FloatField()  
    exit_price = models.FloatField(null=True, blank=True)  
    quantity =models.FloatField()  
    profit_loss = models.FloatField(null=True, blank=True)  
    created_at = models.DateTimeField(default=timezone.now)
    max_drawdown = models.FloatField(null=True, blank=True) 

    def __str__(self):
        return f"{self.symbol.ticker} {self.action} {self.quantity} @ {self.entry_price}"

class StrategyStatistics(models.Model):
    """ Aggregated statistics for a strategy across all symbols. """
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="strategy_statistics")
    backtest = models.ForeignKey(BackTestingStrategy, on_delete=models.CASCADE, related_name="strategy_stats")
    exchange = models.ForeignKey('symbols.Exchange', on_delete=models.CASCADE, null=True, blank=True, related_name="exchange_strategy_stats")
    
    action = models.CharField(max_length=20, choices=[("LONG", "LONG"), ("SHORT", "SHORT"),("PAIR_TRADING","PAIR_TRADING")], null=True, blank=True)  
    total_trades = models.IntegerField(null=True, blank=True)  
    win_rate = models.FloatField(null=True, blank=True)  
    total_roi = models.FloatField(null=True, blank=True) 
    total_profit_loss = models.FloatField(null=True, blank=True)  
    average_holding_period = models.FloatField(null=True, blank=True)  
    average_max_drawdown = models.FloatField(null=True, blank=True)  
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        exchange_name = f" ({self.exchange.name})" if self.exchange else ""
        return f"{self.strategy.name} Statistics{exchange_name}"

class SymbolStatistics(models.Model):
    """ Performance of a specific symbol within a strategy backtest. """
    symbol = models.ForeignKey(Symbols, null=True, blank=True, on_delete=models.CASCADE)  
    correlated_pair = models.ForeignKey(CorrelatedPair, null=True, blank=True, on_delete=models.SET_NULL)  # NEW: Link to correlated pair
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)  
    backtest = models.ForeignKey(BackTestingStrategy, on_delete=models.CASCADE, related_name="symbol_stats")
    exchange = models.ForeignKey('symbols.Exchange', on_delete=models.CASCADE, null=True, blank=True, related_name="exchange_symbol_stats")
    action = models.CharField(max_length=20, choices=[("LONG", "LONG"), ("SHORT", "SHORT"),("PAIR_TRADING","PAIR_TRADING")], null=True, blank=True)  
    total_trades = models.IntegerField(null=True, blank=True)  
    win_rate = models.FloatField(null=True, blank=True)  
    profit_loss = models.FloatField(null=True, blank=True)  
    average_holding_period = models.FloatField(null=True, blank=True)  
    total_roi = models.FloatField(null=True, blank=True)  
    average_max_drawdown = models.FloatField(null=True, blank=True)  
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        exchange_name = f" ({self.exchange.name})" if self.exchange else ""
        return f"({self.strategy.name}) Stats{exchange_name}"
