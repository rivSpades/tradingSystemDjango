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

def execute_backtest(strategy_id, start_date, end_date=date.today(), symbol_list=None,backtest=None):
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

        if not backtest:
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
                print(pair.symbol_1.ticker + "+" + pair.symbol_2.ticker)
                if TradeHistory.objects.filter(backtest=backtest, correlated_pair=pair).exists():
                    continue
                    
                    
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
    has_correlated_pair = TradeHistory.objects.filter(backtest=backtest, correlated_pair__isnull=False).exists()
    if has_correlated_pair:

        pairs = CorrelatedPair.objects.filter(
                id__in=TradeHistory.objects.filter(
                backtest=backtest, correlated_pair__isnull=False
                ).values_list('correlated_pair', flat=True).distinct()
)
        for pair in pairs:
            print(pair)

            symbols_in_pair = [pair.symbol_1, pair.symbol_2]
            for symbol in symbols_in_pair:
                
                for action in ["LONG", "SHORT"]:
                    
                    trades = TradeHistory.objects.filter(backtest=backtest, symbol=symbol,  correlated_pair=pair,action=action, exit_price__isnull=False)    
                    
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
                        symbol=symbol,
                        backtest=backtest,
                        correlated_pair=pair,
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


            trades = TradeHistory.objects.filter(backtest=backtest,action__in=["LONG","SHORT"],  correlated_pair=pair, exit_price__isnull=False)    
            if not trades.exists():
                continue

            # 🚀 Group trades into pairs by entry_date
            trade_pairs = {}
            for trade in trades:
                key = trade.entry_date  # Group by entry date (assuming paired trades have same entry date)
                if key not in trade_pairs:
                    trade_pairs[key] = []
                trade_pairs[key].append(trade)

            # Count the number of valid pairs
            total_trades = len(trade_pairs)

            # Aggregate performance metrics
            total_profit_loss = 0
            win_count = 0
            holding_periods = []
            max_drawdowns = []

            for pair_trades in trade_pairs.values():
                if len(pair_trades) != 2:
                    continue  # Ensure we have both LONG and SHORT trades in a pair

                pair_profit_loss = sum(trade.profit_loss for trade in pair_trades)
                total_profit_loss += pair_profit_loss

                # Check if the pair was profitable
                if pair_profit_loss > 0:
                    win_count += 1

                # Calculate holding period for the pair
                holding_period = max((trade.exit_date - trade.entry_date).days for trade in pair_trades if trade.exit_date and trade.entry_date)
                holding_periods.append(holding_period)

                # Store max drawdowns
                max_drawdowns.append(sum(trade.max_drawdown for trade in pair_trades) / len(pair_trades))

            # Compute final statistics
            win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
            avg_holding_period = np.mean(holding_periods) if holding_periods else 0
            avg_max_drawdown = np.mean(max_drawdowns) if max_drawdowns else 0

            # ROI Calculation
            total_entry_value = sum(sum(trade.entry_price * trade.quantity for trade in pair) for pair in trade_pairs.values() if len(pair) == 2)
            roi = (total_profit_loss / total_entry_value) * 100 if total_entry_value > 0 else 0

            # Save to database
            SymbolStatistics.objects.update_or_create(
                backtest=backtest,
                correlated_pair=pair,
                strategy=backtest.strategy,
                action="PAIR_TRADING",
                defaults={
                    'total_trades': total_trades,
                    'win_rate': win_rate,
                    'profit_loss': total_profit_loss,
                    'average_holding_period': avg_holding_period,
                    'total_roi': roi,
                    'average_max_drawdown': avg_max_drawdown,
                }
            )

            logger.info(f"Calculated Pair Trading stats for {pair}")


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