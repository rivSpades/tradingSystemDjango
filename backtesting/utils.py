import logging
from datetime import date
from strategies.models import Strategy
from symbols.models import Symbols
from .models import BackTestingStrategy
from strategies.strategy_logic import MeanRevertingStrategy

# Setup logging
logger = logging.getLogger(__name__)

def execute_backtest(strategy_id, start_date, end_date=date.today()):
    """
    Executes a backtest for the given strategy on all available symbols.

    :param strategy_id: The ID of the strategy to backtest.
    :param start_date: The start date for historical data.
    :param end_date: The end date for historical data (defaults to today).
    """
    try:
        # Fetch the strategy
        strategy = Strategy.objects.get(id=strategy_id)
        logger.info(f"Starting backtest for strategy: {strategy.name}")

        # Create a new backtest entry
        backtest = BackTestingStrategy.objects.create(
            strategy=strategy,
            parameters=strategy.parameters
        )

        # Fetch all symbols
        symbols = Symbols.objects.all()
        if not symbols.exists():
            logger.warning("No symbols found in the database.")
            return "No symbols available for backtesting."

        # Instantiate the strategy logic
        strategy_logic = MeanRevertingStrategy(strategy.parameters)

        # Loop through all symbols and execute backtest
        for symbol in symbols:
            logger.info(f"Running backtest for {symbol.ticker}...")
            result = strategy_logic.backtest(backtest, symbol.ticker, start_date, end_date)
            logger.info(result)

        return f"Backtest completed for {len(symbols)} symbols."

    except Strategy.DoesNotExist:
        logger.error(f"Strategy with ID {strategy_id} not found.")
        return f"Strategy with ID {strategy_id} not found."

    except Exception as e:
        logger.error(f"Error executing backtest: {e}")
        return f"Error executing backtest: {e}"
