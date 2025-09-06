import numpy as np
from django.db.models import Avg, Count, Sum, F,Q

from .models import SymbolStatistics,TradeHistory
from strategies.models import CorrelatedPair,Strategy

import logging

class BackTestUtils:

    @staticmethod    
    def calculate_symbol_statistics(backtest):
        logger = logging.getLogger(__name__)
        """
        Calculates and stores statistics for each symbol in a backtest, separated by LONG and SHORT actions.
        """
        if(backtest.strategy.slug=='cointegration'):
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
                                exchange=backtest.exchange,
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
                        exchange=backtest.exchange,
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

        else:
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
                        exchange=backtest.exchange,
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