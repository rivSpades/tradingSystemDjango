# Insert Daily Prices Command

This Django management command allows you to insert daily prices for symbols from a specific broker using the existing `update_daily_prices_for_symbols` function from `symbols/utils.py`.

## Overview

The command fetches daily price data from the broker's API and inserts new price records into the database, automatically determining the last available date for each symbol to avoid duplicates.

## Usage

### Basic Usage

```bash
# Insert daily prices for Alpaca broker
python manage.py insert_daily_prices 'Alpaca'

# Insert daily prices for Binance broker
python manage.py insert_daily_prices 'Binance'

# Dry run to see what would happen (recommended first)
python manage.py insert_daily_prices 'Alpaca' --dry-run
```

### Command Options

- `broker_name` (required): Name of the broker (e.g., "Alpaca", "Binance")
- `--exchange`: Name of the exchange to filter symbols (e.g., "NYSE", "NASDAQ", "CRYPTO USDT")
- `--dry-run`: Show what would be done without making changes
- `--start-date`: Start date for price data (default: 2013-01-01)
- `--end-date`: End date for price data (default: yesterday)
- `--symbols`: Comma-separated list of specific symbols to update (optional)

## What It Does

### Function Used
- Uses `DailyPriceManager.update_daily_prices_for_symbols()` from `symbols/utils.py`
- Automatically determines the last available date for each symbol
- Fetches new price data from the broker API
- Inserts only new price records (skips existing ones)
- **Only processes active symbols** (where `active = True`)

### For Each Symbol
- Checks the last available date in the database
- Fetches price data from the last date + 1 day
- Creates `DailyPrice` objects for new data
- Uses `bulk_create` for efficient database insertion

### Data Structure
Each price record includes:
- `symbol`: Reference to the symbol
- `price_date`: Date of the price data
- `open_price`: Opening price
- `high_price`: Highest price of the day
- `low_price`: Lowest price of the day
- `close_price`: Closing price
- `adj_close_price`: Adjusted closing price
- `volume`: Trading volume

## Examples

### 1. Dry Run (Recommended First)
```bash
python manage.py insert_daily_prices 'Alpaca' --dry-run
```
Output:
```
Found broker: Alpaca
DRY RUN: Would insert daily prices for Alpaca
This would:
  - Process 11635 symbols
  - Fetch price data from Alpaca API
  - Insert new daily prices into database
  - Start date: 2013-01-01
  - End date: yesterday

Symbols that would be processed:
  - A
  - AA
  - AAA
  - AAAU
  - AACG
  ... and 11625 more
```

### 2. Insert Prices for All Symbols
```bash
python manage.py insert_daily_prices 'Alpaca'
```
The command will:
1. Ask for confirmation
2. Process each symbol individually
3. Fetch price data from Alpaca API
4. Insert new price records into database
5. Show summary of results

### 3. Insert Prices for Specific Symbols
```bash
python manage.py insert_daily_prices 'Alpaca' --symbols 'AAPL,MSFT,GOOGL'
```
Output:
```
Found broker: Alpaca
Filtering by symbols: AAPL, MSFT, GOOGL
DRY RUN: Would insert daily prices for Alpaca
This would:
  - Process 3 symbols
  - Fetch price data from Alpaca API
  - Insert new daily prices into database
  - Start date: 2013-01-01
  - End date: yesterday

Symbols that would be processed:
  - AAPL
  - GOOGL
  - MSFT
```

### 4. Insert Prices with Custom Date Range
```bash
python manage.py insert_daily_prices 'Alpaca' --start-date '2024-01-01' --end-date '2024-12-31'
```

### 5. Insert Prices for Specific Exchange
```bash
python manage.py insert_daily_prices 'Alpaca' --exchange 'NYSE'
```
Output:
```
Found broker: Alpaca
Filtering by exchange: NYSE
DRY RUN: Would insert daily prices for Alpaca
This would:
  - Process 2862 symbols
  - Fetch price data from Alpaca API
  - Filter by exchange: NYSE
  - Insert new daily prices into database
  - Start date: 2013-01-01
  - End date: yesterday

Symbols that would be processed:
  - A
  - AA
  - AACT
  - AAP
  - AAT
  - AB
  - ABBV
  - ABEV
  - ABG
  - ABM
  ... and 2852 more
```

