# Binance API Integration

This document describes the Binance API integration implemented in the trading system.

## Overview

The trading system now supports Binance as a broker alongside Alpaca. The integration allows for:

- **Daily price data retrieval** from Binance API
- **Real-time market data** (latest minute bars)
- **Order creation** (market and limit orders)
- **Position management** (closing positions)
- **Account information** retrieval
- **Symbol management** (enabling assets)

## Implementation Details

### Broker Configuration

The system uses the existing `Broker` model to store Binance API credentials:

```python
# Example broker entry in Django admin
Broker.objects.create(
    name="Binance",
    api_key="your_binance_api_key",
    secret_key="your_binance_secret_key",
    endpoint="https://api.binance.com"
)
```

### Symbol Format Conversion

The system automatically converts symbol formats between the internal format and Binance format:

| Internal Format | Binance Format | Example |
|----------------|----------------|---------|
| `BTC-USD` | `BTCUSDT` | Bitcoin |
| `ETH-USD` | `ETHUSDT` | Ethereum |
| `BTC-USDT` | `BTCUSDT` | Bitcoin (USDT) |
| `ADA-USDT` | `ADAUSDT` | Cardano |
| `LINK-BTC` | `LINKBTC` | Chainlink/Bitcoin |
| `ETH-BTC` | `ETHBTC` | Ethereum/Bitcoin |
| `BTC` | `BTCUSDT` | Bitcoin (no quote currency) |
| `LINK` | `LINKUSDT` | Chainlink (no quote currency) |

### API Endpoints Used

#### 1. Daily Price Data (`/api/v3/klines`)
- **Purpose**: Retrieve historical daily OHLCV data
- **Parameters**: 
  - `symbol`: Trading pair (e.g., BTCUSDT)
  - `interval`: 1d (daily)
  - `startTime`: Start timestamp in milliseconds
  - `endTime`: End timestamp in milliseconds
  - `limit`: Maximum number of records (1000)

#### 2. Account Information (`/api/v3/account`)
- **Purpose**: Get account balances and permissions
- **Authentication**: Required (API key + signature)

#### 3. Order Creation (`/api/v3/order`)
- **Purpose**: Create market or limit orders
- **Authentication**: Required (API key + signature)
- **Parameters**:
  - `symbol`: Trading pair
  - `side`: BUY/SELL
  - `type`: MARKET/LIMIT
  - `quantity`: Order quantity

#### 4. Latest Kline (`/api/v3/klines`)
- **Purpose**: Get the most recent price data
- **Parameters**:
  - `symbol`: Trading pair
  - `interval`: 1m (1 minute)
  - `limit`: 1

## Code Structure

### BrokerUtils Class

The main integration is in `execution/broker_utils.py`:

```python
class BrokerUtils:
    def __init__(self, broker_name, api_key, secret_key, use_paper=True):
        # Initialize based on broker type
        if broker_name == "Binance":
            self.base_url = "https://api.binance.com"
            self.headers = {"X-MBX-APIKEY": api_key}
    
    def get_daily_price(self, symbol, start_date, end_date=None):
        # Route to appropriate method based on broker
        if self.broker_name == "Binance":
            return self._get_binance_daily_price(symbol, start_date, end_date)
```

### Key Methods

#### 1. `_get_binance_daily_price()`
- Converts symbol format for Binance
- Handles date conversion to milliseconds
- Processes Binance klines data format
- Returns standardized DataFrame with columns: `['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']`

#### 2. `_create_binance_order()`
- Creates market or limit orders
- Handles signature generation for authentication
- Converts internal order types to Binance format

#### 3. `_close_binance_position()`
- Retrieves current account balances
- Creates market sell orders to close positions
- Handles position detection and closure

#### 4. `_get_binance_account_info()`
- Retrieves account information
- Converts Binance format to match Alpaca format for consistency
- Provides account status, balances, and permissions

## Authentication

### HMAC-SHA256 Signature

Binance requires HMAC-SHA256 signatures for authenticated requests:

```python
def _generate_binance_signature(self, params):
    query_string = urlencode(params)
    signature = hmac.new(
        self.secret_key.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature
```

### Required Headers

- `X-MBX-APIKEY`: Your Binance API key
- `signature`: HMAC-SHA256 signature of query parameters

## Usage Examples

### 1. Getting Daily Price Data

```python
from execution.broker_utils import BrokerUtils
from symbols.models import Symbols, Broker

# Get Binance broker
binance_broker = Broker.objects.get(name="Binance")

# Create symbol
btc_symbol = Symbols.objects.get(ticker="BTC-USD")

# Initialize broker utils
broker_utils = BrokerUtils(
    broker_name="Binance",
    api_key=binance_broker.api_key,
    secret_key=binance_broker.secret_key
)

# Get daily prices
daily_prices = broker_utils.get_daily_price(
    btc_symbol, 
    start_date="2024-01-01", 
    end_date="2024-01-31"
)
```

### 2. Creating an Order

```python
# Create a market buy order
order_response = broker_utils.create_order(
    symbol="BTC-USD",
    qty=0.001,  # 0.001 BTC
    side="LONG",  # Will be converted to "BUY"
    type_order="MARKET"
)
```

### 3. Getting Account Information

```python
account_info = broker_utils.get_account_info()
print(f"Account Status: {account_info['status']}")
print(f"Equity: {account_info['equity']}")
```

## Integration with DailyPriceManager

The `DailyPriceManager` in `symbols/utils.py` automatically uses the appropriate broker:

```python
# In DailyPriceManager.get_daily_price()
stock_data = ExecutionUtils.get_daily_price(symbol, start_date=start_date, end_date=end_date)
```

This calls `ExecutionUtils.get_daily_price()` which routes to the correct broker based on the symbol's broker configuration.

## Testing

Run the test script to verify the integration:

```bash
python test_binance_integration.py
```

The test script will:
1. Check for Binance broker configuration
2. Test account information retrieval
3. Test daily price data fetching
4. Test latest minute bar retrieval
5. Verify symbol format conversion

## Error Handling

The integration includes comprehensive error handling:

- **API Errors**: Catches and logs HTTP errors
- **Authentication Errors**: Handles invalid API keys/signatures
- **Data Format Errors**: Handles malformed responses
- **Network Errors**: Handles connection issues

## Security Considerations

1. **API Key Storage**: Store API keys securely in the database
2. **Signature Generation**: Never log or expose secret keys
3. **Rate Limiting**: Respect Binance API rate limits
4. **Test Environment**: Use Binance testnet for development

## Rate Limits

Binance API has the following rate limits:
- **Public endpoints**: 1200 requests per minute
- **Private endpoints**: 10 requests per second
- **Order endpoints**: 10 orders per second

## Troubleshooting

### Common Issues

1. **"Invalid API key"**: Check API key configuration in database
2. **"Invalid signature"**: Verify secret key and timestamp
3. **"Symbol not found"**: Check symbol format conversion
4. **"No data returned"**: Verify date range and symbol availability

### Debug Mode

Enable debug logging to see detailed API requests:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

1. **WebSocket Support**: Real-time price streaming
2. **Futures Trading**: Support for Binance Futures
3. **Margin Trading**: Support for margin accounts
4. **Order Types**: Additional order types (stop-loss, take-profit)
5. **Webhook Support**: Real-time order updates

## Dependencies

The integration requires these Python packages:
- `requests`: HTTP requests
- `pandas`: Data manipulation
- `hmac`: Signature generation
- `hashlib`: Hash functions
- `urllib.parse`: URL encoding

All dependencies are already included in the project's `requirements.txt`.
