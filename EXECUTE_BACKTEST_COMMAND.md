# Execute Backtest Command

This Django management command allows you to execute backtests for specific exchanges and strategies using only active symbols.

## Overview

The command executes backtests using the existing `execute_backtest` function from `backtesting/backtest_logic.py`, with automatic filtering for active symbols and optional symbol filtering.

## Usage

### Basic Usage

```bash
# Execute backtest for NYSE mean-reverting strategy
python manage.py execute_backtest 'NYSE' 'mean-reverting'

# Execute backtest for CRYPTO USDT MA crossover strategy
python manage.py execute_backtest 'CRYPTO USDT' 'ma-crossover'

# Dry run to see what would happen (recommended first)
python manage.py execute_backtest 'NYSE' 'mean-reverting' --dry-run
```

### Command Options

- `exchange_name` (required): Name of the exchange (e.g., "NYSE", "NASDAQ", "CRYPTO USDT")
- `strategy_slug` (required): Strategy slug to execute (e.g., "mean-reverting", "ma-crossover", "cointegration")
- `--start-date`: Start date for backtest (default: 2013-01-01)
- `--end-date`: End date for backtest (default: today)
- `--symbols`: Comma-separated list of specific symbols to backtest (optional)
- `--dry-run`: Show what would be done without executing the backtest

## What It Does

### Function Used
- Uses `execute_backtest()` from `backtesting/backtest_logic.py`
- Automatically filters symbols to only include active ones (`active = True`)
- Creates backtest results in the database
- Generates strategy and symbol statistics

### For Each Backtest
- Validates exchange and strategy exist
- Filters symbols by exchange and active status
- Optionally filters by specific symbols
- Executes the strategy logic on historical data
- Creates `BackTestingStrategy`, `TradeHistory`, `StrategyStatistics`, and `SymbolStatistics` records

### Data Structure
Each backtest creates:
- `BackTestingStrategy`: Main backtest record with parameters
- `TradeHistory`: Individual trade executions
- `StrategyStatistics`: Overall strategy performance metrics
- `SymbolStatistics`: Performance metrics per symbol

## Examples

### 1. Dry Run (Recommended First)
```bash
python manage.py execute_backtest 'NYSE' 'mean-reverting' --dry-run
```
Output:
```
Found exchange: NYSE
Found strategy: Mean Reverting (mean-reverting)
Filtering by active symbols only
DRY RUN: Would execute backtest for NYSE
This would:
  - Execute strategy: Mean Reverting (mean-reverting)
  - Process 2862 active symbols
  - Date range: 2013-01-01 to 2024-12-19
  - Create backtest results in database

Symbols that would be processed:
  - A
  - AA
  - AACT
  - AAP
  - AAT
  ... and 2852 more
```

### 2. Basic Backtest Execution
```bash
python manage.py execute_backtest 'NYSE' 'mean-reverting'
```
The command will:
1. Ask for confirmation
2. Execute the strategy on all active symbols
3. Create backtest results in database
4. Show summary of results

### 3. Backtest with Specific Symbols
```bash
python manage.py execute_backtest 'NASDAQ' 'mean-reverting' --symbols 'AAPL,MSFT,GOOGL'
```
Output:
```
Found exchange: NASDAQ
Found strategy: Mean Reverting (mean-reverting)
Filtering by active symbols only
Filtering by symbols: AAPL, MSFT, GOOGL
DRY RUN: Would execute backtest for NASDAQ
This would:
  - Execute strategy: Mean Reverting (mean-reverting)
  - Process 3 active symbols
  - Date range: 2013-01-01 to 2024-12-19
  - Create backtest results in database

Symbols that would be processed:
  - AAPL
  - GOOGL
  - MSFT
```

### 4. Backtest with Custom Date Range
```bash
python manage.py execute_backtest 'NYSE' 'mean-reverting' --start-date '2023-01-01' --end-date '2023-12-31'
```

### 5. Cointegration Strategy on CRYPTO BTC
```bash
python manage.py execute_backtest 'CRYPTO BTC' 'cointegration'
```

### 6. MA Crossover on CRYPTO USDT
```bash
python manage.py execute_backtest 'CRYPTO USDT' 'ma-crossover'
```

