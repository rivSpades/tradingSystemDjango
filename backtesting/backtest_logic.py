import logging
from datetime import date
from strategies.models import Strategy
from symbols.models import Symbols,Exchange
import numpy as np
from django.db.models import Avg, Count, Sum, F,Q
from .models import BackTestingStrategy,StrategyStatistics,SymbolStatistics,TradeHistory
from strategies.strategy_logic import MeanRevertingStrategy,CoIntegrationStrategy,MACrossoverStrategy
from strategies.models import StrategySymbol,CorrelatedPair
from collections import defaultdict
from backtesting.utils import BackTestUtils
from portfolio.portfolio_logic import analyze_and_enable_strategies
# Setup logging
logger = logging.getLogger(__name__)

def execute_backtest(strategy_id, start_date, end_date=date.today(), symbol_list=None, backtest=None, exchange_name=None, reverse=False, correlated_pair_list=None, exchange_id=None):
    """
    Executes a backtest for the given strategy.

    :param strategy_id: The ID or slug of the strategy to backtest.
    :param start_date: The start date for historical data.
    :param end_date: The end date for historical data (defaults to today).
    :param symbol_list: (Optional) List of specific symbols to backtest.
                        If None, the backtest runs on all symbols.
    :param exchange_name: (Optional) Name of the exchange to filter symbols.
    :param exchange_id: (Optional) ID of the exchange to filter symbols.
    :param backtest: (Optional) Existing backtest instance to use.
    :param reverse: (Optional) Reverse the order of correlated pairs.
    :param correlated_pair_list: (Optional) List of specific correlated pairs to backtest.
    """
    try:
        # Fetch the strategy
        strategy = Strategy.objects.get(slug=strategy_id)
        logger.info(f"Starting backtest for strategy: {strategy.name}")
        print(exchange_name)
        # Get exchange if specified
        exchange = None
        if exchange_id:
            exchange = Exchange.objects.get(id=exchange_id)
        elif exchange_name:
            exchange = Exchange.objects.get(name=exchange_name)
        
        if not backtest:
            # Create a new backtest entry
            backtest = BackTestingStrategy.objects.create(
                strategy=strategy,
                parameters=strategy.parameters,
                exchange=exchange
            )

        if strategy.slug == "mean-reverting":

            # Fetch symbols based on the provided list or all symbols
            if symbol_list:
                symbols = Symbols.objects.filter(ticker__in=symbol_list)
            else:
                symbols = Symbols.objects.all()
            
            # Filter by exchange if specified
            if exchange:
                symbols = symbols.filter(exchange=exchange)
                logger.info(f"Filtering symbols for exchange: {exchange.name}")
            
            # Filter symbols that have brokers assigned
            symbols = symbols.filter(broker__isnull=False)
            logger.info(f"Filtering symbols with brokers assigned")

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

        elif strategy.slug == "ma-crossover":

            # Fetch symbols based on the provided list or all symbols
            if symbol_list:
                symbols = Symbols.objects.filter(ticker__in=symbol_list)
            else:
                symbols = Symbols.objects.all()
            
            # Filter by exchange if specified
            if exchange:
                symbols = symbols.filter(exchange=exchange)
                logger.info(f"Filtering symbols for exchange: {exchange.name}")
            
            # Filter symbols that have brokers assigned
            symbols = symbols.filter(broker__isnull=False)
            logger.info(f"Filtering symbols with brokers assigned")

            if not symbols.exists():
                logger.warning("No symbols found for backtesting.")
                return "No symbols available for backtesting."

            # Instantiate the strategy logic
            strategy_logic = MACrossoverStrategy(strategy.parameters)

            # Loop through selected symbols and execute backtest
            for symbol in symbols:
                logger.info(f"Running backtest for {symbol.ticker}...")
                result = strategy_logic.backtest(backtest, symbol.ticker, start_date, end_date)
                logger.info(result)                

        elif strategy.slug == "cointegration":  
            if exchange_name:
                #exchange = Exchange.objects.get(name=exchange_name)
                correlated_pairs = CorrelatedPair.objects.filter(exchange=exchange)  # You can filter based on certain criteria here if needed
            elif correlated_pair_list:
              

                correlated_pairs = correlated_pair_list                                     
            else:    
                correlated_pairs = CorrelatedPair.objects.all()  # You can filter based on certain criteria here if needed
            print(correlated_pairs)
            if not correlated_pairs.exists():
                logger.warning("No correlated pairs found for Cointegration strategy.")
                return "No correlated pairs available for backtesting."                                     

            if reverse:
                correlated_pairs = correlated_pairs.order_by('-id')  # Or any field you want to reverse by  

            strategy_logic = CoIntegrationStrategy(strategy.parameters)

            for pair in correlated_pairs:
                
                print(pair.symbol_1.ticker + "+" + pair.symbol_2.ticker)
                if TradeHistory.objects.filter(backtest=backtest, correlated_pair=pair).exists():
                    print("already exists")
                    continue
                    
                try:    
                    result = strategy_logic.backtest(backtest, pair.symbol_1.ticker,pair.symbol_2.ticker, start_date, end_date)
                except:
                    continue    
               
                logger.info(result)            

        BackTestUtils.calculate_symbol_statistics(backtest)
        

        #return f"Backtest completed for {len(symbols)} symbols."
        return backtest

    except Strategy.DoesNotExist:
        logger.error(f"Strategy with ID {strategy_id} not found.")
        return f"Strategy with ID {strategy_id} not found."

    except Exception as e:
        logger.error(f"Error executing backtest: {e}")
        return f"Error executing backtest: {e}"


