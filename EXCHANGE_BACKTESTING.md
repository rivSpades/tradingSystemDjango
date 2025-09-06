# Exchange-Specific Backtesting

This document explains the exchange-specific backtesting functionality that allows you to run the same strategy on different exchanges and compare performance across exchanges.

## Overview

The backtesting system now supports running strategies on specific exchanges, allowing you to:

- **Compare strategy performance** across different exchanges
- **Filter symbols by exchange** during backtesting
- **Generate exchange-specific statistics** for detailed analysis
- **Maintain separate backtest sessions** for each exchange/strategy combination

## Key Features

### 1. Exchange-Specific Backtest Sessions
- Each backtest can be associated with a specific exchange
- Unique constraint ensures no duplicate backtests for the same strategy/broker/exchange combination
- Backtest names include exchange information for easy identification

### 2. Symbol Filtering by Exchange
- Automatically filters symbols based on the specified exchange
- Supports both exchange ID and exchange name parameters
- Works with all strategy types (mean-reverting, MA crossover, cointegration)

### 3. Exchange-Specific Statistics
- Symbol statistics include exchange information
- Strategy statistics track performance per exchange
- Easy comparison of results across different exchanges

## Database Schema Changes

### BackTestingStrategy Model
```python
class BackTestingStrategy(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    parameters = models.JSONField(null=True, blank=True)
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, null=True, blank=True)
    exchange = models.ForeignKey('symbols.Exchange', on_delete=models.CASCADE, null=True, blank=True)  # NEW

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['strategy','name', 'broker', 'exchange'], 
                name='unique_strategy_broker_exchange'
            )
        ]
```

### StrategyStatistics Model
```python
class StrategyStatistics(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    backtest = models.ForeignKey(BackTestingStrategy, on_delete=models.CASCADE)
    exchange = models.ForeignKey('symbols.Exchange', on_delete=models.CASCADE, null=True, blank=True)  # NEW
    # ... other fields
```

### SymbolStatistics Model
```python
class SymbolStatistics(models.Model):
    symbol = models.ForeignKey(Symbols, null=True, blank=True, on_delete=models.CASCADE)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    backtest = models.ForeignKey(BackTestingStrategy, on_delete=models.CASCADE)
    exchange = models.ForeignKey('symbols.Exchange', on_delete=models.CASCADE, null=True, blank=True)  # NEW
    # ... other fields
```

## Usage Examples

### 1. Basic Exchange-Specific Backtest
```python
from backtesting.backtest_logic import execute_backtest

# Run backtest for specific exchange by ID
result = execute_backtest(
    strategy_id='mean-reverting',
    start_date='2024-01-01',
    end_date='2024-01-31',
    exchange_id=1
)

# Run backtest for specific exchange by name
result = execute_backtest(
    strategy_id='ma-crossover',
    start_date='2024-01-01',
    end_date='2024-01-31',
    exchange_name='CRYPTO USDT'
)
```

### 2. Cointegration Strategy with Exchange Filtering
```python
# Run cointegration strategy on specific exchange
result = execute_backtest(
    strategy_id='cointegration',
    start_date='2024-01-01',
    end_date='2024-01-31',
    exchange_id=1
)
```

### 3. Multiple Exchanges Comparison
```python
# Run the same strategy on multiple exchanges
exchanges = Exchange.objects.all()[:3]
results = []

for exchange in exchanges:
    result = execute_backtest(
        strategy_id='mean-reverting',
        start_date='2024-01-01',
        end_date='2024-01-31',
        exchange_id=exchange.id
    )
    results.append(result)
```

## API Parameters

### execute_backtest() Function
```python
def execute_backtest(
    strategy_id,           # Strategy slug or ID
    start_date,           # Start date for backtest
    end_date=date.today(), # End date (defaults to today)
    symbol_list=None,     # Optional: specific symbols to test
    backtest=None,        # Optional: existing backtest instance
    exchange_name=None,   # Optional: exchange name
    exchange_id=None,     # Optional: exchange ID
    reverse=False,        # Optional: reverse order for cointegration
    correlated_pair_list=None  # Optional: specific correlated pairs
):
```

### Parameter Priority
1. `exchange_id` - Highest priority (exact exchange lookup)
2. `exchange_name` - Second priority (name-based lookup)
3. No exchange filter - Runs on all symbols across all exchanges

## Statistics and Analysis

### Exchange-Specific Statistics
```python
from backtesting.models import BackTestingStrategy, SymbolStatistics, StrategyStatistics

# Get backtest for specific exchange
backtest = BackTestingStrategy.objects.get(
    strategy__slug='mean-reverting',
    exchange__name='CRYPTO USDT'
)

# Get symbol statistics for this exchange
symbol_stats = SymbolStatistics.objects.filter(
    backtest=backtest,
    exchange=backtest.exchange
)

# Get strategy statistics for this exchange
strategy_stats = StrategyStatistics.objects.filter(
    backtest=backtest,
    exchange=backtest.exchange
)
```