## Available Strategies

### 1. Mean Reverting (`mean-reverting`)
- **Description**: Identifies overbought/oversold conditions and trades mean reversion
- **Parameters**: Lookback period, z-score thresholds
- **Best for**: Range-bound markets, mean-reverting assets

### 2. MA Crossover (`ma-crossover`)
- **Description**: Uses moving average crossovers to generate buy/sell signals
- **Parameters**: Short and long moving average periods
- **Best for**: Trending markets, momentum strategies

### 3. Cointegration (`cointegration`)
- **Description**: Pairs trading based on cointegrated relationships
- **Parameters**: Cointegration test parameters, correlation thresholds
- **Best for**: Pairs trading, statistical arbitrage

## Safety Features

- **Dry Run**: Use `--dry-run` to see what would happen without executing
- **Confirmation**: The command asks for confirmation before executing
- **Transaction Safety**: Uses database transactions to ensure data consistency
- **Error Handling**: Provides clear error messages and validation
- **Active Symbol Filtering**: Only processes active symbols automatically

## Database Changes

The command will:

1. **Validate inputs** (exchange, strategy, symbols)
2. **Filter symbols** to only include active ones
3. **Execute strategy logic** on historical price data
4. **Create backtest records** in the database:
   - `BackTestingStrategy` with parameters and metadata
   - `TradeHistory` for each trade execution
   - `StrategyStatistics` for overall performance
   - `SymbolStatistics` for per-symbol performance

## Requirements

- Exchange must exist in the database
- Strategy must exist with the specified slug
- Symbols must be associated with the exchange and marked as active
- Historical price data should be available for the symbols

## Troubleshooting

### Exchange Not Found
```
CommandError: Exchange "InvalidExchange" not found
```
Solution: Check the exchange name and ensure it exists in the database.

### Strategy Not Found
```
CommandError: Strategy "invalid-strategy" not found
```
Solution: Check the strategy slug and ensure it exists in the database.

### No Active Symbols Found
```
No active symbols found for exchange NYSE
```
Solution: Run the `enable_assets` command first to populate active symbols for the exchange.

### Insufficient Historical Data
```
Error executing backtest: No data available for symbol XYZ
```
Solution: Run the `insert_daily_prices` command first to populate historical price data.

### Strategy Execution Errors
```
Error executing backtest: Strategy-specific error message
```
Solution: Check strategy parameters and ensure they are valid for the selected symbols.

## Integration with Trading System

After running this command:

1. **Backtest results** will be available in the database
2. **Performance metrics** will be calculated and stored
3. **Trade history** will be available for analysis
4. **Strategy optimization** can be performed using the results
5. **Live trading decisions** can be informed by backtest performance

## Performance Considerations

- **Large symbol sets**: Processing thousands of symbols can take significant time
- **Historical data**: Ensure sufficient historical data is available
- **Memory usage**: Large backtests may require significant memory
- **Database performance**: Consider running during off-peak hours
- **Strategy complexity**: More complex strategies take longer to execute

## Related Commands

- `python manage.py enable_assets` - Enable assets for a broker
- `python manage.py insert_daily_prices` - Insert daily price data
- `python manage.py update_symbols` - Update symbol information

## Best Practices

1. **Always use dry-run first** to see what will be executed
2. **Start with specific symbols** for testing before processing all symbols
3. **Ensure historical data** is available before running backtests
4. **Monitor execution time** for large symbol sets
5. **Check strategy parameters** before execution
6. **Use appropriate date ranges** for your analysis needs

## Command Examples Summary

```bash
# Basic usage
python manage.py execute_backtest NYSE mean-reverting

# With specific symbols
python manage.py execute_backtest NASDAQ mean-reverting --symbols "AAPL,MSFT,GOOGL"

# With custom date range
python manage.py execute_backtest NYSE mean-reverting --start-date 2023-01-01 --end-date 2023-12-31

# Dry run (recommended)
python manage.py execute_backtest NYSE mean-reverting --dry-run

# Cointegration strategy
python manage.py execute_backtest "CRYPTO BTC" cointegration

# MA Crossover on crypto
python manage.py execute_backtest "CRYPTO USDT" ma-crossover
```
