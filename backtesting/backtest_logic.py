import logging
from datetime import date
from strategies.models import Strategy
from symbols.models import Symbols
import numpy as np
from django.db.models import Avg, Count, Sum, F
from .models import BackTestingStrategy,StrategyStatistics,SymbolStatistics,TradeHistory
from strategies.strategy_logic import MeanRevertingStrategy,CoIntegrationStrategy
from strategies.models import StrategySymbol,CorrelatedPair

# Setup logging
logger = logging.getLogger(__name__)

def execute_backtest(strategy_id, start_date, end_date=date.today(), symbol_list=None):
    """
    Executes a backtest for the given strategy.

    :param strategy_id: The ID or slug of the strategy to backtest.
    :param start_date: The start date for historical data.
    :param end_date: The end date for historical data (defaults to today).
    :param symbol_list: (Optional) List of specific symbols to backtest.
                        If None, the backtest runs on all symbols.
    """
    try:
        # Fetch the strategy
        strategy = Strategy.objects.get(slug=strategy_id)
        logger.info(f"Starting backtest for strategy: {strategy.name}")

        # Create a new backtest entry
        backtest = BackTestingStrategy.objects.create(
            strategy=strategy,
            parameters=strategy.parameters
        )

        if strategy.slug == "mean-reverting":

            # Fetch symbols based on the provided list or all symbols
            if symbol_list:
                symbols = Symbols.objects.filter(ticker__in=symbol_list)
            else:
                symbols = Symbols.objects.all()

            if not symbols.exists():
                logger.warning("No symbols found for backtesting.")
                return "No symbols available for backtesting."

            # Instantiate the strategy logic
            strategy_logic = MeanRevertingStrategy(strategy.parameters)

            # Loop through selected symbols and execute backtest
            for symbol in symbols:
                logger.info(f"Running backtest for {symbol.ticker}...")
                result = strategy_logic.backtest(backtest, symbol.ticker, start_date, end_date)
                logger.info(result)

        elif strategy.slug == "cointegration":  

            correlated_pairs = CorrelatedPair.objects.all()  # You can filter based on certain criteria here if needed

            if not correlated_pairs.exists():
                logger.warning("No correlated pairs found for Cointegration strategy.")
                return "No correlated pairs available for backtesting."                                     

            strategy_logic = CoIntegrationStrategy(strategy.parameters)

            for pair in correlated_pairs:
                logger.info(f"Running backtest for Correlated Pair: {pair.symbol_1.ticker} & {pair.symbol_2.ticker}...")
               
                result = strategy_logic.backtest(backtest, pair.symbol_1.ticker,pair.symbol_2.ticker, start_date, end_date)
               
                logger.info(result)            

        calculate_symbol_statistics(backtest)
        

        return f"Backtest completed for {len(symbols)} symbols."

    except Strategy.DoesNotExist:
        logger.error(f"Strategy with ID {strategy_id} not found.")
        return f"Strategy with ID {strategy_id} not found."

    except Exception as e:
        logger.error(f"Error executing backtest: {e}")
        return f"Error executing backtest: {e}"


def calculate_symbol_statistics(backtest):
    """
    Calculates and stores statistics for each symbol in a backtest, separated by LONG and SHORT actions.
    """
    symbols = TradeHistory.objects.filter(backtest=backtest).values_list('symbol', flat=True).distinct()

    for symbol in symbols:
        for action in ["LONG", "SHORT"]:
            trades = TradeHistory.objects.filter(backtest=backtest, symbol=symbol, action=action, exit_price__isnull=False)

            if not trades.exists():
                continue

            total_trades = trades.count()
            profitable_trades = trades.filter(profit_loss__gt=0).count()
            win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0

            total_profit_loss = trades.aggregate(Sum('profit_loss'))['profit_loss__sum'] or 0

            holding_periods = [
                (trade.exit_date - trade.entry_date).days
                for trade in trades if trade.exit_date and trade.entry_date
            ]
            avg_holding_period = np.mean(holding_periods) if holding_periods else 0

            roi = (total_profit_loss / sum(trade.entry_price * trade.quantity for trade in trades)) * 100 if trades else 0

            max_drawdowns = trades.aggregate(Avg('max_drawdown'))['max_drawdown__avg'] or 0

            SymbolStatistics.objects.update_or_create(
                symbol_id=symbol,
                backtest=backtest,
                strategy=backtest.strategy,
                action=action,  # Separate LONG and SHORT
                defaults={
                    'total_trades': total_trades,
                    'win_rate': win_rate,
                    'profit_loss': total_profit_loss,
                    'average_holding_period': avg_holding_period,
                    'total_roi': roi,
                    'average_max_drawdown': max_drawdowns,
                }
            )

            logger.info(f"Symbol statistics calculated for {symbol} - {action}")


def calculate_strategy_statistics(backtest):
    """
    Calculates and stores aggregated statistics for the overall strategy, 
    considering only symbols where the strategy is active for LONG or SHORT.
    """
    for action in ["LONG", "SHORT"]:
        # Get symbols where strategy is active for this action
        if action == "LONG":
            active_symbols = StrategySymbol.objects.filter(strategy=backtest.strategy, is_active_long=True).values_list('symbol', flat=True)
        else:  # SHORT
            active_symbols = StrategySymbol.objects.filter(strategy=backtest.strategy, is_active_short=True).values_list('symbol', flat=True)

        # Get trades only for active symbols
        trades = TradeHistory.objects.filter(
            backtest=backtest, 
            action=action, 
            exit_price__isnull=False, 
            symbol__in=active_symbols
        )

        if not trades.exists():
            logger.warning(f"No {action} trades found for active symbols in strategy {backtest.strategy.name}.")
            continue

        total_trades = trades.count()
        profitable_trades = trades.filter(profit_loss__gt=0).count()
        win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0

        total_profit_loss = trades.aggregate(Sum('profit_loss'))['profit_loss__sum'] or 0

        holding_periods = [
            (trade.exit_date - trade.entry_date).days
            for trade in trades if trade.exit_date and trade.entry_date
        ]
        avg_holding_period = np.mean(holding_periods) if holding_periods else 0

        total_entry_value = sum(trade.entry_price * trade.quantity for trade in trades)
        roi = (total_profit_loss / total_entry_value) * 100 if total_entry_value > 0 else 0

        avg_max_drawdown = trades.aggregate(Avg('max_drawdown'))['max_drawdown__avg'] or 0

        # Update or create StrategyStatistics for this action
        StrategyStatistics.objects.update_or_create(
            backtest=backtest,
            strategy=backtest.strategy,
            action=action,
            defaults={
                'total_trades': total_trades,
                'win_rate': win_rate,
                'total_roi': roi,
                'total_profit_loss': total_profit_loss,
                'average_holding_period': avg_holding_period,
                'average_max_drawdown': avg_max_drawdown,
            }
        )

        logger.info(f"Strategy statistics calculated for {backtest.strategy.name} - {action}, considering only active symbols.")