### Cross-Exchange Comparison
```python
# Compare performance across exchanges
exchanges = Exchange.objects.all()
comparison_data = []

for exchange in exchanges:
    backtests = BackTestingStrategy.objects.filter(
        strategy__slug='mean-reverting',
        exchange=exchange
    )
    
    for backtest in backtests:
        symbol_stats = SymbolStatistics.objects.filter(backtest=backtest)
        total_trades = symbol_stats.aggregate(total=Sum('total_trades'))['total'] or 0
        avg_win_rate = symbol_stats.aggregate(avg=Avg('win_rate'))['avg'] or 0
        total_pnl = symbol_stats.aggregate(total=Sum('profit_loss'))['total'] or 0
        
        comparison_data.append({
            'exchange': exchange.name,
            'backtest_id': backtest.id,
            'total_trades': total_trades,
            'avg_win_rate': avg_win_rate,
            'total_pnl': total_pnl
        })
```

## Migration Guide

### For Existing Projects
1. **Run migrations** to add exchange fields:
   ```bash
   python manage.py makemigrations backtesting
   python manage.py migrate backtesting
   ```

2. **Update existing backtests** (optional):
   ```python
   # Set exchange for existing backtests based on symbols
   from backtesting.models import BackTestingStrategy
   from symbols.models import Symbols
    
   for backtest in BackTestingStrategy.objects.filter(exchange__isnull=True):
       # Find the most common exchange for symbols in this backtest
       symbols = Symbols.objects.filter(
           tradehistory__backtest=backtest
       ).distinct()
       
       if symbols.exists():
           most_common_exchange = symbols.values('exchange').annotate(
               count=Count('exchange')
           ).order_by('-count').first()['exchange']
           
           backtest.exchange_id = most_common_exchange
           backtest.save()
   ```

## Best Practices

### 1. Exchange Selection
- Use `exchange_id` for precise exchange selection
- Use `exchange_name` for human-readable exchange filtering
- Consider exchange characteristics when selecting symbols

### 2. Performance Analysis
- Compare strategy performance across different exchanges
- Consider exchange-specific factors (liquidity, volatility, trading hours)
- Analyze symbol availability per exchange

### 3. Data Management
- Keep exchange information consistent across related models
- Use meaningful backtest names that include exchange information
- Archive old backtests to maintain performance

## Troubleshooting

### Common Issues

1. **No symbols found for exchange**
   - Verify exchange exists in database
   - Check if symbols are properly associated with exchange
   - Ensure exchange name matches exactly (case-sensitive)

2. **Duplicate backtest constraint error**
   - Check unique constraint: strategy + name + broker + exchange
   - Use different names for backtests on same strategy/exchange
   - Consider using timestamps in backtest names

3. **Statistics not showing exchange information**
   - Ensure backtest has exchange field populated
   - Check if statistics calculation includes exchange field
   - Verify migration was applied correctly

### Debug Commands
```python
# Check available exchanges
from symbols.models import Exchange
exchanges = Exchange.objects.all()
for e in exchanges:
    print(f"{e.id}: {e.name} - {e.symbols_set.count()} symbols")

# Check backtest exchange association
from backtesting.models import BackTestingStrategy
backtests = BackTestingStrategy.objects.all()
for b in backtests:
    print(f"Backtest {b.id}: {b.strategy.name} on {b.exchange.name if b.exchange else 'No exchange'}")

# Verify statistics include exchange
from backtesting.models import SymbolStatistics
stats = SymbolStatistics.objects.filter(exchange__isnull=False)
print(f"Statistics with exchange info: {stats.count()}")
```

## Future Enhancements

### Planned Features
1. **Exchange Performance Dashboard** - Visual comparison of strategy performance across exchanges
2. **Exchange-Specific Parameters** - Different strategy parameters per exchange
3. **Multi-Exchange Backtests** - Run single backtest across multiple exchanges simultaneously
4. **Exchange Risk Metrics** - Exchange-specific risk analysis and metrics

### Integration Opportunities
1. **Real-time Exchange Data** - Live exchange performance monitoring
2. **Exchange API Integration** - Direct integration with exchange APIs for live trading
3. **Exchange-Specific Alerts** - Notifications based on exchange performance
4. **Portfolio Management** - Multi-exchange portfolio optimization

---

**Note**: This functionality requires the latest database migrations to be applied. Make sure to run `python manage.py migrate` after updating your code.
