import logging
from backtesting.models import SymbolStatistics
from strategies.models import StrategySymbol
from backtesting.backtest_logic import calculate_strategy_statistics
logger = logging.getLogger(__name__)

def analyze_and_enable_strategies(backtest):
    """
    Analyze SymbolStatistics and enable strategies for symbols based on defined filters.
    """
    symbols = SymbolStatistics.objects.filter(backtest=backtest)

    for symbol_stat in symbols:
        # Extract values
        action = symbol_stat.action
        symbol = symbol_stat.symbol
        strategy = symbol_stat.strategy
        
        avg_roi_per_trade = symbol_stat.total_roi / symbol_stat.total_trades if symbol_stat.total_trades else 0
        avg_holding_period = symbol_stat.average_holding_period
        total_trades = symbol_stat.total_trades
        win_rate = symbol_stat.win_rate
        total_profit_loss = symbol_stat.profit_loss

        # Apply Filters
        is_eligible = (
            3 <= avg_roi_per_trade < 1000 and
            avg_holding_period < 70 and
            total_trades >= 2 and
            win_rate >= 80 and
            total_profit_loss > 0
        )

        # Update StrategySymbol
        strategy_symbol, created = StrategySymbol.objects.get_or_create(
            strategy=strategy, symbol=symbol
        )

        if action == "LONG":
            strategy_symbol.is_active_long = is_eligible
        elif action == "SHORT":
            strategy_symbol.is_active_short = is_eligible
        
        strategy_symbol.save()

        # Logging
        status = "Enabled" if is_eligible else "Disabled"
        logger.info(f"{symbol.ticker} ({strategy.name}) {action} -> {status}")

    calculate_strategy_statistics(backtest)
    logger.info(f"Portfolio analysis completed for backtest: {backtest}")
