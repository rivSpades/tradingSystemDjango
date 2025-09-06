# Find Correlated Pairs Command

This Django management command allows you to find highly correlated symbol pairs for a specific exchange using the `StrategyUtils.find_highly_correlated_pairs()` function.

## Overview

The command analyzes all symbols in a specified exchange, calculates their correlation matrix, and identifies pairs with correlation above a specified threshold. It then saves these correlated pairs to the database for use in cointegration strategies.

## Usage

### Basic Usage

```bash
# Find correlated pairs for NYSE exchange (default threshold 0.90)
python manage.py find_correlated_pairs NYSE

# Find correlated pairs for CRYPTO USDC exchange
python manage.py find_correlated_pairs "CRYPTO USDC"

# Dry run to see what would happen (recommended first)
python manage.py find_correlated_pairs NYSE --dry-run
```

### Command Options

- `exchange_name` (required): Name of the exchange to analyze (e.g., "NYSE", "NASDAQ", "CRYPTO USDT")
- `--dry-run`: Show what would be done without executing the correlation analysis
- `--threshold`: Correlation threshold (default: 0.90, range: 0.0 to 1.0)

## What It Does

### Function Used
- Uses `StrategyUtils.find_highly_correlated_pairs()` from `strategies/utils.py`
- Processes all symbols in the specified exchange
- Calculates correlation matrix using daily close prices
- Identifies pairs with correlation above the threshold
- Saves correlated pairs to the `CorrelatedPair` model

### For Each Exchange
- Validates exchange exists in the database
- Fetches all symbols for the exchange
- Retrieves daily price data for each symbol
- Calculates correlation matrix
- Filters pairs above correlation threshold
- Saves results to database (avoids duplicates)

### Data Structure
Each correlated pair creates:
- `CorrelatedPair`: Symbol pair with correlation value
- Links to `Symbol` objects for both symbols
- Associated with the specified `Exchange`

## Examples

### 1. Dry Run (Recommended First)
```bash
python manage.py find_correlated_pairs NYSE --dry-run
```
Output:
```
Found exchange: NYSE
DRY RUN: Would find correlated pairs for NYSE
This would:
  - Process all symbols in NYSE
  - Calculate correlation matrix
  - Find pairs with correlation > 0.9
  - Save correlated pairs to database
  - Use StrategyUtils.find_highly_correlated_pairs()
```

### 2. Basic Correlation Analysis
```bash
python manage.py find_correlated_pairs NYSE
```
The command will:
1. Ask for confirmation
2. Process all symbols in NYSE
3. Calculate correlations
4. Save correlated pairs to database
5. Show summary of results

### 3. Higher Correlation Threshold
```bash
python manage.py find_correlated_pairs NASDAQ --threshold 0.95
```
Output:
```
Found exchange: NASDAQ
DRY RUN: Would find correlated pairs for NASDAQ
This would:
  - Process all symbols in NASDAQ
  - Calculate correlation matrix
  - Find pairs with correlation > 0.95
  - Save correlated pairs to database
  - Use StrategyUtils.find_highly_correlated_pairs()
```

### 4. Crypto Exchange Analysis
```bash
python manage.py find_correlated_pairs "CRYPTO USDC"
```

### 5. Very High Correlation (0.98)
```bash
python manage.py find_correlated_pairs "CRYPTO BTC" --threshold 0.98
```

## Available Exchanges

Based on current database:

### Stock Exchanges
- **NYSE**: 3,569 total / 2,862 active symbols, 24,398 correlated pairs
- **NASDAQ**: 5,735 total / 4,877 active symbols, 39,984 correlated pairs
- **ARCA**: 2,455 total / 2,365 active symbols, 37,264 correlated pairs
- **BATS**: 1,006 total / 965 active symbols, 13,822 correlated pairs
- **NYSE MKT**: 310 total / 249 active symbols, 205 correlated pairs

