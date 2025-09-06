# Enable Assets Command

This Django management command allows you to enable assets (symbols) for a specific broker by executing the `enable_assets()` function from `broker_utils.py`.

## Overview

The command fetches available assets from the broker's API and creates/updates symbols in your database with the appropriate trading permissions.

## Usage

### Basic Usage

```bash
# Enable assets for Alpaca broker
python manage.py enable_assets 'Alpaca'

# Enable assets for Binance broker
python manage.py enable_assets 'Binance'

# Dry run to see what would happen (recommended first)
python manage.py enable_assets 'Alpaca' --dry-run
```

### Command Options

- `broker_name` (required): Name of the broker (e.g., "Alpaca", "Binance")
- `--dry-run`: Show what would be done without making changes

## What It Does

### For Alpaca Broker
- Fetches active US equity assets from Alpaca API (`/v2/assets`)
- Creates or updates symbols in the database
- Sets trading permissions:
  - `long = True` for all symbols
  - `short = True` if the asset is shortable
- Associates symbols with the Alpaca broker
- Sets `slot_free = True` for all symbols

### For Binance Broker
- Fetches exchange info from Binance API (`/api/v3/exchangeInfo`)
- Creates or updates crypto symbols in the database
- Sets trading permissions:
  - `long = True` for all symbols
  - `short = True` if margin trading is allowed
- Creates exchange entries for each quote asset (e.g., "CRYPTO USDT")
- Associates symbols with the Binance broker
- Sets `slot_free = True` for all symbols

## Examples

### 1. Dry Run (Recommended First)
```bash
python manage.py enable_assets 'Alpaca' --dry-run
```
Output:
```
Found broker: Alpaca
DRY RUN: Would enable assets for Alpaca
This would:
  - Fetch available assets from the broker API
  - Create or update symbols in the database
  - Set appropriate trading permissions (long/short)
  - Associate symbols with the broker
```

### 2. Enable Assets for Alpaca
```bash
python manage.py enable_assets 'Alpaca'
```
The command will:
1. Ask for confirmation
2. Fetch assets from Alpaca API
3. Create/update symbols in database
4. Show summary of changes

### 3. Enable Assets for Binance
```bash
python manage.py enable_assets 'Binance'
```
The command will:
1. Ask for confirmation
2. Fetch exchange info from Binance API
3. Create/update crypto symbols in database
4. Show summary of changes

## Safety Features

- **Dry Run**: Use `--dry-run` to see what would happen without making changes
- **Confirmation**: The command asks for confirmation before making changes
- **Transaction Safety**: Uses database transactions to ensure data consistency
- **Error Handling**: Provides clear error messages if something goes wrong

## Database Changes

The command will:

1. **Create new symbols** if they don't exist in the database
2. **Update existing symbols** with latest broker information
3. **Set `slot_free = True`** for all symbols (enabling them for trading)
4. **Update trading permissions** (long/short) based on broker data
5. **Associate symbols** with the specified broker

## Requirements

- Broker must exist in the database with valid API credentials
- For Alpaca: Valid API key and secret key
- For Binance: Valid API key and secret key (though public endpoints may work)

## Troubleshooting

### Broker Not Found
```
CommandError: Broker "InvalidBroker" not found
```
Solution: Check the broker name and ensure it exists in the database.

### API Errors
```
Error enabling assets for Alpaca: Failed to fetch assets from Alpaca: 403 Forbidden
```
Solution: Check your API credentials in the broker settings.

### Database Errors
```
Error enabling assets for Binance: (database error details)
```
Solution: Check database connectivity and permissions.

## Integration with Trading System

After running this command:

1. **Symbols will be available** for backtesting and live trading
2. **Trading permissions** will be set correctly for each symbol
3. **Broker association** will be established for proper API calls
4. **Exchange information** will be populated for filtering

## Related Commands

- `python manage.py update_symbols` - Update symbol information
- `python manage.py update_daily_prices` - Update price data for symbols
