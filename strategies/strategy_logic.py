from datetime import date
import logging
import numpy as np
import pandas as pd
from django.db import models
from .utils import StrategyUtils
from .models import CorrelatedPair
from backtesting.models import TradeHistory
from execution.models import TradeHistoryExec
from strategies.models import StrategySymbol
from symbols.utils import DailyPriceManager
from symbols.models import Symbols, DailyPrice
from execution.utils import ExecutionUtils
import statsmodels.api as sm

logger = logging.getLogger(__name__)

class CoIntegrationStrategy:
    def __init__(self, parameters):
        self.parameters = parameters

    def execute(self,df_1,df_2,Z,buy=False,last_action=''):
        
        Z_df = pd.DataFrame({'Close': Z})

        Z_df.index.name = 'Date'

        if buy==False and StrategyUtils.zscore(Z.values)[-1]<=-2.0   and StrategyUtils.check_johansen_test(df_1,df_2) :
            #Long Spread - long asset 2 short asset 1
            return "LONG"
        elif buy==False and   StrategyUtils.zscore(Z.values)[-1]>=2  and StrategyUtils.check_johansen_test(df_1,df_2):
            #"Short Spread - long asset 1 short asset 2 
            return "SHORT"
        elif buy==True and  last_action=="LONG" and (StrategyUtils.zscore(Z.values)[-1]>0):
            #Exiting from Long Spread
            return 'Exit'
        elif buy==True and  last_action=="SHORT" and (StrategyUtils.zscore(Z.values)[-1]<=0):
            #Exiting from Short Spread
            return 'Exit'            
        else:
            return 'None'


    def backtest(self, backtest, ticker_1,ticker_2, start_date, end_date=date.today()):     
        buy = False
        last_action = ""
        

        try:
            symbol_1 = Symbols.objects.get(ticker=ticker_1)
            symbol_2 = Symbols.objects.get(ticker=ticker_2)
        except Symbols.DoesNotExist:
           
            return f"Symbol {ticker_1} or {ticker_2} not found in database."

        try:
            correlated_pair = CorrelatedPair.objects.get(
             
                symbol_1=symbol_1,
                symbol_2=symbol_2
            )
        except CorrelatedPair.DoesNotExist:
           
            return f"No correlated pair found for {ticker_1} and {ticker_2}"


        #DailyPriceManager.insert_daily_price(symbol_1.ticker,"2013-01-01")
        #DailyPriceManager.insert_daily_price(symbol_2.ticker,"2013-01-01")
        historical_data_1 = DailyPrice.objects.filter(
            symbol=symbol_1, price_date__range=[start_date, end_date]
        ).order_by("price_date")

        historical_data_2 = DailyPrice.objects.filter(
            symbol=symbol_2, price_date__range=[start_date, end_date]
        ).order_by("price_date")        

        if not historical_data_1.exists() or not historical_data_2.exists() or len(historical_data_1)!=len(historical_data_2) :
          
            return f"No data found for {ticker_1} or {ticker_2} between {start_date} and {end_date}."     
 
        # Convert to DataFrame
        df_1 = pd.DataFrame.from_records(
            historical_data_1.values(
                "price_date", "open_price", "high_price", "low_price", "close_price", "volume"
            )
        )
        df_1.rename(
            columns={
                "price_date": "Date",
                "open_price": "Open",
                "high_price": "High",
                "low_price": "Low",
                "close_price": "Close",
                "volume": "Volume",
            },
            inplace=True,
        )

        df_2 = pd.DataFrame.from_records(
            historical_data_2.values(
                "price_date", "open_price", "high_price", "low_price", "close_price", "volume"
            )
        )
        df_2.rename(
            columns={
                "price_date": "Date",
                "open_price": "Open",
                "high_price": "High",
                "low_price": "Low",
                "close_price": "Close",
                "volume": "Volume",
            },
            inplace=True,
        )        

        
        # Split Data
        current_data_1, future_data_1 = StrategyUtils.train_test_split(df_1, split_ratio=0.5)           
        current_data_2, future_data_2 = StrategyUtils.train_test_split(df_2, split_ratio=0.5)           

        for i in range(len(future_data_1.index)):
            current_data_1 = pd.concat([current_data_1, pd.DataFrame(future_data_1.iloc[i]).transpose()], axis=0)
            current_data_2 = pd.concat([current_data_2, pd.DataFrame(future_data_2.iloc[i]).transpose()], axis=0)

            S1 = current_data_1['Close']
            S2 = current_data_2['Close']

            S1 = pd.to_numeric(S1, errors='coerce')
            S2 = pd.to_numeric(S2, errors='coerce')
 
        
          
            S1 = sm.add_constant(S1)
           
            results = sm.OLS(S2, S1).fit()
           
            S1 = current_data_1['Close']
        
            b = results.params["Close"]
          
            Z= S2 - b * S1
           
            signal = self.execute(current_data_1,current_data_2,Z, buy, last_action)

            if buy:
                current_low_price_1 = future_data_1['Low'].iloc[i]
                current_low_price_2 = future_data_2['Low'].iloc[i]
                
                current_high_price_1 = future_data_1['High'].iloc[i]
                current_high_price_2 = future_data_2['High'].iloc[i]

                if current_low_price_1 < lowest_price_1:
                    lowest_price_1 = current_low_price_1

                if current_high_price_1 > highest_price_1:
                    highest_price_1 = current_high_price_1

                if current_low_price_2 < lowest_price_2:
                    lowest_price_2 = current_low_price_2

                if current_high_price_2 > highest_price_2:
                    highest_price_2 = current_high_price_2      

            if signal == "LONG" and not buy:
               
                buy = True
                last_action = "LONG"
                lowest_price_1 = future_data_1["Close"].iloc[i]
                highest_price_1 = future_data_1["Close"].iloc[i]
                lowest_price_2 = future_data_2["Close"].iloc[i]
                highest_price_2 = future_data_2["Close"].iloc[i]                
                entry_price_1 = future_data_1["Close"].iloc[i] 
                entry_price_2 = future_data_2["Close"].iloc[i] 
               
                TradeHistory.objects.create(
                    backtest=backtest,
                    correlated_pair=correlated_pair,
                    symbol=symbol_1,
                    entry_date=future_data_1["Date"].iloc[i],
                    action="SHORT",
                    entry_price=future_data_1["Close"].iloc[i],
                    quantity=(100/future_data_1["Close"].iloc[i]),
                )   


                TradeHistory.objects.create(
                    backtest=backtest,
                    correlated_pair=correlated_pair,
                    symbol=symbol_2,
                    entry_date=future_data_2["Date"].iloc[i],
                    action="LONG",
                    entry_price=future_data_2["Close"].iloc[i],
                    quantity=(100/future_data_2["Close"].iloc[i]),
                )   
               

            elif signal == "SHORT" and not buy:
                buy = True
                last_action = "SHORT"
                lowest_price_1 = future_data_1["Close"].iloc[i]
                highest_price_1 = future_data_1["Close"].iloc[i]
                lowest_price_2 = future_data_2["Close"].iloc[i]
                highest_price_2 = future_data_2["Close"].iloc[i]                
                entry_price_1 = future_data_1["Close"].iloc[i] 
                entry_price_2 = future_data_2["Close"].iloc[i]     

                TradeHistory.objects.create(
                    backtest=backtest,
                    correlated_pair=correlated_pair,
                    symbol=symbol_1,
                    entry_date=future_data_1["Date"].iloc[i],
                    action="LONG",
                    entry_price=future_data_1["Close"].iloc[i],
                    quantity=(100/future_data_1["Close"].iloc[i]),
                )   


                TradeHistory.objects.create(
                    backtest=backtest,
                    symbol=symbol_2,
                    correlated_pair=correlated_pair,
                    entry_date=future_data_2["Date"].iloc[i],
                    action="SHORT",
                    entry_price=future_data_2["Close"].iloc[i],
                    quantity=(100/future_data_2["Close"].iloc[i]),
                )    
                logger.info(f"SHORT")
            elif signal == "Exit" and buy:     
                #adicionar correlated pair
                last_trade_1 = TradeHistory.objects.filter(
                    backtest=backtest, symbol=symbol_1, correlated_pair=correlated_pair, exit_date__isnull=True
                ).order_by("-entry_date").first()        

                last_trade_2 = TradeHistory.objects.filter(
                    backtest=backtest, correlated_pair=correlated_pair, symbol=symbol_2, exit_date__isnull=True
                ).order_by("-entry_date").first()               

                if last_trade_1 and last_trade_2:

                    exit_price_1 = future_data_1["Close"].iloc[i]
                    profit_loss_1 = (
                        (exit_price_1 - last_trade_1.entry_price) * last_trade_1.quantity
                        if last_trade_1.action == "LONG"
                        else (last_trade_1.entry_price - exit_price_1) * last_trade_1.quantity
                    )

                    exit_price_2 = future_data_2["Close"].iloc[i]
                    profit_loss_2 = (
                        (exit_price_2 - last_trade_2.entry_price) * last_trade_2.quantity
                        if last_trade_2.action == "LONG"
                        else (last_trade_2.entry_price - exit_price_2) * last_trade_2.quantity
                    )

                    # Update last trade with exit details
                    last_trade_1.exit_date = future_data_1["Date"].iloc[i]
                    last_trade_1.exit_price = exit_price_1
                    last_trade_1.profit_loss = profit_loss_1
                    last_trade_1.max_drawdown =  (highest_price_1 -entry_price_1) / entry_price_1 * 100 if last_trade_1.action == "SHORT" else (entry_price_1 - lowest_price_1) / entry_price_1 * 100

                    last_trade_2.exit_date = future_data_2["Date"].iloc[i]
                    last_trade_2.exit_price = exit_price_2
                    last_trade_2.profit_loss = profit_loss_2
                    last_trade_2.max_drawdown =  (highest_price_2 -entry_price_2) / entry_price_2 * 100 if last_trade_2.action == "SHORT" else (entry_price_2 - lowest_price_2) / entry_price_2 * 100



                    last_trade_1.save()
                    last_trade_2.save()


                    TradeHistory.objects.create(
                        backtest=backtest,
                        symbol=symbol_1,
                        correlated_pair=correlated_pair,
                        entry_date=last_trade_1.entry_date,
                        exit_date=future_data_1["Date"].iloc[i],
                        action="EXIT",
                        entry_price=last_trade_1.entry_price,
                        exit_price=exit_price_1,
                        quantity=last_trade_1.quantity,
                        profit_loss=profit_loss_1,
                        max_drawdown= last_trade_1.max_drawdown
                    )

                    TradeHistory.objects.create(
                        backtest=backtest,
                        symbol=symbol_2,
                        correlated_pair=correlated_pair,
                        entry_date=last_trade_2.entry_date,
                        exit_date=future_data_2["Date"].iloc[i],
                        action="EXIT",
                        entry_price=last_trade_2.entry_price,
                        exit_price=exit_price_2,
                        quantity=last_trade_2.quantity,
                        profit_loss=profit_loss_2,
                        max_drawdown= last_trade_2.max_drawdown
                    ) 
                    logger.info(f"exit")                   

                buy = False
                last_action = ""   

        return f"Backtest completed for {ticker_1} and {ticker_2} pairs ({start_date} - {end_date})."                                 


    def execution(self, correlated_pair,start_date, end_date=date.today()):


        
        last_action = ""
        symbol_1 = correlated_pair.symbol_1
        symbol_2 = correlated_pair.symbol_2

        is_avaliable_1 = symbol_1.slot_free ==True #slottfree
        is_avaliable_2 = symbol_2.slot_free ==True #slottfree 

        strategy_symbol_1_pair = StrategySymbol.objects.get(symbol=symbol_1 , correlated_pair=correlated_pair)
        strategy_symbol_2_pair = StrategySymbol.objects.get(symbol=symbol_2 , correlated_pair=correlated_pair)

        buy = strategy_symbol_1_pair.slot_free != True or strategy_symbol_2_pair.slot_free != True        

        DailyPriceManager.insert_daily_price(symbol_1.ticker,"2013-01-01")
        DailyPriceManager.insert_daily_price(symbol_2.ticker,"2013-01-01")
        historical_data_1 = DailyPrice.objects.filter(
            symbol=symbol_1, price_date__range=[start_date, end_date]
        ).order_by("price_date")

        historical_data_2 = DailyPrice.objects.filter(
            symbol=symbol_2, price_date__range=[start_date, end_date]
        ).order_by("price_date")        

        if not historical_data_1.exists() or not historical_data_2.exists() or len(historical_data_1)!=len(historical_data_2) :
          
            return f"No data found"     
 
        # Convert to DataFrame
        df_1 = pd.DataFrame.from_records(
            historical_data_1.values(
                "price_date", "open_price", "high_price", "low_price", "close_price", "volume"
            )
        )
        df_1.rename(
            columns={
                "price_date": "Date",
                "open_price": "Open",
                "high_price": "High",
                "low_price": "Low",
                "close_price": "Close",
                "volume": "Volume",
            },
            inplace=True,
        )

        df_2 = pd.DataFrame.from_records(
            historical_data_2.values(
                "price_date", "open_price", "high_price", "low_price", "close_price", "volume"
            )
        )
        df_2.rename(
            columns={
                "price_date": "Date",
                "open_price": "Open",
                "high_price": "High",
                "low_price": "Low",
                "close_price": "Close",
                "volume": "Volume",
            },
            inplace=True,
        )                

        S1 = df_1['Close']
        S2 = df_2['Close']

        S1 = pd.to_numeric(S1, errors='coerce')
        S2 = pd.to_numeric(S2, errors='coerce')

    
        
        S1 = sm.add_constant(S1)
        
        results = sm.OLS(S2, S1).fit()
        
        S1 = df_1['Close']
    
        b = results.params["Close"]
        
        Z= S2 - b * S1
        

        last_trade_1 = TradeHistoryExec.objects.filter(
                symbol=symbol_1, strategy=strategy_symbol_1_pair.strategy
            ).order_by('-created_at').first() 
                     
        last_trade_2 = TradeHistoryExec.objects.filter(
                symbol=symbol_2, strategy=strategy_symbol_2_pair.strategy
            ).order_by('-created_at').first()                      
        

        if (last_trade_2 and  last_trade_2.action =="LONG") or (last_trade_1 and  last_trade_1.action =="SHORT"):
            last_action="LONG"

        elif (last_trade_2 and  last_trade_2.action =="SHORT") or (last_trade_1 and  last_trade_1.action =="LONG"):
            last_action="SHORT"

        elif (last_trade_2 and last_trade_2.action =="EXIT") or (last_trade_1 and last_trade_1.action =="EXIT"):
            last_action="EXIT"            
        
        signal = self.execute(df_1,df_2,Z, buy, last_action)
        
        is_pair_trading = strategy_symbol_1_pair.is_active_long and strategy_symbol_1_pair.is_active_short and strategy_symbol_2_pair.is_active_long and strategy_symbol_2_pair.is_active_short

        is_pair_trading_active = strategy_symbol_1_pair.slot_free and strategy_symbol_2_pair.slot_free



        
        if signal == "LONG"  and not buy:
            
            if (is_avaliable_1 and strategy_symbol_1_pair.is_active_short and not is_pair_trading) or(is_avaliable_1 and is_avaliable_2 and is_pair_trading and is_pair_trading_active ):
                
                if(is_pair_trading and is_pair_trading_active):
                    action="PAIR_TRADING"
                    quantity=((100*ExecutionUtils.calc_betsize(strategy_symbol_1_pair,action))/df_1["Close"].iloc[-1])/2
                    bet_size = (ExecutionUtils.calc_betsize(strategy_symbol_1_pair,action)*100)/2   
                else:
                    action = "SHORT"    
                    quantity=((100*ExecutionUtils.calc_betsize(strategy_symbol_1_pair,action))/df_1["Close"].iloc[-1])
                    bet_size=ExecutionUtils.calc_betsize(strategy_symbol_1_pair,action)*100 

                TradeHistoryExec.objects.create(
                    strategy=strategy_symbol_1_pair.strategy,
                    correlated_pair=correlated_pair,
                    symbol=symbol_1,
                    entry_date=df_1["Date"].iloc[-1],
                    action="SHORT",
                    entry_price=df_1["Close"].iloc[-1],                    
                    quantity=quantity,
                    bet_size=bet_size 
                )   

                strategy_symbol_1_pair.slot_free=False
                symbol_1.slot_free=False
                strategy_symbol_1_pair.save()
                symbol_1.save()

            if (is_avaliable_2 and strategy_symbol_2_pair.is_active_long and not is_pair_trading) or(is_avaliable_1 and is_avaliable_2 and is_pair_trading and is_pair_trading_active ):

                if(is_pair_trading and is_pair_trading_active):
                    action="PAIR_TRADING"
                    quantity=((100*ExecutionUtils.calc_betsize(strategy_symbol_2_pair,action))/df_2["Close"].iloc[-1])/2
                    bet_size=(ExecutionUtils.calc_betsize(strategy_symbol_2_pair,action)*100)/2
                else:
                    action = "LONG"  
                    quantity=((100*ExecutionUtils.calc_betsize(strategy_symbol_2_pair,action))/df_2["Close"].iloc[-1])
                    bet_size=ExecutionUtils.calc_betsize(strategy_symbol_2_pair,action)*100 

                TradeHistoryExec.objects.create(
                    strategy = strategy_symbol_2_pair.strategy,
                    correlated_pair=correlated_pair,
                    symbol=symbol_2,
                    entry_date=df_2["Date"].iloc[-1],
                    action="LONG",
                    entry_price=df_2["Close"].iloc[-1],                    
                    quantity=quantity,
                    bet_size=bet_size                       
                )   

                strategy_symbol_2_pair.slot_free=False
                symbol_2.slot_free=False
                strategy_symbol_2_pair.save()
                symbol_2.save()
                
                

        elif signal == "SHORT"  and not buy:

            
            
            if (is_avaliable_1 and strategy_symbol_1_pair.is_active_long and not is_pair_trading) or (is_avaliable_1 and is_avaliable_2 and is_pair_trading and is_pair_trading_active ):

                if(is_pair_trading and is_pair_trading_active):
                    action="PAIR_TRADING"
                    quantity=((100*ExecutionUtils.calc_betsize(strategy_symbol_1_pair,action))/df_1["Close"].iloc[-1])/2
                    bet_size=(ExecutionUtils.calc_betsize(strategy_symbol_1_pair,action)*100)/2                  
                else:
                    action = "LONG"              
                    quantity=((100*ExecutionUtils.calc_betsize(strategy_symbol_1_pair,action))/df_1["Close"].iloc[-1])
                    bet_size=ExecutionUtils.calc_betsize(strategy_symbol_1_pair,action)*100      

                TradeHistoryExec.objects.create(
                    strategy=strategy_symbol_1_pair.strategy,
                    correlated_pair=correlated_pair,
                    symbol=symbol_1,
                    entry_date=df_1["Date"].iloc[-1],
                    action="LONG",
                    entry_price=df_1["Close"].iloc[-1],
                    quantity=quantity,
                    bet_size=bet_size
                )   

                strategy_symbol_1_pair.slot_free=False
                symbol_1.slot_free=False
                strategy_symbol_1_pair.save()
                symbol_1.save()

            if (is_avaliable_2 and strategy_symbol_2_pair.is_active_short and not is_pair_trading) or (is_avaliable_1 and is_avaliable_2 and is_pair_trading and is_pair_trading_active ):

                if(is_pair_trading and is_pair_trading_active):
                    action="PAIR_TRADING"
                    quantity=((100*ExecutionUtils.calc_betsize(strategy_symbol_2_pair,action))/df_2["Close"].iloc[-1])/2
                    bet_size=(ExecutionUtils.calc_betsize(strategy_symbol_2_pair,action)*100)/2                      
                else:
                    action = "SHORT"                       
                    quantity=((100*ExecutionUtils.calc_betsize(strategy_symbol_2_pair,action))/df_2["Close"].iloc[-1])
                    bet_size=ExecutionUtils.calc_betsize(strategy_symbol_2_pair,action)*100                      

                TradeHistoryExec.objects.create(
                    strategy = strategy_symbol_2_pair.strategy,
                    correlated_pair=correlated_pair,
                    symbol=symbol_2,
                    entry_date=df_2["Date"].iloc[-1],
                    action="SHORT",
                    entry_price=df_2["Close"].iloc[-1],
                    quantity=quantity,
                    bet_size=bet_size
                )   

                strategy_symbol_2_pair.slot_free=False
                symbol_2.slot_free=False
                strategy_symbol_2_pair.save()
                symbol_2.save()


        elif signal == "Exit" and buy:     
            #Isto pode dar conflito se por alguma razao decidir desaticvar um estrategia que ja tenha dados
            last_trade_1 = TradeHistoryExec.objects.filter(
                strategy=strategy_symbol_1_pair.strategy, symbol=symbol_1, correlated_pair=correlated_pair, exit_date__isnull=True
            ).order_by("-entry_date").first()        

            last_trade_2 = TradeHistoryExec.objects.filter(
                strategy=strategy_symbol_2_pair.strategy, correlated_pair=correlated_pair, symbol=symbol_2, exit_date__isnull=True
            ).order_by("-entry_date").first()               

            if last_trade_1:

                exit_price_1 = df_1["Close"].iloc[-1]
                profit_loss_1 = (
                    (exit_price_1 - last_trade_1.entry_price) * last_trade_1.quantity
                    if last_trade_1.action == "LONG"
                    else (last_trade_1.entry_price - exit_price_1) * last_trade_1.quantity
                )

                last_trade_1.exit_date = df_1["Date"].iloc[-1]
                last_trade_1.exit_price = exit_price_1
                last_trade_1.profit_loss = profit_loss_1
                last_trade_1.save()

                TradeHistoryExec.objects.create(
                    strategy=strategy_symbol_1_pair.strategy,
                    symbol=symbol_1,
                    correlated_pair=correlated_pair,
                    entry_date=last_trade_1.entry_date,
                    exit_date=df_1["Date"].iloc[-1],
                    action="EXIT",
                    entry_price=last_trade_1.entry_price,
                    exit_price=exit_price_1,
                    quantity=last_trade_1.quantity,
                    profit_loss=profit_loss_1,
                    bet_size=last_trade_1.bet_size
                    
                )  
                strategy_symbol_1_pair.slot_free = True        
                symbol_1.slot_free=True
                         

            if last_trade_2:
                exit_price_2 = df_2["Close"].iloc[-1]
                profit_loss_2 = (
                    (exit_price_2 - last_trade_2.entry_price) * last_trade_2.quantity
                    if last_trade_2.action == "LONG"
                    else (last_trade_2.entry_price - exit_price_2) * last_trade_2.quantity
                )

                last_trade_2.exit_date = df_2["Date"].iloc[-1]
                last_trade_2.exit_price = exit_price_2
                last_trade_2.profit_loss = profit_loss_2
                last_trade_2.save()
                
                TradeHistoryExec.objects.create(
                    strategy=strategy_symbol_2_pair.strategy,
                    symbol=symbol_2,
                    correlated_pair=correlated_pair,
                    entry_date=last_trade_2.entry_date,
                    exit_date=df_2["Date"].iloc[-1],
                    action="EXIT",
                    entry_price=last_trade_2.entry_price,
                    exit_price=exit_price_2,
                    quantity=last_trade_2.quantity,
                    profit_loss=profit_loss_2,
                    bet_size=last_trade_2.bet_size
                    
                ) 
            
                strategy_symbol_2_pair.slot_free = True        
                symbol_2.slot_free=True            
            



