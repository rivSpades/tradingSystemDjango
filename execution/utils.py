from decimal import Decimal
from backtesting.models import SymbolStatistics,StrategyStatistics
class ExecutionUtils:
    """
    Utility class for strategy-related statistical functions.
    """


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