# def calculate_symbol_statistics(backtest):
#     """
#     Calculates and stores statistics for each symbol in a backtest, separated by LONG and SHORT actions.
#     """
#     if(backtest.strategy.slug=='cointegration'):
#         has_correlated_pair = TradeHistory.objects.filter(backtest=backtest, correlated_pair__isnull=False).exists()
#         if has_correlated_pair:

#             pairs = CorrelatedPair.objects.filter(
#                     id__in=TradeHistory.objects.filter(
#                     backtest=backtest, correlated_pair__isnull=False
#                     ).values_list('correlated_pair', flat=True).distinct()
#     )
#             for pair in pairs:
#                 print(pair)

#                 symbols_in_pair = [pair.symbol_1, pair.symbol_2]
#                 for symbol in symbols_in_pair:
                    
#                     for action in ["LONG", "SHORT"]:
                        
#                         trades = TradeHistory.objects.filter(backtest=backtest, symbol=symbol,  correlated_pair=pair,action=action, exit_price__isnull=False)    
                        
#                         if not trades.exists():
#                             continue

#                         total_trades = trades.count()                        
#                         profitable_trades = trades.filter(profit_loss__gt=0).count()
#                         win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
#                         total_profit_loss = trades.aggregate(Sum('profit_loss'))['profit_loss__sum'] or 0

#                         holding_periods = [
#                             (trade.exit_date - trade.entry_date).days
#                             for trade in trades if trade.exit_date and trade.entry_date
#                         ]    

#                         avg_holding_period = np.mean(holding_periods) if holding_periods else 0         
#                         roi = (total_profit_loss / sum(trade.entry_price * trade.quantity for trade in trades)) * 100 if trades else 0   
#                         max_drawdowns = trades.aggregate(Avg('max_drawdown'))['max_drawdown__avg'] or 0
#                         SymbolStatistics.objects.update_or_create(
#                             symbol=symbol,
#                             backtest=backtest,
#                             correlated_pair=pair,
#                             strategy=backtest.strategy,
#                             action=action,  # Separate LONG and SHORT
#                             defaults={
#                                 'total_trades': total_trades,
#                                 'win_rate': win_rate,
#                                 'profit_loss': total_profit_loss,
#                                 'average_holding_period': avg_holding_period,
#                                 'total_roi': roi,
#                                 'average_max_drawdown': max_drawdowns,
#                             }
#                         )