class MeanRevertingStrategy:
    def __init__(self, parameters):
        self.parameters = parameters

    def execute(self, df, buy=False, last_action=""):
        """
        Executes the mean-reverting strategy on the given DataFrame.
        Determines whether to go LONG, SHORT, or EXIT.
        """
        df = StrategyUtils.calculate_ratio(df)

        if df["ratio"].dropna().empty:
            return "None"

        percentiles = [5, 10, 50, 90, 95]
        p = np.percentile(df["ratio"].dropna(), percentiles)

        if not StrategyUtils.check_stationary(df):
            return "None"  # Only trade if stationary

        if not buy and df["ratio"].iloc[-1] <= p[0]:
            return "LONG"

        elif not buy and df["ratio"].iloc[-1] >= p[-1]:
            return "SHORT"

        elif buy and df["ratio"].iloc[-1] >= p[2] and last_action == "LONG":
            return "Exit"

        elif buy and df["ratio"].iloc[-1] <= p[2] and last_action == "SHORT":
            return "Exit"

        return "None"

    def backtest(self, backtest, ticker, start_date, end_date=date.today()):
        """
        Simulates market data updates by looping through future data,
        making trade decisions at each step.
        """
        buy = False
        last_action = ""
        print(ticker)
        # Fetch symbol
        try:
            symbol = Symbols.objects.get(ticker=ticker)
        except Symbols.DoesNotExist:
            return f"Symbol {ticker} not found in database."

        # Fetch historical price data
        historical_data = DailyPrice.objects.filter(
            symbol=symbol, price_date__range=[start_date, end_date]
        ).order_by("price_date")

        if not historical_data.exists():
            return f"No data found for {ticker} between {start_date} and {end_date}."

        # Convert to DataFrame
        df = pd.DataFrame.from_records(
            historical_data.values(
                "price_date", "open_price", "high_price", "low_price", "close_price", "volume"
            )
        )
        df.rename(
            columns={
                "price_date": "Date",
                "open_price": "Open",
                "high_price": "High",
                "low_price": "Low",
                "close_price": "Close",
                "volume": "Volume",
            },
            inplace=True,
        )

        
        # Split Data
        current_data, future_data = StrategyUtils.train_test_split(df, split_ratio=0.5)

        # Backtest loop
        for i in range(len(future_data.index)):
            # Append new data
            current_data = pd.concat([current_data, pd.DataFrame(future_data.iloc[i]).transpose()], axis=0)

            # Check for signals
            signal = self.execute(current_data, buy, last_action)

            if buy:
                current_low_price = future_data['Low'].iloc[i]
                current_high_price = future_data['High'].iloc[i]
                if current_low_price < lowest_price:
                    lowest_price = current_low_price

                if current_high_price > highest_price:
                    highest_price = current_high_price

            if signal == "LONG" and not buy:
                buy = True
                last_action = "LONG"
                lowest_price = future_data["Close"].iloc[i]
                highest_price = future_data["Close"].iloc[i]
                entry_price = future_data["Close"].iloc[i] 
                TradeHistory.objects.create(
                    backtest=backtest,
                    symbol=symbol,
                    entry_date=future_data["Date"].iloc[i],
                    action="LONG",
                    entry_price=future_data["Close"].iloc[i],
                    quantity=(100/future_data["Close"].iloc[i]),
                )

            elif signal == "SHORT" and not buy:
                buy = True
                last_action = "SHORT"
                lowest_price = future_data["Close"].iloc[i]
                highest_price = future_data["Close"].iloc[i]      
                entry_price = future_data["Close"].iloc[i]          
                TradeHistory.objects.create(
                    backtest=backtest,
                    symbol=symbol,
                    entry_date=future_data["Date"].iloc[i],
                    action="SHORT",
                    entry_price=future_data["Close"].iloc[i],
                    quantity=(100/future_data["Close"].iloc[i]),
                )

            elif signal == "Exit" and buy:
                # Fetch the last open trade from the database
                last_trade = TradeHistory.objects.filter(
                    backtest=backtest, symbol=symbol, exit_date__isnull=True
                ).order_by("-entry_date").first()

                if last_trade:
                    exit_price = future_data["Close"].iloc[i]
                    profit_loss = (
                        (exit_price - last_trade.entry_price) * last_trade.quantity
                        if last_trade.action == "LONG"
                        else (last_trade.entry_price - exit_price) * last_trade.quantity
                    )

                    # Update last trade with exit details
                    last_trade.exit_date = future_data["Date"].iloc[i]
                    last_trade.exit_price = exit_price
                    last_trade.profit_loss = profit_loss
                    last_trade.max_drawdown =  (highest_price -entry_price) / entry_price * 100 if last_trade.action == "SHORT" else (entry_price - lowest_price) / entry_price * 100
                    last_trade.save()

                    # Create a new record for the exit action
                    TradeHistory.objects.create(
                        backtest=backtest,
                        symbol=symbol,
                        entry_date=last_trade.entry_date,
                        exit_date=future_data["Date"].iloc[i],
                        action="EXIT",
                        entry_price=last_trade.entry_price,
                        exit_price=exit_price,
                        quantity=last_trade.quantity,
                        profit_loss=profit_loss,
                        max_drawdown= (highest_price -entry_price) / entry_price * 100 if last_trade.action == "SHORT" else (entry_price - lowest_price) / entry_price * 100
                    )

                buy = False
                last_action = ""




        return f"Backtest completed for {ticker} ({start_date} - {end_date})."


    def execution(self, strategy_symbol,symbol,is_active_long,is_active_short,start_date, end_date=date.today()):
        #todo - if the entry signal is still valid for the 4 or 3 previous days skip
        print(symbol.ticker)
        is_avaliable = symbol.slot_free ==True #slottfree

        buy = strategy_symbol.slot_free != True
        
        ticker=symbol.ticker
        
        DailyPriceManager.insert_daily_price(symbol.ticker,"2013-01-01")
        # Fetch historical price data
        historical_data = DailyPrice.objects.filter(
            symbol=symbol, price_date__range=[start_date, end_date]
        ).order_by("price_date")

        if not historical_data.exists():
            return f"No data found for {ticker} between {start_date} and {end_date}."

        # Convert to DataFrame
        df = pd.DataFrame.from_records(
            historical_data.values(
                "price_date", "open_price", "high_price", "low_price", "close_price", "volume"
            )
        )
        df.rename(
            columns={
                "price_date": "Date",
                "open_price": "Open",
                "high_price": "High",
                "low_price": "Low",
                "close_price": "Close",
                "volume": "Volume",
            },
            inplace=True,
        )

        last_trade = TradeHistoryExec.objects.filter(
                symbol=symbol, strategy=strategy_symbol.strategy
            ).order_by('-created_at').first() 
        if last_trade:
            last_action = last_trade.action   
        else:
            last_action = ""                
        
        signal = self.execute(df, buy, last_action)

        if signal == "LONG" and not buy and is_avaliable and is_active_long:
          
            TradeHistoryExec.objects.create(
                strategy=strategy_symbol.strategy,
                symbol=symbol,
                entry_date=df["Date"].iloc[-1],
                action="LONG",
                entry_price=df["Close"].iloc[-1],
                quantity=((100*ExecutionUtils.calc_betsize(strategy_symbol,signal))/df["Close"].iloc[-1]),
                bet_size=ExecutionUtils.calc_betsize(strategy_symbol,signal)*100
            )      

            symbol.slot_free = False  
            strategy_symbol.slot_free = False
            symbol.save()
            strategy_symbol.save()


        elif signal == "SHORT" and not buy and is_avaliable and is_active_short:
          
            TradeHistoryExec.objects.create(
                strategy=strategy_symbol.strategy,
                symbol=symbol,
                entry_date=df["Date"].iloc[-1],
                action="SHORT",
                entry_price=df["Close"].iloc[-1],
                quantity=((100*ExecutionUtils.calc_betsize(strategy_symbol,signal))/df["Close"].iloc[-1]),
                bet_size=ExecutionUtils.calc_betsize(strategy_symbol,signal)*100
            )      

            symbol.slot_free = False  
            strategy_symbol.slot_free = False
            symbol.save()
            strategy_symbol.save()         

        elif signal == "Exit" and buy:
            # Fetch the last open trade from the database
            last_trade = TradeHistoryExec.objects.filter(
                strategy=strategy_symbol.strategy, symbol=symbol, exit_date__isnull=True
            ).order_by("-entry_date").first()

            if last_trade:
                exit_price = df["Close"].iloc[-1]
                profit_loss = (
                    (exit_price - last_trade.entry_price) * last_trade.quantity
                    if last_trade.action == "LONG"
                    else (last_trade.entry_price - exit_price) * last_trade.quantity
                )

                # Update last trade with exit details
                last_trade.exit_date = df["Date"].iloc[-1]
                last_trade.exit_price = exit_price
                last_trade.profit_loss = profit_loss                
                last_trade.save()

                # Create a new record for the exit action
                TradeHistoryExec.objects.create(
                    strategy=strategy_symbol.strategy,
                    symbol=symbol,
                    entry_date=last_trade.entry_date,
                    exit_date=df["Date"].iloc[-1],
                    action="EXIT",
                    entry_price=last_trade.entry_price,
                    exit_price=exit_price,
                    quantity=last_trade.quantity,
                    profit_loss=profit_loss,
                    bet_size=last_trade.bet_size
                    
                )    

                strategy_symbol.slot_free = True        
                symbol.slot_free=True
                symbol.save()
                strategy_symbol.save()


