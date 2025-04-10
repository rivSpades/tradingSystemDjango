import logging
from backtesting.models import SymbolStatistics
from strategies.models import StrategySymbol
from backtesting.backtest_logic import calculate_strategy_statistics
logger = logging.getLogger(__name__)

def analyze_and_enable_strategies(backtest):
    """
    Analyze SymbolStatistics and enable strategies for symbols based on defined filters.
    """

    if backtest.strategy.slug=="cointegration":
        pairs = SymbolStatistics.objects.filter(backtest=backtest, action="PAIR_TRADING")
        eligible_trades={}
        print(pairs)
        for pair_stat in pairs:
            pair = pair_stat.correlated_pair
            strategy = pair_stat.strategy
            action = pair_stat.action

            avg_roi_per_trade = pair_stat.total_roi 
            avg_holding_period = pair_stat.average_holding_period
            total_trades = pair_stat.total_trades
            win_rate = pair_stat.win_rate
            total_profit_loss = pair_stat.profit_loss

            pair_trading_is_eligible = (
                5 <= avg_roi_per_trade < 1000 and
                avg_holding_period <= 70 and
                total_trades >=3 and
                win_rate >= 80 and
                total_profit_loss > 0
            )


            eligible_trades= {
                "PAIR_TRADING": {
                 
                    "avg_roi": avg_roi_per_trade if pair_trading_is_eligible else 0,
                },
                pair.symbol_1.ticker: {},
                pair.symbol_2.ticker: {},
            }
            
           
            symbols = SymbolStatistics.objects.filter(backtest=backtest, correlated_pair=pair, action__in=["LONG","SHORT"])
            for symbol_stat in symbols:
                action = symbol_stat.action
                symbol = symbol_stat.symbol
                strategy = symbol_stat.strategy
                
                avg_roi_per_trade = symbol_stat.total_roi 
                avg_holding_period = symbol_stat.average_holding_period
                total_trades = symbol_stat.total_trades
                win_rate = symbol_stat.win_rate
                total_profit_loss = symbol_stat.profit_loss    

                is_eligible = (
                5 <= avg_roi_per_trade < 1000 and
                avg_holding_period <= 70 and
                total_trades >= 5 and
                win_rate >= 80 and
                total_profit_loss > 0
            )      
                eligible_trades[symbol.ticker][action] = {
                  
                        
                        "avg_roi": avg_roi_per_trade if is_eligible else 0,
                   
                }
         
            print(eligible_trades)
            roi_long_1 = eligible_trades.get(pair.symbol_1.ticker, {}).get("LONG", {}).get("avg_roi", 0)
            roi_short_1 = eligible_trades.get(pair.symbol_1.ticker, {}).get("SHORT", {}).get("avg_roi", 0)
            roi_long_2 = eligible_trades.get(pair.symbol_2.ticker, {}).get("LONG", {}).get("avg_roi", 0)
            roi_short_2 = eligible_trades.get(pair.symbol_2.ticker, {}).get("SHORT", {}).get("avg_roi", 0)

            total_individual_roi = roi_long_1 + roi_short_1 + roi_long_2 + roi_short_2
            pair_trading_roi = eligible_trades["PAIR_TRADING"]["avg_roi"]

            if pair_trading_roi > total_individual_roi:
          
                strategy_symbol_1, created = StrategySymbol.objects.get_or_create(
                strategy=strategy, symbol=pair.symbol_1,
                correlated_pair=pair
            )

   
                strategy_symbol_1.is_active_long = True
                
                strategy_symbol_1.is_active_short = True
                
                strategy_symbol_1.save()  

                strategy_symbol_2, created = StrategySymbol.objects.get_or_create(
                strategy=strategy, symbol=pair.symbol_2,
                correlated_pair=pair
            )

   
                strategy_symbol_2.is_active_long = True
                
                strategy_symbol_2.is_active_short = True
                
                strategy_symbol_2.save()                  

            else:

                strategy_symbol_1, created = StrategySymbol.objects.get_or_create(
                strategy=strategy, symbol=pair.symbol_1,
                correlated_pair=pair
            )

   
                strategy_symbol_1.is_active_long = roi_long_1 >0
                
                strategy_symbol_1.is_active_short = roi_short_1 >0
                
                strategy_symbol_1.save()  

                strategy_symbol_2, created = StrategySymbol.objects.get_or_create(
                strategy=strategy, symbol=pair.symbol_2,
                correlated_pair=pair
            )

   
                strategy_symbol_2.is_active_long = roi_long_2 >0
                
                strategy_symbol_2.is_active_short = roi_short_2>0
                
                strategy_symbol_2.save()                    
                


    else:

        symbols = SymbolStatistics.objects.filter(backtest=backtest)

        for symbol_stat in symbols:
            # Extract values
            action = symbol_stat.action
            symbol = symbol_stat.symbol
            strategy = symbol_stat.strategy
            
            avg_roi_per_trade = symbol_stat.total_roi 
            avg_holding_period = symbol_stat.average_holding_period
            total_trades = symbol_stat.total_trades
            win_rate = symbol_stat.win_rate
            total_profit_loss = symbol_stat.profit_loss

            # Apply Filters
            is_eligible = (
                5 <= avg_roi_per_trade < 1000 and
                avg_holding_period < 70 and
                total_trades >= 3 and
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