#                 trades = TradeHistory.objects.filter(backtest=backtest,action__in=["LONG","SHORT"],  correlated_pair=pair, exit_price__isnull=False)    
#                 if not trades.exists():
#                     continue

#                 # 🚀 Group trades into pairs by entry_date
#                 trade_pairs = {}
#                 for trade in trades:
#                     key = trade.entry_date  # Group by entry date (assuming paired trades have same entry date)
#                     if key not in trade_pairs:
#                         trade_pairs[key] = []
#                     trade_pairs[key].append(trade)

#                 # Count the number of valid pairs
#                 total_trades = len(trade_pairs)

#                 # Aggregate performance metrics
#                 total_profit_loss = 0
#                 win_count = 0
#                 holding_periods = []
#                 max_drawdowns = []

#                 for pair_trades in trade_pairs.values():
#                     if len(pair_trades) != 2:
#                         continue  # Ensure we have both LONG and SHORT trades in a pair

#                     pair_profit_loss = sum(trade.profit_loss for trade in pair_trades)
#                     total_profit_loss += pair_profit_loss

#                     # Check if the pair was profitable
#                     if pair_profit_loss > 0:
#                         win_count += 1

#                     # Calculate holding period for the pair
#                     holding_period = max((trade.exit_date - trade.entry_date).days for trade in pair_trades if trade.exit_date and trade.entry_date)
#                     holding_periods.append(holding_period)

#                     # Store max drawdowns
#                     max_drawdowns.append(sum(trade.max_drawdown for trade in pair_trades) / len(pair_trades))

#                 # Compute final statistics
#                 win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
#                 avg_holding_period = np.mean(holding_periods) if holding_periods else 0
#                 avg_max_drawdown = np.mean(max_drawdowns) if max_drawdowns else 0

#                 # ROI Calculation
#                 total_entry_value = sum(sum(trade.entry_price * trade.quantity for trade in pair) for pair in trade_pairs.values() if len(pair) == 2)
#                 roi = (total_profit_loss / total_entry_value) * 100 if total_entry_value > 0 else 0

#                 # Save to database
#                 SymbolStatistics.objects.update_or_create(
#                     backtest=backtest,
#                     correlated_pair=pair,
#                     strategy=backtest.strategy,
#                     action="PAIR_TRADING",
#                     defaults={
#                         'total_trades': total_trades,
#                         'win_rate': win_rate,
#                         'profit_loss': total_profit_loss,
#                         'average_holding_period': avg_holding_period,
#                         'total_roi': roi,
#                         'average_max_drawdown': avg_max_drawdown,
#                     }
#                 )

#                 logger.info(f"Calculated Pair Trading stats for {pair}")

#     else:
#         symbols = TradeHistory.objects.filter(backtest=backtest).values_list('symbol', flat=True).distinct()

#         for symbol in symbols:
#             for action in ["LONG", "SHORT"]:
#                 trades = TradeHistory.objects.filter(backtest=backtest, symbol=symbol, action=action, exit_price__isnull=False)

#                 if not trades.exists():
#                     continue

#                 total_trades = trades.count()
#                 profitable_trades = trades.filter(profit_loss__gt=0).count()
#                 win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0

#                 total_profit_loss = trades.aggregate(Sum('profit_loss'))['profit_loss__sum'] or 0

#                 holding_periods = [
#                     (trade.exit_date - trade.entry_date).days
#                     for trade in trades if trade.exit_date and trade.entry_date
#                 ]
#                 avg_holding_period = np.mean(holding_periods) if holding_periods else 0

#                 roi = (total_profit_loss / sum(trade.entry_price * trade.quantity for trade in trades)) * 100 if trades else 0

#                 max_drawdowns = trades.aggregate(Avg('max_drawdown'))['max_drawdown__avg'] or 0

