import logging
from strategies.models import StrategySymbol,Strategy,CorrelatedPair
from strategies.strategy_logic import MeanRevertingStrategy,CoIntegrationStrategy
from symbols.models import Symbols,DailyPrice
from django.db.models import Q
import pandas as pd
from datetime import date
from backtesting.models import BackTestingStrategy
from backtesting.utils import BackTestUtils
logger = logging.getLogger(__name__)

def execute_strategies(end_date=None):
    
    strategy=Strategy.objects.get(slug='mean-reverting')
    strategy_symbols = StrategySymbol.objects.filter(Q(is_active_long=True) | Q(is_active_short=True), strategy=strategy)
    strategy_instance = MeanRevertingStrategy(strategy.parameters)
    for strategy_symbol in strategy_symbols:
                
                strategy_instance.execution(
                strategy_symbol,
                strategy_symbol.symbol,
                strategy_symbol.is_active_long,
                strategy_symbol.is_active_short,
                start_date="2013-01-01",
                end_date= end_date if end_date else date.today()
            )

    strategy=Strategy.objects.get(slug='cointegration')        
    strategy_instance = CoIntegrationStrategy(strategy.parameters)
    correlated_pair_ids = StrategySymbol.objects.filter(Q(is_active_long=True) | Q(is_active_short=True),correlated_pair__isnull=False).values_list('correlated_pair', flat=True).distinct()
    correlated_pairs = CorrelatedPair.objects.filter(id__in=correlated_pair_ids)

    for correlated_pair in correlated_pairs:
        strategy_instance.execution(correlated_pair,start_date="2013-01-01", end_date= end_date if end_date else date.today())            

    #backtest = BackTestingStrategy.objects.get(strategy=strategy)
    #BackTestUtils.calculate_symbol_statistics(backtest)     
