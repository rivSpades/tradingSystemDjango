from decimal import Decimal
from backtesting.models import SymbolStatistics,StrategyStatistics,BackTestingStrategy,TradeHistory
from datetime import date
from .broker_utils import BrokerUtils
class ExecutionUtils:
    """
    Utility class for strategy-related statistical functions.
    """

    @staticmethod
    def last_backtest_trade_valid(strategy, symbol=None ,correlated_pair=None):
         backtest = BackTestingStrategy.objects.get(strategy=strategy)            
         if strategy.name=="cointegration":
             
             #execute_backtest(strategy_id='cointegration',start_date="2023-01-01",correlated_pair_list=[correlated_pair])
             
                 
             last_trade = TradeHistory.objects.filter(
                 backtest=backtest, symbol=symbol, correlated_pair=correlated_pair, exit_date__isnull=True
             ).order_by("-entry_date").first()               
         else:
             
             last_trade = TradeHistory.objects.filter(
                 backtest=backtest,
                 symbol=symbol,
                 exit_date__isnull=True  
             ).order_by("-entry_date").first()
         

         print("last_trade")
         print(last_trade)
         if last_trade:
             days_since_entry = (date.today() - last_trade.entry_date).days
             print("day since last entry were "+str(days_since_entry))
             if days_since_entry > 5:
                 
                 return False  # Not a valid signal
         return True  # Valid signal
    
    @staticmethod
    def calc_betsize(symbol_strategy,action):
        k_f = Decimal('0.10')  

        strategy_statistics = StrategyStatistics.objects.get(strategy=symbol_strategy.strategy ,action=action)
        #atencao pode haver mais que um output porque pode haver varios backtesting para a mesma estrategia. usar .filter no futuro
        if symbol_strategy.strategy.slug == 'mean-reverting':
            symbol_statistics= SymbolStatistics.objects.get(symbol=symbol_strategy.symbol , strategy = symbol_strategy.strategy, action=action)

            avg_roi = Decimal(min(symbol_statistics.total_roi,strategy_statistics.total_roi))/Decimal('100')
            avg_max_drawdown = Decimal(symbol_statistics.average_max_drawdown)/Decimal('100')
            avg_win_rate = Decimal(min(strategy_statistics.win_rate,symbol_statistics.win_rate))/Decimal('100')                



            
            
        elif symbol_strategy.strategy.slug == 'cointegration':    
            if action=="PAIR_TRADING":
                symbol_statistics= SymbolStatistics.objects.get(correlated_pair=symbol_strategy.correlated_pair , strategy = symbol_strategy.strategy, action=action)    
                
            else:
                symbol_statistics= SymbolStatistics.objects.get(correlated_pair=symbol_strategy.correlated_pair , strategy = symbol_strategy.strategy, action=action,symbol=symbol_strategy.symbol)    

            try:
                avg_roi = Decimal(min(symbol_statistics.total_roi,strategy_statistics.total_roi))/Decimal('100')
                avg_max_drawdown = Decimal(symbol_statistics.average_max_drawdown)/Decimal('100')
                avg_win_rate = Decimal(min(strategy_statistics.win_rate,symbol_statistics.win_rate))/Decimal('100')      
            except:
                avg_roi = Decimal(strategy_statistics.total_roi)/Decimal('100')
                avg_max_drawdown = Decimal(strategy_statistics.average_max_drawdown)/Decimal('100')
                avg_win_rate = Decimal(strategy_statistics.win_rate)/Decimal('100')                         
            
        if avg_max_drawdown==0:
            avg_max_drawdown=Decimal(0.00000001)


        ratio = avg_roi / avg_max_drawdown

        f = avg_win_rate - ((Decimal('1') - avg_win_rate) / ratio)
        f = f * k_f

        bet_size = f  #exemplo 20% = 0.20 , vai retornar 0.20
        return float(bet_size)
    
    @staticmethod
    def create_order(symbol,quantity,action,t_id=None):
        broker=symbol.broker
        utils = BrokerUtils(broker.name, broker.api_key, broker.secret_key)
        response = utils.create_order(symbol.ticker, quantity, action)
        print(response)

    @staticmethod
    def close_position(symbol):
        broker=symbol.broker
        utils = BrokerUtils(broker.name, broker.api_key, broker.secret_key)
        response=utils.close_position(symbol.ticker)        
        print(response)
        
    @staticmethod
    def account_info(symbol):
        broker = symbol.broker
        utils = BrokerUtils(broker.name, broker.api_key, broker.secret_key)
        response = utils.get_account_info()
        return response