### 6. Insert Prices for Binance Crypto Exchange
```bash
python manage.py insert_daily_prices 'Binance' --exchange 'CRYPTO USDT'
```
Output:
```
Found broker: Binance
Filtering by active symbols only
Filtering by exchange: CRYPTO USDT
DRY RUN: Would insert daily prices for Binance
This would:
  - Process 408 symbols
  - Fetch price data from Binance API
  - Filter by exchange: CRYPTO USDT
  - Insert new daily prices into database
  - Start date: 2013-01-01
  - End date: yesterday

Symbols that would be processed:
  - BTC-USDT
  - ETH-USDT
  - BNB-USDT
  - NEO-USDT
  - LTC-USDT
  - QTUM-USDT
  - ADA-USDT
  - XRP-USDT
  - TUSD-USDT
  - IOTA-USDT
  ... and 398 more
```

### 7. Insert Prices for Specific Exchange and Symbols
```bash
python manage.py insert_daily_prices 'Alpaca' --exchange 'NASDAQ' --symbols 'AAPL,MSFT,GOOGL'
```

## Safety Features

- **Dry Run**: Use `--dry-run` to see what would happen without making changes
- **Confirmation**: The command asks for confirmation before making changes
- **Transaction Safety**: Uses database transactions to ensure data consistency
- **Error Handling**: Provides clear error messages and continues with other symbols
- **Duplicate Prevention**: Only inserts new price records (skips existing ones)

## Database Changes

The command will:

1. **Filter symbols** to only include active symbols (`active = True`)
2. **Check existing data** for each symbol to determine the last available date
3. **Fetch new price data** from the broker API starting from the last date + 1 day
4. **Create DailyPrice objects** for new price records
5. **Bulk insert** the new records efficiently
6. **Skip existing records** to avoid duplicates

## Requirements

- Broker must exist in the database with valid API credentials
- Symbols must be associated with the broker
- For Alpaca: Valid API key and secret key
- For Binance: Valid API key and secret key (though public endpoints may work)

## Troubleshooting

### Broker Not Found
```
CommandError: Broker "InvalidBroker" not found
```
Solution: Check the broker name and ensure it exists in the database.

### No Symbols Found
```
No symbols found for broker Alpaca
```
Solution: Run the `enable_assets` command first to populate symbols for the broker.

### Exchange Not Found
```
CommandError: Exchange "InvalidExchange" not found
```
Solution: Check the exchange name and ensure it exists in the database. Use the test script to see available exchanges.

### No Symbols Found for Exchange
```
No symbols found for broker Alpaca
```
Solution: The specified exchange may not have symbols associated with the broker. Check the exchange-broker relationship.

### API Errors
```
Error inserting daily prices for Alpaca: Failed to fetch assets from Alpaca: 403 Forbidden
```
Solution: Check your API credentials in the broker settings.

### Database Errors
```
Error inserting daily prices for Binance: (database error details)
```
Solution: Check database connectivity and permissions.

## Integration with Trading System

After running this command:

1. **Price data will be available** for backtesting and analysis
2. **Historical data** will be populated for strategy development
3. **Latest prices** will be available for live trading decisions
4. **Data consistency** will be maintained across the system

## Performance Considerations

- **Large datasets**: Processing thousands of symbols can take time
- **API rate limits**: Be aware of broker API rate limits
- **Memory usage**: Large price datasets may require significant memory
- **Database performance**: Consider running during off-peak hours

## Related Commands

- `python manage.py enable_assets` - Enable assets for a broker
- `python manage.py update_symbols` - Update symbol information
- `python manage.py update_daily_prices` - Update price data for all symbols

## Best Practices

1. **Always use dry-run first** to see what will be processed
2. **Start with specific symbols** for testing before processing all symbols
3. **Monitor API rate limits** when processing large datasets
4. **Run during off-peak hours** for better performance
5. **Check broker credentials** before running the command