#                 SymbolStatistics.objects.update_or_create(
#                     symbol_id=symbol,
#                     backtest=backtest,
#                     strategy=backtest.strategy,
#                     action=action,  # Separate LONG and SHORT
#                     defaults={
#                         'total_trades': total_trades,
#                         'win_rate': win_rate,
#                         'profit_loss': total_profit_loss,
#                         'average_holding_period': avg_holding_period,
#                         'total_roi': roi,
#                         'average_max_drawdown': max_drawdowns,
#                     }
#                 )

#                 logger.info(f"Symbol statistics calculated for {symbol} - {action}")        



def calculate_strategy_statistics(backtest):
    """
    Calculates and stores aggregated statistics for the overall strategy, 
    considering only symbols where the strategy is active for LONG or SHORT.
    """

    if(backtest.strategy.slug=='cointegration'):


        analyze_and_enable_strategies(backtest)
        strategy_symbols = StrategySymbol.objects.filter(
            strategy=backtest.strategy,
            correlated_pair__isnull=False
        ).select_related('symbol', 'correlated_pair')
        
       
        
        
        symbol_map = {
            (ss.symbol_id, ss.correlated_pair_id): ss
            for ss in strategy_symbols
        }

        correlated_pairs = CorrelatedPair.objects.select_related('symbol_1', 'symbol_2')

        for action in ["LONG", "SHORT", "PAIR_TRADING"]:
            valid_combinations = []

            for pair in correlated_pairs:
                s1_id = pair.symbol_1_id
                s2_id = pair.symbol_2_id
                pair_id = pair.id

                s1 = symbol_map.get((s1_id, pair_id))
                s2 = symbol_map.get((s2_id, pair_id))

                if not s1 or not s2:
                    continue

                if action == "LONG":
                    if (
                        s1.is_active_long and (
                            not s1.is_active_short or not s2.is_active_long or not s2.is_active_short
                        )
                    ):
                        valid_combinations.append((s1_id, pair_id))

                    if (
                        s2.is_active_long and (
                            not s2.is_active_short or not s1.is_active_long or not s1.is_active_short
                        )
                    ):
                        valid_combinations.append((s2_id, pair_id))

                elif action == "SHORT":
                    if (
                        s1.is_active_short and (
                            not s1.is_active_long or not s2.is_active_long or not s2.is_active_short
                        )
                    ):
                        valid_combinations.append((s1_id, pair_id))

                    if (
                        s2.is_active_short and (
                            not s2.is_active_long or not s1.is_active_long or not s1.is_active_short
                        )
                    ):
                        valid_combinations.append((s2_id, pair_id))

                elif action == "PAIR_TRADING":
                    if (
                        s1.is_active_long and s1.is_active_short and
                        s2.is_active_long and s2.is_active_short
                    ):
                        valid_combinations.append((s1_id, pair_id))
                        valid_combinations.append((s2_id, pair_id))

            # Now fetch matching SymbolStatistics for these combinations
            if not valid_combinations:
                logger.info(f"No valid symbol/pair combinations for {action}")
                continue

            if action == "PAIR_TRADING":
                stats_qs = SymbolStatistics.objects.filter(
                    backtest=backtest,
                    strategy=backtest.strategy,
                    action=action,
                    correlated_pair_id__in=[pair_id for _, pair_id in valid_combinations]
                )
            else:
                q_filter = Q()
                for symbol_id, pair_id in valid_combinations:
                    q_filter |= Q(symbol_id=symbol_id, correlated_pair_id=pair_id)

                stats_qs = SymbolStatistics.objects.filter(
                    backtest=backtest,
                    strategy=backtest.strategy,
                    action=action
                ).filter(q_filter)

            if not stats_qs.exists():
                logger.info(f"No SymbolStatistics found for action {action}")
                continue

            # Aggregate statistics from SymbolStatistics model
            total_trades = stats_qs.aggregate(Sum("total_trades"))["total_trades__sum"] or 0
            total_profit_loss = stats_qs.aggregate(Sum("profit_loss"))["profit_loss__sum"] or 0
            avg_holding_period = stats_qs.aggregate(Avg("average_holding_period"))["average_holding_period__avg"] or 0
            avg_drawdown = stats_qs.aggregate(Avg("average_max_drawdown"))["average_max_drawdown__avg"] or 0

            # Weighted average or simple mean depending on what's available
            win_rates = [s.win_rate for s in stats_qs if s.win_rate is not None]
            avg_win_rate = np.mean(win_rates) if win_rates else 0

            rois = [s.total_roi for s in stats_qs if s.total_roi is not None]
            avg_roi = np.mean(rois) if rois else 0

            StrategyStatistics.objects.update_or_create(
                strategy=backtest.strategy,
                backtest=backtest,
                action=action,
                defaults={
                    "total_trades": total_trades,
                    "win_rate": avg_win_rate,
                    "total_profit_loss": total_profit_loss,
                    "total_roi": avg_roi,
                    "average_holding_period": avg_holding_period,
                    "average_max_drawdown": avg_drawdown,
                },
            )

            logger.info(f"✅ Strategy stats saved for {action}")
    else:
        # Check if there are any active strategy symbols for mean-reverting strategy
        analyze_and_enable_strategies(backtest)
        active_long_symbols = StrategySymbol.objects.filter(
            strategy=backtest.strategy, 
            is_active_long=True
        ).count()
        
        active_short_symbols = StrategySymbol.objects.filter(
            strategy=backtest.strategy, 
            is_active_short=True
        ).count()
        
        # If no active symbols found, try to analyze and enable strategies
        if active_long_symbols == 0 and active_short_symbols == 0:
            logger.info(f"No active strategy symbols found for {backtest.strategy.name}. Running analyze_and_enable_strategies...")
            analyze_and_enable_strategies(backtest)
        
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


