import logging
from strategies.models import StrategySymbol,Strategy,CorrelatedPair
from strategies.strategy_logic import MeanRevertingStrategy,CoIntegrationStrategy
from symbols.models import Symbols,DailyPrice
from django.db.models import Q
import pandas as pd

logger = logging.getLogger(__name__)

def execute_strategies():
    
    strategy=Strategy.objects.get(slug='mean-reverting')
    strategy_symbols = StrategySymbol.objects.filter(Q(is_active_long=True) | Q(is_active_short=True), strategy=strategy)

    for strategy_symbol in strategy_symbols:
        MeanRevertingStrategy.execution(strategy_symbol.symbol.ticker,is_active_long=strategy_symbol.is_active_long,is_active_short=strategy_symbol.is_active_short, start_date="2013-01-01")
        


