# Broker-Specific Daily Price Updates

This document explains how to use the broker-specific daily price update functionality in the trading system.

## Overview

The system now supports updating daily prices for specific brokers (Binance, Alpaca) using their respective APIs. The `DailyPriceManager` class has been enhanced to:

- **Automatically detect the broker** for each symbol
- **Use the appropriate API** (Binance API for Binance symbols, Alpaca API for Alpaca symbols)
- **Filter updates by broker** to update only specific brokers
- **Provide detailed logging** and error handling

## Key Features

### 1. Automatic Broker Detection
- Each symbol is linked to a broker in the database
- The system automatically uses the correct API based on the symbol's broker
- No manual configuration needed for individual symbols

### 2. Broker-Specific Updates
- Update all symbols from all brokers
- Update only symbols from a specific broker
- Individual symbol updates

### 3. Comprehensive Logging
- Detailed progress information
- Success/error counts
- Individual symbol processing status

## Usage Examples

### 1. Update All Brokers

```python
from symbols.utils import DailyPriceManager

# Update daily prices for all symbols from all brokers
result = DailyPriceManager.update_daily_prices_for_symbols()

print(f"Success: {result['success_count']}")
print(f"Errors: {result['error_count']}")
print(f"Total: {result['total_processed']}")
```

### 2. Update Specific Broker

```python
# Update only Binance symbols
result = DailyPriceManager.update_daily_prices_for_symbols(broker_name='Binance')

# Update only Alpaca symbols
result = DailyPriceManager.update_daily_prices_for_symbols(broker_name='Alpaca')
```

### 3. Convenience Method

```python
# Convenience method for specific broker
result = DailyPriceManager.update_daily_prices_for_broker('Binance')
```

### 4. Individual Symbol Update

```python
from symbols.models import Symbols

# Get a specific symbol
symbol = Symbols.objects.get(ticker='BTC-USD')

# Update daily prices for this symbol
success = DailyPriceManager.insert_daily_price(symbol, '2024-01-01')
```

## API Integration

### Binance API
- **Endpoint**: `/api/v3/klines`
- **Authentication**: API key + HMAC-SHA256 signature
- **Symbol Format**: Converts `BTC-USD` → `BTCUSDT`
- **Data Format**: OHLCV with millisecond timestamps

### Alpaca API
- **Endpoint**: `/v2/stocks/{symbol}/bars`
- **Authentication**: API key + secret key
- **Symbol Format**: Uses original ticker format
- **Data Format**: OHLCV with standard timestamps

## Database Integration

### Symbol-Broker Relationship
```python
# Each symbol is linked to a broker
symbol = Symbols.objects.get(ticker='BTC-USD')
print(f"Symbol: {symbol.ticker}")
print(f"Broker: {symbol.broker.name}")
print(f"API Key: {symbol.broker.api_key}")
```

### Daily Price Storage
```python
# Daily prices are stored with the symbol relationship
from symbols.models import DailyPrice

prices = DailyPrice.objects.filter(symbol__broker__name='Binance')
print(f"Found {prices.count()} price records for Binance symbols")
```

## Web Interface

### API Endpoints

#### Update All Brokers
```http
POST /symbols/update-daily-prices/
Content-Type: application/x-www-form-urlencoded

# No parameters needed
```

#### Update Specific Broker
```http
POST /symbols/update-daily-prices/
Content-Type: application/x-www-form-urlencoded

broker_name=Binance
```

### Response Format
```json
{
    "success": true,
    "broker_name": "Binance",
    "message": "Daily price update completed for Binance",
    "results": {
        "success_count": 10,
        "error_count": 0,
        "total_processed": 10
    }
}
```

## Error Handling

### Common Issues

1. **No Broker Assigned**
   ```
   Symbol BTC-USD has no broker assigned
   ```

2. **API Authentication Error**
   ```
   Error fetching data from Binance API: Invalid API key
   ```

3. **Symbol Not Found**
   ```
   No data available for INVALID-SYMBOL from Binance broker
   ```

### Error Recovery

The system continues processing other symbols even if one fails:

```python
result = DailyPriceManager.update_daily_prices_for_symbols('Binance')
if result['error_count'] > 0:
    print(f"Some symbols failed to update: {result['error_count']} errors")
    print(f"But {result['success_count']} symbols were updated successfully")
```

## Testing

### Run Test Script
```bash
python test_broker_daily_prices.py
```

The test script will:
1. Show symbol statistics
2. Test individual symbol updates
3. Test broker-specific updates
4. Test convenience methods

### Manual Testing
```python
# Test in Django shell
python manage.py shell

from symbols.utils import DailyPriceManager
from symbols.models import Symbols, Broker

# Check available brokers
brokers = Broker.objects.all()
print([b.name for b in brokers])

# Test Binance update
result = DailyPriceManager.update_daily_prices_for_symbols('Binance')
print(result)
```

## Configuration

### Broker Setup
1. **Create Broker Entry** in Django admin:
   ```python
   Broker.objects.create(
       name="Binance",
       api_key="your_binance_api_key",
       secret_key="your_binance_secret_key"
   )
   ```

2. **Assign Symbols to Broker**:
   ```python
   symbol = Symbols.objects.get(ticker='BTC-USD')
   symbol.broker = binance_broker
   symbol.save()
   ```

### API Credentials
- Store API keys securely in the database
- Use environment variables for production
- Test with paper trading accounts first

## Performance Considerations

### Batch Processing
- The system processes symbols one by one
- Each symbol update is independent
- Failed symbols don't affect others

### Rate Limiting
- **Binance**: 1200 requests/minute for public endpoints
- **Alpaca**: Varies by plan, typically 200 requests/minute
- The system respects API rate limits

### Data Volume
- Historical data can be large
- Consider date ranges for initial loads
- Incremental updates are efficient

## Monitoring

### Log Output
```
🔄 Updating daily prices for 5 symbols from Binance broker
📊 Processing BTC-USD (Binance)
   Last date: 2024-01-15, starting from: 2024-01-16
✅ Inserted 3 new price records for BTC-USD
📊 Processing ETH-USD (Binance)
   No existing data found, starting from 2013-01-01
✅ Inserted 100 new price records for ETH-USD
```

### Success Metrics
- **Success Count**: Number of symbols updated successfully
- **Error Count**: Number of symbols that failed
- **Total Processed**: Total number of symbols attempted

## Future Enhancements

1. **Parallel Processing**: Update multiple symbols simultaneously
2. **WebSocket Support**: Real-time price streaming
3. **Scheduled Updates**: Automatic daily updates
4. **Data Validation**: Verify price data quality
5. **Backup/Restore**: Data backup and recovery features