def calculate_strategy_statistics_by_id(backtest_id):
    """
    Calculate strategy statistics by backtest ID
    
    Args:
        backtest_id: The ID of the backtest to calculate statistics for
        
    Returns:
        dict: Result with success status and message
    """
    try:
        # Get the backtest object by ID
        backtest = BackTestingStrategy.objects.get(id=backtest_id)
        logger.info(f"Found backtest: {backtest.strategy.name} (ID: {backtest_id})")
        
        # Check if there are any trades for this backtest
        trade_count = TradeHistory.objects.filter(backtest=backtest).count()
        logger.info(f"Found {trade_count} trades for backtest ID {backtest_id}")
        
        if trade_count == 0:
            return {
                'success': False,
                'error': 'No trades found',
                'message': f'No trades found for backtest ID {backtest_id}. Cannot calculate statistics without trade data.'
            }
        
        # Call the original function
        try:
            calculate_strategy_statistics(backtest)
            logger.info(f"Successfully calculated strategy statistics for backtest ID: {backtest_id}")
            
            # Verify that statistics were created
            stats_count = StrategyStatistics.objects.filter(backtest=backtest).count()
            logger.info(f"Created {stats_count} strategy statistics records")
            
            return {
                'success': True,
                'message': f'Strategy statistics calculated successfully for backtest ID: {backtest_id} ({stats_count} records created)',
                'backtest_name': f"{backtest.strategy.name} - {backtest.name or 'Unnamed'}",
                'stats_count': stats_count
            }
            
        except Exception as calc_error:
            logger.error(f"Error in calculate_strategy_statistics: {str(calc_error)}")
            return {
                'success': False,
                'error': str(calc_error),
                'message': f'Error calculating strategy statistics: {str(calc_error)}'
            }
        
    except BackTestingStrategy.DoesNotExist:
        error_msg = f"Backtest with ID {backtest_id} not found"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'message': error_msg
        }
    except Exception as e:
        error_msg = f"Error calculating strategy statistics for backtest ID {backtest_id}: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            'success': False,
            'error': str(e),
            'message': error_msg
        }