class MACrossoverStrategy:
    def __init__(self, parameters):
        self.parameters = parameters
        self.ma_long_window = "200"
        self.ma_short_window = "60"
        self.wait_ma_crossed = False
        self.initial_perc_diff=False
        self.peak_found=False
        self.last_short_ma=False

    def execute(self, df, buy=False, last_action=""):

        if 'MA_'+self.ma_short_window in df.columns:
            df.drop(columns=['MA_'+self.ma_short_window, 'MA_'+self.ma_long_window,'peak_min','peak_max',"slope","strong_slope"], inplace=True)

        df = StrategyUtils.moving_average(df,self.ma_short_window)
        df = StrategyUtils.moving_average(df,self.ma_long_window)    
        df = StrategyUtils.peak_finder(df, 'MA_'+self.ma_short_window,0.95)        
        df['slope'] =StrategyUtils.get_ma_slope(df, ma_column='MA_'+self.ma_short_window)
        df['strong_slope'] = StrategyUtils.is_slope_strong(df['slope'], lookback=5)        

        if self.wait_ma_crossed==True and  (df['MA_'+self.ma_short_window].iloc[-1]<=(df['MA_'+self.ma_long_window].iloc[-1])):
            self.wait_ma_crossed= False   

        if buy==False and not self.initial_perc_diff and df['MA_'+self.ma_short_window].iloc[-1]>df['MA_'+self.ma_long_window].iloc[-1] :
            self.initial_perc_diff = (df["Close"].iloc[-1] -df['MA_'+self.ma_long_window].iloc[-1])/df['MA_'+self.ma_long_window].iloc[-1]    

        elif  df['MA_'+self.ma_short_window].iloc[-1]< df['MA_'+self.ma_long_window].iloc[-1]  :
            self.initial_perc_diff = False
            self.last_short_ma = False              

        if self.initial_perc_diff and df['peak_max'].iloc[-10:].eq(1).any():
            self.peak_found = True
        else:
            self.peak_found=False                   



        if  buy==False and df['MA_'+self.ma_short_window].iloc[-1]>(df['MA_'+self.ma_long_window].iloc[-1] )  and not self.peak_found and not StrategyUtils.check_stationary(df) and df["strong_slope"].iloc[-1]  and df["Low"].iloc[-1]> df['MA_'+self.ma_short_window].iloc[-1] and  df["Low"].iloc[-1]> df['MA_'+self.ma_long_window].iloc[-1] and (df["Close"].iloc[-1] - df['MA_'+self.ma_long_window].iloc[-1])/df['MA_'+self.ma_long_window].iloc[-1] > 0.10 and (df["Close"].iloc[-1] -df['MA_'+self.ma_long_window].iloc[-1])/df['MA_'+self.ma_long_window].iloc[-1]> self.initial_perc_diff  and df['MA_'+self.ma_short_window].iloc[-1] > self.last_short_ma:            
            return "LONG"
        
        elif buy==True and   (df['MA_'+self.ma_short_window].iloc[-1]<df['MA_'+self.ma_long_window].iloc[-1] or df['peak_max'].iloc[-2:].eq(1).any() )  and last_action=="LONG":
            
            if df['peak_max'].iloc[-2:].eq(1).any():
                self.wait_ma_crossed=True            

            if self.initial_perc_diff and df["Close"].iloc[-1] -df['MA_'+self.ma_long_window].iloc[-1] > self.initial_perc_diff :
                self.initial_perc_diff = (df["Close"].iloc[-1] -df['MA_'+self.ma_long_window].iloc[-1])/df['MA_'+self.ma_long_window].iloc[-1] 

            if self.initial_perc_diff  and self.last_short_ma:
                self.last_short_ma = df['MA_'+self.ma_short_window].iloc[-1]  

            return "Exit" 
        else:
            return "None"                                            
        

    def backtest(self, backtest, ticker, start_date, end_date=date.today()):
        """
        Simulates market data updates by looping through future data,
        making trade decisions at each step.
        """
        buy = False
        last_action = ""
        print(ticker)
        # Fetch symbol
        try:
            symbol = Symbols.objects.get(ticker=ticker)
        except Symbols.DoesNotExist:
            return f"Symbol {ticker} not found in database."
        
        #DailyPriceManager.insert_daily_price(symbol.ticker,"2013-01-01")
        # Fetch historical price data
        historical_data = DailyPrice.objects.filter(
            symbol=symbol, price_date__range=[start_date, end_date]
        ).order_by("price_date")

        if not historical_data.exists():
            return f"No data found for {ticker} between {start_date} and {end_date}."

        # Convert to DataFrame
        df = pd.DataFrame.from_records(
            historical_data.values(
                "price_date", "open_price", "high_price", "low_price", "close_price", "volume"
            )
        )
        df.rename(
            columns={
                "price_date": "Date",
                "open_price": "Open",
                "high_price": "High",
                "low_price": "Low",
                "close_price": "Close",
                "volume": "Volume",
            },
            inplace=True,
        )

        
        # Split Data
        current_data, future_data = StrategyUtils.train_test_split(df, split_ratio=0.25)

        # Backtest loop
        for i in range(len(future_data.index)):
            # Append new data
            current_data = pd.concat([current_data, pd.DataFrame(future_data.iloc[i]).transpose()], axis=0)

            # Check for signals
            signal = self.execute(current_data, buy, last_action)

            if buy:
                current_low_price = future_data['Low'].iloc[i]
                current_high_price = future_data['High'].iloc[i]
                if current_low_price < lowest_price:
                    lowest_price = current_low_price

                if current_high_price > highest_price:
                    highest_price = current_high_price

            if signal == "LONG" and not buy:
                buy = True
                last_action = "LONG"
                lowest_price = future_data["Close"].iloc[i]
                highest_price = future_data["Close"].iloc[i]
                entry_price = future_data["Close"].iloc[i] 
                TradeHistory.objects.create(
                    backtest=backtest,
                    symbol=symbol,
                    entry_date=future_data["Date"].iloc[i],
                    action="LONG",
                    entry_price=future_data["Close"].iloc[i],
                    quantity=(100/future_data["Close"].iloc[i]),
                )

            elif signal == "SHORT" and not buy:
                buy = True
                last_action = "SHORT"
                lowest_price = future_data["Close"].iloc[i]
                highest_price = future_data["Close"].iloc[i]      
                entry_price = future_data["Close"].iloc[i]          
                TradeHistory.objects.create(
                    backtest=backtest,
                    symbol=symbol,
                    entry_date=future_data["Date"].iloc[i],
                    action="SHORT",
                    entry_price=future_data["Close"].iloc[i],
                    quantity=(100/future_data["Close"].iloc[i]),
                )

            elif signal == "Exit" and buy:
                # Fetch the last open trade from the database
                last_trade = TradeHistory.objects.filter(
                    backtest=backtest, symbol=symbol, exit_date__isnull=True
                ).order_by("-entry_date").first()

                if last_trade:
                    exit_price = future_data["Close"].iloc[i]
                    profit_loss = (
                        (exit_price - last_trade.entry_price) * last_trade.quantity
                        if last_trade.action == "LONG"
                        else (last_trade.entry_price - exit_price) * last_trade.quantity
                    )

                    # Update last trade with exit details
                    last_trade.exit_date = future_data["Date"].iloc[i]
                    last_trade.exit_price = exit_price
                    last_trade.profit_loss = profit_loss
                    last_trade.max_drawdown =  (highest_price -entry_price) / entry_price * 100 if last_trade.action == "SHORT" else (entry_price - lowest_price) / entry_price * 100
                    last_trade.save()

                    # Create a new record for the exit action
                    TradeHistory.objects.create(
                        backtest=backtest,
                        symbol=symbol,
                        entry_date=last_trade.entry_date,
                        exit_date=future_data["Date"].iloc[i],
                        action="EXIT",
                        entry_price=last_trade.entry_price,
                        exit_price=exit_price,
                        quantity=last_trade.quantity,
                        profit_loss=profit_loss,
                        max_drawdown= (highest_price -entry_price) / entry_price * 100 if last_trade.action == "SHORT" else (entry_price - lowest_price) / entry_price * 100
                    )

                buy = False
                last_action = ""