### Crypto Exchanges
- **CRYPTO USDC**: 247 total / 218 active symbols, 0 correlated pairs
- **CRYPTO BTC**: 486 total / 209 active symbols, 0 correlated pairs
- **CRYPTO USDT**: 599 total / 408 active symbols, 0 correlated pairs
- **CRYPTO ETH**: 229 total / 51 active symbols, 0 correlated pairs
- **CRYPTO TRY**: 301 total / 267 active symbols, 0 correlated pairs

## Safety Features

- **Dry Run**: Use `--dry-run` to see what would happen without executing
- **Confirmation**: The command asks for confirmation before executing
- **Transaction Safety**: Uses database transactions to ensure data consistency
- **Error Handling**: Provides clear error messages and validation
- **Duplicate Prevention**: Uses `update_or_create` to avoid duplicate pairs

## Database Changes

The command will:

1. **Validate exchange** exists in the database
2. **Fetch symbols** for the specified exchange
3. **Calculate correlations** using daily price data
4. **Filter pairs** above the correlation threshold
5. **Save correlated pairs** to the database:
   - `CorrelatedPair` with symbol references and correlation value
   - Associated with the specified exchange

## Requirements

- Exchange must exist in the database
- Symbols must be associated with the exchange
- Historical price data should be available for the symbols
- Sufficient memory for correlation matrix calculation

## Performance Considerations

- **Large exchanges**: Processing thousands of symbols can take significant time
- **Memory usage**: Correlation matrix calculation requires substantial memory
- **Database performance**: Consider running during off-peak hours
- **Price data**: Ensure sufficient historical data is available

## Troubleshooting

### Exchange Not Found
```
CommandError: Exchange "InvalidExchange" not found
```
Solution: Check the exchange name and ensure it exists in the database.

### No Symbols Found
```
No symbols found for InvalidExchange, skipping.
```
Solution: Ensure symbols are associated with the exchange.

### Insufficient Historical Data
```
Error finding correlated pairs: No price data available
```
Solution: Run the `insert_daily_prices` command first to populate historical price data.

### Memory Issues
```
Error finding correlated pairs: Memory error during correlation calculation
```
Solution: Use a smaller exchange or increase system memory.

## Integration with Trading System

After running this command:

1. **Correlated pairs** will be available in the database
2. **Cointegration strategies** can use these pairs for backtesting
3. **Pair trading** can be executed using the identified correlations
4. **Strategy optimization** can be performed using the correlation data

## Related Commands

- `python manage.py execute_backtest` - Execute backtests using correlated pairs
- `python manage.py insert_daily_prices` - Insert daily price data
- `python manage.py enable_assets` - Enable assets for a broker

## Best Practices

1. **Always use dry-run first** to see what will be processed
2. **Start with smaller exchanges** for testing
3. **Ensure historical data** is available before running
4. **Monitor memory usage** for large exchanges
5. **Use appropriate thresholds** for your strategy needs
6. **Run during off-peak hours** for large exchanges

## Command Examples Summary

```bash
# Basic usage
python manage.py find_correlated_pairs NYSE

# With custom threshold
python manage.py find_correlated_pairs NASDAQ --threshold 0.95

# Crypto exchange
python manage.py find_correlated_pairs "CRYPTO USDC"

# Dry run (recommended)
python manage.py find_correlated_pairs NYSE --dry-run

# Very high correlation
python manage.py find_correlated_pairs "CRYPTO BTC" --threshold 0.98
```

## Technical Details

### Correlation Calculation
- Uses daily close prices from 2013-01-01 onwards
- Handles missing values with forward fill and backward fill
- Calculates Pearson correlation coefficient
- Filters out self-correlations (correlation = 1.0)

### Database Storage
- Uses `update_or_create` to prevent duplicates
- Stores correlation value as float
- Links to both symbols and exchange
- Maintains referential integrity

### Performance Optimization
- Processes symbols in batches for large exchanges
- Uses efficient DataFrame operations
- Minimizes database queries
- Handles memory efficiently

